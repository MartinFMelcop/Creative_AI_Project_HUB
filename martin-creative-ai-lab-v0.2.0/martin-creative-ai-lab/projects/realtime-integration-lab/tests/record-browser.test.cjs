const assert=require('node:assert/strict');
const { test,before,after }=require('node:test');
const fs=require('node:fs');
const { join }=require('node:path');
const { tmpdir }=require('node:os');
const { pathToFileURL }=require('node:url');
const { createHash }=require('node:crypto');
const { createServer }=require('node:http');
const { chromium }=require('playwright-core');
const { createRoomsServer }=require('../rooms-server.cjs');
const { renderRecord }=require('../record-export.cjs');
const { populate }=require('./record-fixture.cjs');
let browser;
before(async()=>{browser=await chromium.launch({executablePath:process.env.CHROMIUM_PATH||'/usr/bin/chromium',headless:true,args:['--no-sandbox']});});
after(async()=>{await browser?.close();});
async function fixture(t) {
  const runtime=createRoomsServer();await new Promise(resolve=>runtime.server.listen(0,'127.0.0.1',resolve));
  let closed=false;const stop=async()=>{if(!closed){closed=true;await new Promise(resolve=>runtime.io.close(resolve));}};
  const dir=fs.mkdtempSync(join(tmpdir(),'p11-reading-browser-')),context=await browser.newContext({acceptDownloads:true});
  const errors=[],page=await context.newPage();page.on('pageerror',error=>errors.push(error.message));
  const f=populate(runtime.store),url=`http://127.0.0.1:${runtime.server.address().port}`;
  t.after(async()=>{await context.close();await stop();fs.rmSync(dir,{recursive:true,force:true});assert.deepEqual(errors,[]);});
  async function enter() {
    await page.goto(url+'/studio/#'+f.room.id);await page.evaluate(identity=>localStorage.setItem('p11-room-identity',JSON.stringify(identity)),f.person);
    await page.reload();await page.waitForFunction(id=>room?.id===id&&!joining,f.room.id);
  }
  return {...f,runtime,dir,context,page,stop,enter};
}
async function offline(t,file,viewport={width:1280,height:900}) {
  const context=await browser.newContext({viewport,acceptDownloads:true}),page=await context.newPage(),errors=[],requests=[];
  let readerUrl=pathToFileURL(file).href,server;
  const transport=process.env.ROOMS_RECORD_READER_TRANSPORT || 'file';assert.ok(['file','loopback'].includes(transport));
  if(transport==='loopback') {
    // Explicit fallback for managed browsers that prohibit file navigation.
    // Serve identical bytes once; close this static server before interactions.
    server=createServer((_request,response)=>response.writeHead(200,{'Content-Type':'text/html;charset=utf-8'}).end(fs.readFileSync(file)));
    await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));readerUrl=`http://127.0.0.1:${server.address().port}/reading.html`;
    t.diagnostic('Reader loaded as identical HTML over loopback; file navigation was not tested in this run. Network and static server disabled before interactions.');
  } else await context.setOffline(true);
  page.on('pageerror',error=>errors.push(error.message));page.on('request',request=>{if(/^https?:/.test(request.url())&&request.url()!==readerUrl)requests.push(request.url());});
  t.after(async()=>{await context.close();assert.deepEqual(errors,[]);assert.deepEqual(requests,[]);});
  try {await page.goto(readerUrl);await page.locator('#snapshot-time').filter({hasText:'Snapshot exported'}).waitFor();}
  finally {if(server)await new Promise(resolve=>server.close(resolve));}
  await context.setOffline(true);
  return {page,context};
}
async function search(page,query,kind='all') {
  await page.locator('#query').fill(query);await page.locator('#record-kind').selectOption(kind);await page.locator('#search-form button').click();
}
async function capture(page,name) {
  if(process.env.ROOMS_RECORD_CAPTURE_DIR){fs.mkdirSync(process.env.ROOMS_RECORD_CAPTURE_DIR,{recursive:true});await page.screenshot({path:join(process.env.ROOMS_RECORD_CAPTURE_DIR,name),fullPage:false});}
}

test('delivered demo opens without a workspace and exposes decision, blocker and remaining work',async t=>{
  const {page}=await offline(t,join(__dirname,'../examples/cistern-handover.html'));
  assert.match(await page.locator('#project-name').textContent(),/Fictional.*Demo/);
  assert.equal(await page.locator('#work-list li').count(),2);await capture(page,'offline-demo.png');
  await search(page,'DEPOSITO valvula','action');await page.locator('#results button').click();
  assert.match(await page.locator('.comparison').textContent(),/Historical|historical/);assert.match(await page.locator('.comparison').textContent(),/Blocked.*Done/s);
  await page.locator('#back').click();await page.locator('#work-owner').selectOption('null');
  assert.match(await page.locator('#work-list').textContent(),/water-sample check/);
  await page.locator('#work-list button').press('Enter');assert.match(await page.locator('#detail-body').textContent(),/Pump repair alone does not authorize reopening/);
});

