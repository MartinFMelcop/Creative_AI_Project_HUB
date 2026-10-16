'use strict';
const assert = require('node:assert/strict');
const { test, before, after } = require('node:test');
const { randomUUID } = require('node:crypto');
const { readFileSync, mkdirSync } = require('node:fs');
const { join } = require('node:path');
const { chromium } = require('playwright-core');
const { createRoomsServer } = require('../rooms-server.cjs');

const baselineClient = process.env.ROOMS_HISTORY_BASELINE_CLIENT;
const captureDirectory = process.env.ROOMS_HISTORY_CAPTURE_DIR;
const historyURL = /\/api\/studio\/rooms\/[^/]+\/history(?:\?|$)/;
let browser;
before(async () => {
  browser = await chromium.launch({
    executablePath: process.env.CHROMIUM_PATH || '/usr/bin/chromium',
    headless: true, args: ['--no-sandbox']
  });
});
after(async () => { await browser?.close(); });

async function fixture(t, viewport = { width: 1280, height: 900 }) {
  const runtime = createRoomsServer(), contexts = [], errors = [];
  await new Promise(resolve => runtime.server.listen(0, '127.0.0.1', resolve));
  t.after(async () => {
    for (const context of contexts) await context.close();
    await new Promise(resolve => runtime.io.close(resolve));
    assert.deepEqual(errors, []);
  });
  const person = runtime.store.session('Reader · fictional fixture');
  const room = runtime.store.createRoom('Chronological handover');
  const other = runtime.store.createRoom('Interleaved project');
  const messages = [];
  for (let index = 0; index < 650; index++) {
    messages.push(runtime.store.append(person, {
      roomId: room.id, clientId: randomUUID(), kind: index % 17 === 0 ? 'decision' : 'note',
      body: 'Archive entry ' + index
    }).message);
    runtime.store.append(person, {
      roomId: other.id, clientId: randomUUID(), kind: 'note', body: 'Other project entry ' + index
    });
  }
  const url = 'http://127.0.0.1:' + runtime.server.address().port + '/studio/';
  async function pageFor(participant = person) {
    const context = await browser.newContext({ viewport });
    contexts.push(context);
    const page = await context.newPage();
    page.on('pageerror', error => errors.push(error.message));
    if (baselineClient) {
      await page.route('**/studio/client.js', route => route.fulfill({
        contentType: 'application/javascript', body: readFileSync(baselineClient, 'utf8')
      }));
    }
    await page.goto(url);
    await page.evaluate(value => localStorage.setItem('p11-room-identity', JSON.stringify(value)), participant);
    await page.goto(url + '#' + room.id);
    await page.reload();
    await page.waitForFunction(id => room?.id === id && !joining && socket?.connected && entries.length === 50, room.id);
    return page;
  }
  return {
    runtime, room, other, person, messages, ids: messages.map(message => message.id),
    page: await pageFor(), pageFor,
    allIds: () => runtime.store.export(room.id).entries.map(message => message.id)
  };
}
const visibleIds = page => page.locator('#entries > li').evaluateAll(nodes => nodes.map(node => Number(node.dataset.id)));
async function expectIds(page, expected) {
  await page.waitForFunction(values => {
    const actual = [...document.querySelectorAll('#entries > li')].map(node => Number(node.dataset.id));
    return actual.length === values.length && actual.every((id, index) => id === values[index]);
  }, expected);
  assert.deepEqual(await visibleIds(page), expected);
  assert.ok(expected.length <= 300, 'The conversation DOM must stay bounded.');
}
async function older(f) {
  const current = await visibleIds(f.page);
  const previous = f.allIds().filter(id => id < current[0]).slice(-50);
  assert.ok(previous.length, 'Test requested an existing earlier page.');
  await f.page.locator('#older').click();
  const expected = [...previous, ...current].slice(0, 300);
  await expectIds(f.page, expected);
  return expected;
}
async function newer(f) {
  const current = await visibleIds(f.page);
  const following = f.allIds().filter(id => id > current.at(-1)).slice(0, 50);
  assert.ok(following.length, 'Test requested an existing newer page.');
  await f.page.locator('#newer').click();
  const expected = [...current, ...following].slice(-300);
  await expectIds(f.page, expected);
  return expected;
}
async function latest(f) {
  const expected = f.allIds().slice(-50);
  await f.page.locator('#latest').click();
  await expectIds(f.page, expected);
  return expected;
}
async function capture(page, name) {
  if (!captureDirectory) return;
  mkdirSync(captureDirectory, { recursive: true });
  await page.screenshot({ path: join(captureDirectory, name), fullPage: false });
}
async function topAnchor(page) {
  return page.locator('#entries').evaluate(list => {
    list.scrollTop = 0;
    const node = list.firstElementChild;
    return { id: Number(node.dataset.id), offset: node.getBoundingClientRect().top - list.getBoundingClientRect().top };
  });
}
async function assertAnchor(page, anchor) {
  const node = page.locator('#entries > li[data-id="' + anchor.id + '"]');
  assert.equal(await node.count(), 1, 'The first visible historical entry must remain present.');
  const offset = await node.evaluate(element => element.getBoundingClientRect().top -
    document.querySelector('#entries').getBoundingClientRect().top);
  assert.ok(Math.abs(offset - anchor.offset) <= 2, 'A live arrival must not move the historical reading anchor.');
}

