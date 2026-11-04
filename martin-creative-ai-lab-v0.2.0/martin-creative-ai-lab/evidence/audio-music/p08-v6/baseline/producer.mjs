import fs from 'node:fs/promises';
import {createRequire} from 'node:module';
import {spawn} from 'node:child_process';
import {createServer} from 'node:net';
const root='/workspace/Creative_AI_Project_HUB/martin-creative-ai-lab-v0.2.0/martin-creative-ai-lab';
const scratch='/workspace/work/p08-v6/engineering';
const require=createRequire(root+'/projects/realtime-integration-lab/package.json');
const {chromium}=require('playwright-core');
const reserve=createServer();await new Promise(r=>reserve.listen(0,'127.0.0.1',r));const port=reserve.address().port;await new Promise(r=>reserve.close(r));
const child=spawn('/workspace/work/authored-scene/dotnet/dotnet',[scratch+'/baseline-artifacts/bin/NorthStar.Presentation/release/NorthStar.Presentation.dll','--serve',String(port),root+'/north-star/csharp/Presentation/web','--seconds','90'],{cwd:root});let log='';child.stdout.on('data',x=>log+=x);child.stderr.on('data',x=>log+=x);
let browser;
try{
 for(let n=0;n<100&&!log.includes('READY');n++)await new Promise(r=>setTimeout(r,40));if(!log.includes('READY'))throw Error(log);
 browser=await chromium.launch({executablePath:'/usr/bin/chromium',headless:true});const page=await browser.newPage();
 await page.addInitScript(()=>{window.sourceLedger=[];const create=AudioContext.prototype.createBufferSource;let id=0;AudioContext.prototype.createBufferSource=function(...a){const s=create.apply(this,a),n=++id,start=s.start.bind(s),stop=s.stop.bind(s);s.start=(...args)=>{window.sourceLedger.push({event:'source-start',id:n,time:this.currentTime,duration:s.buffer?.duration,sequence:window.currentObservation?.sequence,cues:window.currentObservation?.audio?.cues});return start(...args);};s.stop=(...args)=>{window.sourceLedger.push({event:'source-stop',id:n,time:this.currentTime,duration:s.buffer?.duration,sequence:window.currentObservation?.sequence,cues:window.currentObservation?.audio?.cues});return stop(...args);};return s;};});
 await page.goto('http://127.0.0.1:'+port);await page.waitForFunction(()=>document.body.dataset.connected==='true');await page.click('#audio-enable');await page.waitForFunction(()=>window.crossingAudio.snapshot().enabled&&!window.crossingAudio.snapshot().loading);
 const result=await page.evaluate(async()=>{
  const a=window.crossingAudio,c=a.context,p=c.createScriptProcessor(1024,1,1),zero=c.createGain(),samples=[];zero.gain.value=0;a.output.connect(p);p.connect(zero).connect(c.destination);p.onaudioprocess=e=>samples.push(...e.inputBuffer.getChannelData(0));
  const events=[];async function send(command){const r=await fetch('/command',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(command)});if(!r.ok)throw Error('HTTP '+r.status);const s=await r.json();events.push(s);window.currentObservation=s;a.observe(s);return s;}
  await send({op:'restart'});await send({op:'prepare',approach:'anchor',outfit:'plate'});await send({op:'begin'});for(const action of ['skill','walk','dash','skill'])await send({op:'action',action});
  const won=events.at(-1);if(!won.won||won.audio.cues.join(',')!=='won')throw Error('Actual survey did not win');
  await send({op:'begin'});await send({op:'action',action:'walk'});await new Promise(r=>setTimeout(r,850));p.onaudioprocess=null;a.output.disconnect(p);p.disconnect();zero.disconnect();
  const terminal=window.sourceLedger.find(x=>x.event==='source-start'&&x.sequence===won.sequence&&x.duration===.6);const stopped=window.sourceLedger.find(x=>x.event==='source-stop'&&x.id===terminal.id);const age=stopped?stopped.time-terminal.time:null;
  return {schema_version:1,kind:'unchanged_fifo_actual_csharp_browser_baseline',events,ledger:window.sourceLedger,snapshot:a.snapshot(),terminal:{id:terminal.id,sequence:won.sequence,duration:terminal.duration,started:terminal.time,stopped:stopped?.time,age,cut_by_lower_priority:age!==null&&age<terminal.duration},sample_rate:c.sampleRate,samples};
 });
 const samples=result.samples;delete result.samples;result.pcm={frames:samples.length,peak:samples.reduce((m,x)=>Math.max(m,Math.abs(x)),0),rms:Math.sqrt(samples.reduce((s,x)=>s+x*x,0)/samples.length)};const wav=Buffer.alloc(44+samples.length*2);wav.write('RIFF');wav.writeUInt32LE(wav.length-8,4);wav.write('WAVEfmt ',8);wav.writeUInt32LE(16,16);wav.writeUInt16LE(1,20);wav.writeUInt16LE(1,22);wav.writeUInt32LE(result.sample_rate,24);wav.writeUInt32LE(result.sample_rate*2,28);wav.writeUInt16LE(2,32);wav.writeUInt16LE(16,34);wav.write('data',36);wav.writeUInt32LE(samples.length*2,40);for(let n=0;n<samples.length;n++)wav.writeInt16LE(Math.round(samples[n]*32767),44+n*2);
 await fs.writeFile(scratch+'/baseline.json',JSON.stringify(result,null,2)+'\n');await fs.writeFile(scratch+'/baseline.wav',wav);if(!result.terminal.cut_by_lower_priority)throw Error('Baseline expected terminal cut not demonstrated');console.log(JSON.stringify({terminal:result.terminal,pcm:result.pcm}));
}finally{await browser?.close();child.kill('SIGTERM');await fs.writeFile(scratch+'/baseline-host.log',log);}
