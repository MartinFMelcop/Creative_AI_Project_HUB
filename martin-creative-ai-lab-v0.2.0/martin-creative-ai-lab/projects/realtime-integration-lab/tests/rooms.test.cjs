const assert=require('node:assert/strict');
const { test }=require('node:test');
const { mkdtempSync,rmSync }=require('node:fs');
const { tmpdir }=require('node:os');
const { join }=require('node:path');
const { randomUUID }=require('node:crypto');
const { DatabaseSync }=require('node:sqlite');
const { io }=require('socket.io-client');
const { RoomsStore }=require('../rooms-store.cjs');
const { createRoomsServer }=require('../rooms-server.cjs');
const send=(socket,event,payload)=>new Promise((resolve,reject)=>socket.timeout(2000).emit(event,payload,(error,value)=>error?reject(error):resolve(value)));
const entry=(roomId,body='A project note',kind='note')=>({roomId,body,kind,clientId:randomUUID()});
async function start(dbPath=':memory:') {
  const runtime=createRoomsServer({dbPath});
  await new Promise(resolve=>runtime.server.listen(0,'127.0.0.1',resolve));
  return {...runtime,url:`http://127.0.0.1:${runtime.server.address().port}`};
}
async function stop(runtime) { await new Promise(resolve=>runtime.io.close(resolve)); }
async function connect(runtime,token) {
  const client=io(`${runtime.url}/studio`,{auth:{token},autoConnect:false,reconnection:false});
  await new Promise((resolve,reject)=>{client.once('connect',resolve);client.once('connect_error',reject);client.connect();});return client;
}
test('SQLite stores identity, ordered history and decisions across restart; tokens are hashed',()=>{
  const dir=mkdtempSync(join(tmpdir(),'p11-rooms-')),file=join(dir,'rooms.sqlite');
  try {
    let store=new RoomsStore(file);const who=store.session('Mara'),room=store.createRoom('Native playtest');
    const note=entry(room.id,'Amber warning is readable'),decision=entry(room.id,'Keep the two-phase encounter','decision');
    store.append(who,note);store.append(who,decision);
    assert.notEqual(store.db.prepare('SELECT token_hash FROM sessions').get().token_hash,who.token);
    store.close();store=new RoomsStore(file);
    assert.equal(store.authenticate(who.token).name,'Mara');
    assert.deepEqual(store.history(room.id).messages.map(m=>m.body),[note.body,decision.body]);
    assert.equal(store.decisions(room.id)[0].kind,'decision');
    assert.deepEqual(store.export(room.id).entries.map(m=>m.body),[note.body,decision.body]);store.close();
  } finally {rmSync(dir,{recursive:true,force:true});}
});
test('storage rejects invalid content, conflicting retries and duplicate project names',()=>{
  const store=new RoomsStore(':memory:');
  try {
    const who=store.session('Iven'),room=store.createRoom('Route planning'),payload=entry(room.id);
    assert.throws(()=>store.session(' '));assert.throws(()=>store.createRoom('route PLANNING'));
    for(const body of ['',{},'a'.repeat(501)])assert.throws(()=>store.append(who,{...payload,body}));
    assert.throws(()=>store.append(who,{...payload,kind:'invented'}));
    assert.throws(()=>store.history(room.id,-1));assert.equal(store.authenticate('wrong'),null);
    assert.equal(store.append(who,payload).inserted,true);assert.equal(store.append(who,payload).inserted,false);
    assert.throws(()=>store.append(who,{...payload,body:'Changed attempt'}));
    assert.equal(store.history(room.id).messages.length,1);
  } finally {store.close();}
});
test('history pagination is chronological, bounded and complete; export omits identity credentials',()=>{
  const store=new RoomsStore(':memory:');
  try {
    const who=store.session('Keeper'),room=store.createRoom('Repair log');
    for(let i=0;i<123;i++)store.append(who,entry(room.id,`Work ${i}`));
    let page=store.history(room.id),all=page.messages;
    assert.equal(page.messages.length,50);assert.equal(page.messages.at(-1).body,'Work 122');
    while(page.hasMore){page=store.history(room.id,page.before);all=[...page.messages,...all];}
    assert.equal(new Set(all.map(m=>m.id)).size,123);assert.equal(all[0].body,'Work 0');
    const exported=JSON.stringify(store.export(room.id));assert.equal(exported.includes(who.token),false);assert.equal(exported.includes('token_hash'),false);
  } finally {store.close();}
});
test('newer database schemas are refused without downgrading their version',()=>{
  const dir=mkdtempSync(join(tmpdir(),'p11-schema-')),file=join(dir,'rooms.sqlite');
  try {const db=new DatabaseSync(file);db.exec('PRAGMA user_version=3');db.close();assert.throws(()=>new RoomsStore(file),/newer/);
    const reopened=new DatabaseSync(file);assert.equal(reopened.prepare('PRAGMA user_version').get().user_version,3);reopened.close();
  } finally {rmSync(dir,{recursive:true,force:true});}
});
test('real sockets isolate projects, switch rooms and deduplicate uncertain retries',async()=>{
  const runtime=await start(),clients=[];
  try {
    const a=runtime.store.session('Mara'),b=runtime.store.session('Senn');
    const one=runtime.store.createRoom('Flood'),two=runtime.store.createRoom('Rhythm');
    for(const session of [a,b])clients.push(await connect(runtime,session.token));
    const arrivals=[[],[]];clients.forEach((c,i)=>c.on('project entry',m=>arrivals[i].push(m)));
    assert.equal((await send(clients[0],'join project',one.id)).ok,true);
    await send(clients[1],'join project',two.id);
    const payload=entry(one.id,'A decision','decision');
    assert.equal((await send(clients[0],'project entry',payload)).duplicate,false);
    assert.equal((await send(clients[0],'project entry',payload)).duplicate,true);
    assert.equal((await send(clients[0],'project entry',entry(two.id))).ok,false);
    const snapshot=await send(clients[1],'join project',one.id);
    assert.equal(snapshot.messages.length,1);assert.equal(snapshot.decisions.length,1);
    const heard=new Promise(resolve=>clients[1].once('project entry',resolve));
    await send(clients[0],'project entry',entry(one.id,'Joined response'));await heard;
    assert.equal(arrivals[0].filter(m=>m.client_id===payload.clientId).length,1);
    assert.equal(arrivals[1].length,1);
  } finally {clients.forEach(c=>c.close());await stop(runtime);}
});
test('HTTP and namespace require local identity; malformed requests are rejected; legacy remains separate',async()=>{
  const runtime=await start();
  try {
    assert.equal((await fetch(`${runtime.url}/api/studio/rooms`)).status,401);
    const invalid=io(`${runtime.url}/studio`,{auth:{token:'wrong'},reconnection:false});
    await new Promise(resolve=>invalid.once('connect_error',resolve));invalid.close();
    const created=await fetch(`${runtime.url}/api/studio/sessions`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name:'Reader'})});
    const session=await created.json();assert.equal(created.status,201);
    const headers={'Authorization':`Bearer ${session.token}`,'Content-Type':'application/json'};
    assert.equal((await fetch(`${runtime.url}/api/studio/rooms`,{method:'POST',headers,body:'{bad'})).status,400);
    assert.equal((await fetch(`${runtime.url}/health`)).status,200);
    assert.match(await (await fetch(runtime.url)).text(),/Live exchange/);
  } finally {await stop(runtime);}
});
