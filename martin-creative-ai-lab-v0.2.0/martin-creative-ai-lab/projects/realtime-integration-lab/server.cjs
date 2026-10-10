const express = require('express');
const http = require('node:http');
const path = require('node:path');
const { Server } = require('socket.io');

const MAX_MESSAGE_LENGTH = 500;

function createChatServer() {
  const app = express();
  app.disable('x-powered-by');
  app.get('/health', (_request, response) => response.json({ status: 'ok' }));
  app.use(express.static(path.join(__dirname, 'public')));

  const server = http.createServer(app);
  const io = new Server(server, { maxHttpBufferSize: 16 * 1024 });
  io.on('connection', (socket) => {
    socket.on('chat message', (payload, acknowledge) => {
      let error;
      if (typeof payload !== 'string') error = 'Message must be text.';
      else if (!payload.trim()) error = 'Enter a non-empty message.';
      else if (payload.length > MAX_MESSAGE_LENGTH) error = 'Use at most 500 characters.';

      if (error) {
        if (typeof acknowledge === 'function') acknowledge({ ok: false, error });
        return;
      }

      // The sender receives the same broadcast as everyone else; no optimistic copy.
      io.emit('chat message', payload.trim());
      if (typeof acknowledge === 'function') acknowledge({ ok: true });
    });
  });
  return { server, io };
}

if (require.main === module) {
  const port = Number(process.env.PORT || 3000);
  if (!Number.isInteger(port) || port < 1 || port > 65535) {
    console.error('PORT must be an integer from 1 to 65535.');
    process.exit(1);
  }
  const { server, io } = createChatServer();
  const host = process.env.HOST || '127.0.0.1';
  server.on('error', (error) => {
    console.error(`Chat startup failed: ${error.message}`);
    process.exitCode = 1;
  });
  server.listen(port, host, () => console.log(`P11 chat listening on ${host}:${port}`));
  for (const signal of ['SIGINT', 'SIGTERM']) {
    process.once(signal, () => io.close());
  }
}

module.exports = { createChatServer, MAX_MESSAGE_LENGTH };
