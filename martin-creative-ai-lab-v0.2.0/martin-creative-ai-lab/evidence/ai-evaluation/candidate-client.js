const socket = io();
const form = document.getElementById('form');
const input = document.getElementById('input');
const button = form.querySelector('button');
const messages = document.getElementById('messages');
const status = document.getElementById('status');
const feedback = document.getElementById('feedback');
let pending = false;

function updateConnection(text) {
  status.textContent = text;
  button.disabled = !socket.connected || pending;
}

socket.on('connect', () => updateConnection('Connected · messages are live'));
socket.on('disconnect', () => updateConnection('Disconnected · reconnecting'));
socket.on('connect_error', () => updateConnection('Unable to connect · retrying'));

socket.on('chat message', (text) => {
  const item = document.createElement('li');
  item.textContent = text;
  messages.appendChild(item);
  while (messages.children.length > 200) messages.firstElementChild.remove();
  document.getElementById('empty').hidden = true;
  messages.scrollTop = messages.scrollHeight;
});

form.addEventListener('submit', (event) => {
  event.preventDefault();
  // Socket.IO may still report connected after the heartbeat has expired.
  // Check the same liveness condition as emit before allowing a buffered send.
  const engine = socket.io.engine;
  if (!socket.connected || !engine || engine.readyState !== 'open' || engine._hasPingExpired()) {
    feedback.textContent = 'You are offline. Your draft has not been sent.';
    return;
  }
  if (pending) return;
  const draft = input.value;
  pending = true;
  button.disabled = true;
  feedback.textContent = '';
  // A regular emission queues behind a busy live transport. The liveness check
  // above prevents offline buffering; an acknowledgement timeout never retries.
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
});
