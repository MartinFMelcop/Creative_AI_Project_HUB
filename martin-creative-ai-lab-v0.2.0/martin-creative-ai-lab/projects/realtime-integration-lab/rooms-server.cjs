const express = require('express');
const path = require('node:path');
const { createChatServer } = require('./server.cjs');
const { RoomsStore } = require('./rooms-store.cjs');

function createRoomsServer({ dbPath = ':memory:' } = {}) {
  const store = new RoomsStore(dbPath);
  const runtime = createChatServer();
  const { app, io, server } = runtime;
  app.use('/api/studio', express.json({ limit:'8kb' }));
  const route = (handler) => (req,res) => {
    try { handler(req,res); }
    catch (error) { res.status(400).json({ error:error.message }); }
  };
  app.post('/api/studio/sessions',route((req,res) => res.status(201).json(store.session(req.body?.name))));
  app.use('/api/studio', (req,res,next) => {
    req.participant = store.authenticate(req.get('Authorization')?.replace(/^Bearer /,''));
    if (!req.participant) return res.status(401).json({ error:'Your local identity is unavailable. Start a new session.' });
    next();
  });
  app.get('/api/studio/me',route((req,res) => res.json(req.participant)));
  app.get('/api/studio/rooms',route((_req,res) => res.json(store.rooms())));
  app.post('/api/studio/rooms',route((req,res) => {
    const room = store.createRoom(req.body?.name);
    io.of('/studio').emit('rooms changed');
    res.status(201).json(room);
  }));
  app.get('/api/studio/rooms/:id/history',route((req,res) => res.json(store.history(req.params.id,req.query.before === undefined ? undefined : Number(req.query.before)))));
  app.get('/api/studio/rooms/:id/search',route((req,res) => res.json(store.records.search(req.params.id,req.query))));
  app.get('/api/studio/rooms/:id/context/:kind/:record',route((req,res) => res.json(store.records.context(req.params.id,req.params.kind,Number(req.params.record)))));
  app.get('/api/studio/rooms/:id/actions',route((req,res)=>res.json(store.work.snapshot(req.params.id))));
  app.get('/api/studio/rooms/:id/action-attempts/:attempt',route((req,res)=>res.json(store.work.receipt(req.participant,req.params.id,req.params.attempt))));
  app.get('/api/studio/rooms/:id/actions/:action/history',route((req,res)=>res.json(store.work.history(req.params.action,req.params.id))));
  app.get('/api/studio/rooms/:id/export',route((req,res) => {
    res.set('Content-Disposition','attachment; filename="project-conversation.json"').json(store.export(req.params.id));
  }));
  app.use('/api/studio', (error,_req,res,_next) => res.status(400).json({ error:'Invalid JSON request.' }));

  const namespace = io.of('/studio');
  namespace.use((socket,next) => {
    const session = store.authenticate(socket.handshake.auth?.token);
    if (!session) return next(new Error('Local identity required.'));
    socket.data.session = session;
    next();
  });
  namespace.on('connection', (socket) => {
    function reply(ack, action) {
      if (typeof ack !== 'function') return;
      try { ack({ ok:true, ...action() }); }
      catch (error) { ack({ ok:false,error:error.message,...(error.code==='conflict'?{code:'conflict',action:error.action}:{}) }); }
    }
    socket.on('join project',(roomId,ack) => reply(ack,() => {
      const room = store.room(roomId);
      if (socket.data.roomId) socket.leave(socket.data.roomId);
      socket.data.roomId = room.id;
      socket.join(room.id);
      store.work.join(room.id,socket.data.session);
      namespace.to(room.id).emit('project members',{roomId:room.id,members:store.work.members(room.id)});
      // Synchronous DB snapshot and namespace join cannot interleave an append.
      return { room, ...store.history(room.id), decisions:store.decisions(room.id),...store.work.snapshot(room.id) };
    }));
    socket.on('project entry',(payload,ack) => reply(ack,() => {
      if (payload?.roomId !== socket.data.roomId) throw new Error('Join this project before sending.');
      const result = store.append(socket.data.session,payload);
      if (result.inserted) namespace.to(payload.roomId).emit('project entry',result.message);
      return { message:result.message, duplicate:!result.inserted };
    }));
    socket.on('project action',(payload,ack)=>reply(ack,()=>{
      if(payload?.roomId!==socket.data.roomId)throw new Error('Join this project before changing actions.');
      const result=store.work.apply(socket.data.session,payload);
      if(!result.duplicate)namespace.to(payload.roomId).emit('project action',result);
      return result;
    }));
  });
  server.once('close',() => store.close());
  return { ...runtime, store };
}

if (require.main === module) {
  const port = Number(process.env.PORT || 3000);
  if (!Number.isInteger(port) || port < 1 || port > 65535) throw new Error('PORT must be 1–65535.');
  const dbPath = process.env.ROOMS_DB || path.join(__dirname,'data','rooms.sqlite');
  const { server,io } = createRoomsServer({ dbPath });
  const host = process.env.HOST || '127.0.0.1';
  server.on('error',error => { console.error(error.message); io.close(); process.exitCode=1; });
  server.listen(port,host,() => console.log(`P11 Project Rooms: http://${host}:${port}/studio/`));
  for (const signal of ['SIGINT','SIGTERM']) process.once(signal,() => io.close());
}
module.exports = { createRoomsServer };
