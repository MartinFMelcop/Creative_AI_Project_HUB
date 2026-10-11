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

test('new arrivals show their count while preserving the reading position', async () => {
  assert.equal(await page.locator('#latest').isVisible(), false);
  await publish(Array.from({ length: 60 }, (_, index) => message(index)));
  assert.equal(await page.locator('#latest').isVisible(), false);
  await browse(15);
  const previous = await position();
  await publish([message(60)]);
  await page.getByRole('button', { name: '1 new message · Jump to latest', exact: true }).waitFor({ timeout: 4000 });
  await publish([message(61), message(62)]);
  await page.getByRole('button', { name: '3 new messages · Jump to latest', exact: true }).waitFor();
  const current = await position();
  assert.equal(current.anchor, previous.anchor);
  assert.ok(Math.abs(current.offset - previous.offset) <= 1);
});

test('keyboard activation returns to live text and keeps conversation focus', async () => {
  await page.setViewportSize({ width: 390, height: 844 });
  await publish(Array.from({ length: 40 }, (_, index) => message(index)));
  await browse(10);
  await publish([message(40), message(41)]);
  await page.locator('#latest').focus();
  await page.keyboard.press('Enter');
  await page.waitForFunction(() => document.getElementById('latest').hidden);
  assert.ok((await position()).distance <= 1);
  assert.equal(await page.evaluate(() => document.activeElement.id), 'messages');
  await publish([message(42)]);
  assert.ok((await position()).distance <= 1);
  assert.equal(await page.locator('#latest').isVisible(), false);
  await browse(10);
  await publish([message(43)]);
  await page.locator('#latest').focus();
  await page.keyboard.press('Space');
  await page.waitForFunction(() => document.getElementById('latest').hidden);
  assert.ok((await position()).distance <= 1);
  assert.equal(await page.evaluate(() => document.activeElement.id), 'messages');
});

test('manual scrolling to live text clears the count before the next browsing session', async () => {
  await publish(Array.from({ length: 40 }, (_, index) => message(index)));
  await browse(10);
  await publish([message(40), message(41)]);
  await page.locator('#latest').waitFor();
  await page.locator('#messages').focus();
  await page.keyboard.press('Control+End');
  await page.waitForFunction(() => document.getElementById('latest').hidden);
  await browse(10);
  await publish([message(42)]);
  await page.getByRole('button', { name: '1 new message · Jump to latest', exact: true }).waitFor();
});

test('unread counts stay bounded when arrivals exceed the retained history', async () => {
  await publish(Array.from({ length: 200 }, (_, index) => message(index)));
  await page.evaluate(() => { document.getElementById('messages').scrollTop = 0; });
  await publish(Array.from({ length: 205 }, (_, index) => message(index + 200)));
  await page.getByRole('button', { name: '200 new messages · Jump to latest', exact: true }).waitFor();
  const current = await position();
  assert.equal(current.count, 200);
  assert.equal(current.first, message(205));
  assert.equal(current.scrollTop, 0);
});

async function leaveTabInactive() {
  // Playwright forces focus by default. Disable that override on both real tabs.
  await (await context.newCDPSession(page)).send('Emulation.setFocusEmulationEnabled', { enabled: false });
  const away = await context.newPage();
  await (await context.newCDPSession(away)).send('Emulation.setFocusEmulationEnabled', { enabled: false });
  await page.bringToFront();
  await page.waitForFunction(() => document.hasFocus());
  await away.bringToFront();
  await page.waitForFunction(() => !document.hasFocus());
  return away;
}

test('inactive tab counts arrivals at the live edge and clears them on focus', async () => {
  const title = await page.title();
  await publish(Array.from({ length: 30 }, (_, index) => message(index)));
  await leaveTabInactive();
  await publish([message(30)]);
  await page.getByRole('button', { name: '1 new message · Jump to latest', exact: true }).waitFor({ timeout: 4000 });
  assert.equal(await page.title(), `(1) ${title}`);
  await publish([message(31), message(32)]);
  assert.equal(await page.title(), `(3) ${title}`);
  assert.ok((await position()).distance <= 1);
  await page.bringToFront();
  await page.waitForFunction(() => document.hasFocus() && document.getElementById('latest').hidden);
  assert.equal(await page.title(), title);
  await publish([message(33)]);
  assert.equal(await page.locator('#latest').isVisible(), false);
  assert.equal(await page.title(), title);
});

