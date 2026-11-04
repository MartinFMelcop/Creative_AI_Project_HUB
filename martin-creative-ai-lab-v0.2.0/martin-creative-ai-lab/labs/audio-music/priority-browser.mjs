import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import {spawn} from 'node:child_process';
import {createRequire} from 'node:module';
import {createServer} from 'node:net';
import {createHash} from 'node:crypto';
import path from 'node:path';
import {fileURLToPath} from 'node:url';

const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../..');
const executable=process.argv[2],out=path.resolve(process.argv[3]||root);
if(!executable||out===root||out.startsWith(root+path.sep))throw Error('Usage: node priority-browser.mjs DOTNET EXTERNAL_OUTPUT');
const require=createRequire(path.join(root,'projects/realtime-integration-lab/package.json'));
const {chromium}=require('playwright-core');
const sha=b=>createHash('sha256').update(b).digest('hex');
const wait=ms=>new Promise(resolve=>setTimeout(resolve,ms));
const checks=[],observations={},signals={},negatives=[],captures=[],errors=[];
let browser,child,log='';
await fs.mkdir(out,{recursive:true});

async function identities(){
 const result={};
 async function scan(relative){for(const entry of await fs.readdir(path.join(root,relative),{withFileTypes:true})){const name=path.join(relative,entry.name);if(entry.isDirectory()){if(!['bin','obj'].includes(entry.name))await scan(name);}else if(/\.(cs|csproj|js|html|json|mjs)$/.test(entry.name))result[name]=sha(await fs.readFile(path.join(root,name)));}}
 await scan('north-star/csharp/Audio');await scan('north-star/csharp/Presentation');
 for(const name of ['labs/audio-music/priority-browser.mjs','labs/audio-music/priority-protocol.json','projects/realtime-integration-lab/package-lock.json'])result[name]=sha(await fs.readFile(path.join(root,name)));
 return Object.fromEntries(Object.entries(result).sort(([a],[b])=>a.localeCompare(b)));
}
const before=await identities();
function check(name,condition){assert.ok(condition,name);checks.push(name);}
function stats(samples){return{frames:samples.length,peak:samples.reduce((p,v)=>Math.max(p,Math.abs(v)),0),rms:samples.length?Math.sqrt(samples.reduce((s,v)=>s+v*v,0)/samples.length):0};}
function clockWindow(take,start,end){const samples=[];for(const block of take.blocks)for(let i=0;i<block.frames;i++){const t=block.time+i/take.sample_rate;if(t>=start&&t<end)samples.push(take.samples[block.offset+i]);}return{start,end,...stats(samples)};}
function wav(samples,rate){const b=Buffer.alloc(44+samples.length*2);b.write('RIFF');b.writeUInt32LE(b.length-8,4);b.write('WAVEfmt ',8);b.writeUInt32LE(16,16);b.writeUInt16LE(1,20);b.writeUInt16LE(1,22);b.writeUInt32LE(rate,24);b.writeUInt32LE(rate*2,28);b.writeUInt16LE(2,32);b.writeUInt16LE(16,34);b.write('data',36);b.writeUInt32LE(samples.length*2,40);for(let n=0;n<samples.length;n++){assert.ok(Math.abs(samples[n])<1,'Nominal exported PCM must not clip');b.writeInt16LE(Math.round(samples[n]*32767),44+n*2);}return b;}
async function retain(name,take){await fs.writeFile(path.join(out,name+'.wav'),wav(take.samples,take.sample_rate));const record={name,sample_rate:take.sample_rate,...stats(take.samples),blocks:take.blocks,sha256:sha(await fs.readFile(path.join(out,name+'.wav')))};captures.push(record);return record;}