test('live download becomes a complete offline reader with historical comparison and unchanged drafts',async t=>{
  const f=await fixture(t);await f.enter();await f.page.locator('#body').fill('Unsent fixture discussion');
  await f.page.locator('#actions-tab').click();await f.page.locator('#new-action').click();await f.page.locator('#action-title').fill('Unsent fixture work');await f.page.locator('#action-close').click();
  const draft=await f.page.evaluate(()=>JSON.stringify(drafts));
  const pending=f.page.waitForEvent('download');await f.page.locator('#reading-export').click();const download=await pending,file=join(f.dir,'reading.html');await download.saveAs(file);
  assert.equal(download.suggestedFilename(),`project-${f.room.id}-reading.html`);assert.equal(await f.page.evaluate(()=>JSON.stringify(drafts)),draft);
  f.append('Later note must not appear in reading copy');await f.stop();
  const {page}=await offline(t,file);
  await search(page,'DEPOSITO valvula','action');assert.equal(await page.locator('#results li').count(),1);
  assert.match(await page.locator('#results').textContent(),/revision 2.*Historical/s);
  await page.locator('#results button').click();assert.equal(await page.locator('#detail-heading').evaluate(element=>element===document.activeElement),true);
  assert.ok(await page.locator('#detail-heading').evaluate(element=>element.getBoundingClientRect().top<100));
  const comparison=await page.locator('.comparison').textContent();assert.match(comparison,/Selected revision · historical.*Blocked.*Válvula presa.*Current at export.*Return completed pump.*Done.*revision 63/s);
  await capture(page,'offline-comparison.png');
  assert.match(await page.locator('#detail-body').textContent(),/western valve/);
  assert.equal(await page.locator('#detail-body [data-revision]').count(),20);
  await page.locator('#detail-body button').filter({hasText:'Later revisions'}).click();assert.match(await page.locator('#detail-body').textContent(),/21–40 of 63/);
  await page.locator('#detail-body button').filter({hasText:'Later revisions'}).click();await page.locator('#detail-body button').filter({hasText:'Later revisions'}).click();
  assert.match(await page.locator('#detail-body').textContent(),/61–63 of 63/);
  await page.locator('[data-revision="63"] button').click();assert.match(await page.locator('.comparison').textContent(),/Selected revision · current at export/);
  await page.locator('#back').press('Enter');assert.equal(await page.locator('#results button').evaluate(element=>element===document.activeElement),true);
  await search(page,'western loan','decision');await page.locator('#results button').click();assert.match(await page.locator('#detail-body').textContent(),/Linked work at export.*Return completed pump.*Done/s);
  await page.locator('#detail-body button').filter({hasText:'Open action history'}).click();assert.match(await page.locator('#detail-heading').textContent(),/revision 63/);
  await search(page,'Later note');assert.match(await page.locator('#result-count').textContent(),/No matches/);
  const jsonPending=page.waitForEvent('download');await page.locator('#download-json').click();const json=await jsonPending,jsonFile=join(f.dir,'embedded.json');await json.saveAs(jsonFile);
  const source=fs.readFileSync(jsonFile,'utf8'),parsed=JSON.parse(source);assert.equal(parsed.actions.find(action=>action.id===f.action.id).history.length,63);
  assert.ok(!source.includes('Other-room record must stay out'));assert.ok(!source.includes(f.person.token));
  assert.equal(await page.locator('footer code').textContent(),createHash('sha256').update(source).digest('hex'));
});

