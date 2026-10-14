const { test }=require('node:test');
const assert=require('node:assert/strict');
const { createHash }=require('node:crypto');
const fs=require('node:fs');
const { join }=require('node:path');
const { tmpdir }=require('node:os');
const { spawnSync }=require('node:child_process');
const { RoomsStore }=require('../rooms-store.cjs');
const { renderRecord,validateRecord }=require('../record-export.cjs');
const { createRoomsServer }=require('../rooms-server.cjs');
const { populate }=require('./record-fixture.cjs');
function fixture(t) {const store=new RoomsStore(':memory:');t.after(()=>store.close());const f=populate(store);return {...f,store,record:JSON.parse(JSON.stringify(store.export(f.room.id)))};}

test('delivered fictional reader matches its inspectable JSON source and current renderer',()=>{
  const record=JSON.parse(fs.readFileSync(join(__dirname,'../examples/cistern-handover.json'),'utf8'));
  assert.equal(fs.readFileSync(join(__dirname,'../examples/cistern-handover.html'),'utf8'),renderRecord(record));
});

test('renderer preserves complete schema-1 export and confines hostile source text to inert JSON',t=>{
  const f=fixture(t),html=renderRecord(f.record);
  const payload=html.match(/<script id="record-data" type="application\/json">([\s\S]*?)<\/script>/)[1];
  assert.deepEqual(JSON.parse(payload),f.record);assert.ok(!payload.includes('<'));
  assert.equal(f.record.actions.find(a=>a.id===f.action.id).history.length,63);
  assert.ok(!html.includes(f.person.token));assert.ok(!html.includes('Other-room record must stay out'));
  assert.ok(!html.includes('token_hash'));assert.ok(!html.includes('<img'));
  const script=html.match(/<script>([\s\S]*?)<\/script>/)[1],style=html.match(/<style>([\s\S]*?)<\/style>/)[1];
  for(const value of [script,style])assert.ok(html.includes(`sha256-${createHash('sha256').update(value).digest('base64')}`));
  assert.ok(html.includes(createHash('sha256').update(JSON.stringify(f.record)).digest('hex')));
});
test('legacy exports without action data and empty modern records remain usable without invented work',t=>{
  const f=fixture(t),legacy={schema:1,exported_at:f.record.exported_at,project:f.record.project,entries:[]};
  assert.equal(validateRecord(legacy),legacy);assert.ok(renderRecord(legacy).includes('record-data'));
  assert.doesNotThrow(()=>renderRecord({...legacy,actions:[]}));
});
test('converter rejects incompatible, incomplete and contradictory records without silently repairing them',t=>{
  const f=fixture(t);
  const mutations=[
    r=>r.schema=2,r=>r.token='must not be rendered',r=>r.project.extra=true,
    r=>r.entries[1].id=r.entries[0].id,r=>r.entries[1].created_at='yesterday',
    r=>r.entries[0].kind='other',r=>r.entries[0].body='x'.repeat(501),
    r=>r.actions[0].room_id=f.other.id,r=>r.actions[0].history.pop(),
    r=>r.actions[0].history[0].action.source_id=null,
    r=>r.actions[0].history[0].action.owner_name='Invented label',
    r=>r.actions[0].history[1].id=r.actions[0].history[0].id,
    r=>r.actions[0].title='Root differs from final event',
    r=>r.actions[0].decision_body='Invented decision',
    r=>r.actions[0].history[0].action.status='done',
    r=>r.actions[0].history[1].action.note=''
  ];
  // Work ordering is deliberately not assumed when selecting a history fixture.
  f.record.actions.sort((a,b)=>b.revision-a.revision);
  for(const mutate of mutations){const changed=structuredClone(f.record);mutate(changed);assert.throws(()=>renderRecord(changed),/Invalid project record/);}
  assert.throws(()=>renderRecord(null),/Invalid project record/);
});
test('revision order remains authoritative when a recorded machine clock moves backwards',t=>{
  const f=fixture(t),action=f.record.actions.find(a=>a.id===f.action.id);
  action.history[1].created_at='2000-01-01T00:00:00.000Z';action.history[1].action.updated_at=action.history[1].created_at;
  assert.doesNotThrow(()=>renderRecord(f.record));
});
test('CLI runs outside source, refuses overwrites and leaves invalid inputs unpublished',t=>{
  const f=fixture(t),dir=fs.mkdtempSync(join(tmpdir(),'p11-reading-cli-'));t.after(()=>fs.rmSync(dir,{recursive:true,force:true}));
  const input=join(dir,'input.json'),output=join(dir,'reader.html'),cli=join(__dirname,'../rooms-record.cjs');
  fs.writeFileSync(input,JSON.stringify(f.record));
  const run=(...args)=>spawnSync(process.execPath,[cli,...args],{cwd:dir,encoding:'utf8'});
  let result=run(input,output);assert.equal(result.status,0,result.stderr);const bytes=fs.readFileSync(output);
  assert.match(result.stdout,/Reading copy created/);
  assert.notEqual(run(input,output).status,0);assert.deepEqual(fs.readFileSync(output),bytes);
  assert.notEqual(run(input,input).status,0);assert.deepEqual(JSON.parse(fs.readFileSync(input,'utf8')),f.record);
  const link=join(dir,'link.html');fs.symlinkSync(output,link);assert.notEqual(run(input,link).status,0);assert.deepEqual(fs.readFileSync(output),bytes);
  fs.writeFileSync(input,JSON.stringify({...f.record,schema:7}));const invalid=join(dir,'invalid.html');assert.notEqual(run(input,invalid).status,0);assert.ok(!fs.existsSync(invalid));
  assert.equal(run('--help').status,0);assert.notEqual(run().status,0);
});
test('authenticated HTTP export keeps JSON semantics, database schema and snapshot scope intact',async t=>{
  const runtime=createRoomsServer();await new Promise(resolve=>runtime.server.listen(0,'127.0.0.1',resolve));t.after(()=>new Promise(resolve=>runtime.io.close(resolve)));
  const f=populate(runtime.store),base=`http://127.0.0.1:${runtime.server.address().port}/api/studio/rooms/`,url=base+f.room.id+'/reading',headers={Authorization:`Bearer ${f.person.token}`};
  assert.equal((await fetch(url)).status,401);
  const before=JSON.parse(JSON.stringify(runtime.store.export(f.room.id))),schema=runtime.store.db.prepare('PRAGMA user_version').get().user_version;
  const response=await fetch(url,{headers});assert.equal(response.status,200);assert.match(response.headers.get('content-type'),/text\/html/);assert.match(response.headers.get('content-disposition'),/attachment.*reading.html/);
  const html=await response.text(),snapshot=JSON.parse(html.match(/<script id="record-data" type="application\/json">([\s\S]*?)<\/script>/)[1]);
  assert.deepEqual(snapshot.entries,before.entries);assert.deepEqual(snapshot.actions,before.actions);
  f.append('Later real store write in fixture');assert.ok(!html.includes('Later real store write'));
  const json=await (await fetch(base+f.room.id+'/export',{headers})).json();assert.equal(json.schema,1);assert.equal(json.entries.length,before.entries.length+1);
  assert.equal(runtime.store.db.prepare('PRAGMA user_version').get().user_version,schema);
  assert.equal((await fetch(base+'missing/reading',{headers})).status,400);
});
