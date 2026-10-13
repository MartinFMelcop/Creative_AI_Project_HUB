const {test,before,after}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const {join}=require('node:path');
const {tmpdir}=require('node:os');
const {chromium}=require('playwright-core');
const {createRoomsServer}=require('../rooms-server.cjs');
const {createBackup,restoreBackup}=require('../rooms-backup.cjs');
let browser;
before(async()=>{browser=await chromium.launch({executablePath:process.env.CHROMIUM_PATH||'/usr/bin/chromium',headless:true});});
after(async()=>browser.close());
async function fixture(t,viewport={width:1440,height:1000}) {
  const dir=fs.mkdtempSync(join(tmpdir(),'p11-work-browser-'));let dbPath=join(dir,'rooms.sqlite'),runtime=createRoomsServer({dbPath}),port;
  await new Promise(r=>runtime.server.listen(0,'127.0.0.1',r));port=runtime.server.address().port;const contexts=[],errors=[];
  async function stop() {
    const closed=new Promise(r=>runtime.io.close(r));
    // End HTTP keep-alive connections as well as sockets before replacing this test server.
    runtime.server.closeAllConnections();await closed;
  }
  t.after(async()=>{for(const c of contexts)await c.close();await stop();fs.rmSync(dir,{recursive:true,force:true});assert.deepEqual(errors,[]);});
  return {dir,get runtime(){return runtime;},get dbPath(){return dbPath;},
    async page(name){const context=await browser.newContext({viewport,acceptDownloads:true});contexts.push(context);const p=await context.newPage();p.on('pageerror',e=>errors.push(e.message));await p.goto(`http://127.0.0.1:${port}/studio/`);await p.locator('#name').fill(name);await p.locator('#identity-form button').click();await p.waitForFunction(()=>socket?.connected);return p;},
    async restart(path=dbPath){await stop();dbPath=path;runtime=createRoomsServer({dbPath});await new Promise(r=>runtime.server.listen(port,'127.0.0.1',r));}
  };
}
async function create(p,name){await p.locator('#room-name').fill(name);await p.locator('#room-form button').click();await p.waitForFunction(n=>room?.name===n&&!joining,name);}
async function save(p){await p.locator('#action-save').click();await p.waitForFunction(()=>!draft().work.attempt);}
const card=(p,id)=>p.locator(`.action-card[data-id="${id}"]`);
async function capture(p,name){if(process.env.ACTIONS_CAPTURE_DIR){fs.mkdirSync(process.env.ACTIONS_CAPTURE_DIR,{recursive:true});await p.screenshot({path:join(process.env.ACTIONS_CAPTURE_DIR,name+'.png'),fullPage:true});}}
test('two real browsers turn a decision into assigned work, review concurrent edits and finish with history/export',{timeout:35000},async t=>{
  const f=await fixture(t),a=await f.page('Rook'),b=await f.page('Neri');await create(a,'Cinderwatch release');await b.goto(a.url());await b.waitForFunction(()=>room&&!joining);
  const bid=await b.evaluate(()=>identity.id);
  await a.locator('#body').fill('Ship a native trial that can be played outside the source checkout.');await a.locator('#kind').selectOption('decision');await a.locator('#send').click();await b.waitForFunction(()=>decisions.length===1);
  await a.locator('#decisions button').click();await a.locator('#action-title').fill('Package and verify the native trial');await a.locator('#action-owner').selectOption(bid);await save(a);
  await b.locator('#actions-tab').click();await b.locator('.action-card').waitFor();const id=await b.locator('.action-card').getAttribute('data-id');
  assert.match(await card(b,id).textContent(),/Responsible: Neri/);
  await card(a,id).getByRole('button',{name:'Edit action',exact:true}).click();await a.locator('#action-title').fill('Package the trial and its execution instructions');
  await card(b,id).getByRole('button',{name:'Edit action',exact:true}).click();await b.locator('#action-status').selectOption('doing');await b.locator('#action-note').fill('Checking on a runtime-only machine.');await save(b);
  await a.locator('#action-conflict').waitFor();assert.equal(await a.locator('#action-save').isDisabled(),true);assert.equal(await a.locator('#action-title').inputValue(),'Package the trial and its execution instructions');
  await a.locator('#action-rebase').click();assert.equal(await a.locator('#action-title').inputValue(),'Package the trial and its execution instructions');await a.locator('#action-status').selectOption('doing');await a.locator('#action-note').fill('Keep the instructions with the compiled package.');await save(a);
  await b.waitForFunction(()=>document.querySelector('.action-card').textContent.includes('Revision 3'));
  await a.locator('#action-close').click();await a.locator('#conversation-tab').click();
  await card(b,id).getByRole('button',{name:'Edit action',exact:true}).click();await b.locator('#action-status').selectOption('blocked');await b.locator('#action-note').fill('The test machine needs the .NET runtime.');await save(b);assert.equal(await a.locator('#discussion').isVisible(),true);await capture(b,'blocked');
  await b.locator('#action-status').selectOption('done');await b.locator('#action-note').fill('Three encounters completed from the delivered package; runtime requirements documented.');await save(b);
  await a.waitForFunction(()=>document.querySelector('.action-card').dataset.status==='done');assert.equal(await a.locator('#discussion').isVisible(),true);await a.locator('#actions-tab').click();await card(a,id).getByRole('button',{name:'History',exact:true}).click();await a.waitForFunction(()=>byId('action-events').children.length===5);assert.equal(await a.locator('#action-events li').count(),5);await capture(a,'completed');
  const event=a.waitForEvent('download');await a.locator('#export').click();const file=await event,data=JSON.parse(fs.readFileSync(await file.path(),'utf8'));assert.equal(data.actions.length,1);assert.equal(data.actions[0].history.length,5);assert.equal(data.actions[0].status,'done');assert.equal(data.entries[0].kind,'decision');
  await a.locator('#action-filter').selectOption('mine');assert.equal(await a.locator('.action-card').count(),0);await a.locator('#action-filter').selectOption('all');
  await card(a,id).getByRole('button',{name:'Edit action',exact:true}).click();await a.locator('#action-status').selectOption('doing');await a.locator('#action-note').fill('Repeat on a second machine.');await save(a);assert.equal(f.runtime.store.work.history(id,await a.evaluate(()=>room.id)).events.length,6);
});
for(const committed of [true,false])test(`unconfirmed ${committed?'committed':'uncommitted'} actions survive reload/recovery; offline drafts require explicit save`,{timeout:30000},async t=>{
  const f=await fixture(t),p=await f.page('Reviewer');await create(p,'Recovery review');await p.locator('#actions-tab').click();await p.locator('#new-action').click();await p.locator('#action-title').fill('Record the recovered action workflow');
  const serverSocket=[...f.runtime.io.of('/studio').sockets.values()][0];serverSocket.removeAllListeners('project action');serverSocket.on('project action',payload=>{if(committed)f.runtime.store.work.apply(serverSocket.data.session,payload);});
  await p.locator('#action-save').click();await p.waitForFunction(()=>byId('feedback').textContent.includes('could not be confirmed'));assert.equal(await p.locator('#action-title').isDisabled(),true);
  if(committed) {
    // A declared peer write occurs after the missing acknowledgement and before reload.
    const target=await p.evaluate(()=>room.id),current=f.runtime.store.work.snapshot(target).actions[0],peer=f.runtime.store.session('Other reviewer');f.runtime.store.work.join(target,peer);
    f.runtime.store.work.apply(peer,{op:'update',roomId:target,clientId:require('node:crypto').randomUUID(),actionId:current.id,expectedRevision:1,title:current.title,ownerId:current.owner_id,status:'doing',note:'A newer peer update must survive the older receipt.'});
  }
  await p.reload();await p.waitForFunction(()=>room&&!joining);await p.locator('#actions-tab').click();
  if(!committed){assert.equal(await p.locator('.action-card').count(),0);assert.equal(await p.locator('#action-pending').isVisible(),true);await p.locator('#action-retry').click();}
  await p.waitForFunction(()=>!draft().work.attempt);assert.equal(await p.locator('.action-card').count(),1);
  const baseRevision=committed?2:1;
  if(committed)assert.match(await p.locator('.action-card').textContent(),/A newer peer update/);
  const id=await p.locator('.action-card').getAttribute('data-id');await card(p,id).getByRole('button',{name:'Edit action',exact:true}).click();await p.evaluate(()=>socket.disconnect());await p.locator('#action-note').fill('Draft kept while the server is offline.');assert.equal(await p.locator('#action-save').isDisabled(),true);
  await p.evaluate(()=>socket.connect());await p.waitForFunction(()=>online&&!joining);assert.equal(await p.locator('#action-note').inputValue(),'Draft kept while the server is offline.');assert.equal(f.runtime.store.work.get(id,await p.evaluate(()=>room.id)).revision,baseRevision);await save(p);
  const bundle=join(f.dir,'backup'),saved=await createBackup(f.dbPath,bundle),restored=join(f.dir,'recovered.sqlite');await restoreBackup(bundle,restored,saved.database.sha256);await f.restart(restored);await p.waitForFunction(()=>online&&!joining);
  assert.equal(await p.locator('#participant').textContent(),'Reviewer');assert.equal(f.runtime.store.work.get(id,await p.evaluate(()=>room.id)).revision,baseRevision+1);
  await p.locator('#action-status').selectOption('done');await p.locator('#action-note').fill('Continued from a recovered database with the same participant.');await save(p);assert.equal(f.runtime.store.work.history(id,await p.evaluate(()=>room.id)).events.length,baseRevision+2);
});
test('narrow action workflow keeps drafts per room, literal text, owner choices and a server conflict intact',{timeout:30000},async t=>{
  const f=await fixture(t,{width:390,height:844}),p=await f.page('Mobile maker');await create(p,'One');await p.locator('#actions-tab').click();await p.locator('#new-action').click();await p.locator('#action-title').fill('<b>Literal action title</b>');await save(p);
  assert.equal(await p.locator('.action-card b').count(),0);const id=await p.locator('.action-card').getAttribute('data-id'),roomId=await p.evaluate(()=>room.id),who=f.runtime.store.authenticate(await p.evaluate(()=>identity.token));
  await p.locator('#action-title').fill('My mobile draft');
  const current=f.runtime.store.work.get(id,roomId);f.runtime.store.work.apply(who,{op:'update',roomId,clientId:require('node:crypto').randomUUID(),actionId:id,expectedRevision:current.revision,title:current.title,ownerId:current.owner_id,status:'blocked',note:'A separate update.'});
  await p.locator('#action-save').click();await p.locator('#action-conflict').waitFor();assert.equal(await p.locator('#action-title').inputValue(),'My mobile draft');await capture(p,'mobile-conflict');
  await p.locator('#action-use-latest').click();assert.equal(await p.locator('#action-title').inputValue(),'<b>Literal action title</b>');
  await p.locator('#action-note').fill('Local note draft');await p.locator('#action-close').click();assert.equal(await p.locator('#new-action').isDisabled(),true);await p.locator('#action-resume').click();assert.equal(await p.locator('#action-note').inputValue(),'Local note draft');await create(p,'Two');assert.equal(await p.locator('.action-card').count(),0);assert.equal(await p.locator('#action-history').isVisible(),false);
  await p.locator('#rooms button').filter({hasText:'One'}).click();await p.waitForFunction(()=>room?.name==='One'&&!joining);assert.equal(await p.locator('#action-note').inputValue(),'Local note draft');assert.equal(await p.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true);
  let release;const delayed=new Promise(r=>{release=r;});await p.route('**/studio/actions.js',async route=>{await delayed;await route.continue();});
  await p.reload({waitUntil:'commit'});await p.waitForFunction(()=>typeof room!=='undefined'&&room?.name==='One'&&!joining);release();
  await p.waitForFunction(()=>document.querySelectorAll('.action-card').length===1&&!byId('actions-tab').disabled);
  await p.locator('#actions-tab').click();assert.equal(await p.locator('#action-note').inputValue(),'Local note draft');await p.unroute('**/studio/actions.js');
});