test('mobile filters, literal text, pinned pages and source payload remain safe without network access',async t=>{
  const f=await fixture(t),record=f.runtime.store.export(f.room.id),file=join(f.dir,'mobile.html');fs.writeFileSync(file,renderRecord(record));await f.stop();
  const {page}=await offline(t,file,{width:390,height:844});
  await page.locator('#work-status').selectOption('done');assert.equal(await page.locator('#work-list li').count(),1);
  await page.locator('#work-owner').selectOption(JSON.stringify('Fixture Neri'));assert.match(await page.locator('#work-list').textContent(),/Return completed pump/);
  await page.locator('#work-owner').selectOption('null');assert.match(await page.locator('#work-count').textContent(),/No actions/);
  await page.locator('#work-status').selectOption('all');assert.match(await page.locator('#work-list').textContent(),/Unassigned fixture check/);
  await search(page,'cable_%');assert.match(await page.locator('#result-count').textContent(),/1–20 of 25/);assert.equal(await page.locator('#results b,#results img').count(),0);
  assert.match(await page.locator('#results').textContent(),/<b>Câble_%<\/b>/);assert.equal(await page.evaluate(()=>globalThis.leaked),undefined);
  const first=await page.locator('#results li').evaluateAll(elements=>elements.map(element=>element.dataset.entry));
  await page.locator('#result-next').click();assert.match(await page.locator('#result-count').textContent(),/21–25 of 25/);assert.equal(await page.locator('#result-next').isEnabled(),false);
  await page.locator('#result-prev').click();assert.deepEqual(await page.locator('#results li').evaluateAll(elements=>elements.map(element=>element.dataset.entry)),first);
  await page.locator('#results button').first().click();assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true);
  await capture(page,'offline-mobile.png');
  await search(page,'a b c d e f g h i');assert.match(await page.locator('#result-count').textContent(),/up to 8 literal words/);assert.equal(await page.locator('#results li').count(),0);
  await search(page,'\u0301');assert.match(await page.locator('#result-count').textContent(),/searchable character/);
  await search(page,'');assert.ok((await page.locator('#results li').count())>0);
  await search(page,'DEPOSITO valvula','action');await page.locator('#results button').click();
  assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true);
  const cards=await page.locator('.comparison .card').evaluateAll(elements=>elements.map(element=>({top:element.getBoundingClientRect().top,bottom:element.getBoundingClientRect().bottom})));
  assert.ok(cards[1].top>=cards[0].bottom);await capture(page,'offline-mobile-comparison.png');
});

test('legacy and empty snapshots disclose unavailable action data and support JSON download',async t=>{
  const f=await fixture(t),record=JSON.parse(JSON.stringify(f.runtime.store.export(f.room.id)));delete record.actions;record.entries=[];
  const file=join(f.dir,'legacy.html');fs.writeFileSync(file,renderRecord(record));await f.stop();const {page}=await offline(t,file);
  assert.match(await page.locator('#work-help').textContent(),/earlier JSON export.*no action data.*does not establish/s);
  assert.equal(await page.locator('#work-list li,#results li').count(),0);assert.equal(await page.locator('#result-next').isEnabled(),false);
  const pending=page.waitForEvent('download');await page.locator('#download-json').click();const downloaded=await pending,jsonFile=join(f.dir,'legacy.json');await downloaded.saveAs(jsonFile);
  assert.deepEqual(JSON.parse(fs.readFileSync(jsonFile,'utf8')),record);
});

test('late reading exports cannot download across project or participant switches',async t=>{
  const f=await fixture(t);await f.enter();const downloads=[];f.page.on('download',download=>downloads.push(download));
  async function delayed(change) {
    let release,seen,finished;const gate=new Promise(resolve=>release=resolve),intercepted=new Promise(resolve=>seen=resolve),done=new Promise(resolve=>finished=resolve);
    await f.page.route('**/api/studio/rooms/*/reading',async route=>{const response=await route.fetch();seen();await gate;await route.fulfill({response});finished();});
    await f.page.locator('#reading-export').click();await intercepted;await change();release();await done;
    await f.page.waitForFunction(()=>readingRequest===null);await f.page.unroute('**/api/studio/rooms/*/reading');assert.equal(downloads.length,0);
  }
  await delayed(async()=>{await f.page.locator('#rooms button').filter({hasText:'Other fixture room'}).click();await f.page.waitForFunction(id=>room?.id===id&&!joining,f.other.id);assert.equal(await f.page.locator('#reading-export').isEnabled(),true);});
  await f.page.locator('#rooms button').filter({hasText:'Fictional cistern handover'}).click();await f.page.waitForFunction(id=>room?.id===id&&!joining,f.room.id);
  await delayed(()=>f.page.locator('#change').click());assert.equal(await f.page.locator('#welcome').isVisible(),true);
});

test('HTTP export errors preserve discussion drafts and allow a successful retry',async t=>{
  const f=await fixture(t);await f.enter();await f.page.locator('#body').fill('Draft before rejected export');
  await f.page.route('**/api/studio/rooms/*/reading',route=>route.fulfill({status:401,contentType:'application/json',body:JSON.stringify({error:'Fixture session rejected.'})}));
  await f.page.locator('#reading-export').click();await f.page.locator('#feedback').filter({hasText:'Fixture session rejected.'}).waitFor();
  assert.equal(await f.page.locator('#body').inputValue(),'Draft before rejected export');assert.equal(await f.page.locator('#reading-export').isEnabled(),true);
  await f.page.unroute('**/api/studio/rooms/*/reading');const pending=f.page.waitForEvent('download');await f.page.locator('#reading-export').click();await pending;
});