test('keyboard history boundaries preserve a surviving decision control across variable-height rows',
  { skip: !!baselineClient, timeout: 60000 }, async t => {
    const f = await fixture(t);
    await f.page.evaluate(() => {
      const rows = [...document.querySelectorAll('#entries > li')];
      rows.forEach((row, index) => { if(index % 3 === 0) row.style.paddingBlock = '2rem'; });
      const decision = rows.find(row => row.querySelector('button'));
      decision.querySelector('button').focus();
    });
    const focused = await f.page.evaluate(() => Number(document.activeElement.closest('li').dataset.id));
    // A request can complete while a decision control, rather than its paging button, owns focus.
    await f.page.evaluate(() => loadHistory('older'));
    assert.equal(await f.page.evaluate(() => Number(document.activeElement.closest('li').dataset.id)), focused);
    assert.equal(await f.page.locator('#entries > li[data-id="'+focused+'"] button').isVisible(), true);
    for(let count=0;(await visibleIds(f.page))[0]!==f.ids[0];count++) {
      assert.ok(count<20);
      await f.page.locator('#older').focus();await f.page.keyboard.press('Enter');
      await f.page.waitForFunction(() => !historyRequest);
      if(await f.page.locator('#older').isVisible())
        assert.equal(await f.page.locator('#older').evaluate(node => node===document.activeElement), true);
    }
    assert.equal(await f.page.locator('#older').isVisible(), false);
    assert.equal(await f.page.locator('#entries').evaluate(node => node===document.activeElement), true);
    await f.page.locator('#latest').focus();await f.page.keyboard.press('Space');
    await expectIds(f.page, f.allIds().slice(-50));
    assert.equal(await f.page.locator('#entries').evaluate(node => node===document.activeElement), true);
  });

test('baseline probe records the deliberate 300-entry stop and loss of the oldest reading anchor on arrival',
  { skip: !baselineClient, timeout: 60000 }, async t => {
    const f = await fixture(t);
    for (let count = 0; count < 5; count++) {
      const length = (count + 2) * 50;
      await f.page.locator('#older').click();
      await f.page.waitForFunction(expected => entries.length === expected, length);
    }
    assert.deepEqual(await visibleIds(f.page), f.ids.slice(-300));
    assert.equal(await f.page.locator('#older').isVisible(), false);
    assert.match(await f.page.locator('#room-hint').textContent(), /300.*Search record/);
    const anchor = await topAnchor(f.page);
    const writer = await f.pageFor(f.runtime.store.session('Writer · fictional fixture'));
    await writer.locator('#body').fill('A real socket arrival during historical reading');
    await writer.locator('#send').click();
    await f.page.waitForFunction(id => !document.querySelector('#entries > li[data-id="' + id + '"]'), anchor.id);
    assert.equal(await f.page.locator('#entries > li[data-id="' + anchor.id + '"]').count(), 0);
    assert.equal(await f.page.locator('#entries > li').count(), 300);
    await capture(f.page, 'baseline-cap-arrival.png');
    console.log(JSON.stringify({
      evidence: 'baseline-history-runtime', storedBefore: 650, rendered: 300,
      olderControlHidden: true, oldestVisibleAnchorEvicted: true,
      scope: 'Controlled SQLite fixture and actual Chromium/socket execution; no human-use claim'
    }));
  });

