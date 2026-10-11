const socket = io();
const form = document.getElementById('form');
const input = document.getElementById('input');
const button = form.querySelector('button');
const messages = document.getElementById('messages');
const status = document.getElementById('status');
const feedback = document.getElementById('feedback');
const latest = document.getElementById('latest');
let pending = false;
let scrollRemainder = 0;
let unread = 0;
// Own anchoring while retention can remove earlier messages from the list.
messages.style.overflowAnchor = 'none';

function followingLatest() {
  return messages.scrollHeight - messages.clientHeight - messages.scrollTop <= 24;
}

function clearUnread() {
  unread = 0;
  latest.hidden = true;
  latest.textContent = 'Jump to latest';
}

messages.addEventListener('scroll', () => {
  if (followingLatest()) clearUnread();
});

latest.addEventListener('click', () => {
  // Keep keyboard focus in the conversation when its navigation control disappears.
  messages.focus({ preventScroll: true });
  messages.scrollTop = messages.scrollHeight;
  scrollRemainder = 0;
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
  const following = followingLatest();
  const top = messages.getBoundingClientRect().top;
  const anchor = following ? null : [...messages.children].find((item) => item.getBoundingClientRect().bottom > top);
  const offset = anchor ? anchor.getBoundingClientRect().top - top : 0;
  const item = document.createElement('li');
  item.textContent = text;
  messages.appendChild(item);
  while (messages.children.length > 200) messages.firstElementChild.remove();
  document.getElementById('empty').hidden = true;
  if (following) {
    scrollRemainder = 0;
    messages.scrollTop = messages.scrollHeight;
    clearUnread();
  } else if (anchor?.isConnected) {
    // Preserve content position, including when variable-height earlier items expire.
    const target = messages.scrollTop + anchor.getBoundingClientRect().top - messages.getBoundingClientRect().top - offset + scrollRemainder;
    messages.scrollTop = target;
    // Carry subpixel correction so rounded scrollTop values do not accumulate drift.
    scrollRemainder = target - messages.scrollTop;
  } else {
    // Evicted text cannot be recovered; stay at the retained-history boundary.
    messages.scrollTop = 0;
    scrollRemainder = 0;
  }
  if (!following) {
    // Counts describe arrivals still available in this page's retained window.
    unread = Math.min(unread + 1, 200);
    latest.textContent = `${unread} new ${unread === 1 ? 'message' : 'messages'} · Jump to latest`;
    latest.hidden = false;
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
      feedback.textContent = 'Delivery is uncertain. Your draft is kept; check the conversation before sending again.';
    } else if (!response.ok) {
      feedback.textContent = response.error;
    } else if (input.value === draft) {
      input.value = '';
    }
  });
  // Heartbeat expiry can enqueue despite connected=true. Never replay that attempt.
  socket.sendBuffer.length = 0;
});
