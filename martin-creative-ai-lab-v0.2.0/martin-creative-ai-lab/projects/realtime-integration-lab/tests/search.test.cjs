const { test } = require('node:test');
const assert = require('node:assert/strict');
const { randomUUID } = require('node:crypto');
const { mkdtempSync, rmSync, mkdirSync } = require('node:fs');
const { tmpdir } = require('node:os');
const { join } = require('node:path');
const { RoomsStore } = require('../rooms-store.cjs');
const { createRoomsServer } = require('../rooms-server.cjs');
const { createBackup, restoreBackup } = require('../rooms-backup.cjs');

function fixture(t) {
  const store = new RoomsStore(':memory:'); t.after(() => store.close());
  const person = store.session('Reviewer'), room = store.createRoom('Waterworks');
  const append = (body, kind = 'note', roomId = room.id) => store.append(person, { roomId, kind, body, clientId: randomUUID() }).message;
  store.work.join(room.id, person);
  const update = (a, changes) => store.work.apply(person, { op: 'update', roomId: room.id, clientId: randomUUID(), actionId: a.id, expectedRevision: a.revision, title: a.title, ownerId: a.owner_id, status: a.status, note: a.note, ...changes }).action;
  return { store, person, room, append, update };
}

test('full-record search retrieves old decisions and superseded blockers with exact context', t => {
  const f = fixture(t), decision = f.append('Inspect the western valve before return.', 'decision');
  let action = f.store.work.apply(f.person, { op: 'create', roomId: f.room.id, clientId: randomUUID(), sourceId: decision.id, title: 'Repair the water pump', ownerId: f.person.id }).action;
  action = f.update(action, { status: 'blocked', note: 'Válvula presa no depósito.' });
  for (let i = 0; i < 60; i++) action = f.update(action, { status: 'doing', note: `Later progress ${i}` });
  action = f.update(action, { status: 'done', note: 'Pressure restored.' });
  for (let i = 0; i < 350; i++) f.append(`Recent record ${i}`, i < 120 ? 'decision' : 'note');
  assert.ok(!f.store.history(f.room.id).messages.some(e => e.id === decision.id));
  assert.ok(!f.store.decisions(f.room.id).some(e => e.id === decision.id));
  assert.ok(!f.store.work.history(action.id, f.room.id).events.some(e => e.revision === 2));
  const found = f.store.records.search(f.room.id, { q: 'DEPOSITO valvula', kind: 'action' });
  assert.equal(found.total, 1); assert.equal(found.results[0].revision, 2); assert.equal(found.results[0].status, 'blocked');
  const context = f.store.records.context(f.room.id, 'action', found.results[0].id);
  assert.equal(context.decision.id, decision.id); assert.equal(context.actions[0].status, 'done');
  assert.equal(context.actions[0].revision, 63); assert.deepEqual(context.events.map(e => e.revision), [1, 2, 3, 4]);
  const source = f.store.records.search(f.room.id, { q: 'western return', kind: 'decision' }).results[0];
  const entryContext = f.store.records.context(f.room.id, 'entry', source.id);
  assert.equal(entryContext.entries[0].id, decision.id); assert.equal(entryContext.actions[0].id, action.id);
});

test('pinned mixed-stream pages keep order without duplicate or lost matches after new records', t => {
  const f = fixture(t);
  for (let i = 0; i < 43; i++) f.append(`Return valve ${i}`, i % 2 ? 'note' : 'decision');
  let action = f.store.work.apply(f.person, { op: 'create', roomId: f.room.id, clientId: randomUUID(), title: 'Return valve work' }).action;
  for (let i = 0; i < 19; i++) action = f.update(action, { note: `Return valve update ${i}` });
  const first = f.store.records.search(f.room.id, { q: 'return valve' }); assert.equal(first.total, 63); assert.equal(first.stale, false);
  f.append('Return valve new arrival'); f.update(action, { note: 'Return valve new update' });
  const ids = [], keys = rows => rows.map(r => `${r.kind === 'action' ? 'action' : 'entry'}:${r.id}`);
  let page = first;
  do {
    ids.push(...keys(page.results)); assert.equal(page.total, 63);
    page = page.next ? f.store.records.search(f.room.id, { q: 'return valve', cursor: page.next }) : null;
  } while (page);
  assert.equal(ids.length, 63); assert.equal(new Set(ids).size, 63);
  const previous = f.store.records.search(f.room.id, { q: 'return valve', cursor: first.cursor });
  assert.deepEqual(keys(previous.results), keys(first.results)); assert.equal(previous.stale, true);
  assert.equal(f.store.records.search(f.room.id, { q: 'return valve' }).total, 65);
});

