import test, { before, after } from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import { createRequire } from 'node:module';
import { createServer } from '../server.mjs';
const require=createRequire(new URL('../../realtime-integration-lab/package.json',import.meta.url));
const {chromium}=require('playwright-core');
let server,browser,url;
const contexts=[];
before(async()=>{
  server=createServer();await new Promise(r=>server.listen(0,'127.0.0.1',r));
  url=`http://127.0.0.1:${server.address().port}`;
  browser=await chromium.launch({executablePath:process.env.CHROMIUM_PATH||'/usr/bin/chromium',headless:true});
});
after(async()=>{for(const c of contexts)await c.close();await browser?.close();await new Promise(r=>server?.close(r));});
async function fixture(options={}){
  const context=await browser.newContext(options);contexts.push(context);const page=await context.newPage();
  const errors=[];page.on('pageerror',e=>errors.push(e.message));
  await page.goto(url);await page.locator('#start:not([disabled])').waitFor();
  return {context,page,errors};
}
const pos=page=>page.locator('#stage').getAttribute('data-position').then(Number);
const mode=async(page,value)=>page.waitForFunction(v=>document.querySelector('#stage').dataset.mode===v,value);
const at=async(page,time)=>page.waitForFunction(t=>Number(document.querySelector('#stage').dataset.position)>=t,time,{polling:'raf'});
test('desktop and narrow views expose the complete playable workflow without horizontal overflow',async()=>{
  const {page,errors}=await fixture({viewport:{width:1280,height:900}});
  assert.equal(await page.title(),'Tokyo 80s — Midnight Signal');
  assert.equal(await page.locator('[data-lane]').count(),4);
  assert.equal(await page.locator('#start').isEnabled(),true);
  assert.equal(await page.locator('#pause').isDisabled(),true);
  assert.equal(await page.locator('#pulse').isDisabled(),true);
  assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
  if(process.env.RHYTHM_SCREENSHOT_DIR)await page.screenshot({path:process.env.RHYTHM_SCREENSHOT_DIR+'/desktop.png',fullPage:true});
  await page.setViewportSize({width:390,height:844});
  assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
  assert.ok(await page.locator('#board').evaluate(c=>c.width>0&&c.height>0));
  await page.locator('#calibrate').click();assert.equal(await page.locator('#calibration').evaluate(d=>d.open),true);
  await page.keyboard.press('Escape');assert.equal(await page.locator('#calibration').evaluate(d=>d.open),false);
  if(process.env.RHYTHM_SCREENSHOT_DIR)await page.screenshot({path:process.env.RHYTHM_SCREENSHOT_DIR+'/mobile.png',fullPage:true});
  assert.deepEqual(errors,[]);await page.context().close();
});
test('real audio starts, repeated input does not double-hit, pause freezes and restart resets',async()=>{
  const {page,errors}=await fixture();await page.locator('#start').click();await mode(page,'playing');
  await page.evaluate(()=>new Promise(resolve=>{
    const check=()=>{if(Number(document.querySelector('#stage').dataset.position)>=3){
      document.dispatchEvent(new KeyboardEvent('keydown',{code:'KeyD',bubbles:true}));
      document.dispatchEvent(new KeyboardEvent('keydown',{code:'KeyD',repeat:true,bubbles:true}));resolve();
    }else requestAnimationFrame(check);};check();
  }));
  assert.equal(Number(await page.locator('#score').textContent()),1000);
  await page.keyboard.up('d');await page.locator('#pause').click();await mode(page,'paused');
  const frozen=await pos(page),score=await page.locator('#score').textContent();
  await page.waitForTimeout(350);
  assert.ok(Math.abs(await pos(page)-frozen)<.02);assert.equal(await page.locator('#score').textContent(),score);
  await page.locator('#pause').click();await mode(page,'playing');await at(page,frozen+.2);
  await page.locator('#restart').click();await mode(page,'playing');
  assert.ok(await pos(page)<1);assert.equal(Number(await page.locator('#score').textContent()),0);
  assert.equal(await page.locator('#combo').textContent(),'0');assert.deepEqual(errors,[]);await page.context().close();
});
test('leaving the tab pauses the actual song before unobserved notes can pass',async()=>{
  const {page,context,errors}=await fixture();
  const cdp=await context.newCDPSession(page);await cdp.send('Emulation.setFocusEmulationEnabled',{enabled:false});
  await page.bringToFront();await page.locator('#start').click();await mode(page,'playing');await at(page,1);
  const peer=await context.newPage();await peer.goto('about:blank');await peer.bringToFront();await mode(page,'paused');
  const frozen=await pos(page);await page.waitForTimeout(250);assert.ok(Math.abs(await pos(page)-frozen)<.02);
  await page.bringToFront();assert.equal(await page.locator('#stage').getAttribute('data-mode'),'paused');
  await page.locator('#pause').click();await mode(page,'playing');assert.deepEqual(errors,[]);await context.close();
});
test('touch input scores a note through the same judgment path',async()=>{
  const {page,errors}=await fixture({viewport:{width:390,height:844},hasTouch:true,isMobile:true});
  await page.locator('#start').click();await mode(page,'playing');
  assert.ok(await page.locator('#stage').evaluate(el=>el.getBoundingClientRect().top>=0&&el.getBoundingClientRect().bottom<=innerHeight));
  if(process.env.RHYTHM_SCREENSHOT_DIR)await page.screenshot({path:process.env.RHYTHM_SCREENSHOT_DIR+'/playing-mobile.png'});
  await at(page,3.92);
  await page.locator('[data-lane="0"]').tap();
  assert.ok(Number(await page.locator('#score').textContent())>0);
  assert.ok(Number(await page.locator('#combo').textContent())>=1);
  assert.deepEqual(errors,[]);await page.context().close();
});
test('calibration uses scheduled real audio clicks, persists offset and stops when closed',async()=>{
  const {context,page,errors}=await fixture();
  await page.addInitScript(()=>{
    const Original=window.AudioContext;
    window.AudioContext=class extends Original{
      constructor(...args){super(...args);window.probeAudio=this;window.probeClicks=[];}
      createOscillator(){const osc=super.createOscillator(),start=osc.start.bind(osc);osc.start=t=>{window.probeClicks.push(t);start(t);};return osc;}
    };
  });
  await page.reload();await page.locator('#start:not([disabled])').waitFor();
  await page.locator('#calibrate').click();await page.locator('#clicks').click();
  await page.waitForFunction(()=>window.probeClicks?.length===12);
  await page.evaluate(()=>new Promise(resolve=>{
    let i=2;
    const check=()=>{
      if(window.probeAudio.currentTime>=window.probeClicks[i]+.08){
        document.dispatchEvent(new KeyboardEvent('keydown',{code:'KeyF',bubbles:true}));i++;
        if(i===12){resolve();return;}
      }requestAnimationFrame(check);
    };check();
  }));
  await page.waitForFunction(()=>document.querySelector('#cal-status').textContent.includes('Suggested offset'));
  const learned=Number(await page.locator('#offset').inputValue());assert.ok(learned>=75&&learned<=110,`Actual scheduled taps learned ${learned} ms`);
  await page.locator('#apply').click();await page.reload();await page.locator('#start:not([disabled])').waitFor();
  await page.locator('#calibrate').click();assert.equal(Number(await page.locator('#offset').inputValue()),learned);
  await page.locator('#clicks').click();await page.keyboard.press('Escape');
  assert.equal(await page.locator('#tap').isDisabled(),true);assert.deepEqual(errors,[]);await context.close();
});
test('audio failure keeps a retryable interface and recovers on a real second request',async()=>{
  const {page,errors}=await fixture();let rejected=false;
  await page.route('**/midnight-signal.ogg',route=>{if(!rejected){rejected=true;route.abort();}else route.continue();});
  await page.locator('#start').click();await mode(page,'error');
  assert.match(await page.locator('#status').textContent(),/fetch|track|network/i);
  assert.equal(await page.locator('#start').isEnabled(),true);
  await page.locator('#start').click();await mode(page,'playing');await at(page,.2);
  assert.deepEqual(errors,[]);await page.context().close();
});
test('a full Arcade run uses the real 69-second audio clock and exports actual results for replay', {timeout:100000},async()=>{
  const {page,errors}=await fixture({acceptDownloads:true});
  await page.locator('#difficulty').selectOption('arcade');await page.locator('#start').click();await mode(page,'playing');
  await page.evaluate(async()=>{
    const track=await fetch('track.json').then(r=>r.json()),notes=track.charts.arcade;
    const codes=['KeyD','KeyF','KeyJ','KeyK'];let index=0,pulsed=false;
    await new Promise(resolve=>{
      const check=()=>{
        const t=Number(document.querySelector('#stage').dataset.position);
        while(index<notes.length&&t>=notes[index].time){const code=codes[notes[index++].lane];
          document.dispatchEvent(new KeyboardEvent('keydown',{code,bubbles:true}));
          document.dispatchEvent(new KeyboardEvent('keyup',{code,bubbles:true}));
        }
        if(!pulsed&&document.querySelector('#aura').value===100){
          document.dispatchEvent(new KeyboardEvent('keydown',{code:'Space',bubbles:true}));pulsed=true;
        }
        if(document.querySelector('#stage').dataset.mode==='results'){resolve();return;}
        requestAnimationFrame(check);
      };check();
    });
  });
  await mode(page,'results');assert.equal(await page.locator('#results').isVisible(),true);
  const promise=page.waitForEvent('download');await page.locator('#export').click();const download=await promise;
  const result=JSON.parse(await fs.readFile(await download.path(),'utf8'));
  assert.equal(result.chart,'arcade');const currentTrack=await page.evaluate(()=>fetch('track.json').then(r=>r.json()));
  assert.equal(result.notes.length,currentTrack.charts.arcade.length);
  assert.equal(result.counts.pending,0);assert.equal(Object.values(result.counts).reduce((a,b)=>a+b),currentTrack.charts.arcade.length);
  assert.ok(result.accuracy>=90,`Synthetic audio-clock inputs achieved ${result.accuracy}%`);
  assert.equal(result.pulses,1);assert.ok(result.score>100000);assert.equal(result.strays,0);
  assert.match(await page.locator('#best').textContent(),/Arcade best/);
  assert.equal(result.mode,'full');assert.equal(result.playbackRate,1);
  assert.equal(result.phrases.length,8);assert.equal(result.phrases.reduce((sum,p)=>sum+p.notes,0),result.notes.length);
  assert.equal(await page.locator('#phrase-results button').count(),8);
  if(process.env.RHYTHM_SCREENSHOT_DIR){await fs.writeFile(process.env.RHYTHM_SCREENSHOT_DIR+'/actual-run.json',JSON.stringify(result,null,2)+'\n');await page.screenshot({path:process.env.RHYTHM_SCREENSHOT_DIR+'/results.png',fullPage:true});}
  const best=await page.evaluate(()=>localStorage.getItem('tokyo80s-best-v1-arcade'));
  await page.locator('#phrase-results button[data-phrase="7"]').click();await mode(page,'playing');
  assert.equal(await page.locator('#phrase').inputValue(),'7');assert.equal(await page.locator('#stage').getAttribute('data-session'),'rehearsal');
  assert.ok(Number(await page.locator('#stage').getAttribute('data-song-position'))>=49);
  assert.equal(await page.evaluate(()=>localStorage.getItem('tokyo80s-best-v1-arcade')),best);
  await page.locator('#full-run').click();await mode(page,'ready');await page.locator('#start').click();await mode(page,'playing');
  assert.equal(await page.locator('#stage').getAttribute('data-session'),'full');assert.equal(Number(await page.locator('#score').textContent()),0);
  assert.deepEqual(errors,[]);await page.context().close();
});