test('read all 650 entries in both directions with a bounded DOM and preserve discussion, action and search drafts',
  { skip: !!baselineClient, timeout: 90000 }, async t => {
    const f = await fixture(t);
    await f.page.locator('#body').fill('Unsent discussion while reading the earlier account');
    await f.page.locator('#kind').selectOption('decision');
    await f.page.locator('#actions-tab').click();
    await f.page.locator('#new-action').click();
    await f.page.locator('#action-title').fill('Unsaved historical follow-up');
    await f.page.locator('#action-note').fill('Keep this draft while paging.');
    await f.page.locator('#action-close').click();
    await f.page.locator('#search-tab').click();
    await f.page.locator('#search-query').fill('Archive');
    await f.page.locator('#search-submit').click();
    await f.page.waitForFunction(() => !document.querySelector('#search-submit').disabled &&
      document.querySelectorAll('#search-results > li').length === 20);
    const searchRows = await f.page.locator('#search-results > li').evaluateAll(nodes => nodes.map(node => node.dataset.id));
    await f.page.locator('#conversation-tab').click();

    const trace = [];
    for (let count = 0; (await visibleIds(f.page))[0] !== f.ids[0]; count++) {
      assert.ok(count < 20, 'Earlier navigation must reach the first saved entry.');
      const values = await older(f); trace.push({ direction: 'older', first: values[0], last: values.at(-1), size: values.length });
    }
    assert.equal(await f.page.locator('#older').isVisible(), false);
    await topAnchor(f.page);
    await capture(f.page, 'history-first-entry.png');
    for (let count = 0; (await visibleIds(f.page)).at(-1) !== f.ids.at(-1); count++) {
      assert.ok(count < 20, 'Newer navigation must reach the latest saved entry.');
      const values = await newer(f); trace.push({ direction: 'newer', first: values[0], last: values.at(-1), size: values.length });
    }
    await older(f);
    await latest(f);
    assert.equal(await f.page.locator('#body').inputValue(), 'Unsent discussion while reading the earlier account');
    assert.equal(await f.page.locator('#kind').inputValue(), 'decision');
    await f.page.locator('#actions-tab').click();
    await f.page.locator('#action-resume').click();
    assert.equal(await f.page.locator('#action-title').inputValue(), 'Unsaved historical follow-up');
    assert.equal(await f.page.locator('#action-note').inputValue(), 'Keep this draft while paging.');
    await f.page.locator('#action-close').click();
    await f.page.locator('#search-tab').click();
    assert.equal(await f.page.locator('#search-query').inputValue(), 'Archive');
    assert.deepEqual(await f.page.locator('#search-results > li').evaluateAll(nodes => nodes.map(node => node.dataset.id)), searchRows);
    assert.equal(f.runtime.store.export(f.room.id).entries.length, 650);
    assert.equal(f.runtime.store.export(f.room.id).actions.length, 0);
    console.log(JSON.stringify({ evidence: 'bidirectional-history-runtime', stored: 650, maximumDOM: 300, trace }));
  });