async function installCapture(page){
 await page.evaluate(()=>{window.priorityCapture=async(ms,stereo=false,delay=0)=>{
  const a=window.crossingAudio,c=a.context;if(c.state!=='running')throw Error('Capture requires the actual running context');
  const processor=c.createScriptProcessor(1024,stereo?2:1,stereo?2:1),zero=c.createGain(),channels=stereo?[[],[]]:[[]],blocks=[];
  zero.gain.value=0;let input=a.output,merger,delayed;const sources=a.transportOutputs;
  if(stereo){if(sources.length!==2)throw Error('Two real stem transports required');merger=c.createChannelMerger(2);sources[0].connect(merger,0,0);if(delay){delayed=c.createDelay(1);delayed.delayTime.value=delay;sources[1].connect(delayed).connect(merger,0,1);}else sources[1].connect(merger,0,1);input=merger;}
  input.connect(processor);processor.connect(zero).connect(c.destination);
  processor.onaudioprocess=e=>{blocks.push({time:e.playbackTime,read_time:c.currentTime,offset:channels[0].length,frames:e.inputBuffer.length});for(let n=0;n<channels.length;n++)channels[n].push(...e.inputBuffer.getChannelData(n));};
  await new Promise(resolve=>setTimeout(resolve,ms));processor.onaudioprocess=null;input.disconnect(processor);processor.disconnect();zero.disconnect();
  if(merger){sources[0].disconnect(merger);if(delayed){sources[1].disconnect(delayed);delayed.disconnect();}else sources[1].disconnect(merger);merger.disconnect();}
  const phase=stereo?[100,150].map(hz=>{const angle=x=>{let re=0,im=0;for(let n=0;n<x.length;n++){const t=2*Math.PI*hz*n/c.sampleRate;re+=x[n]*Math.cos(t);im+=x[n]*Math.sin(t);}return Math.atan2(im,re);};const d=angle(channels[0])-angle(channels[1]);return Math.atan2(Math.sin(d),Math.cos(d));}):[];
  return{sample_rate:c.sampleRate,blocks,phase,samples:channels[0],channel_stats:channels.map(x=>({frames:x.length,peak:x.reduce((p,v)=>Math.max(p,Math.abs(v)),0),rms:Math.sqrt(x.reduce((s,v)=>s+v*v,0)/x.length)}))};
 };});
}
async function startCapture(page,ms){await page.evaluate(ms=>{window.priorityPending=window.priorityCapture(ms);},ms);}
async function finishCapture(page){return page.evaluate(()=>window.priorityPending);}
async function state(page){return page.evaluate(()=>fetch('/state').then(r=>r.json()));}
async function audit(page){return page.evaluate(()=>window.crossingAudio.snapshot());}
async function command(page,payload){return page.evaluate(async payload=>{await command(payload);return fetch('/state').then(r=>r.json());},payload);}
async function prepare(page){await command(page,{op:'restart'});await command(page,{op:'prepare',approach:'anchor',outfit:'plate'});return command(page,{op:'begin'});}
async function enable(page){await page.click('#audio-enable');await page.waitForFunction(()=>{const a=window.crossingAudio.snapshot();return a.enabled&&!a.suspended&&!a.loading;});}
async function level(page,music,effects=.65){await page.evaluate(({music,effects})=>{for(const[id,value]of[['music-volume',music],['effects-volume',effects]]){const e=document.getElementById(id);e.value=String(value);e.dispatchEvent(new Event('input'));}},{music,effects});}

async function terminalTrial(page,label){
 await prepare(page);await level(page,0);for(const action of ['skill','walk','dash'])await command(page,{op:'action',action});
 await wait(420);await startCapture(page,1000);
 const actual=await page.evaluate(async()=>{const rows=[];for(const payload of [{op:'action',action:'skill'},{op:'begin'},{op:'action',action:'walk'}]){await command(payload);rows.push(await fetch('/state').then(r=>r.json()));}return{states:rows,audit:window.crossingAudio.snapshot()};});
 const take=await finishCapture(page),history=actual.audit.history,terminal=history.findLast(e=>e.event==='cue'&&e.name==='won'&&e.sequence===actual.states[0].sequence);
 assert.ok(terminal,'Actual accepted terminal cue must exist');
 const began=terminal.started??terminal.time;
 const later=history.filter(e=>e.event==='cue'&&e.sequence>terminal.sequence);
 const laterEnd=Math.max(began,...later.map(e=>e.ends??(e.time+(e.name==='pulse'?.36:.24))));
 const late=clockWindow(take,Math.max(began+.44,laterEnd+.075),began+.58);
 const stopped=history.filter(e=>e.event==='voice-stop'&&e.sequence===terminal.sequence&&e.name==='won');
 const alive=actual.audit.activeVoices?.some(v=>v.name==='won'&&v.sequence===terminal.sequence)??false;
 const overlap=actual.states.every(s=>s.accepted)&&later.length>=1&&later.every(e=>(e.started??e.time)-began<.15);
 const result={states:actual.states,audit:actual.audit,terminal,lower_cues:later,late_window:late,terminal_stops:stopped,terminal_alive_at_overlap:alive,commands_within_overlap:overlap,criterion:overlap&&late.frames>512&&late.rms>.001&&alive&&stopped.length===0};
 await retain(label,take);return result;
}

