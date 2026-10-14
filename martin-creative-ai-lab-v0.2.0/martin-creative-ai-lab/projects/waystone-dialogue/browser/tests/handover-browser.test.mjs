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
test('full causeway journey reaches a voiced handover, records the actual loan and all decisions',async()=>{
  const {page,errors}=await fixture({viewport:{width:1440,height:1050}});
  await runMorning(page,road,['grain','seed','plant','ready-ferry']);
  assert.equal(await page.locator('#play').getAttribute('data-phase'),'handover');
  assert.match(await page.locator('#narrative').textContent(),/Dain/);assert.equal(await page.locator('#remaining').textContent(),'1');
  await click(page,['hear-senn']);assert.match(await page.locator('#narrative').textContent(),/soil beneath her nails/);await shot(page,'handover-senn');
  await click(page,['hear-keeper','hear-mara','read-list','settle']);assert.equal(await page.locator('[data-action="send-guide"]').count(),0);
  await click(page,['back-to-table','hear-iven','settle']);assert.equal(await page.locator('[data-action="send-guide"]').count(),1);
  await click(page,['lend-ferry','return-at-dusk']);
  assert.equal(await page.locator('#play').getAttribute('data-ending'),'lend-ferry');
  assert.match(await page.locator('#outcome').textContent(),/causeway.*4 crate\(s\) \/ 1 shift/s);
  assert.match(await page.locator('#epilogue').textContent(),/No one has returned yet/);assert.match(await page.locator('#epilogue').textContent(),/harvest unknown/);
  const data=await save(page);assert.equal(data.schema,3);assert.equal(data.engine_version,'0.5.0');
  await page.locator('#journal summary').click();assert.equal(await page.locator('#journal-entries>li').count(),data.actions.length);
  assert.doesNotMatch(await page.locator('#journal-entries').textContent(),/undefined/);await page.locator('#journal summary').click();await shot(page,'handover-receipt');
  assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));assert.deepEqual(errors,[]);
});
test('same ferry ending renders the capacity cost of boat, guide and refusal through real controls',async()=>{
  for(const [decision,capacity] of [['lend-ferry','1 crate(s) / 2 shift(s)'],['send-guide','2 crate(s) / 2 shift(s)'],['keep-crossing','2 crate(s) / 1 shift(s)']]) {
    const {page,errors}=await fixture();await runMorning(page,wet,work);
    await click(page,['hear-iven','settle',decision,decision==='keep-crossing'?'decline':'open-return']);
    assert.ok((await page.locator('#outcome').textContent()).includes(capacity));
    assert.match(await page.locator('#epilogue').textContent(),/4 of 4 grain crates delivered/);
    assert.deepEqual(errors,[]);
  }
});
test('old morning save continues; reload and export/import retain consent, pending terms and ending',async()=>{
  const {page,errors}=await fixture();const old={format:'waystone-save',schema:2,engine_version:'0.4.0',actions:[...wet,'morning',...work]};
  await upload(page,old);await page.locator('#continue-handover').click();await click(page,['hear-iven','settle','send-guide']);
  const data=await save(page);await page.reload();assert.match(await page.locator('#resume-note').textContent(),/handover.*terms/);
  await page.locator('#resume').click();assert.equal(await page.locator('#scene-title').textContent(),'Write the limit.');
  const {page:other,errors:otherErrors}=await fixture();await upload(other,data);await click(other,['return-at-dusk']);
  assert.match(await other.locator('#outcome').textContent(),/Iven, by his own offer/);
  await other.reload();await other.locator('#resume').click();assert.equal(await other.locator('#play').getAttribute('data-ending'),'send-guide');
  const before=await save(other);await upload(other,{...before,actions:[...before.actions,'lend-ferry']});
  await other.locator('#notice').filter({hasText:'could not be restored'}).waitFor();
  assert.match(await other.locator('#notice').textContent(),/could not be restored/);assert.deepEqual(await save(other),before);
  await other.locator('#replay').click();await other.locator('#confirm-replacement').click();
  assert.equal(await other.locator('#play').getAttribute('data-phase'),'pack');assert.equal(await other.locator('#continue-handover').isVisible(),false);
  assert.deepEqual([...errors,...otherErrors],[]);
});
test('touch fallback keeps absent witnesses absent and corrections local; files work with blocked storage',async()=>{
  const {page,errors}=await fixture({viewport:{width:390,height:844},hasTouch:true,isMobile:true},true);
  await runMorning(page,['rope','timber','ready','lie','leave','retreat'],['close']);
  assert.equal(await page.locator('[data-action="hear-iven"]').count(),0);assert.equal(await page.locator('[data-action="hear-senn"]').count(),0);
  await page.locator('[data-action="hear-mara"]').tap();assert.match(await page.locator('#narrative').textContent(),/haven't brought any/);
  await page.locator('[data-action="correct-order"]').tap();assert.match(await page.locator('#narrative').textContent(),/no one adds their signature/);
  assert.equal(await page.locator('[data-action="hear-keeper"]').count(),0);await shot(page,'handover-mobile');
  await page.locator('[data-action="settle"]').tap();assert.equal(await page.locator('[data-action="lend-ferry"]').count(),0);
  await page.locator('[data-action="keep-crossing"]').focus();await page.keyboard.press('Enter');
  await page.locator('[data-action="review-later"]').tap();assert.match(await page.locator('#outcome').textContent(),/Later review requested/);
  assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));assert.match(await page.locator('#save-status').textContent(),/unavailable/);
  const saved=await save(page);const {page:other,errors:otherErrors}=await fixture();
  // setInputFiles dispatches change; it does not await the async File.text read.
  // Gate that real read to cover slow completion without a timing-dependent sleep.
  await other.evaluate(()=>{const read=File.prototype.text;File.prototype.text=function(){const file=this;return new Promise(resolve=>{globalThis.finishFileRead=()=>resolve(read.call(file));});};});
  await upload(other,saved);assert.equal(await other.locator('#outcome').textContent(),'');
  await other.evaluate(()=>globalThis.finishFileRead());
  await other.locator('#outcome').filter({hasText:'Crossing crew’s request'}).waitFor();
  assert.match(await other.locator('#outcome').textContent(),/Crossing crew’s request/);
  assert.deepEqual([...errors,...otherErrors],[]);
});