test('a real second-client arrival preserves the oldest loaded reading anchor until newer or latest is requested',
  { skip: !!baselineClient, timeout: 60000 }, async t => {
    const f = await fixture(t, { width: 390, height: 844 });
    for (let count = 0; count < 5; count++) await older(f);
    const before = await visibleIds(f.page), anchor = await topAnchor(f.page);
    const writer = await f.pageFor(f.runtime.store.session('Writer · fictional fixture'));
    await writer.locator('#body').fill('A newly saved discussion while the reader is at the old boundary');
    await writer.locator('#send').click();
    await f.page.waitForFunction(() => !document.querySelector('#newer').disabled &&
      !document.querySelector('#newer').hidden);
    assert.deepEqual(await visibleIds(f.page), before);
    await assertAnchor(f.page, anchor);
    assert.equal(await f.page.locator('#latest').isVisible(), true);
    assert.ok(await f.page.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
    await capture(f.page, 'history-mobile-new-entry.png');
    await f.page.locator('#actions-tab').click();
    await writer.locator('#body').fill('Another arrival while the conversation is hidden by the action board');
    await writer.locator('#send').click();
    await writer.waitForFunction(() => entries.some(entry => entry.body.startsWith('Another arrival while')));
    await f.page.waitForFunction(id => latestKnown === id, f.allIds().at(-1));
    assert.deepEqual(await visibleIds(f.page), before);
    await f.page.locator('#conversation-tab').click();
    await assertAnchor(f.page, anchor);
    await newer(f);
    assert.equal((await visibleIds(f.page)).at(-1), f.allIds().at(-1));
    await older(f);
    await latest(f);
    assert.equal((await visibleIds(f.page)).at(-1), f.allIds().at(-1));
    const currentEnd = await visibleIds(f.page);
    assert.equal(await f.page.evaluate(() => hasNewer), false);
    await f.page.locator('#actions-tab').click();
    await writer.locator('#body').fill('A hidden current-end conversation must remain unchanged');
    await writer.locator('#send').click();
    await writer.waitForFunction(() => entries.some(entry => entry.body.startsWith('A hidden current-end')));
    await f.page.waitForFunction(id => latestKnown === id, f.allIds().at(-1));
    assert.deepEqual(await visibleIds(f.page), currentEnd);
    await f.page.locator('#conversation-tab').click();
    await newer(f);
    assert.equal((await visibleIds(f.page)).at(-1), f.allIds().at(-1));
  });

test('a delayed own-send acknowledgement resolves its attempt without discarding newer typing or replacing historical rows',
  { skip: !!baselineClient, timeout: 60000 }, async t => {
    const f = await fixture(t);
    for (let count = 0; count < 5; count++) await older(f);
    const before = await visibleIds(f.page), anchor = await topAnchor(f.page);
    const serverSocket = [...f.runtime.io.of('/studio').sockets.values()]
      .find(socket => socket.data.session.id === f.person.id);
    serverSocket.removeAllListeners('project entry');
    let saved;
    const received = new Promise(resolve => { saved = resolve; });
    // Deliberately withhold both broadcast and acknowledgement after a real DB commit.
    serverSocket.on('project entry', (payload, acknowledge) => {
      const result = f.runtime.store.append(serverSocket.data.session, payload);
      saved({ result, acknowledge });
    });
    await f.page.locator('#body').fill('Earlier saved attempt with delayed acknowledgement');
    await f.page.locator('#send').click();
    const held = await received;
    await f.page.locator('#pending').waitFor();
    await f.page.locator('#body').fill('Newer typing must remain');
    held.acknowledge({ ok: true, ...held.result });
    await f.page.locator('#pending').waitFor({ state: 'hidden' });
    assert.equal(await f.page.locator('#body').inputValue(), 'Newer typing must remain');
    assert.deepEqual(await visibleIds(f.page), before);
    await assertAnchor(f.page, anchor);
    assert.equal(f.runtime.store.export(f.room.id).entries.filter(entry =>
      entry.body === 'Earlier saved attempt with delayed acknowledgement').length, 1);
    await latest(f);
    assert.equal((await visibleIds(f.page)).filter(id => id === held.result.message.id).length, 1);
    assert.equal(await f.page.locator('#body').inputValue(), 'Newer typing must remain');
  });

test('failed paging preserves the current window and cursor, and a delayed page cannot cross a project switch',
  { skip: !!baselineClient, timeout: 60000 }, async t => {
    const f = await fixture(t), initial = await visibleIds(f.page);
    await f.page.locator('#body').fill('Draft kept after a failed read');
    await f.page.route(historyURL, route => route.fulfill({
      status: 503, contentType: 'application/json', body: JSON.stringify({ error: 'Controlled history failure' })
    }), { times: 1 });
    await f.page.locator('#older').click();
    await f.page.waitForFunction(() => document.querySelector('#feedback').textContent.includes('Controlled history failure'));
    assert.deepEqual(await visibleIds(f.page), initial);
    assert.equal(await f.page.locator('#older').isEnabled(), true);
    assert.equal(await f.page.locator('#body').inputValue(), 'Draft kept after a failed read');
    await older(f);

    let release, seen, finished;
    const gate = new Promise(resolve => { release = resolve; });
    const intercepted = new Promise(resolve => { seen = resolve; });
    const complete = new Promise(resolve => { finished = resolve; });
    await f.page.route(historyURL, async route => {
      const response = await route.fetch(); seen();
      await gate; await route.fulfill({ response }); finished();
    }, { times: 1 });
    await f.page.locator('#older').click(); await intercepted;
    await f.page.locator('#rooms button').filter({ hasText: 'Interleaved project' }).click();
    await f.page.waitForFunction(id => room?.id === id && !joining, f.other.id);
    await f.page.locator('#body').fill('Other project draft');
    const otherRows = await visibleIds(f.page);
    release(); await complete;
    // Wait for the fulfilled request and its continuation, without assuming a client variable name.
    await f.page.evaluate(() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve))));
    assert.equal(await f.page.evaluate(() => room.id), f.other.id);
    assert.deepEqual(await visibleIds(f.page), otherRows);
    assert.equal(await f.page.locator('#body').inputValue(), 'Other project draft');
    assert.ok((await f.page.locator('#entries').textContent()).includes('Other project entry'));
    assert.equal((await f.page.locator('#entries').textContent()).includes('Archive entry'), false);
    await f.page.locator('#rooms button').filter({ hasText: 'Chronological handover' }).click();
    await f.page.waitForFunction(id => room?.id === id && !joining, f.room.id);
    assert.equal(await f.page.locator('#body').inputValue(), 'Draft kept after a failed read');
  });

