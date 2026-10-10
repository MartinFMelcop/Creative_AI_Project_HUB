const assert = require('node:assert/strict');
const { before, after, beforeEach, afterEach, test } = require('node:test');
const { chromium } = require('playwright-core');

let browser;
let runtime;
let url;
let context;
let first;
let second;
let errors;

before(async () => {
  // An external URL allows the same delivery check to reproduce the legacy defect.
  url = process.env.CHAT_TEST_URL;
  if (!url) {
    runtime = require('../server.cjs').createChatServer();
    await new Promise((resolve) => runtime.server.listen(0, '127.0.0.1', resolve));
    url = `http://127.0.0.1:${runtime.server.address().port}`;
  }
  browser = await chromium.launch({
    executablePath: process.env.CHROMIUM_PATH || '/usr/bin/chromium',
    headless: true,
    args: ['--no-sandbox'],
  });
});

after(async () => {
  await browser?.close();
  if (runtime) await new Promise((resolve) => runtime.io.close(resolve));
});

beforeEach(async () => {
  context = await browser.newContext();
  errors = [];
  first = await context.newPage();
  second = await context.newPage();
  for (const page of [first, second]) {
    page.on('pageerror', (error) => errors.push(error.message));
    await page.goto(url);
    await page.waitForFunction(() => socket.connected);
  }
});

afterEach(async () => {
  await context?.close();
  assert.deepEqual(errors, [], 'No uncaught browser errors');
});

async function send(page, text) {
  await page.locator('#input').fill(text);
  await page.locator('#form button').click();
}

async function expectMessages(page, expected) {
  await page.waitForFunction((values) => {
    const actual = [...document.querySelectorAll('#messages li')].map((li) => li.textContent);
    return JSON.stringify(actual) === JSON.stringify(values);
  }, expected, { timeout: 4000 });
  assert.deepEqual(await page.locator('#messages li').allTextContents(), expected);
}

test('two browser clients display accepted messages once in both directions', async () => {
  await send(first, 'First participant');
  await expectMessages(first, ['First participant']);
  await expectMessages(second, ['First participant']);
  await send(second, 'Second participant');
  await expectMessages(first, ['First participant', 'Second participant']);
  await expectMessages(second, ['First participant', 'Second participant']);
});

test('markup remains literal text in both browsers', async () => {
  const text = '<img src=x onerror="window.injected=true"><script>window.injected=true</script>';
  await send(first, text);
  for (const page of [first, second]) {
    await expectMessages(page, [text]);
    assert.equal(await page.locator('#messages img, #messages script').count(), 0);
    assert.equal(await page.evaluate(() => window.injected), undefined);
  }
});

test('rejection is visible, preserves the draft, and does not broadcast', async () => {
  await send(first, '   ');
  await first.locator('#feedback').filter({ hasText: 'Enter a non-empty message.' }).waitFor();
  assert.equal(await first.locator('#input').inputValue(), '   ');
  await send(first, 'Accepted afterwards');
  await expectMessages(first, ['Accepted afterwards']);
  await expectMessages(second, ['Accepted afterwards']);
  assert.equal(await first.locator('#feedback').textContent(), '');
});

test('a departed client keeps its draft and receives only future messages on rejoining', async () => {
  await first.evaluate(() => socket.disconnect());
  await first.locator('#status').filter({ hasText: 'Disconnected' }).waitFor();
  assert.equal(await first.locator('#form button').isDisabled(), true);
  await first.locator('#input').fill('Offline draft');
  // Exercise the handler directly: the disabled button alone is not a buffering check.
  await first.evaluate(() => document.getElementById('form').dispatchEvent(new Event('submit', { cancelable: true })));
  await first.locator('#feedback').filter({ hasText: 'Your draft has not been sent' }).waitFor();
  await send(second, 'While away');
  await expectMessages(second, ['While away']);
  await first.evaluate(() => socket.connect());
  await first.waitForFunction(() => socket.connected);
  await send(second, 'After rejoining');
  await expectMessages(first, ['After rejoining']);
  await expectMessages(second, ['While away', 'After rejoining']);
  assert.equal(await first.locator('#input').inputValue(), 'Offline draft');
  await first.locator('#form button').click();
  await expectMessages(first, ['After rejoining', 'Offline draft']);
  await expectMessages(second, ['While away', 'After rejoining', 'Offline draft']);
});

test('transport interruption reconnects automatically without duplicating listeners', async () => {
  const previousId = await first.evaluate(() => socket.id);
  await first.evaluate(() => socket.io.engine.close());
  await first.waitForFunction((id) => socket.connected && socket.id !== id, previousId);
  await first.locator('#status').filter({ hasText: 'Connected' }).waitFor();
  await send(second, 'After transport reconnect');
  await expectMessages(first, ['After transport reconnect']);
  await expectMessages(second, ['After transport reconnect']);
});

test('browser retains only the latest 200 messages', async () => {
  await first.evaluate(async () => {
    for (let index = 0; index < 205; index++) {
      await new Promise((resolve, reject) => socket.timeout(2000).emit('chat message', `Message ${index}`, (error, response) => {
        if (error || !response.ok) reject(error || new Error(response.error));
        else resolve();
      }));
    }
  });
  const expected = Array.from({ length: 200 }, (_, index) => `Message ${index + 5}`);
  await expectMessages(first, expected);
  await expectMessages(second, expected);
});

test('new browser receives future messages without server-side history', async () => {
  await send(first, 'Before joining');
  await expectMessages(second, ['Before joining']);
  const newcomer = await context.newPage();
  newcomer.on('pageerror', (error) => errors.push(error.message));
  await newcomer.goto(url);
  await newcomer.waitForFunction(() => socket.connected);
  await send(first, 'After joining');
  await expectMessages(newcomer, ['After joining']);
});

test('missing acknowledgement reports uncertainty and does not retry automatically', async () => {
  const id = await first.evaluate(() => socket.id);
  const peer = runtime.io.sockets.sockets.get(id);
  // Simulate a delivered broadcast whose acknowledgement is lost.
  peer.removeAllListeners('chat message');
  peer.on('chat message', (text) => runtime.io.emit('chat message', text));
  await send(first, 'Acknowledgement lost');
  await expectMessages(second, ['Acknowledgement lost']);
  await first.locator('#feedback').filter({ hasText: 'Delivery is uncertain' }).waitFor();
  assert.equal(await first.locator('#input').inputValue(), 'Acknowledgement lost');
  await send(second, 'Still connected');
  await expectMessages(first, ['Acknowledgement lost', 'Still connected']);
  await expectMessages(second, ['Acknowledgement lost', 'Still connected']);
});

test('an acknowledgement does not erase a newer draft typed during sending', async () => {
  const id = await first.evaluate(() => socket.id);
  const peer = runtime.io.sockets.sockets.get(id);
  let release;
  let capture;
  const captured = new Promise((resolve) => { capture = resolve; });
  peer.removeAllListeners('chat message');
  peer.on('chat message', (text, acknowledge) => {
    runtime.io.emit('chat message', text);
    release = () => acknowledge({ ok: true });
    capture();
  });
  await send(first, 'Original draft');
  await captured;
  await first.locator('#input').fill('Next draft');
  release();
  await first.waitForFunction(() => !document.querySelector('#form button').disabled);
  assert.equal(await first.locator('#input').inputValue(), 'Next draft');
  await expectMessages(second, ['Original draft']);
});
