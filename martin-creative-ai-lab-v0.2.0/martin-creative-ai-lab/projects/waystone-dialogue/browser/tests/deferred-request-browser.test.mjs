import test,{before,after} from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import {createRequire} from 'node:module';
import {Campaign,serialize} from '../dist/campaign.js';
import {createServer} from '../server.mjs';
const {chromium}=createRequire(new URL('../../../realtime-integration-lab/package.json',import.meta.url))('playwright-core');
let server,browser,url;const contexts=[];
before(async()=>{server=createServer();await new Promise(r=>server.listen(0,'127.0.0.1',r));url=`http://127.0.0.1:${server.address().port}`;browser=await chromium.launch({executablePath:process.env.CHROMIUM_PATH||'/usr/bin/chromium',headless:true});});
after(async()=>{for(const c of contexts)await c.close();await browser?.close();await new Promise(r=>server.close(r));});
async function fixture(options={},blocked=false){const c=await browser.newContext(options);contexts.push(c);if(blocked)await c.addInitScript(()=>{Storage.prototype.setItem=()=>{throw new Error('Declared storage failure');};});const page=await c.newPage(),errors=[];page.on('pageerror',e=>errors.push(e.message));await page.goto(url);return {page,errors};}
const click=async(p,actions)=>{for(const a of actions)await p.locator(`[data-action="${a}"]`).click();};
const wet=['timber','oil','ready','leave','ferry','iven','roof','board','row','row','load','board','row'];
const noon=[...wet,'morning','depot','supply-clinic','close','handover','hear-iven','settle','keep-crossing','review-later'];
async function save(p){const pending=p.waitForEvent('download');await p.locator('#export').click();return JSON.parse(await fs.readFile(await (await pending).path(),'utf8'));}
const upload=(p,data)=>p.locator('#save-input').setInputFiles({name:'declared-journey.json',mimeType:'application/json',buffer:Buffer.from(JSON.stringify(data))});
async function shot(p,name){if(process.env.WAYSTONE_SCREENSHOT_DIR)await p.screenshot({path:process.env.WAYSTONE_SCREENSHOT_DIR+'/'+name+'.png',fullPage:true});}
const overflow=p=>p.evaluate(()=>document.documentElement.scrollWidth>innerWidth);

test('actual keyboard consultation reloads tentative terms, then applies only the new guide departure',async()=>{
  const {page,errors}=await fixture({viewport:{width:1440,height:1050}});await page.locator('#begin').click();await click(page,wet);
  await page.locator('#continue-morning').click();await click(page,['depot','supply-clinic','close']);await page.locator('#continue-handover').click();
  await click(page,['hear-iven','settle','keep-crossing','review-later']);const before=await save(page);assert.equal(before.schema,3);
  await page.locator('#continue-afternoon').click();await click(page,['grain']);
  await page.locator('[data-action="revisit-request"]').focus();await page.keyboard.press('Enter');
  assert.match(await page.locator('#scene-title').textContent(),/request comes back/);assert.equal(await page.evaluate(()=>document.activeElement.id),'scene-title');
  await click(page,['review-list','review-mara']);await shot(page,'request-table-desktop');
  await click(page,['review-settle']);assert.equal(await page.locator('[data-action="review-guide"]').count(),0);
  await click(page,['review-back','review-iven','review-settle','review-guide']);
  assert.match(await page.locator('#equipment').textContent(),/2 crate\(s\) \/ 1 shift/);assert.match(await page.locator('#roster').textContent(),/IvenWith the crew/);
  assert.equal(await page.locator('#remaining').textContent(),'3');const tentative=await save(page);assert.equal(tentative.schema,5);
  const boatPosition=await page.locator('#boat-marker').getAttribute('transform');assert.equal(boatPosition,'translate(445 293)');
  await page.reload();await page.locator('#resume').click();assert.match(await page.locator('#scene-title').textContent(),/Agree the loan’s terms/);
  assert.equal(await page.locator('#remaining').textContent(),'3');assert.equal(await page.locator('#boat-marker').getAttribute('transform'),boatPosition);await shot(page,'request-terms-desktop');
  await click(page,['review-dusk']);assert.match(await page.locator('#roster').textContent(),/IvenVolunteering upstream/);
  assert.match(await page.locator('#equipment').textContent(),/2 crate\(s\) \/ 2 shift/);
  await click(page,['grain','close']);const end=await save(page);assert.deepEqual(end.actions.slice(0,before.actions.length),before.actions);
  assert.match(await page.locator('#outcome').textContent(),/Kitchen grain4 \/ 4/);
  assert.match(await page.locator('#epilogue').textContent(),/left after 1 afternoon shift.*3 shift/);
  assert.match(await page.locator('#epilogue').textContent(),/No return or upstream rescue has been observed/);
  await page.locator('#journal summary').click();assert.equal(await page.locator('#journal-entries>li').count(),end.actions.length);
  assert.doesNotMatch(await page.locator('#journal-entries').textContent(),/undefined/);assert.deepEqual(errors,[]);
});

test('mobile boat loan after work preserves old receipt and recovers schema 5 with blocked storage',async()=>{
  const g=new Campaign();for(const a of [...noon,'afternoon','grain'])g.act(a);const old=serialize(g);assert.equal(old.schema,4);
  const {page,errors}=await fixture({viewport:{width:390,height:844},hasTouch:true,isMobile:true},true);
  await upload(page,old);await page.locator('#scene-title').filter({hasText:'Four shifts'}).waitFor();
  await page.locator('[data-action="revisit-request"]').tap();await click(page,['review-settle','review-boat']);
  await page.locator('[data-action="review-pause"]').tap();assert.equal(await page.locator('#remaining').textContent(),'3');
  assert.match(await page.locator('#equipment').textContent(),/ferry/);await page.locator('[data-action="revisit-request"]').tap();
  assert.match(await page.locator('#narrative').textContent(),/gets down from the wall/);
  await click(page,['review-settle','review-boat','review-dusk']);assert.match(await page.locator('#equipment').textContent(),/ridge trail/);
  await click(page,['grain','close']);assert.match(await page.locator('#outcome').textContent(),/Kitchen grain3 \/ 4/);
  assert.match(await page.locator('#save-status').textContent(),/unavailable/);assert.equal(await overflow(page),false);await shot(page,'request-dusk-mobile');
  const saved=await save(page);assert.equal(saved.schema,5);assert.deepEqual(saved.actions.slice(0,old.actions.length),old.actions);
  const {page:other,errors:otherErrors}=await fixture();
  // File selection finishes before its actual asynchronous read. Hold and release
  // that read, then assert the restored view rather than relying on selection.
  await other.evaluate(()=>{const read=File.prototype.text;File.prototype.text=function(){const file=this;return new Promise(resolve=>{globalThis.finishFileRead=()=>resolve(read.call(file));});};});
  await upload(other,saved);assert.equal(await other.locator('#epilogue').textContent(),'');await other.evaluate(()=>globalThis.finishFileRead());
  await other.locator('#epilogue').filter({hasText:'ferry left after 1'}).waitFor();assert.deepEqual(await save(other),saved);
  await upload(other,{...saved,schema:4,engine_version:'0.6.0'});await other.evaluate(()=>globalThis.finishFileRead());
  await other.locator('#notice').filter({hasText:'could not be restored'}).waitFor();assert.deepEqual(await save(other),saved);
  assert.deepEqual([...errors,...otherErrors],[]);
});
