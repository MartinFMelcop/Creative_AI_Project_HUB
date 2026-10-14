import test,{before,after} from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import {createRequire} from 'node:module';
import {createServer} from '../server.mjs';
const require=createRequire(new URL('../../realtime-integration-lab/package.json',import.meta.url));
const {chromium}=require('playwright-core');
let server,browser,url;
before(async()=>{
  server=createServer();await new Promise(r=>server.listen(0,'127.0.0.1',r));url=`http://127.0.0.1:${server.address().port}`;
  browser=await chromium.launch({executablePath:process.env.CHROMIUM_PATH||'/usr/bin/chromium',headless:true});
});
after(async()=>{await browser?.close();await new Promise(r=>server?.close(r));});
async function fixture(options={}) {
  const context=await browser.newContext({acceptDownloads:true,...options}),page=await context.newPage(),errors=[];
  page.on('pageerror',e=>errors.push(e.message));
  // Observe real Web Audio nodes without replacing time, decoding or playback.
  await page.addInitScript(()=>{
    const Original=window.AudioContext;
    window.audioStarts=[];window.clickStarts=[];
    window.AudioContext=class extends Original {
      constructor(...args){super(...args);window.soundProbe=this;}
      createBufferSource(){const node=super.createBufferSource(),start=node.start.bind(node);
        node.start=(...args)=>{window.audioStarts.push({args,rate:node.playbackRate.value,bufferDuration:node.buffer.duration});return start(...args);};return node;}
      createOscillator(){const node=super.createOscillator(),start=node.start.bind(node);
        node.start=(when)=>{window.clickStarts.push(when);return start(when);};return node;}
    };
  });
  await page.goto(url);await page.locator('#start:not([disabled])').waitFor();return {context,page,errors};
}
const mode=(page,value)=>page.waitForFunction(v=>document.querySelector('#stage').dataset.mode===v,value);
const at=(page,time)=>page.waitForFunction(t=>Number(document.querySelector('#stage').dataset.position)>=t,time,{polling:'raf'});
async function setup(page,{track='rain-circuit',chart='arcade',phrase='3',rate='0.75'}={}) {
  await page.locator('#song').selectOption(track);await page.locator('#difficulty').selectOption(chart);
  await page.locator('#phrase').selectOption(phrase);await page.locator('#rate').selectOption(rate);
}
async function exported(page) {
  const pending=page.waitForEvent('download');await page.locator('#export').click();const download=await pending;
  return {name:download.suggestedFilename(),data:JSON.parse(await fs.readFile(await download.path(),'utf8'))};
}
async function perform(page,{skipHold=false}={}) {
  return page.evaluate(async({skipHold})=>{
    const track=await fetch(document.querySelector('#song').value==='rain-circuit'?'rain-circuit.json':'track.json').then(r=>r.json());
    const rate=Number(document.querySelector('#rate').value),start=track.leadIn+Number(document.querySelector('#phrase').value)*960/track.bpm;
    const cue=Math.max(0,start-240/track.bpm),end=Math.min(track.musicEnd,start+960/track.bpm);
    const notes=track.charts[document.querySelector('#difficulty').value].filter(n=>n.time>=start&&n.time<end);
    const omit=skipHold?notes.find(n=>n.duration)?.id:null;
    const events=notes.filter(n=>n.id!==omit).flatMap(n=>[
      {time:(n.time-cue)/rate,lane:n.lane,head:true},
      {time:(n.time-cue+(n.duration||.015))/rate,lane:n.lane,head:false}
    ]).sort((a,b)=>a.time-b.time||Number(a.head)-Number(b.head));
    let index=0;const codes=['KeyD','KeyF','KeyJ','KeyK'];
    await new Promise(resolve=>{const tick=()=>{
      if(document.querySelector('#stage').dataset.mode==='results'){resolve();return;}
      if(document.querySelector('#stage').dataset.mode==='playing'){
        const time=Number(document.querySelector('#stage').dataset.position);
        while(index<events.length&&events[index].time<=time){const event=events[index++];document.dispatchEvent(new KeyboardEvent(event.head?'keydown':'keyup',{code:codes[event.lane],bubbles:true}));}
      }
      requestAnimationFrame(tick);
    };tick();});
    return {noteIds:notes.map(n=>n.id),omittedHold:omit,events:index};
  },{skipHold});
}
test('75% original-pitch backing uses its stretched offset and four clicks; pause preserves a real carried tail',{timeout:20000},async()=>{
  const {context,page,errors}=await fixture();await setup(page);
  assert.equal(await page.locator('#phrase option').count(),9);assert.match(await page.locator('#rehearsal-info').textContent(),/72 BPM/);
  await page.locator('#start').click();await mode(page,'playing');
  const probe=await page.evaluate(()=>({audio:audioStarts[0],clicks:clickStarts}));
  assert.equal(probe.audio.rate,1);assert.equal(probe.audio.args[1],40);assert.ok(Math.abs(probe.audio.bufferDuration-84.5/.75)<.05);
  assert.ok(Math.abs(probe.audio.args[2]-12.725/.75)<1e-8);
  assert.equal(probe.clicks.length,4);assert.ok(Math.abs(probe.clicks[1]-probe.clicks[0]-60/96/.75)<1e-6);
  assert.equal(await page.locator('#phrase').isDisabled(),true);assert.equal(await page.locator('#rate').isDisabled(),true);
  await page.evaluate(()=>new Promise(resolve=>{const tick=()=>{
    if(Number(document.querySelector('#stage').dataset.position)>=2.5/.75){document.dispatchEvent(new KeyboardEvent('keydown',{code:'KeyF',bubbles:true}));resolve();}
    else requestAnimationFrame(tick);};tick();}));
  await at(page,2.5/.75+.25);await page.locator('#pause').click();await mode(page,'paused');
  const frozen=Number(await page.locator('#stage').getAttribute('data-position'));
  await page.waitForTimeout(250);assert.ok(Math.abs(Number(await page.locator('#stage').getAttribute('data-position'))-frozen)<.02);
  await page.keyboard.down('f');await page.locator('#pause').click();await mode(page,'playing');
  await at(page,(2.5+1.25)/.75+.02);await page.keyboard.up('f');
  assert.equal(Number(await page.locator('#score').textContent()),1000);
  await page.locator('#full-run').click();await mode(page,'ready');
  assert.equal(await page.locator('#phrase').inputValue(),'full');assert.equal(await page.locator('#progress').getAttribute('max'),'84.5');
  await page.locator('#start').click();await mode(page,'playing');
  assert.equal((await page.evaluate(()=>audioStarts.at(-1))).rate,1);assert.equal((await page.evaluate(()=>audioStarts.at(-1))).args[1],0);
  assert.deepEqual(errors,[]);await context.close();
});
test('actual phrase attempts report errors, repeat with comparison, export source identity and preserve full bests',{timeout:65000},async()=>{
  const {context,page,errors}=await fixture({viewport:{width:1280,height:900}});await setup(page);
  await page.evaluate(()=>localStorage.setItem('tokyo80s-best-v2-rain-circuit-arcade','54321'));
  await page.locator('#start').click();await mode(page,'playing');await perform(page,{skipHold:true});await mode(page,'results');
  const playback=await page.evaluate(()=>({source:audioStarts[0],clicks:clickStarts.slice(0,4),elapsedAudioSeconds:soundProbe.currentTime-audioStarts[0].args[0]}));
  assert.ok(Math.abs(playback.elapsedAudioSeconds-12.725/.75)<.3);
  const first=await exported(page);assert.equal(first.name,'rain-circuit-arcade-phrase-3-75.json');
  assert.equal(first.data.mode,'rehearsal');assert.equal(first.data.playbackRate,.75);assert.equal(first.data.phrases.length,1);
  assert.equal(first.data.counts.miss,1);assert.equal(first.data.phrases[0].lostHolds,1);assert.equal(first.data.counts.pending,0);
  assert.equal(first.data.timeUnit,'performance-seconds');assert.equal(first.data.cueStart,30);
  assert.equal(first.data.backing.url,'assets/rehearsal/rain-circuit-75.ogg');
  assert.equal(first.data.backing.playbackRate,1);assert.equal(first.data.backing.tempoRate,.75);
  assert.equal(first.data.backing.pitch,'original');assert.equal(first.data.backing.offset,40);
  for(const n of first.data.notes)assert.ok(Math.abs(n.time*.75+30-n.sourceTime)<1e-8);
  assert.equal(await page.evaluate(()=>localStorage.getItem('tokyo80s-best-v2-rain-circuit-arcade')),'54321');
  await page.locator('#replay').click();await mode(page,'playing');await perform(page);await mode(page,'results');
  const second=await exported(page);assert.ok(second.data.accuracy>95);assert.equal(second.data.counts.miss,0);
  assert.match(await page.locator('#best').textContent(),/Previous identical setup:/);
  assert.equal(await page.evaluate(()=>localStorage.getItem('tokyo80s-best-v2-rain-circuit-arcade')),'54321');
  if(process.env.RHYTHM_SCREENSHOT_DIR){
    await page.screenshot({path:process.env.RHYTHM_SCREENSHOT_DIR+'/rehearsal-results.png',fullPage:true});
    await fs.writeFile(process.env.RHYTHM_SCREENSHOT_DIR+'/rehearsal-attempts.json',JSON.stringify({playback,first:first.data,second:second.data},null,2));
  }
  await page.locator('#rate').selectOption('0.9');await page.locator('#replay').click();await mode(page,'playing');await perform(page);await mode(page,'results');
  assert.doesNotMatch(await page.locator('#best').textContent(),/Previous identical setup:/);
  assert.equal((await exported(page)).data.playbackRate,.9);
  assert.deepEqual(errors,[]);await context.close();
});
test('both songs load each delivered tempo variant at native pitch and return to the unchanged full backing',{timeout:20000},async()=>{
  for(const track of ['midnight-signal','rain-circuit'])for(const rate of ['0.75','0.9']) {
    const {context,page,errors}=await fixture();const requested=[];
    page.on('request',request=>{if(request.url().endsWith('.ogg'))requested.push(new URL(request.url()).pathname);});
    await setup(page,{track,rate,phrase:'0'});
    await page.locator('#start').click();await mode(page,'playing');
    const probe=await page.evaluate(()=>audioStarts.at(-1));
    const duration=track==='midnight-signal'?69:84.5;
    assert.equal(probe.rate,1);assert.ok(Math.abs(probe.bufferDuration-duration/Number(rate))<.05);
    assert.equal(requested.at(-1),`/assets/rehearsal/${track}-${Math.round(Number(rate)*100)}.ogg`);
    await page.locator('#full-run').click();await mode(page,'ready');
    await page.locator('#start').click();await mode(page,'playing');
    const full=await page.evaluate(()=>audioStarts.at(-1));assert.equal(full.rate,1);
    assert.equal(full.args[1],0);assert.ok(Math.abs(full.bufferDuration-duration)<.05);
    assert.equal(requested.at(-1),`/assets/${track}.ogg`);
    assert.deepEqual(errors,[]);await context.close();
  }
});
test('missing or wrong-duration slow backing stops before any source/click; explicit retry uses the valid derivative',{timeout:20000},async()=>{
  const {context,page,errors}=await fixture();await setup(page,{phrase:'0'});
  const pattern='**/assets/rehearsal/rain-circuit-75.ogg';
  await page.route(pattern,route=>route.fulfill({status:404,body:'Not found'}));
  await page.locator('#start').click();await mode(page,'error');
  assert.match(await page.locator('#status').textContent(),/backing could not load/);
  assert.equal(await page.evaluate(()=>audioStarts.length+clickStarts.length),0);
  await page.unroute(pattern);
  await page.route(pattern,async route=>route.fulfill({contentType:'audio/ogg',body:await fs.readFile(new URL('../dist/assets/rain-circuit.ogg',import.meta.url))}));
  await page.locator('#start').click();await mode(page,'error');
  assert.match(await page.locator('#status').textContent(),/duration does not match/);
  assert.equal(await page.evaluate(()=>audioStarts.length+clickStarts.length),0);
  await page.unroute(pattern);await page.locator('#start').click();await mode(page,'playing');
  assert.equal((await page.evaluate(()=>audioStarts[0])).rate,1);
  assert.equal(await page.evaluate(()=>clickStarts.length),4);
  assert.deepEqual(errors,[]);await context.close();
});
test('tab interruption while backing loads cancels startup; returning requires an explicit new start',{timeout:20000},async()=>{
  const {context,page,errors}=await fixture();let release;
  const gate=new Promise(resolve=>{release=resolve;});
  const pattern='**/assets/rehearsal/rain-circuit-75.ogg';
  await page.route(pattern,async route=>{await gate;if(!page.isClosed())await route.continue();});
  try {
    const cdp=await context.newCDPSession(page);await cdp.send('Emulation.setFocusEmulationEnabled',{enabled:false});
    await page.bringToFront();await setup(page,{phrase:'0'});await page.locator('#start').click();await mode(page,'loading');
    const peer=await context.newPage();await peer.goto('about:blank');await peer.bringToFront();
    await page.waitForFunction(()=>document.querySelector('#stage').dataset.mode==='ready',null,{timeout:3000});
    assert.equal(await page.evaluate(()=>audioStarts.length+clickStarts.length),0);
    await page.bringToFront();assert.equal(await page.locator('#stage').getAttribute('data-mode'),'ready');
    await setup(page,{track:'midnight-signal',rate:'0.9',phrase:'0'});
    await page.locator('#start').click();await mode(page,'playing');
    release();await page.waitForTimeout(300);
    assert.equal(await page.evaluate(()=>audioStarts.length),1);assert.equal(await page.evaluate(()=>clickStarts.length),4);
    assert.ok(Math.abs((await page.evaluate(()=>audioStarts[0])).bufferDuration-69/.9)<.05);
    assert.equal(await page.locator('#stage').getAttribute('data-track'),'midnight-signal');
    assert.deepEqual(errors,[]);
  } finally {release();await context.close();}
});
test('narrow touch rehearsal carries a slowed hold; cancellation stops sound and restart enters a fresh take',{timeout:20000},async()=>{
  const {context,page,errors}=await fixture({viewport:{width:390,height:844},hasTouch:true,isMobile:true});
  await setup(page,{phrase:'0',rate:'0.9'});
  assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
  if(process.env.RHYTHM_SCREENSHOT_DIR)await page.screenshot({path:process.env.RHYTHM_SCREENSHOT_DIR+'/rehearsal-mobile.png',fullPage:true});
  await page.locator('#start').click();await mode(page,'playing');
  const cdp=await context.newCDPSession(page),box=await page.locator('[data-lane="1"]').boundingBox();
  await at(page,2.5/.9);
  await cdp.send('Input.dispatchTouchEvent',{type:'touchStart',touchPoints:[{x:box.x+box.width/2,y:box.y+box.height/2,id:1}]});
  await at(page,3.75/.9+.02);await cdp.send('Input.dispatchTouchEvent',{type:'touchEnd',touchPoints:[]});
  assert.ok(Number(await page.locator('#score').textContent())>=700);
  await page.locator('#restart').click();await mode(page,'playing');assert.equal(Number(await page.locator('#score').textContent()),0);
  assert.ok(Number(await page.locator('#stage').getAttribute('data-position'))<1);
  await page.locator('#full-run').click();await mode(page,'ready');
  // Mode changes in the handler; the previous playing position lasts until RAF.
  await page.waitForFunction(()=>Number(document.querySelector('#stage').dataset.position)===0,null,{polling:'raf'});
  const frozen=Number(await page.locator('#stage').getAttribute('data-position'));
  await page.waitForTimeout(250);assert.equal(Number(await page.locator('#stage').getAttribute('data-position')),frozen);
  assert.deepEqual(errors,[]);await context.close();
});
