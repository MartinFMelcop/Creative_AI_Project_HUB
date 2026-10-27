import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';
import os from 'node:os';
import {spawn,execFileSync} from 'node:child_process';
import {createRequire} from 'node:module';
import {createHash} from 'node:crypto';
import {createServer} from 'node:net';
import {fileURLToPath} from 'node:url';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const output=process.argv[2]&&path.resolve(process.argv[2]);
if(!output||output===root||output.startsWith(root+path.sep))throw Error('New external output required');
const require=createRequire(path.join(root,'projects/realtime-integration-lab/package.json'));
const {chromium}=require('playwright-core');
const digest=b=>createHash('sha256').update(b).digest('hex');
const archive='delivery/authored-scene/dist/authored-scene-demo-linux-x64.zip';
const protocol=JSON.parse(await fs.readFile(path.join(root,'evidence/portfolio/protocol.json')));
const guarded=[archive,'showcase/capture.mjs','evidence/portfolio/protocol.json','projects/realtime-integration-lab/package.json','projects/realtime-integration-lab/package-lock.json'];
async function identities(){return Object.fromEntries(await Promise.all(guarded.map(async n=>[n,digest(await fs.readFile(path.join(root,n)))])));}
const before=await identities();assert.equal(before[archive],protocol.baseline.recipient_sha256);assert.equal((await fs.stat(path.join(root,archive))).size,protocol.baseline.recipient_bytes);
await fs.mkdir(output,{recursive:false});
const scratch=await fs.mkdtemp(path.join(os.tmpdir(),'portfolio-recipient-')),hosts=[],trials=[],errors=[];
let browser,complete=false;
async function start(id){
 const folder=path.join(scratch,id);await fs.mkdir(folder);
 execFileSync('python3',['-c',`import zipfile,pathlib,sys,os
with zipfile.ZipFile(sys.argv[1]) as z:
 for i in z.infolist():
  p=pathlib.PurePosixPath(i.filename)
  if p.is_absolute() or '..' in p.parts:raise ValueError('Unsafe member')
  z.extract(i,sys.argv[2])
  if not i.is_dir():os.chmod(pathlib.Path(sys.argv[2])/i.filename,(i.external_attr>>16)&0o777)
`,path.join(root,archive),folder]);
 const reserve=createServer();await new Promise(r=>reserve.listen(0,'127.0.0.1',r));const port=reserve.address().port;await new Promise(r=>reserve.close(r));
 const bundle=path.join(folder,'AuthoredSceneDemo'),command=['sh',path.join(bundle,'run-demo.sh'),String(port),'150'];
 const child=spawn(command[0],command.slice(1),{cwd:folder,env:{...process.env,NORTH_STAR_SAVE_DIR:path.join(folder,'Saves')},stdio:['ignore','pipe','pipe']});
 const log={id,command,stdout:'',stderr:''};hosts.push({child,log});child.stdout.on('data',b=>log.stdout+=b);child.stderr.on('data',b=>log.stderr+=b);
 for(let i=0;i<250&&!log.stdout.includes('READY');i++){if(child.exitCode!==null)throw Error(JSON.stringify(log));await new Promise(r=>setTimeout(r,25));}
 assert.match(log.stdout,/READY/);return {url:`http://127.0.0.1:${port}/`,folder,bundle};
}
async function stop(child){if(child.exitCode!==null||child.signalCode!==null)return;child.kill('SIGTERM');await Promise.race([new Promise(r=>child.once('exit',r)),new Promise(r=>setTimeout(r,1500))]);if(child.exitCode===null&&child.signalCode===null){child.kill('SIGKILL');await new Promise(r=>child.once('exit',r));}}
try{
 browser=await chromium.launch({executablePath:process.env.CHROMIUM_PATH||'/usr/bin/chromium',headless:true,args:['--no-sandbox']});
 const browserVersion=browser.version();
 for(const id of ['guided','refusal']){
  const host=await start(id);const videoDir=path.join(output,id+'-raw');await fs.mkdir(videoDir);
  const context=await browser.newContext({viewport:{width:1280,height:1120},recordVideo:{dir:videoDir,size:{width:1280,height:1120}}});const page=await context.newPage();page.on('pageerror',e=>errors.push(e.message));
  const started=performance.now(),trial={id,trace:[],fresh_save:true,preexisting_save:false};trials.push(trial);
  await page.goto(host.url);await page.waitForFunction(()=>window.authoredScene?.snapshot()?.state);
  async function observe(command){const actual=await(await fetch(host.url+'state')).json();assert.deepEqual(await page.evaluate(()=>window.authoredScene.snapshot()),actual);assert.equal(await page.locator('body').getAttribute('data-delivered'),String(actual.state.delivered));assert.equal(await page.locator('body').getAttribute('data-returned'),String(actual.state.returned));assert.equal(parseInt(await page.locator('#crates').textContent(),10),actual.state.crates);trial.trace.push({elapsed_ms:Math.round(performance.now()-started),command,observation:actual});return actual;}
  trial.initial=await observe('initial');assert.equal(trial.initial.state.crates,0);assert.equal(trial.initial.state.remaining,4);
  await page.waitForTimeout(2000);
  async function act(command){const prior=await page.evaluate(()=>window.authoredScene.snapshot());const button=page.locator(`[data-command=${JSON.stringify(command)}]`);await button.scrollIntoViewIfNeeded();await page.waitForTimeout(500);const reply=page.waitForResponse(r=>r.url()===host.url+'command'&&r.request().method()==='POST');await button.click();const received=await(await reply).json();await page.waitForFunction(o=>JSON.stringify(window.authoredScene.snapshot())===JSON.stringify(o),received);const o=await observe(command);await page.waitForTimeout(1400);return o;}
  const survey=['survey','skill','skill','walk','skill'];
  if(id==='guided'){
   for(const cmd of [...survey,'open','hear','offer','terms dusk','confirm'])assert.equal((await act(cmd)).accepted,true);
   const prepared=trial.trace.at(-1).observation.state;assert.equal(prepared.capacity,1);assert.equal(prepared.guide_location,'local-preparing');assert.equal(prepared.delivered,false);
   await page.locator('.stage').scrollIntoViewIfNeeded();await page.waitForTimeout(2000);
   assert.equal((await act('depart guided')).state.remaining,1);
   for(const cmd of ['skill','skill','walk','skill','walk','skill'])assert.equal((await act(cmd)).accepted,true);
   trial.final=await act('work');const s=trial.final.state;assert.equal(s.returned,true);assert.equal(s.delivered,true);assert.equal(s.crates,2);assert.equal(s.remaining,0);assert.equal(s.guide_location,'local');
   await page.locator('.stage').scrollIntoViewIfNeeded();await page.waitForTimeout(2500);await page.locator('.stage').screenshot({path:path.join(output,'poster.png')});
  }else{
   await act('open');trial.refused=await act('hear');assert.equal(trial.refused.accepted,false);assert.equal(trial.refused.state.guide_available,true);
   for(const cmd of ['decline','work','work','work'])await act(cmd);
   trial.final=trial.trace.at(-1).observation;const s=trial.final.state;assert.equal(s.crates,5);assert.equal(s.delivered,false);assert.equal(s.returned,false);assert.equal(s.guide_available,true);
   await page.locator('.stage').scrollIntoViewIfNeeded();await page.waitForTimeout(2500);await page.locator('.stage').screenshot({path:path.join(output,'choices.png')});
  }
  trial.journal=JSON.parse(await fs.readFile(path.join(host.folder,'Saves/scene.json')));
  const video=page.video();await context.close();const videoPath=path.join(output,id==='guided'?'walkthrough.webm':'refusal.webm');await video.saveAs(videoPath);trial.video=path.basename(videoPath);trial.video_sha256=digest(await fs.readFile(videoPath));
  trial.probe=JSON.parse(execFileSync('ffprobe',['-v','error','-show_streams','-show_format','-of','json',videoPath],{encoding:'utf8'}));assert.equal(trial.probe.streams.length,1);assert.equal(trial.probe.streams[0].codec_type,'video');
  await fs.rm(videoDir,{recursive:true});await stop(hosts.at(-1).child);
 }
 assert.equal(errors.length,0);assert.deepEqual(await identities(),before);complete=true;
 await fs.writeFile(path.join(output,'capture.json'),JSON.stringify({schema_version:1,kind:'actual_continuous_recipient_capture',baseline_commit:'c808d57cb7b09c3947e48b93cb0047ee1c4d6e55',source_sha256:before,source_stable:true,runtime:{node:process.version,chromium:browserVersion,playwright:require('playwright-core/package.json').version,os:os.platform(),architecture:os.arch(),ffmpeg:execFileSync('ffmpeg',['-version'],{encoding:'utf8'}).split('\n')[0],capture_encoder:'System FFmpeg selected through an explicit task-local Playwright executable adapter; not the unavailable Playwright-downloaded build.'},viewport:[1280,1120],trials,errors,limits:'Automated Linux private-runtime recipient execution. Known source action policy and read-only API observations; no blind/human play, Unity, Windows, Steam, ordinary-user/device, balance, enjoyment or commercial approval. Each video is one continuous browser recording, silent and unedited; poster/choices are direct stage screenshots. Two fresh local trials, not participants or independent studies.'},null,2)+'\n');
 console.log('PASS: continuous actual guided recipient and separately identified refusal recordings');
}catch(e){await fs.writeFile(path.join(output,'failure.json'),JSON.stringify({complete,error:{name:e.name,message:e.message,stack:e.stack},trials},null,2)+'\n');throw e;}
finally{for(const {child}of hosts)await stop(child);await browser?.close();await fs.writeFile(path.join(output,'hosts.json'),JSON.stringify({complete,hosts:hosts.map(({child,log})=>({...log,exit_code:child.exitCode,signal:child.signalCode}))},null,2)+'\n');await fs.rm(scratch,{recursive:true});}
