const assert = require('node:assert/strict');
const { test, before, after } = require('node:test');
const { randomUUID } = require('node:crypto');
const { mkdirSync } = require('node:fs');
const { join } = require('node:path');
const { chromium } = require('playwright-core');
const { createRoomsServer } = require('../rooms-server.cjs');
let browser;
before(async () => { browser = await chromium.launch({ executablePath: process.env.CHROMIUM_PATH || '/usr/bin/chromium', headless: true, args: ['--no-sandbox'] }); });
after(async () => { await browser?.close(); });
async function fixture(t, viewport = { width: 1280, height: 900 }) {
  const runtime = createRoomsServer(), errors = [];
  await new Promise(r => runtime.server.listen(0, '127.0.0.1', r));
  const context = await browser.newContext({ viewport });
  t.after(async () => { await context.close(); await new Promise(r => runtime.io.close(r)); assert.deepEqual(errors, []); });
  const page = await context.newPage(); page.on('pageerror', e => errors.push(e.message));
  const person = runtime.store.session('Mara · fictional fixture'), room = runtime.store.createRoom('Cistern handoff');
  const append = (body, kind = 'note', roomId = room.id) => runtime.store.append(person, { roomId, kind, body, clientId: randomUUID() }).message;
  runtime.store.work.join(room.id, person);
  const url = `http://127.0.0.1:${runtime.server.address().port}/studio/`;
  const enter = async () => {
    await page.goto(url); await page.evaluate(p => localStorage.setItem('p11-room-identity', JSON.stringify(p)), person);
    await page.goto(url + '#' + room.id); await page.reload(); await page.waitForFunction(() => room && !joining && socket.connected);
  };
  return { runtime, page, person, room, append, enter };
}
async function search(page, q, kind = 'all') {
  await page.locator('#search-tab').click(); await page.locator('#search-query').fill(q);
  await page.locator('#search-kind').selectOption(kind); await page.locator('#search-submit').click();
  await page.waitForFunction(() => !byId('search-submit').disabled);
}
async function capture(page, name) {
  if (process.env.ROOMS_SEARCH_CAPTURE_DIR) { mkdirSync(process.env.ROOMS_SEARCH_CAPTURE_DIR, { recursive: true }); await page.locator('#search-tab').scrollIntoViewIfNeeded(); await page.screenshot({ path: join(process.env.ROOMS_SEARCH_CAPTURE_DIR, name), fullPage: false }); }
}

test('old blocker context distinguishes historical and current work while preserving both drafts', async t => {
  const f = await fixture(t), s = f.runtime.store;
  const decision = f.append('Inspect the western valve before returning the loan.', 'decision');
  let action = s.work.apply(f.person, { op: 'create', roomId: f.room.id, clientId: randomUUID(), sourceId: decision.id, title: 'Return the borrowed pump', ownerId: f.person.id }).action;
  const update = changes => { action = s.work.apply(f.person, { op: 'update', roomId: f.room.id, clientId: randomUUID(), actionId: action.id, expectedRevision: action.revision, title: action.title, ownerId: action.owner_id, status: action.status, note: action.note, ...changes }).action; };
  update({ status: 'blocked', note: 'Válvula presa no depósito. Waiting for a replacement.' });
  for (let i = 0; i < 60; i++) update({ status: 'doing', note: `Pressure check ${i}` });
  update({ status: 'done', note: 'Replacement fitted; borrowed pump returned.' });
  for (let i = 0; i < 360; i++) f.append(`Recent saved observation ${i}`, i < 125 ? 'decision' : 'note');
  await f.enter();
  assert.equal(await f.page.locator(`#entries [data-id="${decision.id}"]`).count(), 0);
  assert.equal(await f.page.locator(`#decisions [data-id="${decision.id}"]`).count(), 0);
  await f.page.locator('#body').fill('My unsent discussion draft');
  await f.page.locator('#actions-tab').click(); await f.page.locator('#new-action').click();
  await f.page.locator('#action-title').fill('My unsaved follow-up'); await f.page.locator('#action-close').click();
  const work = await f.page.evaluate(() => JSON.stringify(draft().work));
  await search(f.page, 'DEPOSITO valvula', 'action');
  assert.equal(await f.page.locator('#search-results li').count(), 1);
  assert.match(await f.page.locator('#search-results').textContent(), /revision 2 · Blocked/);
  await f.page.locator('#search-results button').click(); await f.page.locator('#search-context').waitFor();
  assert.match(await f.page.locator('#search-context-body').textContent(), /western valve/);
  assert.match(await f.page.locator('#search-context-body .context-action').textContent(), /Done.*revision 63/s);
  assert.match(await f.page.locator('#search-context-body [data-selected=true]').textContent(), /Válvula presa/);
  assert.equal(await f.page.locator('#search-context-title').evaluate(e => e === document.activeElement), true);
  await f.page.locator('#search-context-back').press('Enter');
  assert.equal(await f.page.locator('#search-results button').evaluate(e => e === document.activeElement), true);
  await capture(f.page, 'search-history.png');
  if(process.env.ROOMS_SEARCH_CAPTURE_DIR)await f.page.locator('#search-context').screenshot({path:join(process.env.ROOMS_SEARCH_CAPTURE_DIR,'search-context.png')});
  await f.page.locator('#search-context-body .context-action button').click(); await f.page.locator('#action-panel').waitFor();
  assert.equal(await f.page.evaluate(() => JSON.stringify(draft().work)), work);
  await f.page.locator('#conversation-tab').click(); assert.equal(await f.page.locator('#body').inputValue(), 'My unsent discussion draft');
  assert.equal(s.export(f.room.id).actions.length, 1);
  await search(f.page, 'western loan', 'decision'); await f.page.locator('#search-results button').click(); await f.page.locator('#search-context').waitFor();
  assert.equal(await f.page.locator('#search-context-body [data-selected=true] .decision-action').count(), 1);
});

