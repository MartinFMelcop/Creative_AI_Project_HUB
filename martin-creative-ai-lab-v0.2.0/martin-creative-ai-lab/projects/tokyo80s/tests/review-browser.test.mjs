import test, {before, after} from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';
import {createRequire} from 'node:module';
import {createServer} from '../server.mjs';

const require=createRequire(new URL('../../realtime-integration-lab/package.json',import.meta.url));
const {chromium}=require('playwright-core');
const baselineRoot=process.env.RHYTHM_REVIEW_BASELINE_ROOT;
const sourceTrack=JSON.parse(await fs.readFile(new URL('../dist/track.json',import.meta.url),'utf8'));
let server,browser,url;
const contexts=[];

before(async()=>{
  server=createServer();await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
  url=`http://127.0.0.1:${server.address().port}`;
  browser=await chromium.launch({executablePath:process.env.CHROMIUM_PATH||'/usr/bin/chromium',headless:true});
});
after(async()=>{
  for(const context of contexts)await context.close();
  await browser?.close();await new Promise(resolve=>server?.close(resolve));
});

const mode=(page,value,timeout=30000)=>page.waitForFunction(value=>document.querySelector('#stage').dataset.mode===value,value,{timeout});
const at=(page,time)=>page.waitForFunction(time=>Number(document.querySelector('#stage').dataset.position)>=time,time,{polling:'raf'});
const position=page=>page.locator('#stage').getAttribute('data-position').then(Number);

// Declared controlled four-bar charts exercise diagnosis and input routing. The
// original 120 BPM, duration, media URL and real delivered OGGs are retained. This
// is browser execution over actual audio, not an unmodified-chart/human playtest.
const diagnosisNotes=[
  {id:100,time:3.4,lane:0},{id:101,time:3.8,lane:1},
  {id:102,time:4.2,lane:0},{id:103,time:4.6,lane:1},
  {id:104,time:5.2,lane:2,duration:.6},
  {id:105,time:6.2,lane:3,duration:.7},
  {id:106,time:7.6,lane:2,duration:.7}
];
const focusNotes=[...Array.from({length:4},(_,group)=>
  Array.from({length:4},(_,lane)=>({id:200+group*4+lane,time:3.4+group*.6,lane}))).flat(),
  {id:220,time:6.2,lane:1,duration:1.4}
];

async function fixture(notes,{viewport={width:1280,height:900},musicEnd=11}={}) {
  const context=await browser.newContext({acceptDownloads:true,viewport});contexts.push(context);
  const page=await context.newPage(),errors=[];
  page.on('pageerror',error=>errors.push(error.message));
  const track={...sourceTrack,musicEnd,charts:{practice:notes,arcade:notes}};
  await page.route('**/track.json',route=>route.fulfill({contentType:'application/json',body:JSON.stringify(track)}));
  if(baselineRoot)for(const name of ['index.html','style.css','app.js','core.js','rehearsal.js']) {
    const type=name.endsWith('.html')?'text/html':name.endsWith('.css')?'text/css':'text/javascript';
    await page.route(name==='index.html'?`${url}/`:`**/${name}`,async route=>route.fulfill({contentType:type,body:await fs.readFile(path.join(baselineRoot,name))}));
  }
  await page.addInitScript(()=>{
    const Original=window.AudioContext;window.reviewAudioStarts=[];
    window.AudioContext=class extends Original {
      createBufferSource(){
        const node=super.createBufferSource(),start=node.start.bind(node);
        node.start=(...args)=>{window.reviewAudioStarts.push({args,rate:node.playbackRate.value,bufferDuration:node.buffer.duration});return start(...args);};
        return node;
      }
    };
  });
  await page.goto(url);await page.locator('#start:not([disabled])').waitFor();
  if(baselineRoot)assert.equal(await page.locator('#take-review').count(),0,'baseline must render its original HTML');
  await page.locator('#phrase').selectOption('0');
  return {context,page,errors,track};
}

async function exported(page) {
  const pending=page.waitForEvent('download');await page.locator('#export').click();
  const download=await pending;
  return {name:download.suggestedFilename(),data:JSON.parse(await fs.readFile(await download.path(),'utf8'))};
}

