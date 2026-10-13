const {test}=require('node:test');
const assert=require('node:assert/strict');
const {randomUUID}=require('node:crypto');
const fs=require('node:fs');
const {join}=require('node:path');
const {tmpdir}=require('node:os');
const {DatabaseSync}=require('node:sqlite');
const {RoomsStore}=require('../rooms-store.cjs');
const {initialize}=require('../rooms-schema.cjs');
const {validateActionData}=require('../rooms-actions.cjs');
const {createBackup,inspectBackup,restoreBackup}=require('../rooms-backup.cjs');
const {createRoomsServer}=require('../rooms-server.cjs');
const {io}=require('socket.io-client');
function fixture(t) {
  const dir=fs.mkdtempSync(join(tmpdir(),'p11-actions-')),file=join(dir,'rooms.sqlite'),store=new RoomsStore(file);
  t.after(()=>{store.close();fs.rmSync(dir,{recursive:true,force:true});});
  const a=store.session('Rook'),b=store.session('Neri'),room=store.createRoom('Native release');
  store.work.join(room.id,a);store.work.join(room.id,b);
  const decision=store.append(a,{roomId:room.id,clientId:randomUUID(),kind:'decision',body:'Deliver an executable native trial.'}).message;
  const command={op:'create',roomId:room.id,clientId:randomUUID(),sourceId:decision.id,title:'Package the native trial',ownerId:b.id};
  const update=(action,changes={})=>({op:'update',roomId:room.id,clientId:randomUUID(),actionId:action.id,expectedRevision:action.revision,title:action.title,ownerId:action.owner_id,status:action.status,note:action.note,...changes});
  return {dir,file,store,a,b,room,decision,command,update};
}
test('decision to assigned work, blockers, completion and reopening retain an auditable history',t=>{
  const f=fixture(t);let task=f.store.work.apply(f.a,f.command).action;
  assert.equal(task.source_id,f.decision.id);assert.equal(task.owner_name,'Neri');
  task=f.store.work.apply(f.b,f.update(task,{status:'doing'})).action;
  task=f.store.work.apply(f.b,f.update(task,{status:'blocked',note:'Waiting for the runtime installation.'})).action;
  task=f.store.work.apply(f.a,f.update(task,{status:'doing',note:'Runtime supplied.'})).action;
  task=f.store.work.apply(f.b,f.update(task,{status:'done',note:'Native package opened outside source; three stages completed.'})).action;
  assert.throws(()=>f.store.work.apply(f.a,f.update(task,{status:'doing',note:''})),/reason/);
  assert.throws(()=>f.store.work.apply(f.a,f.update(task,{status:'doing'})),/new reason/);
  task=f.store.work.apply(f.a,f.update(task,{status:'doing',note:'Retest on the second machine.'})).action;
  const history=f.store.work.history(task.id,f.room.id).events;
  assert.deepEqual(history.map(e=>e.action.status),['todo','doing','blocked','doing','done','doing']);
  assert.deepEqual(history.map(e=>e.author),['Rook','Neri','Neri','Rook','Neri','Rook']);
  assert.equal(validateActionData(f.store.db).action_updates,6);
  const output=f.store.export(f.room.id);assert.equal(output.schema,1);assert.equal(output.actions[0].history.length,6);
  assert.ok(!JSON.stringify(output).includes(f.a.token));assert.ok(!JSON.stringify(output).includes('token_hash'));
});
test('immutable retries precede revision checks; changed attempts and stale writes have no effects',t=>{
  const f=fixture(t),created=f.store.work.apply(f.a,f.command),edit=f.update(created.action,{status:'doing'});
  const accepted=f.store.work.apply(f.b,edit);
  f.store.work.apply(f.a,f.update(accepted.action,{status:'blocked',note:'Need confirmation.'}));
  const retried=f.store.work.apply(f.b,edit);assert.equal(retried.duplicate,true);assert.equal(retried.action.revision,2);
  assert.equal(f.store.work.snapshot(f.room.id).actions[0].revision,3);
  assert.throws(()=>f.store.work.apply(f.b,{...edit,note:'Changed'}),/different action content/);
  assert.throws(()=>f.store.work.apply(f.a,{...edit,clientId:randomUUID()}),e=>e.code==='conflict'&&e.action.revision===3);
  assert.equal(f.store.work.history(created.action.id,f.room.id).events.length,3);
  assert.equal(f.store.work.receipt(f.b,f.room.id,edit.clientId).accepted,true);
  assert.equal(f.store.work.receipt(f.a,f.room.id,edit.clientId).accepted,false);
});
test('invalid linkage, ownership, outcomes and unchanged edits cannot create partial events',t=>{
  const f=fixture(t),other=f.store.createRoom('Other project'),outsider=f.store.session('Visitor');
  const note=f.store.append(f.a,{roomId:f.room.id,clientId:randomUUID(),kind:'note',body:'Discussion only'}).message;
  for(const bad of [{sourceId:note.id},{ownerId:outsider.id},{title:''},{title:'x'.repeat(141)},{status:'done',note:'Result'},{sourceId:-1},{sourceId:f.decision.id,roomId:other.id}])
    assert.throws(()=>f.store.work.apply(f.a,{...f.command,clientId:randomUUID(),...bad}));
  assert.equal(f.store.work.snapshot(f.room.id).actions.length,0);
  const created=f.store.work.apply(f.a,f.command).action;
  assert.throws(()=>f.store.work.apply(f.a,f.update(created)),/Make a change/);
  for(const status of ['done','blocked'])assert.throws(()=>f.store.work.apply(f.a,f.update(created,{status,note:''})),/outcome/);
  assert.equal(f.store.work.history(created.id,f.room.id).events.length,1);
});
test('schema-1 data migrates transactionally without losing identities, entries or decision links',t=>{
  const dir=fs.mkdtempSync(join(tmpdir(),'p11-migrate-')),file=join(dir,'old.sqlite');t.after(()=>fs.rmSync(dir,{recursive:true,force:true}));
  let db=new DatabaseSync(file);initialize(db,1);
  const sid=randomUUID(),rid=randomUUID(),now=new Date().toISOString();
  db.prepare('INSERT INTO sessions VALUES (?,?,?)').run(sid,'Previous author','a'.repeat(64));db.prepare('INSERT INTO rooms VALUES (?,?,?)').run(rid,'Previous project',now);
  db.prepare('INSERT INTO entries(room_id,session_id,client_id,kind,body,created_at) VALUES (?,?,?,?,?,?)').run(rid,sid,randomUUID(),'decision','Keep prior records.',now);db.close();
  const store=new RoomsStore(file);try {
    assert.equal(store.db.prepare('PRAGMA user_version').get().user_version,2);
    assert.equal(store.history(rid).messages[0].body,'Keep prior records.');assert.equal(store.work.members(rid)[0].id,sid);
    store.work.apply({id:sid,name:'Previous author'},{op:'create',roomId:rid,clientId:randomUUID(),title:'Continue the prior decision',sourceId:1,ownerId:sid});
    assert.equal(validateActionData(store.db).actions,1);
  }finally{store.close();}
});
test('live backup/restore preserves action history, owner identity and accepted retry receipts',async t=>{
  const f=fixture(t),created=f.store.work.apply(f.a,f.command).action,edit=f.update(created,{status:'done',note:'Executed outside source.'});f.store.work.apply(f.b,edit);
  const bundle=join(f.dir,'savepoint'),saved=await createBackup(f.file,bundle);assert.equal(saved.schema,2);assert.equal(saved.summary.action_updates,2);
  await inspectBackup(bundle);const restored=join(f.dir,'recovered.sqlite');await restoreBackup(bundle,restored,saved.database.sha256);
  const recovered=new RoomsStore(restored);try {
    assert.equal(recovered.authenticate(f.b.token).id,f.b.id);assert.equal(recovered.work.apply(f.b,edit).duplicate,true);
    assert.equal(recovered.work.history(created.id,f.room.id).events.length,2);assert.equal(recovered.work.snapshot(f.room.id).actions[0].status,'done');
  }finally{recovered.close();}
});
test('a schema-1 backup remains inspectable/restorable and upgrades only on application open',async t=>{
  const dir=fs.mkdtempSync(join(tmpdir(),'p11-old-backup-')),file=join(dir,'old.sqlite');t.after(()=>fs.rmSync(dir,{recursive:true,force:true}));
  const db=new DatabaseSync(file);initialize(db,1);db.close();const bundle=join(dir,'bundle');
  await createBackup(file,bundle);assert.equal((await inspectBackup(bundle)).schema,1);
  const target=join(dir,'restored.sqlite');await restoreBackup(bundle,target);
  let reopened=new DatabaseSync(target);assert.equal(reopened.prepare('PRAGMA user_version').get().user_version,1);reopened.close();
  const store=new RoomsStore(target);assert.equal(store.db.prepare('PRAGMA user_version').get().user_version,2);store.close();
});
test('failed schema migration rolls back new tables and retains the previous data/version',t=>{
  const dir=fs.mkdtempSync(join(tmpdir(),'p11-rollback-')),file=join(dir,'old.sqlite');t.after(()=>fs.rmSync(dir,{recursive:true,force:true}));
  let db=new DatabaseSync(file);initialize(db,1);db.exec('CREATE TABLE actions (unexpected TEXT)');db.close();
  assert.throws(()=>new RoomsStore(file),/already exists/);
  db=new DatabaseSync(file);try {
    assert.equal(db.prepare('PRAGMA user_version').get().user_version,1);
    assert.equal(db.prepare("SELECT count(*) AS n FROM sqlite_schema WHERE name='room_members'").get().n,0);
    assert.equal(db.prepare("SELECT count(*) AS n FROM sqlite_schema WHERE name='actions'").get().n,1);
  }finally{db.close();}
});
test('tampered action/audit bytes fail semantic validation even with valid SQLite foreign keys',t=>{
  const f=fixture(t),task=f.store.work.apply(f.a,f.command).action;
  const original=f.store.db.prepare('SELECT snapshot FROM action_events').get().snapshot;
  f.store.db.prepare('UPDATE action_events SET snapshot=?').run(JSON.stringify({...JSON.parse(original),note:'Invented outcome'}));
  assert.throws(()=>validateActionData(f.store.db),/Invalid saved/);
  f.store.db.prepare('UPDATE action_events SET snapshot=?').run(original);
  f.store.db.prepare('UPDATE actions SET revision=7 WHERE id=?').run(task.id);assert.throws(()=>validateActionData(f.store.db),/Invalid saved/);
});
test('real sockets scope action broadcasts to the joined project and surface revision conflicts',async t=>{
  const runtime=createRoomsServer();await new Promise(r=>runtime.server.listen(0,'127.0.0.1',r));const clients=[];
  t.after(async()=>{clients.forEach(c=>c.close());await new Promise(r=>runtime.io.close(r));});
  const people=['First','Second','Elsewhere'].map(n=>runtime.store.session(n)),one=runtime.store.createRoom('One'),two=runtime.store.createRoom('Two');
  const send=(s,event,p)=>new Promise((resolve,reject)=>s.timeout(2000).emit(event,p,(e,r)=>e?reject(e):resolve(r)));
  for(const p of people){const c=io(`http://127.0.0.1:${runtime.server.address().port}/studio`,{auth:{token:p.token},autoConnect:false,reconnection:false});await new Promise(r=>{c.once('connect',r);c.connect();});clients.push(c);}
  await send(clients[0],'join project',one.id);await send(clients[1],'join project',one.id);await send(clients[2],'join project',two.id);
  const heard=[[],[],[]];clients.forEach((c,i)=>c.on('project action',r=>heard[i].push(r)));
  const result=await send(clients[0],'project action',{op:'create',roomId:one.id,clientId:randomUUID(),title:'Assigned work',ownerId:people[1].id});assert.equal(result.ok,true);
  const update={op:'update',roomId:one.id,clientId:randomUUID(),actionId:result.action.id,expectedRevision:1,title:'Assigned work',ownerId:people[1].id,status:'doing',note:''};
  assert.equal((await send(clients[1],'project action',update)).ok,true);
  assert.equal((await send(clients[0],'project action',{...update,clientId:randomUUID()})).code,'conflict');
  assert.equal((await send(clients[2],'project action',update)).ok,false);
  await new Promise(r=>setTimeout(r,30));assert.equal(heard[0].length,2);assert.equal(heard[1].length,2);assert.equal(heard[2].length,0);
});
