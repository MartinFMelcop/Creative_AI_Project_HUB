import test,{before,after} from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import {createRequire} from 'node:module';
import {createServer} from '../server.mjs';
const require=createRequire(new URL('../../../realtime-integration-lab/package.json',import.meta.url));
const {chromium}=require('playwright-core');
let browser,server,url;
const contexts=[];
before(async()=>{
  server=createServer();await new Promise(r=>server.listen(0,'127.0.0.1',r));url=`http://127.0.0.1:${server.address().port}`;
  browser=await chromium.launch({executablePath:process.env.CHROMIUM_PATH||'/usr/bin/chromium',headless:true});
});
after(async()=>{for(const c of contexts)await c.close();await browser?.close();await new Promise(r=>server?.close(r));});
async function fixture(options={},init) {
  const context=await browser.newContext(options);contexts.push(context);if(init)await context.addInitScript(init);
  const page=await context.newPage(),errors=[];page.on('pageerror',e=>errors.push(e.message));
  await page.goto(url);await page.locator('#begin').waitFor();return {page,context,errors};
}
const click=async(page,actions)=>{for(const a of actions)await page.locator(`[data-action="${a}"]`).click();};
const start=page=>page.locator('#begin').click();
const snapshot=page=>page.evaluate(()=>JSON.parse(localStorage.getItem('waystone-crossing-v1')));
const result=page=>page.locator('#play').getAttribute('data-ending');
async function download(page) {
  const wait=page.waitForEvent('download');await page.locator('#export').click();
  const file=await wait;return JSON.parse(await fs.readFile(await file.path(),'utf8'));
}
async function shot(page,name) {if(process.env.WAYSTONE_SCREENSHOT_DIR)await page.screenshot({path:process.env.WAYSTONE_SCREENSHOT_DIR+'/'+name+'.png',fullPage:true});}
test('cover, help and desktop/mobile layouts render without overflow',async()=>{
  const {page,errors}=await fixture({viewport:{width:1440,height:1050}});
  assert.equal(await page.title(),'The Last Waystone — Flood Crossing');
  assert.equal(await page.locator('#map').isVisible(),true);assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
  await shot(page,'cover');await page.locator('#help').click();assert.equal(await page.locator('#instructions').evaluate(d=>d.open),true);
  await page.keyboard.press('Escape');assert.equal(await page.locator('#instructions').evaluate(d=>d.open),false);
  await page.setViewportSize({width:390,height:844});assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
  await start(page);assert.equal(await page.locator('#scene-title').textContent(),'What can you carry?');
  assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));await shot(page,'mobile-pack');
  assert.deepEqual(errors,[]);
});
test('complete causeway rescue displays consequences, epilogue, actual journal and portable save',async()=>{
  const {page,errors}=await fixture({viewport:{width:1440,height:1050}});await start(page);
  const actions=['rope','timber','ready','herbs','bargain','causeway','iven','roof','span','convoy'];
  await click(page,actions);assert.equal(await result(page),'FULL_RESCUE');
  assert.match(await page.locator('#outcome').textContent(),/4 \/ 4/);assert.match(await page.locator('#outcome').textContent(),/Repaired causeway/);
  assert.match(await page.locator('#epilogue').textContent(),/Four people answer/);assert.equal(await page.locator('#remaining').textContent(),'0');
  await page.locator('#journal summary').click();assert.equal(await page.locator('#journal-entries>li').count(),10);
  assert.match(await page.locator('#journal-entries').textContent(),/consum|boards|rune/);
  const saved=await download(page);assert.deepEqual(saved.actions,actions);assert.equal(saved.engine_version,'0.2.0');
  await page.locator('#journal summary').click();await shot(page,'causeway-ending');
  await page.locator('#replay').click();await page.locator('#cancel-replacement').click();assert.equal(await result(page),'FULL_RESCUE');
  await page.locator('#replay').click();await page.locator('#confirm-replacement').click();
  assert.equal(await page.locator('#play').getAttribute('data-phase'),'pack');assert.deepEqual((await snapshot(page)).actions,[]);
  assert.deepEqual(errors,[]);
});
test('ferry medicine order produces different outcomes in actual browser play',async()=>{
  const outcomes=[];
  for(const ending of [['load','board','row','row','board','row'],['board','row','row','load','board','row']]) {
    const {page,errors}=await fixture({viewport:{width:1440,height:1050}});await start(page);
    await click(page,['timber','oil','ready','leave','ferry','iven','roof']);
    assert.equal(await page.locator('#remaining').textContent(),'3');
    assert.match(await page.locator('#boat-info').textContent(),/0\/3 cargo slots.*1 beat/);
    await click(page,ending.slice(0,2));await shot(page,'ferry-loaded-'+ending[0]);
    if(ending[0]==='load')assert.match(await page.locator('[data-action="row"] .detail').textContent(),/projected hull 4/);
    await click(page,ending.slice(2));outcomes.push(await result(page));
    assert.match(await page.locator('#outcome').textContent(),/4 \/ 4/);
    assert.match(await page.locator('#outcome').textContent(),ending[0]==='load'?/Dry & delivered/:/Water-damaged/);
    assert.deepEqual(errors,[]);
  }
  assert.deepEqual(outcomes,['FULL_RESCUE','PEOPLE_SAFE']);
});
test('reload and file import recover loaded cargo and the same remaining journey',async()=>{
  const {page,errors}=await fixture();await start(page);
  const before=['timber','oil','ready','leave','ferry','iven','roof','load','board'];await click(page,before);
  const saved=await download(page);await page.reload();await page.locator('#resume').click();
  assert.equal(await page.locator('#play').getAttribute('data-phase'),'ferry');assert.match(await page.locator('#boat-info').textContent(),/3\/3 cargo slots/);
  assert.match(await page.locator('#roster').textContent(),/Aboard the ferry/);assert.equal(await page.locator('#remaining').textContent(),'3');
  await click(page,['row','row','board','row']);assert.equal(await result(page),'FULL_RESCUE');
  const {page:other,errors:otherErrors}=await fixture();
  await other.locator('#save-input').setInputFiles({name:'crossing.json',mimeType:'application/json',buffer:Buffer.from(JSON.stringify(saved))});
  // A fresh browser profile imports the file without sharing localStorage.
  await click(other,['row','row','board','row']);assert.deepEqual(otherErrors,[]);
  assert.equal(await result(other),'FULL_RESCUE');assert.deepEqual((await snapshot(other)).actions,[...before,'row','row','board','row']);assert.deepEqual(errors,[]);
});
test('malformed and incompatible imports preserve the active crossing, including literal hostile data',async()=>{
  const {page,errors}=await fixture();await start(page);await click(page,['rope','oil','ready','leave','ferry','load']);
  const before=await snapshot(page);
  for(const value of ['{broken',JSON.stringify({...before,engine_version:'old'}),JSON.stringify({...before,actions:['<img src=x onerror=alert(1)>']}),'x'.repeat(65537)]) {
    await page.locator('#save-input').setInputFiles({name:'bad.json',mimeType:'application/json',buffer:Buffer.from(value)});
    await page.waitForFunction(()=>document.querySelector('#notice').textContent.includes('could not be restored'));
    assert.deepEqual(await snapshot(page),before);assert.equal(await page.locator('#play').getAttribute('data-phase'),'ferry');
  }
  const good={...before,actions:['timber','oil','ready']};
  await page.locator('#save-input').setInputFiles({name:'good.json',mimeType:'application/json',buffer:Buffer.from(JSON.stringify(good))});
  await page.keyboard.press('Escape');assert.deepEqual(await snapshot(page),before);assert.deepEqual(errors,[]);
});
test('storage failure still allows complete play, export and file recovery',async()=>{
  const {page,errors}=await fixture({},()=>{
    Storage.prototype.setItem=function(){throw new DOMException('Unavailable','QuotaExceededError');};
    Storage.prototype.getItem=function(){throw new DOMException('Unavailable','SecurityError');};
  });
  await start(page);await click(page,['rope','timber','ready','herbs','bargain','causeway','iven','roof','span','convoy']);
  assert.equal(await result(page),'FULL_RESCUE');assert.match(await page.locator('#save-status').textContent(),/unavailable/);
  const saved=await download(page);assert.equal(saved.actions.at(-1),'convoy');
  await page.locator('#save-input').setInputFiles({name:'own.json',mimeType:'application/json',buffer:Buffer.from(JSON.stringify(saved))});
  await page.locator('#confirm-replacement').click();assert.equal(await result(page),'FULL_RESCUE');assert.deepEqual(errors,[]);
});
test('touch cargo controls expose capacity and certain surge risk before accepting a trip',async()=>{
  const {page,errors}=await fixture({viewport:{width:390,height:844},hasTouch:true,isMobile:true});
  await page.locator('#begin').tap();
  await page.locator('#toggle-map').tap();assert.equal(await page.locator('#map-frame').isVisible(),true);
  await page.locator('#toggle-map').tap();assert.equal(await page.locator('#map-frame').isVisible(),false);
  for(const a of ['timber','oil','ready','leave','ferry','iven','roof','board','row','row','load','board'])await page.locator(`[data-action="${a}"]`).tap();
  assert.match(await page.locator('[data-action="row"] .detail').textContent(),/medicine will spoil/);
  assert.match(await page.locator('#boat-info').textContent(),/2\/3 cargo slots/);
  assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));await shot(page,'mobile-ferry-surge');
  await page.locator('[data-action="row"]').tap();assert.equal(await result(page),'PEOPLE_SAFE');assert.deepEqual(errors,[]);
});
test('keyboard-only equipment and workshop choices retain focus and preserve lie memory',async()=>{
  const {page,errors}=await fixture();await page.locator('#begin').focus();await page.keyboard.press('Enter');
  for(const a of ['rope','timber','ready','lie','apologize','herbs','bargain','causeway','roof','span','lead']) {
    await page.locator(`[data-action="${a}"]`).focus();await page.keyboard.press('Enter');
    assert.equal(await page.evaluate(()=>document.activeElement.id),a==='rope'||a==='timber'?'': 'scene-title');
  }
  assert.equal(await result(page),'PEOPLE_SAFE');assert.match(await page.locator('#epilogue').textContent(),/Withdrawn/);
  assert.deepEqual(errors,[]);
});
test('early stop, partial arrival and lost boat show truthful endings and stranded residents',async()=>{
  const cases=[
    {actions:['rope','oil','ready','leave','retreat'],ending:'SHELTERED',people:'0 / 4',text:'must wait above the flood'},
    {actions:['rope','oil','ready','leave','ferry','board','row','finish'],ending:'PARTIAL_CROSSING',people:'2 / 4',text:'missing names'},
    {actions:['rope','oil','ready','leave','ferry','board','row','row','load','row'],ending:'BOAT_LOST',people:'2 / 4',text:'safety chains'}
  ];
  for(const c of cases) {
    const {page,errors}=await fixture();await start(page);await click(page,c.actions);
    assert.equal(await result(page),c.ending);assert.ok((await page.locator('#outcome').textContent()).includes(c.people));
    assert.ok((await page.locator('#narrative').textContent()+await page.locator('#epilogue').textContent()).includes(c.text));
    assert.match(await page.locator('#roster').textContent(),/stranded/);assert.doesNotMatch(await page.locator('#roster').textContent(),/leave(s)? at beat/);
    assert.equal(await page.locator('#party-marker').getAttribute('opacity'),'0');assert.deepEqual(errors,[]);
  }
});
test('workshop beyond the flood window explains the closed crossing without reopening time',async()=>{
  const {page,errors}=await fixture();await start(page);await click(page,['rope','timber','ready',...Array(9).fill('wait')]);
  assert.equal(await page.locator('#remaining').textContent(),'0');assert.equal(await page.locator('#play').getAttribute('data-phase'),'workshop');
  assert.match(await page.locator('#context').textContent(),/no crossing can begin tonight/);
  await click(page,['wait','wait','wait']);assert.equal(await result(page),'SHELTERED');
  assert.equal(await page.locator('[data-action="ferry"]').count(),0);assert.deepEqual(errors,[]);
});