async function diagnosticTake(page,track,{mixed=false,missedHead=false}={}) {
  return page.evaluate(async({track,mixed,missedHead})=>{
    const rate=Number(document.querySelector('#rate').value),cue=Math.max(0,track.leadIn-240/track.bpm);
    const offsets=mixed?[-.085,.085,.085,-.085]:[0,0,0,0];
    const events=track.charts.practice.flatMap((note,index)=>{
      if(note.id===104&&missedHead)return [];
      const head=(note.time-cue)/rate+(offsets[index]||0);
      const release=note.id===104?head+.2:note.duration?(note.time-cue+note.duration)/rate+.02:head+.02;
      return [{time:head,lane:note.lane,down:true},{time:release,lane:note.lane,down:false}];
    }).sort((a,b)=>a.time-b.time||Number(a.down)-Number(b.down));
    let index=0;
    // RAF schedules declared synthetic judgments against the actual audio clock;
    // events target the real active element. Focus routing has a separate real
    // Playwright keyboard journey below, rather than dispatching on document.
    await new Promise(resolve=>{
      const tick=()=>{
        const stage=document.querySelector('#stage');
        if(stage.dataset.mode==='results'){resolve();return;}
        if(stage.dataset.mode==='playing')while(index<events.length&&events[index].time<=Number(stage.dataset.position)) {
          const event=events[index++],target=document.activeElement;
          target.dispatchEvent(new KeyboardEvent(event.down?'keydown':'keyup',{code:['KeyD','KeyF','KeyJ','KeyK'][event.lane],bubbles:true,cancelable:true}));
        }
        requestAnimationFrame(tick);
      };tick();
    });
    return {scheduledEvents:events.length,deliveredEvents:index,fixture:'controlled-four-bar-diagnostic-chart'};
  },{track,mixed,missedHead});
}

function reviewExport(data,{mixed,missedHead}) {
  assert.equal(data.version,'0.5.0');assert.equal(data.mode,'rehearsal');
  assert.equal(data.timeUnit,'performance-seconds');assert.equal(data.playbackRate,.75);
  assert.equal(data.backing.pitch,'original');assert.equal(data.backing.playbackRate,1);
  assert.equal(data.phrases.length,1);assert.equal(data.phrases[0].id,'0');
  assert.deepEqual(data.phrases[0].review,data.review);
  assert.equal(data.review.noteCount,7);assert.equal(data.review.receivedHeads,missedHead?6:7);
  assert.equal(data.review.missedHeads,missedHead?1:0);
  assert.deepEqual(data.review.holds,{total:3,carried:2,missedHead:missedHead?1:0,
    earlyRelease:missedHead?0:1,regrabTimeout:0,unheldAtFinish:0,unknown:0});
  for(const lane of data.review.lanes.slice(0,2)) {
    assert.equal(lane.receivedHeads,2);assert.equal(lane.missedHeads,0);
    assert.equal(lane.early,mixed?1:0);assert.equal(lane.late,mixed?1:0);
    assert.equal(lane.withinPerfect,mixed?0:2);
    assert.ok(Math.abs(lane.meanHeadErrorMs)<30,'opposite head errors should cancel in signed mean');
    assert.ok(mixed?lane.meanAbsoluteHeadErrorMs>65&&lane.meanAbsoluteHeadErrorMs<110:lane.meanAbsoluteHeadErrorMs<30,
      'mean absolute distance must expose spread despite a near-zero signed mean');
  }
  const hold=data.notes.find(note=>note.id===104);
  assert.equal(hold.state,'miss');assert.equal(hold.failureReason,missedHead?'missed-head':'early-release');
  assert.ok(Number.isFinite(hold.failureTime)&&hold.failureTime>hold.time);
  assert.equal(hold.errorMs===null,missedHead);
  for(const note of data.notes.filter(note=>note.state!=='miss')) {
    assert.equal(note.failureReason,null);assert.equal(note.failureTime,null);
  }
}

