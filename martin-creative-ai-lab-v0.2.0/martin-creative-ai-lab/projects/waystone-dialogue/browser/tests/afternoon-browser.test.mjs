import test,{before,after} from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import {createRequire} from 'node:module';
import {createServer} from '../server.mjs';
const {chromium}=createRequire(new URL('../../../realtime-integration-lab/package.json',import.meta.url))('playwright-core');
let server,browser,url;const contexts=[];
before(async()=>{server=createServer();await new Promise(r=>server.listen(0,'127.0.0.1',r));url=`http://127.0.0.1:${server.address().port}`;browser=await chromium.launch({executablePath:process.env.CHROMIUM_PATH||'/usr/bin/chromium',headless:true});});
after(async()=>{for(const c of contexts)await c.close();await browser?.close();await new Promise(r=>server.close(r));});
async function fixture(options={},blockStorage=false) {
  const c=await browser.newContext(options);contexts.push(c);
  if(blockStorage)await c.addInitScript(()=>{Storage.prototype.setItem=()=>{throw new Error('Declared storage failure');};});
  const page=await c.newPage(),errors=[];page.on('pageerror',e=>errors.push(e.message));await page.goto(url);return {page,errors};
}
const click=async(p,actions)=>{for(const a of actions)await p.locator(`[data-action="${a}"]`).click();};
const road=['rope','timber','ready','herbs','bargain','causeway','iven','roof','span','convoy'];
const wet=['timber','oil','ready','leave','ferry','iven','roof','board','row','row','load','board','row'];
const work=['depot','supply-clinic','grain','grain','seed'];
async function runMorning(page,night,actions) {
  await page.locator('#begin').click();await click(page,night);await page.locator('#continue-morning').click();await click(page,actions);
  await page.locator('#continue-handover').click();
}
async function shot(page,name){if(process.env.WAYSTONE_SCREENSHOT_DIR)await page.screenshot({path:process.env.WAYSTONE_SCREENSHOT_DIR+'/'+name+'.png',fullPage:true});}
async function save(page) {
  const waiting=page.waitForEvent('download');await page.locator('#export').click();return JSON.parse(await fs.readFile(await (await waiting).path(),'utf8'));
}
const upload=(page,data)=>page.locator('#save-input').setInputFiles({name:'journey.json',mimeType:'application/json',buffer:Buffer.from(JSON.stringify(data))});
test('afternoon controls expose loan cost, persist work and keep the receipt immutable',async()=>{
  for(const [decision,grain,time] of [['keep-crossing',4,2],['lend-ferry',2,0],['send-guide',4,0]]) {
    const {page,errors}=await fixture({viewport:{width:390,height:844},hasTouch:true,isMobile:true});
    await runMorning(page,wet,['depot','supply-clinic','close']);
    await click(page,['hear-iven','settle',decision,decision==='keep-crossing'?'decline':'return-at-dusk']);
    const before=await save(page);await page.locator('#continue-afternoon').tap();
    assert.equal(await page.locator('#play').getAttribute('data-phase'),'afternoon');
    assert.match(await page.locator('#context').textContent(),/Noon commitments/);
    await page.locator('[data-action="grain"]').focus();await page.keyboard.press('Enter');
    await page.reload();assert.match(await page.locator('#resume-note').textContent(),/Saved afternoon/);await page.locator('#resume').click();
    await click(page,['grain']);assert.equal(await page.locator('#remaining').textContent(),String(time));
    if(time){await click(page,['seed','close']);}
    assert.match(await page.locator('#outcome').textContent(),new RegExp(`Kitchen grain${grain} / 4`));
    assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
    const data=await save(page);assert.equal(data.schema,4);assert.deepEqual(data.actions.slice(0,before.actions.length),before.actions);
    await page.locator('#journal summary').click();assert.equal(await page.locator('#journal-entries>li').count(),data.actions.length);
    assert.doesNotMatch(await page.locator('#journal-entries').textContent(),/undefined/);await page.locator('#journal summary').click();
    if(decision==='lend-ferry'){assert.match(await page.locator('#epilogue').textContent(),/return is due now/);await shot(page,'afternoon-boat-mobile');}
    const {page:other}=await fixture();await upload(other,data);assert.match(await other.locator('#scene-title').textContent(),/light is going/);
    await upload(other,{...data,actions:[...data.actions,'grain']});await other.locator('#notice').filter({hasText:'could not be restored'}).waitFor();assert.deepEqual(await save(other),data);
    await other.locator('#replay').click();await other.locator('#confirm-replacement').click();assert.equal(await other.locator('#continue-afternoon').isVisible(),false);
    assert.deepEqual(errors,[]);
  }
});
test('blocked browser storage still permits late-care workflow and portable recovery',async()=>{
  const {page,errors}=await fixture({viewport:{width:1440,height:1050}},true);
  await runMorning(page,wet,['grain','grain','depot','supply-clinic','seed']);
  await click(page,['settle','keep-crossing','review-later']);await page.locator('#continue-afternoon').click();
  await click(page,['recall']);assert.match(await page.locator('#narrative').textContent(),/mending a shutter/);
  await shot(page,'afternoon-recall');await click(page,['plant','close']);
  assert.match(await page.locator('#outcome').textContent(),/Contacted for afternoon care/);assert.match(await page.locator('#save-status').textContent(),/unavailable/);
  const saved=await save(page),{page:other}=await fixture();await upload(other,saved);
  assert.match(await other.locator('#epilogue').textContent(),/original late supply time remains/);assert.deepEqual(errors,[]);
});
