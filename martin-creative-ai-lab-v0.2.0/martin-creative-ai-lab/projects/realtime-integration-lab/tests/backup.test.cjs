const assert = require('node:assert/strict');
const { test } = require('node:test');
const fs = require('node:fs');
const { tmpdir } = require('node:os');
const { join,resolve } = require('node:path');
const { randomUUID,createHash } = require('node:crypto');
const { spawnSync } = require('node:child_process');
const { DatabaseSync } = require('node:sqlite');
const { RoomsStore } = require('../rooms-store.cjs');
const { createBackup,inspectBackup,restoreBackup } = require('../rooms-backup.cjs');
const attempt = (room,body,kind='note') => ({roomId:room.id,clientId:randomUUID(),body,kind});
function fixture(t) {
  const dir = fs.mkdtempSync(join(tmpdir(),'p11-recovery-'));
  const file = join(dir,'live.sqlite'),bundle=join(dir,'savepoint');
  const store = new RoomsStore(file);
  t.after(()=>{store.close();fs.rmSync(dir,{recursive:true,force:true});});
  return {dir,file,bundle,store};
}
function rewriteManifest(bundle) {
  const file=join(bundle,'workspace.sqlite'),manifestFile=join(bundle,'manifest.json');
  const m=JSON.parse(fs.readFileSync(manifestFile));
  m.database.bytes=fs.statSync(file).size;m.database.sha256=createHash('sha256').update(fs.readFileSync(file)).digest('hex');
  fs.writeFileSync(manifestFile,JSON.stringify(m));
}
test('live WAL snapshot includes all projects, authors and attempts; restored writes continue independently',async t=>{
  const f=fixture(t),a=f.store.session('Mara'),b=f.store.session('Senn');
  const r=f.store.createRoom('Bell Warden'),other=f.store.createRoom('Rain Circuit');
  const payload=attempt(r,'<b>Warning</b> remains literal','decision');
  f.store.append(a,payload);f.store.append(b,attempt(other,'Review the sustained phrase'));
  for(let i=0;i<125;i++)f.store.append(b,attempt(r,`Review ${i}`));
  assert.ok(fs.statSync(f.file+'-wal').size>0);
  // Copying just the main file misses the uncheckpointed schema/data in this fixture.
  const raw=join(f.dir,'wrong-copy.sqlite');fs.copyFileSync(f.file,raw);
  const incomplete=new DatabaseSync(raw,{readOnly:true});
  try {assert.equal(incomplete.prepare("SELECT count(*) AS n FROM sqlite_schema WHERE name='entries'").get().n,0);} finally {incomplete.close();}
  const saved=await createBackup(f.file,f.bundle);
  assert.deepEqual([saved.summary.projects,saved.summary.participants,saved.summary.entries,saved.summary.decisions],[2,2,127,1]);
  assert.deepEqual(fs.readdirSync(f.bundle).sort(),['manifest.json','workspace.sqlite']);
  if(process.platform!=='win32') {
    assert.equal(fs.statSync(f.bundle).mode&0o777,0o700);
    for(const name of fs.readdirSync(f.bundle))assert.equal(fs.statSync(join(f.bundle,name)).mode&0o777,0o600);
  }
  const inspection=await inspectBackup(f.bundle);
  assert.equal(JSON.stringify(inspection).includes(a.token),false);assert.equal(JSON.stringify(inspection).includes('token_hash'),false);
  f.store.append(a,attempt(r,'Written AFTER the savepoint'));
  const destination=join(f.dir,'recovered.sqlite');
  await restoreBackup(f.bundle,destination,inspection.database.sha256);
  const restored=new RoomsStore(destination);
  try {
    assert.equal(restored.authenticate(a.token).id,a.id);assert.equal(restored.authenticate(b.token).name,'Senn');
    assert.equal(restored.append(restored.authenticate(a.token),payload).inserted,false);
    assert.equal(restored.decisions(r.id)[0].author,'Mara');assert.equal(restored.export(r.id).entries.length,126);
    let page=restored.history(r.id),all=page.messages;
    while(page.hasMore){page=restored.history(r.id,page.before);all=[...page.messages,...all];}
    assert.equal(all.length,126);assert.equal(all[0].body,payload.body);
    assert.equal(all.some(row=>row.body.includes('AFTER')),false);
    assert.equal(restored.append(b,attempt(r,'Recovered continuation')).message.id,128);
    assert.equal(f.store.export(r.id).entries.at(-1).body,'Written AFTER the savepoint');
  } finally {restored.close();}
  assert.equal((await inspectBackup(f.bundle)).database.sha256,inspection.database.sha256);
});
test('empty workspace also produces a complete independently restorable bundle',async t=>{
  const f=fixture(t);await createBackup(f.file,f.bundle);
  const dest=join(f.dir,'empty.sqlite');await restoreBackup(f.bundle,dest);
  const restored=new RoomsStore(dest);
  try {const who=restored.session('First'),room=restored.createRoom('Start');assert.equal(restored.append(who,attempt(room,'First recovered note')).message.id,1);} finally {restored.close();}
});
test('existing bundle, main database, symlink and journal paths are never overwritten',async t=>{
  const f=fixture(t);await createBackup(f.file,f.bundle);
  const manifest=fs.readFileSync(join(f.bundle,'manifest.json'));
  await assert.rejects(createBackup(f.file,f.bundle));assert.deepEqual(fs.readFileSync(join(f.bundle,'manifest.json')),manifest);
  const existing=join(f.dir,'existing.sqlite');fs.writeFileSync(existing,'author work');
  await assert.rejects(restoreBackup(f.bundle,existing),/already exists/);assert.equal(fs.readFileSync(existing,'utf8'),'author work');
  const dest=join(f.dir,'future.sqlite');
  for(const suffix of ['-wal','-shm','-journal']) {
    fs.writeFileSync(dest+suffix,'retained sidecar');await assert.rejects(restoreBackup(f.bundle,dest),/already exists/);
    assert.equal(fs.existsSync(dest),false);fs.unlinkSync(dest+suffix);
  }
  const link=join(f.dir,'linked.sqlite');fs.symlinkSync(existing,link);
  await assert.rejects(restoreBackup(f.bundle,link),/already exists/);assert.equal(fs.readFileSync(existing,'utf8'),'author work');
  await assert.rejects(restoreBackup(f.bundle,dest,'0'.repeat(64)),/reviewed/);assert.equal(fs.existsSync(dest),false);
});
test('damaged bytes and incomplete bundles are refused before any destination exists',async t=>{
  const f=fixture(t);await createBackup(f.file,f.bundle);
  const image=join(f.bundle,'workspace.sqlite'),bytes=fs.readFileSync(image);bytes[100]^=255;fs.writeFileSync(image,bytes);
  const dest=join(f.dir,'refused.sqlite');await assert.rejects(restoreBackup(f.bundle,dest),/checksum/);assert.equal(fs.existsSync(dest),false);
  fs.unlinkSync(join(f.bundle,'manifest.json'));await assert.rejects(inspectBackup(f.bundle),/incomplete/);
});
test('a replaced manifest cannot authorize changed schema, broken references or invalid entry contents',async t=>{
  const f=fixture(t),who=f.store.session('Keeper'),room=f.store.createRoom('Recovery');f.store.append(who,attempt(room,'Saved note'));
  for(const [name,sql,error] of [
    ['trigger',"CREATE TRIGGER altered AFTER INSERT ON entries BEGIN DELETE FROM entries; END",/schema/],
    ['reference',"PRAGMA foreign_keys=OFF; UPDATE entries SET session_id='missing'",/references/],
    ['content',"UPDATE entries SET body=''",/entry/],
    ['future','PRAGMA user_version=2',/schema/],
    ['sequence','UPDATE sqlite_sequence SET seq=0',/sequence/]
  ]) {
    const bundle=join(f.dir,name);await createBackup(f.file,bundle);
    const changed=new DatabaseSync(join(bundle,'workspace.sqlite'));try{changed.exec(sql);}finally{changed.close();}rewriteManifest(bundle);
    const dest=join(f.dir,name+'.sqlite');await assert.rejects(restoreBackup(bundle,dest),error);assert.equal(fs.existsSync(dest),false);
  }
});
test('inventory changes and linked image files are refused',async t=>{
  const f=fixture(t);await createBackup(f.file,f.bundle);
  const manifestPath=join(f.bundle,'manifest.json'),m=JSON.parse(fs.readFileSync(manifestPath));m.summary.entries=12;fs.writeFileSync(manifestPath,JSON.stringify(m));
  await assert.rejects(inspectBackup(f.bundle),/inventory/);
  const image=join(f.bundle,'workspace.sqlite');fs.unlinkSync(image);fs.symlinkSync(f.file,image);await assert.rejects(inspectBackup(f.bundle),/unlinked/);
});
test('CLI works outside the project and reports failures without creating missing sources or overwriting destinations',t=>{
  const f=fixture(t),who=f.store.session('Operator'),room=f.store.createRoom('CLI workflow');f.store.append(who,attempt(room,'Restorable decision','decision'));
  const cli=resolve(__dirname,'../rooms-backup.cjs');
  const run=(...args)=>{const result=spawnSync(process.execPath,[cli,...args],{cwd:f.dir,encoding:'utf8',timeout:20000});assert.ifError(result.error);return result;};
  const saved=run('backup','--db',f.file,'--out',f.bundle);assert.equal(saved.status,0,saved.stderr);
  const view=run('inspect','--from',f.bundle);assert.equal(view.status,0,view.stderr);const hash=JSON.parse(view.stdout).database.sha256;
  const dest=join(f.dir,'cli-recovered.sqlite');const recovered=run('restore','--from',f.bundle,'--db',dest,'--expect-sha',hash);assert.equal(recovered.status,0,recovered.stderr);
  assert.equal(JSON.parse(recovered.stdout).summary.entries,1);assert.equal(recovered.stdout.includes(who.token),false);
  assert.equal(run('restore','--from',f.bundle,'--db',dest).status,1);
  for(const args of [['backup'],['inspect','--from',f.bundle,'--from',f.bundle],['restore','--force','yes'],['invented']])assert.equal(run(...args).status,1);
  const missing=join(f.dir,'does-not-exist.sqlite');assert.equal(run('backup','--db',missing,'--out',join(f.dir,'missing')).status,1);assert.equal(fs.existsSync(missing),false);
  assert.match(run('--help').stdout,/Restart with ROOMS_DB/);
});
