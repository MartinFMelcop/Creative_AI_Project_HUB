import test,{before,after} from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import {createRequire} from 'node:module';
import {createServer} from '../server.mjs';
const {chromium}=createRequire(new URL('../../../realtime-integration-lab/package.json',import.meta.url))('playwright-core');
let server,browser,url;const contexts=[];
before(async()=>{server=createServer();await new Promise(r=>server.listen(0,'127.0.0.1',r));url=`http://127.0.0.1:${server.address().port}`;browser=await chromium.launch({executablePath:process.env.CHROMIUM_PATH||'/usr/bin/chromium',headless:true});});
after(async()=>{for(const c of contexts)await c.close();await browser?.close();await new Promise(r=>server.close(r));});
async function fixture(options={}){const c=await browser.newContext(options);contexts.push(c);const page=await c.newPage(),errors=[];page.on('pageerror',e=>errors.push(e.message));await page.goto(url);return {page,errors};}
const click=async(p,actions)=>{for(const a of actions)await p.locator(`[data-action="${a}"]`).click();};
const road=['rope','timber','ready','herbs','bargain','causeway','iven','roof','span','convoy'];
const wet=['timber','oil','ready','leave','ferry','iven','roof','board','row','row','load','board','row'];
async function morning(page,night){await page.locator('#begin').click();await click(page,night);await page.locator('#continue-morning').click();}
async function shot(page,name){if(process.env.WAYSTONE_SCREENSHOT_DIR)await page.screenshot({path:process.env.WAYSTONE_SCREENSHOT_DIR+'/'+name+'.png',fullPage:true});}
test('full two-day road campaign renders new scenes, honest outcomes and complete journal',async()=>{
  const {page,errors}=await fixture({viewport:{width:1440,height:1050}});await morning(page,road);
  assert.match(await page.locator('#narrative').textContent(),/six work counters/);assert.equal(await page.locator('#remaining').textContent(),'6');
  assert.match(await page.locator('#roster').textContent(),/Supplied on time/);await shot(page,'morning-opening');
  await click(page,['grain','seed','plant','ready-ferry']);assert.equal(await page.locator('#play').getAttribute('data-ending'),'READY_FOR_NOON');
  assert.match(await page.locator('#outcome').textContent(),/Planted/);assert.match(await page.locator('#epilogue').textContent(),/check the rows/);
  await page.locator('#journal summary').click();assert.equal(await page.locator('#journal-entries>li').count(),15);await page.locator('#journal summary').click();await shot(page,'morning-ending');
  assert.deepEqual(errors,[]);
});
test('clinic priority and grain priority produce different care timing through actual controls',async()=>{
  for(const [actions,onTime] of [[['depot','supply-clinic','grain','grain','seed'],true],[['grain','grain','depot','supply-clinic','seed'],false]]) {
    const {page,errors}=await fixture();await morning(page,wet);assert.match(await page.locator('#context').textContent(),/two crates/);
    await click(page,actions);assert.match(await page.locator('#outcome').textContent(),onTime?/On time/:/Late/);
    assert.match(await page.locator('#outcome').textContent(),/4 \/ 4 crates/);assert.deepEqual(errors,[]);
  }
});
test('legacy ending imports, morning reload and campaign export recover in a fresh profile',async()=>{
  const {page,errors}=await fixture();const legacy={format:'waystone-save',schema:1,engine_version:'0.2.0',actions:road};
  await page.locator('#save-input').setInputFiles({name:'old.json',mimeType:'application/json',buffer:Buffer.from(JSON.stringify(legacy))});
  await page.locator('#continue-morning').click();await click(page,['grain','seed']);await page.reload();await page.locator('#resume').click();
  assert.match(await page.locator('#roster').textContent(),/Dry in the yard/);assert.equal(await page.locator('#remaining').textContent(),'4');
  const download=page.waitForEvent('download');await page.locator('#export').click();const saved=JSON.parse(await fs.readFile(await (await download).path(),'utf8'));assert.equal(saved.schema,2);
  const {page:other}=await fixture();await other.locator('#save-input').setInputFiles({name:'campaign.json',mimeType:'application/json',buffer:Buffer.from(JSON.stringify(saved))});
  await click(other,['plant','ready-ferry']);assert.equal(await other.locator('#play').getAttribute('data-ending'),'READY_FOR_NOON');
  await other.locator('#restart').click();await other.locator('#confirm-replacement').click();assert.equal(await other.locator('#play').getAttribute('data-phase'),'pack');assert.equal(await other.locator('#flood-title').textContent(),'The flood window');assert.deepEqual(errors,[]);
});
test('mobile fallback campaign accounts for stranded people and keeps planting tied to crew recovery',async()=>{
  const {page,errors}=await fixture({viewport:{width:390,height:844},hasTouch:true});
  await morning(page,['rope','oil','ready','leave','retreat']);await page.locator('[data-action="seed"]').tap();
  assert.equal(await page.locator('[data-action="plant"]').count(),0);assert.match(await page.locator('#context').textContent(),/whole mill party/);
  await page.locator('[data-action="recover-crew"]').tap();assert.match(await page.locator('#roster').textContent(),/4 of 4/);
  await shot(page,'morning-mobile');assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
  await page.locator('[data-action="close"]').tap();assert.equal(await page.locator('#play').getAttribute('data-ending'),'WORK_REMAINS');assert.deepEqual(errors,[]);
});