test('complete report ignores filters/pages and preserves every source entry/revision without executing text',async t=>{
  const f=await fixture(t);
  for(let i=0;i<24;i++)f.runtime.store.work.apply(f.person,{op:'create',roomId:f.room.id,clientId:require('node:crypto').randomUUID(),title:`Additional report action ${i}`});
  const record=f.runtime.store.export(f.room.id),file=join(f.dir,'report.html');fs.writeFileSync(file,renderRecord(record));await f.stop();
  const {page}=await offline(t,file,{width:390,height:844});
  assert.equal(await page.locator('#complete-report').textContent(),'');
  await search(page,'cable_%');await page.locator('#result-next').click();await page.locator('#work-status').selectOption('done');
  const before=await page.locator('#results').textContent(),payload=await page.locator('#record-data').textContent();
  await page.locator('#prepare-report').click();
  assert.equal(await page.locator('#report-heading').evaluate(el=>el===document.activeElement),true);
  assert.equal(await page.locator('#reader').isVisible(),false);
  assert.equal(await page.locator('[data-report-action]').count(),26);
  assert.deepEqual(await page.locator('[data-report-entry]').evaluateAll(els=>els.map(el=>Number(el.dataset.reportEntry))),record.entries.map(e=>e.id));
  assert.deepEqual(await page.locator('[data-report-event]').evaluateAll(els=>els.map(el=>Number(el.dataset.reportEvent))),record.actions.flatMap(a=>a.history.map(e=>e.id)));
  assert.match(await page.locator('#complete-report').textContent(),/Source decision #.*western valve/s);
  assert.match(await page.locator('#complete-report').textContent(),/Revision 2 · Historical.*Blocked.*Válvula presa/s);
  assert.equal(await page.locator('#complete-report img,#complete-report b').count(),0);
  assert.equal(await page.evaluate(()=>globalThis.leaked),undefined);
  assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true);
  await capture(page,'complete-report-mobile.png');await page.locator('#close-report').click();
  assert.equal(await page.locator('#results').textContent(),before);
  assert.equal(await page.locator('#query').inputValue(),'cable_%');assert.equal(await page.locator('#work-status').inputValue(),'done');
  assert.equal(await page.locator('#prepare-report').evaluate(el=>el===document.activeElement),true);
  await page.locator('#prepare-report').click();assert.equal(await page.locator('[data-report-event]').count(),88);
  assert.equal(await page.locator('#record-data').textContent(),payload);
});

test('browser print creates a complete PDF while retaining the filtered reading state',async t=>{
  const f=await fixture(t),record=f.runtime.store.export(f.room.id),file=join(f.dir,'print.html');fs.writeFileSync(file,renderRecord(record));await f.stop();
  const {page}=await offline(t,file);await search(page,'western','decision');
  const before=await page.locator('#results').textContent(),pdf=await page.pdf({format:'A4',printBackground:true});
  assert.ok(pdf.length>10000);assert.equal(await page.locator('[data-report-entry]').count(),record.entries.length);
  assert.equal(await page.locator('[data-report-event]').count(),64);
  assert.equal(await page.locator('#results').textContent(),before);assert.equal(await page.locator('#reader').isVisible(),true);
  assert.equal(await page.locator('#complete-report').isVisible(),false);
  await page.emulateMedia({media:'print'});assert.equal(await page.locator('#reader').isVisible(),false);
  assert.equal(await page.locator('#complete-report').isVisible(),true);
  if(process.env.ROOMS_RECORD_CAPTURE_DIR){fs.mkdirSync(process.env.ROOMS_RECORD_CAPTURE_DIR,{recursive:true});fs.writeFileSync(join(process.env.ROOMS_RECORD_CAPTURE_DIR,'complete-report.pdf'),pdf);}
});

test('legacy/empty reports disclose unavailable action history and return to reading',async t=>{
  const f=await fixture(t),record=f.runtime.store.export(f.room.id);delete record.actions;record.entries=[];
  const file=join(f.dir,'legacy-report.html');fs.writeFileSync(file,renderRecord(record));await f.stop();
  const {page}=await offline(t,file);await page.locator('#prepare-report').click();
  assert.match(await page.locator('#complete-report').textContent(),/Action data is unavailable.*does not establish.*No discussion.*history is unavailable/s);
  await page.locator('#close-report').press('Enter');assert.equal(await page.locator('#reader').isVisible(),true);
});
