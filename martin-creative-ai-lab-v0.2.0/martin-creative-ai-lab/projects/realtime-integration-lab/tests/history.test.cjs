'use strict';
const assert = require('node:assert/strict');
const { test } = require('node:test');
const { randomUUID } = require('node:crypto');
const { RoomsStore } = require('../rooms-store.cjs');
const { createRoomsServer } = require('../rooms-server.cjs');

function populate(store, count = 650) {
  const person = store.session('History fixture');
  const room = store.createRoom('Chronological handover');
  const other = store.createRoom('Interleaved project');
  const messages = [];
  for (let index = 0; index < count; index++) {
    messages.push(store.append(person, {
      roomId: room.id, clientId: randomUUID(), kind: index % 17 === 0 ? 'decision' : 'note',
      body: 'Archive entry ' + index
    }).message);
    store.append(person, {
      roomId: other.id, clientId: randomUUID(), kind: 'note', body: 'Other project entry ' + index
    });
  }
  return { person, room, other, messages };
}
const ids = messages => messages.map(message => message.id);
function assertPage(page, expected, all) {
  assert.deepEqual(ids(page.messages), ids(expected));
  assert.ok(page.messages.length <= 50, 'Each API page must stay bounded.');
  assert.equal(page.before, expected[0]?.id ?? null);
  assert.equal(page.after, expected.at(-1)?.id ?? null);
  if (expected.length) {
    assert.equal(page.hasMore, all.some(message => message.id < expected[0].id));
    assert.equal(page.hasNewer, all.some(message => message.id > expected.at(-1).id));
  }
}

test('bidirectional history crosses the 300-row client boundary without skipping interleaved room IDs', () => {
  const store = new RoomsStore(':memory:');
  try {
    const f = populate(store);
    assert.ok(f.messages[1].id > f.messages[0].id + 1, 'Fixture IDs must interleave with another room.');
    let page = store.history(f.room.id);
    assertPage(page, f.messages.slice(-50), f.messages);
    let backward = page.messages;
    while (page.hasMore) {
      const previous = page.before;
      page = store.history(f.room.id, previous);
      assert.ok(page.messages.length, 'An earlier boundary must make progress.');
      backward = [...page.messages, ...backward];
      assertPage(page, f.messages.filter(message => message.id < previous).slice(-50), f.messages);
    }
    assert.deepEqual(ids(backward), ids(f.messages));

    page = store.history(f.room.id, f.messages[50].id);
    assertPage(page, f.messages.slice(0, 50), f.messages);
    let forward = page.messages;
    while (page.hasNewer) {
      const previous = page.after;
      page = store.history(f.room.id, undefined, previous);
      assert.ok(page.messages.length, 'A newer boundary must make progress.');
      forward.push(...page.messages);
      assertPage(page, f.messages.filter(message => message.id > previous).slice(0, 50), f.messages);
    }
    assert.deepEqual(ids(forward), ids(f.messages));
    assert.equal(new Set(ids(forward)).size, 650);
    assert.equal(forward.some(message => message.room_id === f.other.id), false);
  } finally { store.close(); }
});

test('before remains compatible while after returns the closest newer page and detects real arrivals', () => {
  const store = new RoomsStore(':memory:');
  try {
    const f = populate(store, 153);
    assertPage(store.history(f.room.id, f.messages[80].id), f.messages.slice(30, 80), f.messages);
    assertPage(store.history(f.room.id, undefined, f.messages[80].id), f.messages.slice(81, 131), f.messages);
    const originalLatest = store.history(f.room.id);
    assert.equal(originalLatest.hasNewer, false);
    const arrival = store.append(f.person, {
      roomId: f.room.id, clientId: randomUUID(), kind: 'note', body: 'Saved after the reading window opened'
    }).message;
    const all = [...f.messages, arrival];
    assertPage(store.history(f.room.id, undefined, originalLatest.after), [arrival], all);
    assertPage(store.history(f.room.id, f.messages[80].id), f.messages.slice(30, 80), all);
    assert.equal(store.export(f.room.id).entries.length, 154);
  } finally { store.close(); }
});

test('empty and partial history pages stay bounded and invalid or conflicting cursors are rejected', () => {
  const store = new RoomsStore(':memory:');
  try {
    const f = populate(store, 3), empty = store.createRoom('Empty conversation');
    const page = store.history(empty.id);
    assert.deepEqual(page.messages, []);
    assert.equal(page.hasMore, false);
    assert.equal(page.hasNewer, false);
    assert.equal(page.before, null);
    assert.equal(page.after, null);
    assertPage(store.history(f.room.id), f.messages, f.messages);
    assertPage(store.history(f.room.id, f.messages[2].id), f.messages.slice(0, 2), f.messages);
    assertPage(store.history(f.room.id, undefined, f.messages[0].id), f.messages.slice(1), f.messages);
    for (const value of [null, 0, -1, 0.5, '12', NaN, Infinity, Number.MAX_SAFE_INTEGER + 1]) {
      assert.throws(() => store.history(f.room.id, value), 'Invalid before cursor must be rejected.');
      assert.throws(() => store.history(f.room.id, undefined, value), 'Invalid after cursor must be rejected.');
    }
    assert.throws(() => store.history(f.room.id, 1, 2), 'Choose one direction per request.');
    assert.throws(() => store.history('missing-project', undefined, 1));
    assert.equal(store.export(f.room.id).entries.length, 3);
  } finally { store.close(); }
});

test('authenticated HTTP history exposes both directions with room isolation and failure responses', async t => {
  const runtime = createRoomsServer();
  await new Promise(resolve => runtime.server.listen(0, '127.0.0.1', resolve));
  t.after(() => new Promise(resolve => runtime.io.close(resolve)));
  const f = populate(runtime.store, 111);
  const base = 'http://127.0.0.1:' + runtime.server.address().port + '/api/studio/rooms/' + f.room.id + '/history';
  const headers = { Authorization: 'Bearer ' + f.person.token };
  async function read(query = '') {
    const response = await fetch(base + query, { headers });
    return { response, body: await response.json() };
  }
  assert.equal((await fetch(base)).status, 401);
  let result = await read();
  assert.equal(result.response.status, 200);
  assertPage(result.body, f.messages.slice(-50), f.messages);
  result = await read('?before=' + f.messages[80].id);
  assert.equal(result.response.status, 200);
  assertPage(result.body, f.messages.slice(30, 80), f.messages);
  result = await read('?after=' + f.messages[30].id);
  assert.equal(result.response.status, 200);
  assertPage(result.body, f.messages.slice(31, 81), f.messages);
  for (const query of ['?before=0', '?after=-1', '?after=1.5', '?after=invalid', '?before=2&after=3']) {
    const rejected = await read(query);
    assert.equal(rejected.response.status, 400, query);
    assert.equal(typeof rejected.body.error, 'string');
  }
  assert.equal(runtime.store.export(f.room.id).entries.length, 111);
});