test('mobile literal search keeps pinned pages, signals real arrivals and refreshes explicitly', async t => {
  const f = await fixture(t, { width: 390, height: 844 });
  for (let i = 0; i < 61; i++) f.append(`<b>Câble_%</b> return record ${i}`);
  const other = f.runtime.store.createRoom('Other room'); f.append('<b>Câble_%</b> other-room secret', 'note', other.id);
  await f.enter(); await search(f.page, 'cable_%');
  assert.match(await f.page.locator('#search-status').textContent(), /1–20 of 61/);
  assert.equal(await f.page.locator('#search-results b').count(), 0);
  assert.ok(!(await f.page.locator('#search-results').textContent()).includes('other-room secret'));
  const first = await f.page.locator('#search-results li').evaluateAll(es => es.map(e => e.dataset.id));
  const message = f.append('<b>Câble_%</b> arrived while searching');
  f.runtime.io.of('/studio').to(f.room.id).emit('project entry', message);
  await f.page.locator('#search-stale').waitFor();
  await f.page.locator('#search-next').click(); await f.page.waitForFunction(() => byId('search-status').textContent.startsWith('21–40'));
  await f.page.locator('#search-prev').click(); await f.page.waitForFunction(() => byId('search-status').textContent.startsWith('1–20'));
  assert.deepEqual(await f.page.locator('#search-results li').evaluateAll(es => es.map(e => e.dataset.id)), first);
  // Snapshot pages must keep the refresh signal until a new search, including Previous.
  assert.equal(await f.page.locator('#search-stale').isVisible(), true);
  await f.page.locator('#search-refresh').click(); await f.page.waitForFunction(() => byId('search-status').textContent.includes('of 62'));
  assert.equal(await f.page.locator('#search-stale').isVisible(), false);
  await f.page.locator('#search-results button').first().click(); await f.page.locator('#search-context').waitFor();
  assert.equal(await f.page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true);
  await capture(f.page, 'search-mobile.png');
  await search(f.page, 'word-with-no-match'); assert.match(await f.page.locator('#search-status').textContent(), /No matches/);
  assert.equal(await f.page.locator('#search-next').isEnabled(), false);
});

test('late search and context responses cannot cross a project or participant switch', async t => {
  const f = await fixture(t); f.append('Valve needle'); const other = f.runtime.store.createRoom('Other project');
  await f.enter(); let release, intercepted, finished;
  const gate = new Promise(r => { release = r; }); const seen = new Promise(r => { intercepted = r; }); const done = new Promise(r => { finished = r; });
  await f.page.route('**/api/studio/rooms/*/search?*', async route => { const response = await route.fetch(); intercepted(); await gate; await route.fulfill({ response }); finished(); });
  await f.page.locator('#search-tab').click(); await f.page.locator('#search-query').fill('needle'); await f.page.locator('#search-submit').click(); await seen;
  await f.page.locator('#rooms button').filter({ hasText: 'Other project' }).click(); await f.page.waitForFunction(id => room?.id === id && !joining, other.id); release();
  await done; await f.page.unroute('**/api/studio/rooms/*/search?*');
  await search(f.page, 'needle'); assert.match(await f.page.locator('#search-status').textContent(), /No matches/);
  await f.page.locator('#rooms button').filter({ hasText: 'Cistern handoff' }).click(); await f.page.waitForFunction(id => room?.id === id && !joining, f.room.id);
  await search(f.page, 'needle');
  let releaseContext, sawContext, finishedContext;
  const contextGate = new Promise(r => { releaseContext = r; }); const contextSeen = new Promise(r => { sawContext = r; }); const contextDone = new Promise(r => { finishedContext = r; });
  await f.page.route('**/api/studio/rooms/*/context/*/*', async route => { const response = await route.fetch(); sawContext(); await contextGate; await route.fulfill({ response }); finishedContext(); });
  await f.page.locator('#search-results button').click(); await contextSeen; await f.page.locator('#change').click(); releaseContext();
  await contextDone; await f.page.unroute('**/api/studio/rooms/*/context/*/*');
  assert.equal(await f.page.locator('#search-context').isVisible(), false); assert.equal(await f.page.locator('#welcome').isVisible(), true);
  assert.equal(await f.page.locator('#search-context-body').textContent(), '');
});