try{
 const reservation=createServer();await new Promise(r=>reservation.listen(0,'127.0.0.1',r));const port=reservation.address().port;await new Promise(r=>reservation.close(r));
 child=spawn(executable,[path.join(root,'north-star/csharp/Presentation/bin/Release/net10.0/NorthStar.Presentation.dll'),'--serve',String(port),path.join(root,'north-star/csharp/Presentation/web'),'--seconds','180'],{cwd:root,stdio:['ignore','pipe','pipe']});child.stdout.on('data',x=>log+=x);child.stderr.on('data',x=>log+=x);
 for(let n=0;n<160&&!log.includes('READY');n++){if(child.exitCode!==null)throw Error(log);await wait(50);}assert.match(log,/READY/);
 browser=await chromium.launch({executablePath:process.env.CHROMIUM_PATH||'/usr/bin/chromium',headless:true});
 const page=await browser.newPage({viewport:{width:1280,height:1100}}),url=`http://127.0.0.1:${port}/`;
 page.on('pageerror',e=>errors.push(e.message));await page.goto(url);await page.waitForFunction(()=>document.body.dataset.connected==='true');await installCapture(page);
 observations.beforeEnable=await prepare(page);check('Actual C# begin is accepted before optional audio enable',observations.beforeEnable.accepted&&!(await audit(page)).enabled);
 const past=observations.beforeEnable.sequence;await enable(page);check('Late enable consumes earlier cue without replay',!(await audit(page)).history.some(e=>e.event==='cue'&&e.sequence===past));
 const policy=observations.beforeEnable.audio.playback;
 check('Actual C# plan supplies bounded priority catalog and finite decisions',policy?.maxvoices===2&&policy.catalog.won.priority>policy.catalog.hurt.priority&&policy.catalog.hurt.priority>policy.catalog.bolt.priority&&policy.rules);
 const phase=await page.evaluate(()=>priorityCapture(700,true));signals.phase={phase:phase.phase,channel_stats:phase.channel_stats};check('Actual stem capture retains shared harmonic phase',phase.channel_stats.every(x=>x.frames>4096&&x.rms>.001)&&phase.phase.every(v=>Math.abs(v)<.06));
 const shifted=await page.evaluate(()=>priorityCapture(700,true,.037));signals.shifted={phase:shifted.phase,channel_stats:shifted.channel_stats};check('Actual 37 ms capture-path delay is detected',shifted.phase.some(v=>Math.abs(v)>.3));negatives.push({policy:'actual isolated 37ms delayed stem capture path',detected:true,phase:shifted.phase});

 observations.terminal=await terminalTrial(page,'terminal-overlap');
 check('Three actual accepted observations overlap terminal playback',observations.terminal.commands_within_overlap&&observations.terminal.states[0].won&&observations.terminal.states[1].active&&observations.terminal.states[2].active);
 check('Critical terminal survives later begin and contact in ownership and final PCM',observations.terminal.criterion);
 check('Music duck remains scheduled through the greatest live voice end',observations.terminal.audit.duck.until>=Math.max(...observations.terminal.audit.activeVoices.map(v=>v.ends))&&observations.terminal.audit.duck.until>=observations.terminal.terminal.ends);
 const decodedBudget=observations.terminal.audit.history.find(e=>e.event==='decoded-budget');
 check('Actual decoded conservative voice budget remains below the reserved ceiling',decodedBudget?.bound>0&&decodedBudget.bound<decodedBudget.ceiling&&observations.terminal.audit.headroom.decoded_bound<observations.terminal.audit.headroom.ceiling);
 check('Terminal overlap remains below nominal sample ceiling',captures.at(-1).peak<.9&&captures.at(-1).rms>.001);
 check('Later threat saturation is explicit during terminal plus contact',observations.terminal.audit.history.some(e=>e.event==='cue-suppressed'&&e.sequence===observations.terminal.states[2].sequence&&e.reason==='priority-saturation'));

 await prepare(page);await wait(420);await startCapture(page,650);
 observations.saturation=await page.evaluate(async()=>{const states=[],snapshots=[];for(let n=0;n<3;n++){await command({op:'action',action:'wait'});states.push(await fetch('/state').then(r=>r.json()));snapshots.push(window.crossingAudio.snapshot());}return{states,snapshots};});
 let take=await finishCapture(page);await retain('contact-saturation',take);const satur=observations.saturation,first=satur.states[0].sequence,third=satur.states[2].sequence,latest=satur.snapshots[2];
 check('Real contact and later threat cannot exceed two active voices',satur.states.every(s=>s.accepted)&&satur.snapshots.every(s=>s.voices<=2&&s.activeVoices.length<=2));
 check('New threat cannot cut the first actual contact',!latest.history.some(e=>e.event==='voice-stop'&&e.sequence===first&&e.name==='hurt'));
 check('Equal critical saturation explicitly suppresses incoming contact',latest.history.some(e=>e.event==='cue-suppressed'&&e.sequence===third&&e.name==='hurt'&&e.reason==='priority-saturation'));
 const beforeRead=await audit(page),same=await state(page);await page.evaluate(s=>{window.crossingAudio.observe(s);window.crossingAudio.observe(s);},same);const afterRead=await audit(page);
 check('Repeated GET and stale observations preserve cue identity',beforeRead.history.filter(e=>e.event==='cue').length===afterRead.history.filter(e=>e.event==='cue').length&&(await state(page)).sequence===same.sequence);
 await wait(450);check('Suppressed equal-priority contact never enters a later backlog',!(await audit(page)).history.some(e=>e.event==='cue'&&e.sequence===third&&e.name==='hurt'));

 await prepare(page);await page.check('#audio-mute');await wait(90);observations.muted=await command(page,{op:'action',action:'wait'});take=await page.evaluate(()=>priorityCapture(250));signals.muted=stats(take.samples);
 check('Actual mute is captured silence with consumed sequence',signals.muted.frames>4096&&signals.muted.peak<1e-7&&(await audit(page)).cursor===observations.muted.sequence&&(await audit(page)).voices===0);
 const mutedCount=(await audit(page)).history.filter(e=>e.event==='cue').length;await page.uncheck('#audio-mute');check('Unmute cannot replay consumed critical content',(await audit(page)).history.filter(e=>e.event==='cue').length===mutedCount);
 await page.evaluate(()=>window.dispatchEvent(new Event('blur')));await page.waitForFunction(()=>window.crossingAudio.context.state==='suspended');observations.suspended=await command(page,{op:'action',action:'wait'});let a=await audit(page);
 check('Suspension clears actual voices and transports while consuming observation',a.suspended&&a.voices===0&&a.stems===0&&a.cursor===observations.suspended.sequence);await enable(page);a=await audit(page);check('Explicit resume has no suspended-event playback',!a.history.some(e=>e.event==='cue'&&e.sequence===observations.suspended.sequence));
 await level(page,0,.8);await prepare(page);await wait(450);await page.evaluate(()=>window.crossingAudio.output.gain.setValueAtTime(12,window.crossingAudio.context.currentTime));await startCapture(page,450);await command(page,{op:'action',action:'wait'});take=await finishCapture(page);signals.overgain=stats(take.samples);check('Actual excess master gain fixture is detected',signals.overgain.frames>4096&&signals.overgain.peak>.9);negatives.push({policy:'actual master gain12 fixture',detected:true,...signals.overgain});await page.evaluate(()=>window.crossingAudio.output.gain.setValueAtTime(.8,window.crossingAudio.context.currentTime));

 await page.route('**/command',route=>route.abort());await command(page,{op:'action',action:'wait'});await page.waitForFunction(()=>document.body.dataset.connected==='false'&&window.crossingAudio.context.state==='suspended');a=await audit(page);check('Actual connection failure suspends and clears audio ownership',a.suspended&&a.voices===0&&a.stems===0);await page.unroute('**/command');await command(page,{op:'restart'});check('A later actual successful command reconnects without automatic audio resume',(await page.evaluate(()=>document.body.dataset.connected==='true'))&&(await audit(page)).suspended);
 await enable(page);check('Reconnect still requires explicit enable',(await audit(page)).enabled&&!(await audit(page)).suspended);

 const loading=await browser.newPage();await loading.route('**/audio/*.wav',async route=>{await wait(180);await route.continue();});await loading.goto(url);await loading.waitForFunction(()=>document.body.dataset.connected==='true');await loading.click('#audio-enable');await loading.waitForFunction(()=>window.crossingAudio.snapshot().loading);await loading.evaluate(()=>window.dispatchEvent(new Event('blur')));await wait(350);a=await audit(loading);check('Blur during async decode invalidates playback and leaves master silent',a.suspended&&!a.loading&&a.stems===0&&await loading.evaluate(()=>window.crossingAudio.output.gain.value===0));await loading.close();

 // Force FIFO on the actual adapter while keeping the C# owner and cue sources unchanged.
 const source=await fs.readFile(path.join(root,'north-star/csharp/Presentation/web/audio.js'),'utf8');
 const mutationTarget='const decision=policy.rules[state]?.[descriptor.priority-1];';
 assert.equal(source.split(mutationTarget).length,2,'Actual priority mutation target must resolve exactly once');
 const mutated=source.replace(mutationTarget,'const decision=voices.length>=policy.maxvoices?0:-2;');
 assert.notEqual(mutated,source,'The controlled priority mutation must change actual policy');
 const mutant=await browser.newPage();await mutant.route('**/audio.js',route=>route.fulfill({contentType:'text/javascript',body:mutated}));await mutant.goto(url);await mutant.waitForFunction(()=>document.body.dataset.connected==='true');await installCapture(mutant);await enable(mutant);observations.mutant=await terminalTrial(mutant,'critical-cut-mutant');
 check('Actual isolated critical-cut mutation fails the same terminal PCM criterion',!observations.mutant.criterion&&observations.mutant.states.every(s=>s.accepted)&&observations.mutant.terminal_stops.length>0&&observations.mutant.late_window.rms<.0001);
 negatives.push({policy:'isolated actual adapter critical admission mutation',source_sha256:sha(source),mutated_sha256:sha(mutated),detected:true,late_window:observations.mutant.late_window,terminal_stops:observations.mutant.terminal_stops});await mutant.close();
 check('No application browser exceptions',errors.length===0);
 const after=await identities();check('Actual source and producer identities stay stable through execution',JSON.stringify(before)===JSON.stringify(after));
 const result={schema:'north-star.actual-audio-priority-browser.v1',runtime:{node:process.version,chromium:browser.version()},identities:before,checks,observations,signals,negatives,captures,timing:{capture_block_frames:1024,clock:'ScriptProcessor event playbackTime labels input blocks; this is a browser signal-clock proxy, not hardware latency calibration.',terminal_window:'Start at least 440ms after terminal start and 75ms after every later short admitted effect end; stop before terminal start+580ms. The same clock/window must reject the actual forced-FIFO cut mutant.'},limits:'Actual C# loopback commands and final Chromium AudioContext PCM, with silent instrument capture branches. Sample observations are not certified true peak, human recognition, masking, preference, physical-device listening, Unity, Windows or Steam execution.'};
 await fs.writeFile(path.join(out,'priority-browser.json'),JSON.stringify(result,null,2)+'\n');console.log(`PASS ${checks.length} actual priority browser controls; ${negatives.length} detected controlled negatives`);
}catch(error){
 await fs.writeFile(path.join(out,'priority-failure.json'),JSON.stringify({error:error.stack,identities:before,checks,observations,signals,negatives,captures,errors},null,2)+'\n');throw error;
}finally{
 await browser?.close();if(child){child.kill();await new Promise(resolve=>{if(child.exitCode!==null)resolve();else child.once('exit',resolve);});}await fs.writeFile(path.join(out,'host.log'),log);
}