test('returning to an inactive tab at earlier text retains its unread count and anchor', async () => {
  const title = await page.title();
  await publish(Array.from({ length: 40 }, (_, index) => message(index)));
  await browse(10);
  const previous = await position();
  await leaveTabInactive();
  await publish([message(40), message(41), message(42)]);
  assert.equal(await page.title(), `(3) ${title}`);
  await page.bringToFront();
  await page.waitForFunction(() => document.hasFocus());
  await page.getByRole('button', { name: '3 new messages · Jump to latest', exact: true }).waitFor();
  const current = await position();
  assert.equal(current.anchor, previous.anchor);
  assert.ok(Math.abs(current.offset - previous.offset) <= 1);
  assert.equal(await page.title(), `(3) ${title}`);
  await page.locator('#latest').focus();
  await page.keyboard.press('Enter');
  await page.waitForFunction(() => document.getElementById('latest').hidden);
  assert.equal(await page.title(), title);
  assert.equal(await page.evaluate(() => document.activeElement.id), 'messages');
});

test('hidden page keeps unread arrivals until visible at the live edge', async () => {
  const title = await page.title();
  await publish(Array.from({ length: 30 }, (_, index) => message(index)));
  // Headless tabs remain visible: this is an explicit Page Visibility API boundary.
  await page.evaluate(() => {
    Object.defineProperty(document, 'visibilityState', { configurable: true, value: 'hidden' });
    document.dispatchEvent(new Event('visibilitychange'));
  });
  await publish([message(30), message(31)]);
  await page.getByRole('button', { name: '2 new messages · Jump to latest', exact: true }).waitFor({ timeout: 4000 });
  assert.equal(await page.title(), `(2) ${title}`);
  await page.evaluate(() => {
    const list = document.getElementById('messages');
    list.scrollTop = 0;
    list.scrollTop = list.scrollHeight;
    list.dispatchEvent(new Event('scroll'));
  });
  assert.equal(await page.title(), `(2) ${title}`, 'Hidden scroll events cannot mark arrivals read');
  await page.evaluate(() => {
    delete document.visibilityState;
    document.dispatchEvent(new Event('visibilitychange'));
  });
  await page.waitForFunction(() => document.getElementById('latest').hidden);
  assert.equal(await page.title(), title);
});

test('inactive tab unread count stays bounded to retained messages', async () => {
  const title = await page.title();
  await leaveTabInactive();
  await publish(Array.from({ length: 205 }, (_, index) => message(index)));
  await page.getByRole('button', { name: '200 new messages · Jump to latest', exact: true }).waitFor({ timeout: 4000 });
  assert.equal(await page.title(), `(200) ${title}`);
  const current = await position();
  assert.equal(current.count, 200);
  assert.equal(current.first, message(5));
  await page.bringToFront();
  await page.waitForFunction(() => document.getElementById('latest').hidden);
  assert.equal(await page.title(), title);
});

async function settleLayout() {
  await page.evaluate(() => new Promise((resolve) => {
    requestAnimationFrame(() => requestAnimationFrame(resolve));
  }));
}

test('viewport height changes keep live readers at the bottom', async () => {
  await publish(Array.from({ length: 40 }, (_, index) => message(index)));
  await settleLayout();
  for (const height of [480, 1000, 600]) {
    await page.setViewportSize({ width: 1280, height });
    await settleLayout();
    assert.ok((await position()).distance <= 1, `Live text stays visible at height ${height}`);
  }
  await publish([message(40)]);
  assert.ok((await position()).distance <= 1);
  assert.equal(await page.locator('#latest').isVisible(), false);
});

test('viewport width reflow preserves earlier text through narrowing and widening', async () => {
  const title = await page.title();
  const reflowMessage = (index) => `Message ${index}: ${'A long sentence wraps on a narrow screen and stays readable. '.repeat(2 + index % 3)}`.trim();
  await publish(Array.from({ length: 200 }, (_, index) => reflowMessage(index)));
  await browse(100);
  await settleLayout();
  const previous = await position();
  let next = 200;
  for (const viewport of [{ width: 390, height: 844 }, { width: 1280, height: 800 }]) {
    await page.setViewportSize(viewport);
    await settleLayout();
    let current = await position();
    assert.equal(current.anchor, previous.anchor, 'Reflow keeps the same visible message');
    assert.ok(Math.abs(current.offset - previous.offset) <= 1, 'Reflow keeps the visible offset');
    await publish([reflowMessage(next++)]);
    current = await position();
    assert.equal(current.anchor, previous.anchor, 'Eviction after reflow keeps the same anchor');
    assert.ok(Math.abs(current.offset - previous.offset) <= 1);
  }
  await page.getByRole('button', { name: '2 new messages · Jump to latest', exact: true }).waitFor();
  assert.equal(await page.title(), `(2) ${title}`);
  await page.locator('#latest').click();
  assert.ok((await position()).distance <= 1);
  assert.equal(await page.title(), title);
});