async function visibleReview(page,data) {
  assert.equal(await page.locator('#take-review').isVisible(),true);
  assert.equal(await page.locator('#lane-review article[data-review-lane]').count(),4);
  const summary=await page.locator('#head-review-summary').textContent();
  assert.ok(summary.includes(`${data.review.receivedHeads}/${data.review.noteCount} heads hit`));
  assert.ok(summary.includes(`missed: ${data.review.missedHeads}`));
  for(const lane of data.review.lanes) {
    const text=await page.locator(`#lane-review article[data-review-lane="${lane.lane}"]`).textContent();
    if(!lane.noteCount){assert.match(text,/No notes in this passage/);continue;}
    assert.ok(text.includes(`${lane.receivedHeads}/${lane.noteCount} heads hit`));
    assert.ok(text.includes(`${lane.missedHeads} missed`));
    assert.ok(text.includes(`${lane.early} early`));
    assert.ok(text.includes(`${lane.withinPerfect} within ±45 ms`));
    assert.ok(text.includes(`${lane.late} late`));
    if(lane.receivedHeads) {
      assert.ok(text.includes(`Average offset ${lane.meanHeadErrorMs>0?'+':''}${lane.meanHeadErrorMs.toFixed(1)} ms`));
      assert.ok(text.includes(`average distance ${lane.meanAbsoluteHeadErrorMs.toFixed(1)} ms`));
    } else assert.match(text,/No heads hit/);
  }
  const holds=await page.locator('#hold-review').textContent();
  assert.ok(holds.includes(`${data.review.holds.carried}/${data.review.holds.total} carried`));
  for(const [key,label] of [['missedHead','missed head'],['earlyRelease','released early'],
    ['regrabTimeout','not re-held after pause'],['unheldAtFinish','unheld when the take ended']]) {
    if(data.review.holds[key])assert.ok(holds.includes(`${data.review.holds[key]} ${label}`));
  }
}

test('two real-audio phrase takes separate cancelling head errors from missed heads and broken tails; review exports and rehearses',{timeout:60000},async()=>{
  const {context,page,errors,track}=await fixture(diagnosisNotes);
  try {
    await page.locator('#rate').selectOption('0.75');
    await page.evaluate(()=>localStorage.setItem('tokyo80s-best-v1-practice','54321'));
    await page.locator('#start').click();await mode(page,'playing');
    const firstSchedule=await diagnosticTake(page,track,{mixed:true,missedHead:true});
    assert.equal(firstSchedule.deliveredEvents,firstSchedule.scheduledEvents);
    const first=await exported(page),firstTiming=await page.locator('#timing-result').textContent();
    if(baselineRoot) {
      assert.equal(first.data.version,'0.4.0');assert.equal(first.data.review,undefined);
      assert.match(firstTiming,/close to the beat/);
      if(process.env.RHYTHM_SCREENSHOT_DIR)await page.locator('#results').screenshot({path:path.join(process.env.RHYTHM_SCREENSHOT_DIR,'take-review-baseline-results.png')});
    } else {
      reviewExport(first.data,{mixed:true,missedHead:true});await visibleReview(page,first.data);
      if(process.env.RHYTHM_SCREENSHOT_DIR) {
        await page.screenshot({path:path.join(process.env.RHYTHM_SCREENSHOT_DIR,'take-review-mixed.png'),fullPage:true});
        await page.locator('#take-review').screenshot({path:path.join(process.env.RHYTHM_SCREENSHOT_DIR,'take-review-mixed-section.png')});
      }
    }
    await page.locator('#replay').click();await mode(page,'playing');
    const secondSchedule=await diagnosticTake(page,track);
    assert.equal(secondSchedule.deliveredEvents,secondSchedule.scheduledEvents);
    const second=await exported(page),secondTiming=await page.locator('#timing-result').textContent();
    assert.equal(first.data.counts.miss,1);assert.equal(second.data.counts.miss,1);
    assert.equal(first.data.phrases[0].lostHolds,1);assert.equal(second.data.phrases[0].lostHolds,1);
    assert.equal(await page.evaluate(()=>localStorage.getItem('tokyo80s-best-v1-practice')),'54321');
    const audio=await page.evaluate(()=>reviewAudioStarts);
    assert.equal(audio.length,2);assert.ok(audio.every(source=>source.rate===1&&Math.abs(source.bufferDuration-69/.75)<.1));
    assert.ok(audio.every(source=>Math.abs(source.args[1]-1/.75)<1e-8));
    if(baselineRoot) {
      assert.match(secondTiming,/close to the beat/);assert.equal(second.data.review,undefined);
    } else {
      reviewExport(second.data,{mixed:false,missedHead:false});await visibleReview(page,second.data);
      assert.equal(await page.locator('#review-phrase').inputValue(),'take');
      assert.equal(await page.locator('#review-phrase').isDisabled(),true);
      assert.equal(await page.locator('#review-rehearse').isVisible(),false);
      await page.setViewportSize({width:390,height:844});
      assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
      assert.equal(await page.locator('#stage').getAttribute('data-mode'),'results');
      assert.equal(await page.evaluate(()=>reviewAudioStarts.length),2);
      if(process.env.RHYTHM_SCREENSHOT_DIR) {
        await page.screenshot({path:path.join(process.env.RHYTHM_SCREENSHOT_DIR,'take-review-narrow.png'),fullPage:true});
        await page.locator('#take-review').screenshot({path:path.join(process.env.RHYTHM_SCREENSHOT_DIR,'take-review-narrow-section.png')});
      }
      await page.locator('#phrase-results button[data-phrase="0"]').click();await mode(page,'playing');
      assert.equal(await page.locator('#phrase').inputValue(),'0');
      assert.equal(await page.locator('#stage').getAttribute('data-session'),'rehearsal');
      assert.equal(await page.locator('#rate').inputValue(),'0.75');
      assert.equal(await page.evaluate(()=>reviewAudioStarts.length),3);
      await page.locator('#full-run').click();await mode(page,'ready');
    }
    if(process.env.RHYTHM_SCREENSHOT_DIR)await fs.writeFile(path.join(process.env.RHYTHM_SCREENSHOT_DIR,baselineRoot?'take-review-baseline.json':'take-review-attempts.json'),
      JSON.stringify({fixture:'controlled four-bar notes; unchanged delivered audio',firstSchedule,secondSchedule,firstTiming,secondTiming,audio,first,second},null,2)+'\n');
    assert.deepEqual(errors,[]);
  } finally {await context.close();}
});

