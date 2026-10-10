const assert = require('node:assert/strict');
const { before, after, beforeEach, afterEach, test } = require('node:test');
const { chromium } = require('playwright-core');
const { io } = require('socket.io-client');

let browser;
let runtime;
let url;
let context;
let page;
let sender;
let errors;

before(async () => {
  runtime = require('../server.cjs').createChatServer();
  await new Promise((resolve) => runtime.server.listen(0, '127.0.0.1', resolve));
  url = `http://127.0.0.1:${runtime.server.address().port}`;
  browser = await chromium.launch({
    executablePath: process.env.CHROMIUM_PATH || '/usr/bin/chromium',
    headless: true, args: ['--no-sandbox'],
  });
});

after(async () => {
  await browser?.close();
  if (runtime) await new Promise((resolve) => runtime.io.close(resolve));
});

beforeEach(async () => {
  context = await browser.newContext({ viewport: { width: 1280, height: 800 } });
  if (process.env.CHAT_TEST_CLIENT_PATH) {
    // Reproduce a recorded client without replacing any repository file.
    await context.route('**/client.js', (route) => route.fulfill({
      path: process.env.CHAT_TEST_CLIENT_PATH, contentType: 'application/javascript',
    }));
  }
  errors = [];
  page = await context.newPage();
  page.on('pageerror', (error) => errors.push(error.message));
  await page.goto(url);
  await page.waitForFunction(() => socket.connected);
  sender = io(url, { reconnection: false });
  await new Promise((resolve, reject) => {
    sender.once('connect', resolve);
    sender.once('connect_error', reject);
  });
});

afterEach(async () => {
  sender?.disconnect();
  await context?.close();
  assert.deepEqual(errors, [], 'No uncaught browser errors');
});

function message(index) {
  return `Message ${index}\n${`A readable line for item ${index}.\n`.repeat(1 + index % 3)}`.trim();
}

async function publish(texts) {
  for (const text of texts) {
    await new Promise((resolve, reject) => sender.timeout(2000).emit('chat message', text, (error, response) => {
      if (error || !response.ok) reject(error || new Error(response.error));
      else resolve();
    }));
  }
  await page.waitForFunction((text) => document.querySelector('#messages li:last-child')?.textContent === text,
    texts.at(-1));
}

async function position() {
  return page.evaluate(() => {
    const list = document.getElementById('messages');
    const top = list.getBoundingClientRect().top;
    const anchor = [...list.children].find((item) => item.getBoundingClientRect().bottom > top);
    return {
      anchor: anchor?.textContent, offset: anchor?.getBoundingClientRect().top - top,
      scrollTop: list.scrollTop, distance: list.scrollHeight - list.clientHeight - list.scrollTop,
      count: list.children.length, first: list.firstElementChild?.textContent,
    };
  });
}

async function browse(index) {
  await page.evaluate((value) => {
    const list = document.getElementById('messages');
    list.scrollTop += list.children[value].getBoundingClientRect().top - list.getBoundingClientRect().top + 12;
  }, index);
}

test('the conversation follows initial messages and readers within 24 pixels of the bottom', async () => {
  await publish(Array.from({ length: 40 }, (_, index) => message(index)));
  assert.ok((await position()).distance <= 1);
  await page.evaluate(() => { document.getElementById('messages').scrollTop -= 16; });
  assert.ok((await position()).distance > 1 && (await position()).distance <= 24);
  await publish([message(40)]);
  assert.ok((await position()).distance <= 1, 'Near-bottom readers continue following live messages');
});

test('new broadcasts preserve the visible message and pixel offset while browsing earlier text', async () => {
  await publish(Array.from({ length: 60 }, (_, index) => message(index)));
  await browse(15);
  const previous = await position();
  assert.ok(previous.distance > 24);
  await publish([message(60), message(61), message(62)]);
  const current = await position();
  assert.equal(current.anchor, previous.anchor);
  assert.ok(Math.abs(current.offset - previous.offset) <= 1, 'Reading position must not jump');
  assert.equal(current.count, 63);
});

test('scrolling back to the bottom resumes following subsequent messages', async () => {
  await publish(Array.from({ length: 40 }, (_, index) => message(index)));
  await browse(10);
  assert.ok((await position()).distance > 24);
  await page.evaluate(() => {
    const list = document.getElementById('messages');
    list.scrollTop = list.scrollHeight;
  });
  await publish([message(40)]);
  assert.ok((await position()).distance <= 1);
});

test('retention eviction preserves a surviving reading anchor across variable-height messages', async () => {
  await publish(Array.from({ length: 200 }, (_, index) => message(index)));
  await browse(100);
  const previous = await position();
  await publish(Array.from({ length: 10 }, (_, index) => message(index + 200)));
  const current = await position();
  assert.equal(current.count, 200);
  assert.equal(current.first, message(10));
  assert.equal(current.anchor, previous.anchor);
  assert.ok(Math.abs(current.offset - previous.offset) <= 1, `Eviction must preserve the retained anchor: ${JSON.stringify({ previous, current })}`);
});

test('an evicted reading anchor falls back to the earliest retained message', async () => {
  await publish(Array.from({ length: 200 }, (_, index) => message(index)));
  await page.evaluate(() => { document.getElementById('messages').scrollTop = 0; });
  await publish([message(200)]);
  const current = await position();
  assert.equal(current.count, 200);
  assert.equal(current.first, message(1));
  assert.equal(current.scrollTop, 0, 'Stay at the retained-history boundary instead of jumping to live text');
});