// Delayed snapshots must not claim control of an editor the reader used meanwhile.
test('a delayed return to latest preserves composer focus and signals arrivals newer than its snapshot',
  { skip: !!baselineClient, timeout: 60000 }, async t => {
    const f = await fixture(t);
    for (let count = 0; count < 6; count++) await older(f);
    const snapshotIds = f.allIds().slice(-50);
    let release, seen, finished;
    const gate = new Promise(resolve => { release = resolve; });
    const intercepted = new Promise(resolve => { seen = resolve; });
    const complete = new Promise(resolve => { finished = resolve; });
    await f.page.route(historyURL, async route => {
      const response = await route.fetch(); seen();
      await gate; await route.fulfill({ response }); finished();
    }, { times: 1 });
    await f.page.locator('#latest').click(); await intercepted;
    await f.page.locator('#body').fill('Continue this draft while the latest snapshot is loading');
    const writer = await f.pageFor(f.runtime.store.session('Concurrent writer · fictional fixture'));
    await writer.locator('#body').fill('Saved after the delayed snapshot was taken');
    await writer.locator('#send').click();
    await writer.waitForFunction(() => entries.some(entry => entry.body === 'Saved after the delayed snapshot was taken'));
    await f.page.waitForFunction(id => latestKnown === id, f.allIds().at(-1));
    release(); await complete;
    await expectIds(f.page, snapshotIds);
    assert.equal(await f.page.locator('#body').inputValue(), 'Continue this draft while the latest snapshot is loading');
    assert.equal(await f.page.locator('#body').evaluate(node => node === document.activeElement), true);
    assert.equal(await f.page.locator('#latest').isVisible(), true);
    assert.equal(await f.page.locator('#newer').isVisible(), true);
    assert.match(await f.page.locator('#history-status').textContent(), /Newer entries available/);
    await newer(f);
    assert.equal((await visibleIds(f.page)).at(-1), f.allIds().at(-1));
    assert.equal(await f.page.locator('#body').inputValue(), 'Continue this draft while the latest snapshot is loading');
  });

for (const boundary of ['participant change', 'disconnect and reconnect']) {
  test('a delayed historical page cannot overwrite the rejoined window after ' + boundary,
    { skip: !!baselineClient, timeout: 60000 }, async t => {
      const f = await fixture(t);
      let release, seen, finished;
      const gate = new Promise(resolve => { release = resolve; });
      const intercepted = new Promise(resolve => { seen = resolve; });
      const complete = new Promise(resolve => { finished = resolve; });
      await f.page.route(historyURL, async route => {
        const response = await route.fetch(); seen();
        await gate; await route.fulfill({ response }); finished();
      }, { times: 1 });
      await f.page.locator('#older').click(); await intercepted;
      let participant = f.person.name;
      if (boundary === 'participant change') {
        await f.page.locator('#change').click();
        await f.page.locator('#name').fill('Replacement reader · fictional fixture');
        await f.page.locator('#identity-form button').click();
        participant = 'Replacement reader · fictional fixture';
        await f.page.waitForFunction(id => room?.id === id && !joining && socket?.connected, f.room.id);
      } else {
        await f.page.evaluate(() => socket.disconnect());
        await f.page.waitForFunction(() => !online);
        f.runtime.store.append(f.person, {
          roomId: f.room.id, clientId: randomUUID(), kind: 'note', body: 'Saved while the reader was disconnected'
        });
        await f.page.evaluate(() => socket.connect());
        await f.page.waitForFunction(id => room?.id === id && !joining && socket?.connected && entries.at(-1)?.id === latestKnown,
          f.room.id);
      }
      const expected = f.allIds().slice(-50);
      await expectIds(f.page, expected);
      await f.page.locator('#body').fill('Current reader draft remains');
      release(); await complete;
      await f.page.evaluate(() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve))));
      assert.deepEqual(await visibleIds(f.page), expected);
      assert.equal(await f.page.locator('#participant').textContent(), participant);
      assert.equal(await f.page.locator('#body').inputValue(), 'Current reader draft remains');
      assert.equal(await f.page.locator('#body').evaluate(node => node === document.activeElement), true);
      assert.equal(await f.page.locator('#older').isEnabled(), true);
    });
}