test('actual 69-second full backing completes; keyboard passage review stays silent and rehearses the selected passage',{timeout:100000},async()=>{
  const notes=diagnosisNotes.map(note=>note.id>=104?{...note,time:note.time+6}:note);
  const {context,page,errors}=await fixture(notes,{musicEnd:19});
  try {
    await page.locator('#phrase').selectOption('full');
    await page.locator('#start').click();await mode(page,'playing');
    await mode(page,'results',85000);
    const result=await exported(page);
    assert.equal(result.data.mode,'full');assert.equal(result.data.counts.miss,7);
    assert.equal(result.data.phrases.length,2);
    assert.equal(result.data.phrases.reduce((total,phrase)=>total+phrase.notes,0),7);
    const audio=await page.evaluate(()=>reviewAudioStarts);
    assert.equal(audio.length,1);assert.equal(audio[0].rate,1);
    assert.ok(Math.abs(audio[0].bufferDuration-69)<.05);assert.equal(audio[0].args[1],0);assert.equal(audio[0].args[2],69);
    if(baselineRoot) {
      assert.equal(result.data.review,undefined);
      assert.equal(await page.locator('#phrase-results button').count(),2);
    } else {
      assert.equal(result.data.version,'0.5.0');await visibleReview(page,result.data);
      assert.equal(await page.locator('#review-phrase').isEnabled(),true);
      assert.equal(await page.locator('#review-rehearse').isVisible(),false);
      const score=await page.locator('#score').textContent();
      await page.locator('#review-phrase').focus();await page.keyboard.press('End');
      assert.equal(await page.locator('#review-phrase').inputValue(),'1');
      assert.equal(await page.locator('#review-rehearse').isVisible(),true);
      const phrase=result.data.phrases.find(phrase=>phrase.id==='1');
      assert.equal(phrase.review.noteCount,3);await visibleReview(page,{review:phrase.review});
      assert.equal(await page.locator('#score').textContent(),score);
      assert.equal(await page.locator('#stage').getAttribute('data-mode'),'results');
      assert.equal(await page.evaluate(()=>reviewAudioStarts.length),1);
      assert.deepEqual((await exported(page)).data,result.data,'inspection must not change the saved take');
      await page.locator('#review-phrase').focus();await page.keyboard.press('Home');
      assert.equal(await page.locator('#review-rehearse').isVisible(),false);
      await visibleReview(page,result.data);await page.keyboard.press('End');
      if(process.env.RHYTHM_SCREENSHOT_DIR) {
        await page.screenshot({path:path.join(process.env.RHYTHM_SCREENSHOT_DIR,'take-review-full-passage.png'),fullPage:true});
        await page.locator('#take-review').screenshot({path:path.join(process.env.RHYTHM_SCREENSHOT_DIR,'take-review-full-section.png')});
      }
      await page.locator('#review-rehearse').click();await mode(page,'playing');
      assert.equal(await page.locator('#phrase').inputValue(),'1');
      assert.equal(await page.locator('#stage').getAttribute('data-session'),'rehearsal');
      assert.equal(await page.evaluate(()=>reviewAudioStarts.length),2);
      assert.equal((await page.evaluate(()=>reviewAudioStarts.at(-1))).args[1],9);
      await page.locator('#full-run').click();await mode(page,'ready');
    }
    if(process.env.RHYTHM_SCREENSHOT_DIR)await fs.writeFile(path.join(process.env.RHYTHM_SCREENSHOT_DIR,baselineRoot?'take-review-full-baseline.json':'take-review-full.json'),
      JSON.stringify({fixture:'controlled two-passage notes; unchanged complete 69-second audio',audio,result},null,2)+'\n');
    assert.deepEqual(errors,[]);
  } finally {await context.close();}
});

