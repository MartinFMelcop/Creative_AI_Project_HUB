const assert=require('node:assert/strict');
const { test }=require('node:test');
const fs=require('node:fs');
const { tmpdir }=require('node:os');
const { join,resolve,dirname }=require('node:path');
const { randomUUID }=require('node:crypto');
const { execFile }=require('node:child_process');
const { promisify }=require('node:util');
const { chromium }=require('playwright-core');
const { createRoomsServer }=require('../rooms-server.cjs');
const exec=promisify(execFile);
const count=(page,n)=>page.waitForFunction(n=>document.querySelectorAll('#entries li').length===n,n);
async function post(page,body,kind='note') {await page.locator('#body').fill(body);await page.locator('#kind').selectOption(kind);await page.locator('#send').click();}
async function create(page,name) {await page.locator('#room-name').fill(name);await page.locator('#room-form button').click();await page.waitForFunction(n=>byId('room-title').textContent===n&&!joining,name);}
test('operator CLI recovers a live multi-project workspace after simulated loss; original browsers resume and retry safely',{timeout:60000},async t=>{
  const dir=fs.mkdtempSync(join(tmpdir(),'p11-recovery-browser-')),file=join(dir,'live.sqlite'),bundle=join(dir,'savepoint'),restored=join(dir,'recovered.sqlite');
  const errors=[],contexts=[];
  let runtime=createRoomsServer({dbPath:file}),browser;
  t.after(async()=>{for(const c of contexts)await c.close();await browser?.close();if(runtime.server.listening)await new Promise(r=>runtime.io.close(r));fs.rmSync(dir,{recursive:true,force:true});assert.deepEqual(errors,[]);});
  await new Promise(r=>runtime.server.listen(0,'127.0.0.1',r));const port=runtime.server.address().port,url=`http://127.0.0.1:${port}/studio/`;
  browser=await chromium.launch({executablePath:process.env.CHROMIUM_PATH||'/usr/bin/chromium',headless:true,args:['--no-sandbox']});
  const cli=async(...args)=>JSON.parse((await exec(process.execPath,[resolve(__dirname,'../rooms-backup.cjs'),...args],{cwd:dir,timeout:20000})).stdout);
  async function page(name) {
    const context=await browser.newContext({viewport:{width:1280,height:900},acceptDownloads:true});contexts.push(context);const p=await context.newPage();
    p.on('pageerror',e=>errors.push(e.message));await p.goto(url);await p.locator('#name').fill(name);await p.locator('#identity-form button').click();await p.waitForFunction(()=>socket?.connected);return p;
  }
  const a=await page('Mara'),b=await page('Senn');
  await create(a,'Veilbreak decisions');const permalink=a.url();await b.goto(permalink);await b.waitForFunction(()=>room&&!joining);
  const identities=await Promise.all([a,b].map(p=>p.evaluate(()=>({id:identity.id,token:identity.token}))));
  await post(a,'The charge warning remains readable.');await count(b,1);
  await post(b,'Keep the two-phase trial for the next review.','decision');await count(a,2);
  const target=runtime.store.rooms()[0],first=runtime.store.history(target.id).messages[0];
  // Declared history fixture makes recovery exercise real pagination, not just two fresh entries.
  for(let i=0;i<60;i++)runtime.store.append(runtime.store.authenticate(identities[1].token),{roomId:target.id,clientId:randomUUID(),kind:'note',body:`Earlier review ${i+1}`});
  await create(a,'Rain Circuit reviews');await post(a,'Carry the long phrase through the bridge.','decision');await count(a,1);
  await a.locator('#rooms button').filter({hasText:'Veilbreak decisions'}).click();await count(a,50);
  await a.locator('#body').fill('Draft: compare the next keyboard trial');
  assert.ok(fs.statSync(file+'-wal').size>0);
  const saved=await cli('backup','--db',file,'--out',bundle),inspection=await cli('inspect','--from',bundle);
  assert.equal(inspection.database.sha256,saved.database.sha256);assert.equal(saved.summary.entries,63);assert.equal(saved.summary.projects,2);
  await b.reload();await count(b,50);await post(b,'This later note is outside the savepoint.');await count(b,51);
  const controlled=[...runtime.io.of('/studio').sockets.values()].find(s=>s.data.session.id===identities[0].id);
  controlled.removeAllListeners('project entry');controlled.on('project entry',()=>{});
  await post(a,'Earlier uncommitted attempt survives in this browser');await a.locator('#body').fill('Newer typing stays editable after recovery');
  await a.waitForFunction(()=>byId('feedback').textContent.includes('could not be confirmed'));
  await new Promise(r=>runtime.io.close(r));
  fs.renameSync(file,join(dir,'unavailable.sqlite'));assert.equal(fs.existsSync(file),false);
  const recovered=await cli('restore','--from',bundle,'--db',restored,'--expect-sha',inspection.database.sha256);
  runtime=createRoomsServer({dbPath:restored});await new Promise(r=>runtime.server.listen(port,'127.0.0.1',r));
  await a.reload();await b.reload();await Promise.all([a,b].map(p=>p.waitForFunction(()=>room&&!joining&&socket.connected)));
  await count(a,50);await count(b,50);assert.equal(a.url(),permalink);
  for(let i=0;i<2;i++)assert.equal(runtime.store.authenticate(identities[i].token).id,identities[i].id);
  assert.equal(await a.locator('#participant').textContent(),'Mara');assert.equal(await b.locator('#participant').textContent(),'Senn');
  assert.equal(await a.locator('#body').inputValue(),'Newer typing stays editable after recovery');
  assert.equal(await a.locator('#pending-body').textContent(),'Earlier uncommitted attempt survives in this browser');
  assert.equal(runtime.store.export(target.id).entries.some(e=>e.body.includes('later note')),false);
  assert.match(await a.locator('#decisions').textContent(),/Senn/);
  const originalPayload={roomId:target.id,clientId:first.client_id,kind:first.kind,body:first.body};
  const duplicate=await a.evaluate(p=>request('project entry',p),originalPayload);assert.equal(duplicate.duplicate,true);assert.equal(runtime.store.export(target.id).entries.length,62);
  await a.locator('#retry').click();await count(a,51);await count(b,51);
  assert.equal(await a.locator('#body').inputValue(),'Newer typing stays editable after recovery');assert.equal(await a.locator('#pending').isVisible(),false);
  assert.equal(runtime.store.export(target.id).entries.filter(e=>e.body==='Earlier uncommitted attempt survives in this browser').length,1);
  await a.locator('#older').click();await count(a,63);assert.equal(await a.locator('#entries .entry-body').first().textContent(),first.body);
  const downloadEvent=a.waitForEvent('download');await a.locator('#export').click();const download=await downloadEvent;
  const exported=JSON.parse(fs.readFileSync(await download.path(),'utf8'));assert.equal(exported.entries.length,63);assert.equal(exported.entries[1].author,'Senn');
  await a.locator('#rooms button').filter({hasText:'Rain Circuit reviews'}).click();await count(a,1);
  assert.equal(await a.locator('#entries .entry-body').textContent(),'Carry the long phrase through the bridge.');
  await post(a,'Restored workspace is ready for another review.');await count(a,2);
  assert.equal(runtime.store.export(runtime.store.rooms().find(r=>r.name==='Rain Circuit reviews').id).entries.at(-1).id,65);
  if(process.env.ROOMS_RECOVERY_CAPTURE) {fs.mkdirSync(dirname(process.env.ROOMS_RECOVERY_CAPTURE),{recursive:true});await a.screenshot({path:process.env.ROOMS_RECOVERY_CAPTURE,fullPage:true});}
  if(process.env.ROOMS_RECOVERY_EVIDENCE) {
    fs.mkdirSync(dirname(process.env.ROOMS_RECOVERY_EVIDENCE),{recursive:true});
    fs.writeFileSync(process.env.ROOMS_RECOVERY_EVIDENCE,JSON.stringify({application_version:require('../package.json').version,node:process.version,chromium:browser.version(),
      backup:{sha256:saved.database.sha256,bytes:saved.database.bytes,projects:2,participants:2,entries:63,decisions:2},
      restored_entries:recovered.summary.entries,continued_entries:runtime.store.rooms().reduce((n,r)=>n+r.entries,0),
      checks:['live WAL via separate CLI process','inspect inventory and digest','original file unavailable','restore to new file and restart same origin','both remembered identities and permalink','later write excluded','earlier retry deduplicated','uncommitted browser retry exactly once; newer draft retained','history pagination and downloaded export','switch project and continue sequential IDs'],
      fixture:'Fictional participants, 60 explicitly seeded history entries and synthetic Chromium input; no human collaboration or disaster recovery service claim.'},null,2)+'\n');
  }
});
