const assert = require('node:assert/strict');
const { test } = require('node:test');
const { io } = require('socket.io-client');
const { createChatServer } = require('../server.cjs');

async function connect(url) {
  const client = io(url, { autoConnect: false, reconnection: false });
  await new Promise((resolve, reject) => {
    client.once('connect', resolve);
    client.once('connect_error', reject);
    client.connect();
  });
  return client;
}

async function fixture(t) {
  const runtime = createChatServer();
  const clients = [];
  t.after(async () => {
    for (const client of clients) client.close();
    await new Promise((resolve) => runtime.io.close(resolve));
  });
  await new Promise((resolve) => runtime.server.listen(0, '127.0.0.1', resolve));
  const url = `http://127.0.0.1:${runtime.server.address().port}`;
  for (let index = 0; index < 2; index++) clients.push(await connect(url));
  const received = clients.map(() => []);
  clients.forEach((client, index) => client.on('chat message', (text) => received[index].push(text)));
  return { clients, received };
}

function send(client, payload) {
  return new Promise((resolve, reject) => {
    client.timeout(2000).emit('chat message', payload, (error, reply) => {
      if (error) reject(error);
      else resolve(reply);
    });
  });
}

async function barrier(clients, received) {
  const arrivals = clients.map((client) => new Promise((resolve) => client.once('chat message', resolve)));
  assert.deepEqual(await send(clients[0], 'sentinel'), { ok: true });
  await Promise.all(arrivals);
  assert.deepEqual(received, [['sentinel'], ['sentinel']]);
}

test('protocol broadcasts trimmed messages to sender and peer in order', { timeout: 10000 }, async (t) => {
  const { clients, received } = await fixture(t);
  for (const [client, payload] of [[clients[0], '  Hello  '], [clients[1], 'Reply']]) {
    const arrivals = clients.map((peer) => new Promise((resolve) => peer.once('chat message', resolve)));
    assert.deepEqual(await send(client, payload), { ok: true });
    await Promise.all(arrivals);
  }
  assert.deepEqual(received, [['Hello', 'Reply'], ['Hello', 'Reply']]);
});

test('non-string payloads are rejected without broadcasts', { timeout: 10000 }, async (t) => {
  const { clients, received } = await fixture(t);
  for (const payload of [null, 42, true, [], { text: 'Hello' }]) {
    assert.deepEqual(await send(clients[0], payload), { ok: false, error: 'Message must be text.' });
  }
  await barrier(clients, received);
});

test('empty and whitespace-only payloads are rejected without broadcasts', { timeout: 10000 }, async (t) => {
  const { clients, received } = await fixture(t);
  for (const payload of ['', '  \n\t ']) {
    assert.deepEqual(await send(clients[0], payload), { ok: false, error: 'Enter a non-empty message.' });
  }
  await barrier(clients, received);
});

test('501 code units are rejected even when trimming would shorten the payload', { timeout: 10000 }, async (t) => {
  const { clients, received } = await fixture(t);
  for (const payload of ['a'.repeat(501), ` ${'a'.repeat(500)}`]) {
    assert.deepEqual(await send(clients[0], payload), { ok: false, error: 'Use at most 500 characters.' });
  }
  await barrier(clients, received);
});

test('500 UTF-16 code units are accepted including non-ASCII text', { timeout: 10000 }, async (t) => {
  const { clients } = await fixture(t);
  for (const payload of ['a'.repeat(500), '🎵'.repeat(250), 'é']) {
    const arrival = new Promise((resolve) => clients[1].once('chat message', resolve));
    assert.deepEqual(await send(clients[0], payload), { ok: true });
    assert.equal(await arrival, payload);
  }
});

test('messages without acknowledgement callbacks do not crash the server', { timeout: 10000 }, async (t) => {
  const { clients } = await fixture(t);
  clients[0].emit('chat message', { invalid: true });
  const arrival = new Promise((resolve) => clients[1].once('chat message', resolve));
  clients[0].emit('chat message', 'No callback');
  assert.equal(await arrival, 'No callback');
});
