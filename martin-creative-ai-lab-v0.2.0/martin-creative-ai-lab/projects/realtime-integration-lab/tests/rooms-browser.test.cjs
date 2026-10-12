const assert=require('node:assert/strict');
const { test,before,after }=require('node:test');
const { mkdtempSync,rmSync,readFileSync,mkdirSync }=require('node:fs');
const { tmpdir }=require('node:os');
const { join }=require('node:path');
const { randomUUID }=require('node:crypto');
const { chromium }=require('playwright-core');
const { createRoomsServer }=require('../rooms-server.cjs');
let browser;
before(async()=>{browser=await chromium.launch({executablePath:process.env.CHROMIUM_PATH||'/usr/bin/chromium',headless:true,args:['--no-sandbox']});});
after(async()=>{await browser?.close();});
async function fixture(t,viewport={width:1280,height:900}) {
  const dir=mkdtempSync(join(tmpdir(),'p11-room-browser-')),dbPath=join(dir,'rooms.sqlite');
  let runtime=createRoomsServer({dbPath}),port;
  await new Promise(resolve=>runtime.server.listen(0,'127.0.0.1',resolve));port=runtime.server.address().port;
  const contexts=[],errors=[];
  t.after(async()=>{for(const c of contexts)await c.close();await new Promise(resolve=>runtime.io.close(resolve));rmSync(dir,{recursive:true,force:true});assert.deepEqual(errors,[]);});
  return {
    get runtime(){return runtime;},url:`http://127.0.0.1:${port}/studio/`,
    async page(name) {
      const context=await browser.newContext({viewport,acceptDownloads:true});contexts.push(context);
      const page=await context.newPage();page.on('pageerror',error=>errors.push(error.message));await page.goto(this.url);
      if(name){await page.locator('#name').fill(name);await page.locator('#identity-form button').click();await page.waitForFunction(()=>socket?.connected);}
      return page;
    },
    async restart() {
      await new Promise(resolve=>runtime.io.close(resolve));runtime=createRoomsServer({dbPath});
      await new Promise(resolve=>runtime.server.listen(port,'127.0.0.1',resolve));
    }
  };
}
async function create(page,name) {await page.locator('#room-name').fill(name);await page.locator('#room-form button').click();await page.waitForFunction(n=>byId('room-title').textContent===n,name);await page.waitForFunction(()=>!joining);}
async function post(page,body,kind='note') {await page.locator('#body').fill(body);await page.locator('#kind').selectOption(kind);await page.locator('#send').click();}
async function count(page,n) {await page.waitForFunction(n=>document.querySelectorAll('#entries li').length===n,n);}
async function joinFirst(page) {await page.locator('#rooms button').first().click();await page.waitForFunction(()=>room&&!joining);}
test('two browser identities share notes/decisions, isolate projects and retain drafts on switching',async t=>{
  const f=await fixture(t),a=await f.page('Mara'),b=await f.page('Senn');
  await create(a,'Veilbreak playtest');await b.waitForFunction(()=>rooms.length===1);await b.goto(a.url());await b.waitForFunction(()=>room&&!joining);
  await post(a,'<b>Amber warning</b> stays literal');await count(b,1);
  assert.equal(await b.locator('#entries b').count(),0);
  await post(b,'Keep the two-phase encounter for the next trial.','decision');await count(a,2);
  assert.equal(await a.locator('#decisions li').count(),1);assert.match(await a.locator('#entries').textContent(),/Senn/);
  await a.locator('#body').fill('Draft: observe keyboard pacing');
  await create(a,'Midnight Signal');await post(a,'Review the original mix');await count(a,1);await count(b,2);
  await a.locator('#rooms button').filter({hasText:'Veilbreak playtest'}).click();await count(a,2);
  assert.equal(await a.locator('#body').inputValue(),'Draft: observe keyboard pacing');
  if(process.env.ROOMS_CAPTURE_DIR){mkdirSync(process.env.ROOMS_CAPTURE_DIR,{recursive:true});await a.screenshot({path:join(process.env.ROOMS_CAPTURE_DIR,'desktop.png'),fullPage:true});}
  await a.reload();await count(a,2);assert.equal(await a.locator('#body').inputValue(),'Draft: observe keyboard pacing');
  assert.equal(await a.locator('#participant').textContent(),'Mara');
});
test('missed entries are recovered after real disconnect and server restart using the same local identity',async t=>{
  const f=await fixture(t),a=await f.page('Iven'),b=await f.page('Keeper');
  await create(a,'Crossing record');await b.waitForFunction(()=>rooms.length===1);await joinFirst(b);
  await post(a,'First saved note');await count(b,1);
  await b.evaluate(()=>socket.disconnect());await post(a,'While the other participant is away');await count(a,2);
  await b.evaluate(()=>socket.connect());await count(b,2);
  await f.restart();await b.waitForFunction(()=>socket.connected&&!joining);await count(b,2);
  await a.reload();await count(a,2);assert.equal(await a.locator('#participant').textContent(),'Iven');
  await post(a,'After restart','decision');await count(b,3);
});
for(const committed of [true,false]) test(`uncertain ${committed?'committed':'uncommitted'} send survives reload without replacing newer typing or duplicating a retry`,async t=>{
  const f=await fixture(t),a=await f.page('Reviewer');await create(a,'Uncertainty trial');
  const serverSocket=[...f.runtime.io.of('/studio').sockets.values()][0];
  serverSocket.removeAllListeners('project entry');
  serverSocket.on('project entry',payload=>{if(committed)f.runtime.store.append(serverSocket.data.session,payload);});
  await post(a,'Earlier unconfirmed text');await a.locator('#body').fill('Newer typing must remain');
  await a.waitForFunction(()=>byId('feedback').textContent.includes('could not be confirmed'));
  await f.restart();await a.reload();await a.waitForFunction(()=>socket.connected&&!joining&&room);
  if(committed) {await count(a,1);assert.equal(await a.locator('#pending').isVisible(),false);}
  else {assert.equal(await a.locator('#pending-body').textContent(),'Earlier unconfirmed text');await a.locator('#retry').click();await count(a,1);}
  assert.equal(await a.locator('#body').inputValue(),'Newer typing must remain');
  assert.equal(f.runtime.store.export(f.runtime.store.rooms()[0].id).entries.length,1);
});
test('earlier history loads in order and the actual downloaded export contains the complete record',async t=>{
  const f=await fixture(t),a=await f.page('Reader');await create(a,'Archive review');
  const participant=f.runtime.store.authenticate(await a.evaluate(()=>identity.token)),target=f.runtime.store.rooms()[0];
  // Large history is a declared database fixture, then exercised through the real UI/API.
  for(let i=0;i<123;i++)f.runtime.store.append(participant,{roomId:target.id,clientId:randomUUID(),kind:i%20===0?'decision':'note',body:`Entry ${i}`});
  await a.reload();await count(a,50);assert.equal(await a.locator('#entries .entry-body').first().textContent(),'Entry 73');
  await a.locator('#older').click();await count(a,100);await a.locator('#older').click();await count(a,123);
  assert.equal(await a.locator('#entries .entry-body').first().textContent(),'Entry 0');
  assert.equal(await a.locator('#older').isVisible(),false);
  const downloadEvent=a.waitForEvent('download');await a.locator('#export').click();const download=await downloadEvent;
  const data=JSON.parse(readFileSync(await download.path(),'utf8'));
  assert.equal(data.entries.length,123);assert.equal(data.project.name,'Archive review');assert.equal(data.entries[0].body,'Entry 0');
});
test('narrow workspace supports the complete workflow without horizontal clipping',async t=>{
  const f=await fixture(t,{width:390,height:844}),a=await f.page('Mobile reviewer');
  await create(a,'A long project title for a real narrow viewport');
  await post(a,'x'.repeat(500),'decision');await count(a,1);
  assert.equal(await a.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true);
  await a.locator('#change').click();assert.equal(await a.locator('#welcome').isVisible(),true);
  await a.locator('#name').fill('Another participant');await a.locator('#identity-form button').click();await a.waitForFunction(()=>byId('participant').textContent==='Another participant');await count(a,1);
  assert.equal(await a.locator('#participant').textContent(),'Another participant');
  if(process.env.ROOMS_CAPTURE_DIR)await a.screenshot({path:join(process.env.ROOMS_CAPTURE_DIR,'mobile.png'),fullPage:true});
});
test('explicit rejection preserves editable draft and does not leave an uncertain retry',async t=>{
  const f=await fixture(t),a=await f.page('Editor');await create(a,'Review room');
  const serverSocket=[...f.runtime.io.of('/studio').sockets.values()][0];serverSocket.removeAllListeners('project entry');
  serverSocket.on('project entry',(_payload,ack)=>ack({ok:false,error:'Controlled rejection'}));
  await post(a,'Keep this editable draft');await a.waitForFunction(()=>byId('feedback').textContent==='Controlled rejection');
  assert.equal(await a.locator('#body').inputValue(),'Keep this editable draft');assert.equal(await a.locator('#pending').isVisible(),false);assert.equal(await a.locator('#send').isEnabled(),true);
});
test('denied browser storage still permits current-session collaboration with a persistent warning',async t=>{
  const f=await fixture(t),a=await f.page();
  await a.evaluate(()=>{Storage.prototype.getItem=()=>{throw new Error('Controlled denial');};Storage.prototype.setItem=()=>{throw new Error('Controlled denial');};});
  await a.locator('#name').fill('Temporary participant');await a.locator('#identity-form button').click();await a.waitForFunction(()=>socket?.connected);
  await create(a,'Unsaved browser session');await post(a,'The project record is saved on the server');await count(a,1);
  assert.equal(await a.locator('#storage').isVisible(),true);assert.equal(f.runtime.store.export(f.runtime.store.rooms()[0].id).entries.length,1);
});
