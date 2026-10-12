import test,{before,after} from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import {createRequire} from 'node:module';
import {createServer} from '../server.mjs';
import {WINDOWS} from '../dist/core.js';
const require=createRequire(new URL('../../realtime-integration-lab/package.json',import.meta.url));
const {chromium}=require('playwright-core');
const rain=JSON.parse(await fs.readFile(new URL('../dist/rain-circuit.json',import.meta.url),'utf8'));
const expectedHolds=rain.charts.arcade.filter(n=>n.duration).length;
let server,browser,url;
before(async()=>{
  server=createServer();await new Promise(r=>server.listen(0,'127.0.0.1',r));url=`http://127.0.0.1:${server.address().port}`;
  browser=await chromium.launch({executablePath:process.env.CHROMIUM_PATH||'/usr/bin/chromium',headless:true});
});
after(async()=>{await browser?.close();await new Promise(r=>server?.close(r));});
async function fixture(options={}) {
  const context=await browser.newContext(options),page=await context.newPage(),errors=[];
  page.on('pageerror',e=>errors.push(e.message));
  await page.addInitScript(()=>{
    const Original=window.AudioContext;
    window.AudioContext=class extends Original {constructor(...args){super(...args);window.soundProbe=this;window.decodedDurations=[];}
      async decodeAudioData(...args){const buffer=await super.decodeAudioData(...args);window.decodedDurations.push(buffer.duration);return buffer;}};
  });
  await page.goto(url);await page.locator('#start:not([disabled])').waitFor();return {context,page,errors};
}
const mode=(page,m)=>page.waitForFunction(m=>document.querySelector('#stage').dataset.mode===m,m);
const at=(page,t)=>page.waitForFunction(t=>Number(document.querySelector('#stage').dataset.position)>=t,t,{polling:'raf'});
async function pressAt(page,time,codes) {
  await page.evaluate(({time,codes})=>new Promise(resolve=>{
    const tick=()=>{if(Number(document.querySelector('#stage').dataset.position)>=time){
      for(const code of codes)document.dispatchEvent(new KeyboardEvent('keydown',{code,bubbles:true}));resolve();
    }else requestAnimationFrame(tick);};tick();
  }),{time,codes});
}
test('track selection decodes the right audio; early release fails, paused holds can be armed before resume',{timeout:30000},async()=>{
  const {context,page,errors}=await fixture();
  assert.equal(await page.locator('#song option').count(),2);
  await page.locator('#song').selectOption('rain-circuit');assert.equal(await page.title(),'Tokyo 80s — Rain Circuit');
  assert.equal(await page.locator('#progress').getAttribute('max'),'84.5');
  assert.equal(await page.evaluate(()=>!!window.soundProbe),false);
  await page.locator('#start').click();await mode(page,'playing');assert.equal(await page.locator('#song').isDisabled(),true);
  await pressAt(page,2.5,['KeyD','KeyF']);await at(page,2.65);await page.keyboard.up('f');
  await page.waitForFunction(()=>document.querySelector('#judgment').textContent==='HOLD LOST');
  assert.equal(Number(await page.locator('#score').textContent()),1000);
  await page.keyboard.up('d');await pressAt(page,7.5,['KeyF']);await at(page,7.66);
  await page.locator('#pause').click();await mode(page,'paused');
  const frozen=Number(await page.locator('#stage').getAttribute('data-position'));
  await page.waitForTimeout(200);assert.ok(Math.abs(Number(await page.locator('#stage').getAttribute('data-position'))-frozen)<.02);
  assert.equal(await page.locator('[data-lane="1"]').isEnabled(),true);
  await page.keyboard.down('f');await page.locator('#pause').click();await mode(page,'playing');
  await at(page,8.8);await page.keyboard.up('f');assert.equal(Number(await page.locator('#score').textContent()),2000);
  assert.ok(Math.abs((await page.evaluate(()=>window.decodedDurations[0]))-84.5)<.05);
  assert.deepEqual(errors,[]);await context.close();
});
test('a complete Rain Circuit Arcade performance carries actual tails and moves into the original stage',{timeout:115000},async()=>{
  const {context,page,errors}=await fixture({acceptDownloads:true,viewport:{width:1280,height:900}});
  await page.evaluate(()=>localStorage.setItem('tokyo80s-best-v1-arcade','12345'));
  await page.locator('#song').selectOption('rain-circuit');await page.locator('#difficulty').selectOption('arcade');
  await page.locator('#start').click();await mode(page,'playing');
  const performance=page.evaluate(async()=>{
    const track=await fetch('rain-circuit.json').then(r=>r.json());
    const events=track.charts.arcade.flatMap(n=>[{time:n.time,lane:n.lane,head:true},...(n.duration?[{time:n.time+n.duration,lane:n.lane,head:false}]:[{time:n.time+.01,lane:n.lane,head:false}])]).sort((a,b)=>a.time-b.time||Number(a.head)-Number(b.head));
    const codes=['KeyD','KeyF','KeyJ','KeyK'];let index=0;
    await new Promise(resolve=>{const tick=()=>{
      const time=Number(document.querySelector('#stage').dataset.position);
      while(index<events.length&&events[index].time<=time){const event=events[index++];document.dispatchEvent(new KeyboardEvent(event.head?'keydown':'keyup',{code:codes[event.lane],bubbles:true}));}
      if(index===events.length)resolve();else requestAnimationFrame(tick);
    };tick();});
  });
  if(process.env.RHYTHM_SCREENSHOT_DIR){await at(page,13);await page.screenshot({path:process.env.RHYTHM_SCREENSHOT_DIR+'/rain-playing.png',fullPage:true});}
  await performance;await mode(page,'results');
  const download=page.waitForEvent('download');await page.locator('#export').click();
  const file=await download;assert.equal(file.suggestedFilename(),'rain-circuit-arcade-run.json');
  const data=JSON.parse(await fs.readFile(await file.path(),'utf8'));
  assert.equal(data.track,'rain-circuit');assert.equal(data.notes.length,rain.charts.arcade.length);assert.equal(data.notes.filter(n=>n.duration>0).length,expectedHolds);
  assert.equal(data.counts.pending,0);assert.ok(data.accuracy>95);assert.ok(data.notes.filter(n=>n.duration>0&&n.state==='perfect').length>=Math.ceil(expectedHolds*.9));
  assert.equal(await page.evaluate(()=>localStorage.getItem('tokyo80s-best-v1-arcade')),'12345');
  assert.equal(Number(await page.evaluate(()=>localStorage.getItem('tokyo80s-best-v2-rain-circuit-arcade'))),data.score);
  if(process.env.RHYTHM_SCREENSHOT_DIR){await page.screenshot({path:process.env.RHYTHM_SCREENSHOT_DIR+'/rain-results.png',fullPage:true});await fs.writeFile(process.env.RHYTHM_SCREENSHOT_DIR+'/rain-run.json',JSON.stringify(data,null,2));}
  await page.locator('#next-stage').click();await mode(page,'playing');
  assert.equal(await page.locator('#song').inputValue(),'midnight-signal');assert.equal(await page.locator('#progress').getAttribute('max'),'69');
  assert.equal(Number(await page.locator('#score').textContent()),0);
  assert.ok(Math.abs((await page.evaluate(()=>window.decodedDurations.at(-1)))-69)<.05);
  assert.deepEqual(errors,[]);await context.close();
});
test('narrow touch carries a hold at its actual head judgment and calibrated offset',{timeout:12000},async()=>{
  const {context,page,errors}=await fixture({viewport:{width:390,height:844},hasTouch:true,isMobile:true});
  await page.locator('#song').selectOption('rain-circuit');assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
  await page.locator('#calibrate').click();await page.locator('#offset').fill('20');await page.locator('#apply').click();
  // Observe the real model input without changing its timing, scoring or return value.
  await page.evaluate(async()=>{
    const {RhythmRun}=await import('/core.js'),original=RhythmRun.prototype.hit;
    RhythmRun.prototype.hit=function(lane,time){
      const note=original.call(this,lane,time);
      if(note?.duration)window.touchHead={state:note.state,lane:note.lane,error:note.error,duration:note.duration};
      return note;
    };
  });
  const cdp=await context.newCDPSession(page);
  await page.locator('#start').click();await mode(page,'playing');
  // Starting the mobile stage scrolls it into view, so resolve coordinates before the timed input.
  const activeBox=await page.locator('[data-lane="1"]').boundingBox();
  await at(page,2.52);
  await cdp.send('Input.dispatchTouchEvent',{type:'touchStart',touchPoints:[{x:activeBox.x+activeBox.width/2,y:activeBox.y+activeBox.height/2,id:1}]});
  const head=await page.evaluate(()=>window.touchHead);
  assert.equal(head?.state,'holding');assert.equal(head.lane,1);assert.equal(head.duration,1.25);
  assert.ok(Number.isFinite(head.error)&&Math.abs(head.error)<=WINDOWS.ok+1e-9);
  assert.equal(Number(await page.locator('#score').textContent()),0,'A head earns no sustain points before the tail.');
  await at(page,3.81);await cdp.send('Input.dispatchTouchEvent',{type:'touchEnd',touchPoints:[]});
  const expected=Math.abs(head.error)<=WINDOWS.perfect+1e-9?1000:Math.abs(head.error)<=WINDOWS.good+1e-9?700:400;
  assert.equal(Number(await page.locator('#score').textContent()),expected,'The carried tail must award exactly its real head judgment.');
  assert.equal(Number(await page.locator('#combo').textContent()),1);
  assert.equal(await page.locator('#offset').inputValue(),'20');
  if(process.env.RHYTHM_SCREENSHOT_DIR)await page.screenshot({path:process.env.RHYTHM_SCREENSHOT_DIR+'/rain-mobile.png'});
  assert.deepEqual(errors,[]);await context.close();
});