test('viewport resizing preserves inactive unread state at the live edge', async () => {
  const title = await page.title();
  await publish(Array.from({ length: 40 }, (_, index) => message(index)));
  await leaveTabInactive();
  await publish([message(40), message(41)]);
  await settleLayout();
  await page.setViewportSize({ width: 390, height: 600 });
  await settleLayout();
  assert.ok((await position()).distance <= 1, 'Inactive live readers still follow after reflow');
  assert.equal(await page.title(), `(2) ${title}`, 'Resize does not mark inactive arrivals read');
  await page.bringToFront();
  await page.waitForFunction(() => document.hasFocus() && document.getElementById('latest').hidden);
  assert.equal(await page.title(), title);
});

async function textStyle(style) {
  // Controlled user styles change text metrics without resizing the panel.
  await page.locator('#messages').evaluate((list, values) => Object.assign(list.style, values), style);
  await settleLayout();
}

async function panelSize() {
  return page.locator('#messages').evaluate((list) => ({ width: list.clientWidth, height: list.clientHeight }));
}

test('text enlargement with an unchanged panel keeps live readers at the bottom', async () => {
  await publish(Array.from({ length: 60 }, (_, index) => message(index)));
  await settleLayout();
  const size = await panelSize();
  for (const fontSize of ['24px', '16px']) {
    await textStyle({ fontSize });
    assert.deepEqual(await panelSize(), size, 'Only text metrics change');
    assert.ok((await position()).distance <= 1, `Live text stays visible at ${fontSize}`);
  }
  await publish([message(60)]);
  assert.ok((await position()).distance <= 1);
  assert.equal(await page.locator('#latest').isVisible(), false);
});

test('text size and spacing reflow preserves an earlier anchor through retention eviction', async () => {
  const title = await page.title();
  await publish(Array.from({ length: 200 }, (_, index) => message(index)));
  await browse(100);
  await settleLayout();
  const previous = await position();
  const size = await panelSize();
  let next = 200;
  for (const style of [
    { fontSize: '24px', lineHeight: '1.5', letterSpacing: '.12em' },
    { fontSize: '16px', lineHeight: 'normal', letterSpacing: 'normal' },
  ]) {
    await textStyle(style);
    assert.deepEqual(await panelSize(), size, 'The panel has not resized');
    let current = await position();
    assert.equal(current.anchor, previous.anchor, 'Text reflow keeps the same message');
    assert.ok(Math.abs(current.offset - previous.offset) <= 1, 'Text reflow keeps its pixel offset');
    await publish([message(next++)]);
    current = await position();
    assert.equal(current.count, 200);
    assert.equal(current.anchor, previous.anchor, 'Eviction after text reflow keeps the anchor');
    assert.ok(Math.abs(current.offset - previous.offset) <= 1);
  }
  await page.getByRole('button', { name: '2 new messages · Jump to latest', exact: true }).waitFor();
  assert.equal(await page.title(), `(2) ${title}`);
});

test('text enlargement preserves inactive unread arrivals at the live edge', async () => {
  const title = await page.title();
  await publish(Array.from({ length: 40 }, (_, index) => message(index)));
  await leaveTabInactive();
  await publish([message(40), message(41)]);
  await settleLayout();
  const size = await panelSize();
  await textStyle({ fontSize: '24px' });
  assert.deepEqual(await panelSize(), size);
  assert.ok((await position()).distance <= 1, 'Inactive live readers still follow after text reflow');
  assert.equal(await page.title(), `(2) ${title}`, 'Text reflow cannot mark inactive arrivals read');
  await page.bringToFront();
  await page.waitForFunction(() => document.hasFocus() && document.getElementById('latest').hidden);
  assert.equal(await page.title(), title);
});
