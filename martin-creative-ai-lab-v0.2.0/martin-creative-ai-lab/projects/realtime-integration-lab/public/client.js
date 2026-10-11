const socket = io();
const form = document.getElementById('form');
const input = document.getElementById('input');
const button = form.querySelector('button');
const messages = document.getElementById('messages');
const status = document.getElementById('status');
const feedback = document.getElementById('feedback');
const latest = document.getElementById('latest');
const pageTitle = document.title;
let pending = false;
let scrollRemainder = 0;
let unread = 0;
// Own anchoring while retention can remove earlier messages from the list.
messages.style.overflowAnchor = 'none';

function followingLatest() {
  return messages.scrollHeight - messages.clientHeight - messages.scrollTop <= 24;
}

function pageActive() {
  return document.visibilityState === 'visible' && document.hasFocus();
}

function clearUnread() {
  unread = 0;
  latest.hidden = true;
  latest.textContent = 'Jump to latest';
  document.title = pageTitle;
}

function clearVisibleUnread() {
  if (pageActive() && followingLatest()) clearUnread();
}

function captureReadingPosition() {
  const following = followingLatest();
  const top = messages.getBoundingClientRect().top;
  const anchor = following ? null : [...messages.children].find((item) => item.getBoundingClientRect().bottom > top);
  return { following, anchor, offset: anchor ? anchor.getBoundingClientRect().top - top : 0 };
}

function restoreReadingPosition({ following, anchor, offset }) {
  if (following) {
    scrollRemainder = 0;
    messages.scrollTop = messages.scrollHeight;
  } else if (anchor?.isConnected) {
    const target = messages.scrollTop + anchor.getBoundingClientRect().top - messages.getBoundingClientRect().top - offset + scrollRemainder;
    messages.scrollTop = target;
    // Carry subpixel correction so rounded scrollTop values do not accumulate drift.
    scrollRemainder = target - messages.scrollTop;
  } else {
    // Evicted text cannot be recovered; stay at the retained-history boundary.
    messages.scrollTop = 0;
    scrollRemainder = 0;
  }
}

let readingPosition;
let layoutWidth;
let layoutHeight;
let contentHeight;
function rememberReadingPosition() {
  readingPosition = captureReadingPosition();
  layoutWidth = messages.clientWidth;
  layoutHeight = messages.clientHeight;
  contentHeight = messages.scrollHeight;
}

function layoutChanged() {
  return layoutWidth !== messages.clientWidth || layoutHeight !== messages.clientHeight ||
    contentHeight !== messages.scrollHeight;
}

function restoreReflowedPosition() {
  if (!layoutChanged()) return;
  restoreReadingPosition(readingPosition);
  rememberReadingPosition();
  clearVisibleUnread();
}

rememberReadingPosition();
// Text can reflow inside a fixed-size panel. Observe retained items too.
const readingObserver = new ResizeObserver(restoreReflowedPosition);
readingObserver.observe(messages);
messages.addEventListener('scroll', () => {
  // Reflow can itself dispatch scroll before ResizeObserver restores the old anchor.
  if (layoutChanged()) return;
  rememberReadingPosition();
  clearVisibleUnread();
});
window.addEventListener('focus', clearVisibleUnread);
document.addEventListener('visibilitychange', clearVisibleUnread);

latest.addEventListener('click', () => {
  // Keep keyboard focus in the conversation when its navigation control disappears.
  messages.focus({ preventScroll: true });
  messages.scrollTop = messages.scrollHeight;
  scrollRemainder = 0;
  rememberReadingPosition();
  clearUnread();
});

function updateConnection(text) {
  status.textContent = text;
  button.disabled = !socket.connected || pending;
}

socket.on('connect', () => updateConnection('Connected · messages are live'));
socket.on('disconnect', () => updateConnection('Disconnected · reconnecting'));
socket.on('connect_error', () => updateConnection('Unable to connect · retrying'));

socket.on('chat message', (text) => {
  // A broadcast can arrive before the observer delivers a pending reflow.
  restoreReflowedPosition();
  const position = captureReadingPosition();
  const item = document.createElement('li');
  item.textContent = text;
  messages.appendChild(item);
  readingObserver.observe(item);
  while (messages.children.length > 200) {
    const oldest = messages.firstElementChild;
    readingObserver.unobserve(oldest);
    oldest.remove();
  }
  document.getElementById('empty').hidden = true;
  restoreReadingPosition(position);
  rememberReadingPosition();
  if (position.following && pageActive()) {
    clearUnread();
  } else {
    // Counts describe arrivals still available in this page's retained window.
    unread = Math.min(unread + 1, 200);
    latest.textContent = `${unread} new ${unread === 1 ? 'message' : 'messages'} · Jump to latest`;
    latest.hidden = false;
    document.title = `(${unread}) ${pageTitle}`;
  }
});

form.addEventListener('submit', (event) => {
  event.preventDefault();
  if (!socket.connected) {
    feedback.textContent = 'You are offline. Your draft has not been sent.';
    return;
  }
  if (pending) return;
  const draft = input.value;
  pending = true;
  button.disabled = true;
  feedback.textContent = '';
  // Let the live transport queue this text behind an in-flight polling write.
  socket.timeout(3000).emit('chat message', draft, (error, response) => {
    pending = false;
    button.disabled = !socket.connected;
    if (error) {
      feedback.textContent = input.value === draft
        ? 'Delivery is uncertain. Your draft is kept; check the conversation before sending again.'
        : `Delivery is uncertain. Your current draft is unchanged. Check the conversation before resending this earlier message:\n${draft}`;
    } else if (!response.ok) {
      feedback.textContent = response.error;
    } else if (input.value === draft) {
      input.value = '';
    }
  });
  // Heartbeat expiry can enqueue despite connected=true. Never replay that attempt.
  socket.sendBuffer.length = 0;
});
