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
  if (!socket.connected) {
    feedback.textContent = 'You are offline. Your draft has not been sent.';
    return;
  }
  if (pending) return;
  const draft = input.value;
  pending = true;
  button.disabled = true;
  feedback.textContent = '';
  // Volatile emission prevents offline buffering. A timeout never triggers a retry.
  socket.timeout(3000).volatile.emit('chat message', draft, (error, response) => {
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