test('literal Unicode matching, room isolation and cursor validation do not mutate records', t => {
  const f = fixture(t), other = f.store.createRoom('Elsewhere');
  const first = f.append('<b>Câble_%</b> "x" OR * / café');
  f.append('Secret needle', 'decision', other.id);
  // Compatibility expansion can make a valid short query's UTF-8 cursor larger.
  const expandedQuery = '㍿'.repeat(100);
  for (let i = 0; i < 21; i++) f.append(expandedQuery);
  const before = JSON.stringify(f.store.export(f.room.id), (k, v) => k === 'exported_at' ? undefined : v);
  const expandedPage = f.store.records.search(f.room.id, { q: expandedQuery });
  assert.ok(expandedPage.next.length > 1024);
  assert.equal(f.store.records.search(f.room.id, { q: expandedQuery, cursor: expandedPage.next }).results.length, 1);
  assert.equal(f.store.records.search(f.room.id, { q: 'cable_% café' }).total, 1);
  assert.equal(f.store.records.search(f.room.id, { q: 'OR *' }).total, 1);
  assert.equal(f.store.records.search(f.room.id, { q: 'cableX' }).total, 0);
  assert.equal(f.store.records.search(f.room.id, { q: 'needle' }).total, 0);
  assert.throws(() => f.store.records.context(other.id, 'entry', first.id), /not found/);
  for (const bad of [{ q: '' }, { q: '\u0301' }, { q: 'x'.repeat(161) }, { q: '1 2 3 4 5 6 7 8 9' }, { q: ['x'] }, { q: 'x', kind: 'unknown' }]) assert.throws(() => f.store.records.search(f.room.id, bad));
  const cursor = f.store.records.search(f.room.id, { q: 'cafe' }).cursor;
  assert.throws(() => f.store.records.search(other.id, { q: 'cafe', cursor }), /cursor/);
  assert.throws(() => f.store.records.search(f.room.id, { q: 'other', cursor }), /cursor/);
  assert.throws(() => f.store.records.search(f.room.id, { q: 'cafe', kind: 'decision', cursor }), /cursor/);
  for (const token of ['{', 'x'.repeat(1025), Buffer.from(JSON.stringify({ ...JSON.parse(Buffer.from(cursor, 'base64url')), offset: -1 })).toString('base64url')])
    assert.throws(() => f.store.records.search(f.room.id, { q: 'cafe', cursor: token }), /cursor/);
  assert.equal(JSON.stringify(f.store.export(f.room.id), (k, v) => k === 'exported_at' ? undefined : v), before);
  assert.equal(f.store.db.prepare('PRAGMA user_version').get().user_version, 2);
});

test('search and context routes require local identity and exclude credentials', async t => {
  const runtime = createRoomsServer(); await new Promise(r => runtime.server.listen(0, '127.0.0.1', r));
  t.after(() => new Promise(r => runtime.io.close(r)));
  const f = runtime.store, p = f.session('Reader'), r = f.createRoom('Record');
  f.append(p, { roomId: r.id, clientId: randomUUID(), kind: 'note', body: 'Needle record' });
  const base = `http://127.0.0.1:${runtime.server.address().port}/api/studio/rooms/${r.id}`;
  for (const route of ['/search?q=needle', '/context/entry/1']) {
    assert.equal((await fetch(base + route)).status, 401);
    const response = await fetch(base + route, { headers: { Authorization: `Bearer ${p.token}` } }); assert.equal(response.status, 200);
    const text = await response.text(); assert.ok(!text.includes(p.token)); assert.ok(!text.includes('token_hash')); assert.ok(!text.includes('client_id'));
  }
  assert.equal((await fetch(base + '/search?q=', { headers: { Authorization: `Bearer ${p.token}` } })).status, 400);
});

test('existing schema-2 recovery bundles remain searchable without an index migration', async t => {
  const dir = mkdtempSync(join(tmpdir(), 'p11-search-recovery-')); t.after(() => rmSync(dir, { recursive: true, force: true }));
  const file = join(dir, 'source.sqlite'), store = new RoomsStore(file);
  const p = store.session('Reviewer'), room = store.createRoom('Recovered record');
  store.append(p, { roomId: room.id, clientId: randomUUID(), kind: 'decision', body: 'Remember the valve deadline.' });
  mkdirSync(join(dir, 'bundles'));
  const from = join(dir, 'bundles', 'savepoint'); await createBackup(file, from); store.close();
  const target = join(dir, 'restored.sqlite'); await restoreBackup(from, target);
  const recovered = new RoomsStore(target); t.after(() => recovered.close());
  assert.equal(recovered.authenticate(p.token).id, p.id);
  assert.equal(recovered.records.search(room.id, { q: 'valve deadline' }).total, 1);
  assert.equal(recovered.db.prepare('PRAGMA user_version').get().user_version, 2);
});