test('real keyboard stays playable on focused volume, preserves native arrows, pauses and records missed regrab',{timeout:45000},async()=>{
  const {context,page,errors}=await fixture(focusNotes);
  try {
    await page.locator('#rate').selectOption('1');await page.locator('#start').click();await mode(page,'playing');
    const volume=page.locator('#volume');await volume.focus();
    assert.equal(await page.evaluate(()=>document.activeElement.id),'volume');
    const initialVolume=Number(await volume.inputValue());await page.keyboard.press('ArrowRight');
    assert.equal(Number(await volume.inputValue()),initialVolume+1);
    assert.equal(Number(await page.locator('#score').textContent()),0);
    for(let group=0;group<4;group++) {
      await at(page,2.4+group*.6);
      for(const key of ['d','f','j','k'])await page.keyboard.press(key);
      assert.equal(await page.evaluate(()=>document.activeElement.id),'volume');
    }
    const score=Number(await page.locator('#score').textContent());
    if(baselineRoot) {
      assert.equal(score,0,'baseline swallows lane keys targeted at the focused volume');
      await page.keyboard.press('p');await page.waitForTimeout(100);
      assert.equal(await page.locator('#stage').getAttribute('data-mode'),'playing');
      assert.deepEqual(errors,[]);return;
    }
    assert.ok(score>=12000,'all four physical lane keys should score while the range retains focus');
    assert.equal(await page.locator('#aura').evaluate(element=>element.value),100);
    await page.keyboard.press('Space');assert.match(await page.locator('#shield').textContent(),/Pulse: 2/);
    assert.equal(await page.locator('#aura').evaluate(element=>element.value),0);
    assert.equal(await page.evaluate(()=>document.activeElement.id),'volume');
    await page.keyboard.press('p');await mode(page,'paused');
    const frozen=await position(page);await page.waitForTimeout(180);
    assert.ok(Math.abs(await position(page)-frozen)<.02);
    await page.keyboard.press('Escape');await mode(page,'playing');
    await at(page,5.2);await page.keyboard.down('f');
    await at(page,5.55);await page.keyboard.press('p');await mode(page,'paused');
    await page.keyboard.up('f');await page.keyboard.press('Escape');await mode(page,'playing');
    await mode(page,'results');
    const result=await exported(page),hold=result.data.notes.find(note=>note.id===220);
    assert.equal(hold.failureReason,'regrab-timeout');assert.equal(hold.state,'miss');
    assert.ok(hold.errorMs!==null&&Number.isFinite(hold.failureTime));
    assert.equal(result.data.review.holds.regrabTimeout,1);
    assert.equal(result.data.review.holds.missedHead,0);assert.equal(result.data.pulses,1);
    assert.equal(result.data.review.receivedHeads,17);assert.equal(result.data.review.missedHeads,0);
    if(process.env.RHYTHM_SCREENSHOT_DIR)await fs.writeFile(path.join(process.env.RHYTHM_SCREENSHOT_DIR,'take-review-focused-volume.json'),
      JSON.stringify({fixture:'controlled four-bar chord/hold notes; actual page.keyboard on focused range',initialVolume,score,result},null,2)+'\n');
    assert.deepEqual(errors,[]);
  } finally {await context.close();}
});
