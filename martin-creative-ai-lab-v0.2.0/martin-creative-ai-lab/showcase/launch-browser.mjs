import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';
import {spawn} from 'node:child_process';
import {createServer} from 'node:net';
import {createRequire} from 'node:module';
import {createHash} from 'node:crypto';
import {fileURLToPath} from 'node:url';

const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const [dotnet,rawOut]=process.argv.slice(2),out=rawOut&&path.resolve(rawOut);
if(!dotnet||!out||out===root||out.startsWith(root+path.sep))throw Error('Usage: node showcase/launch-browser.mjs DOTNET NEW_EXTERNAL_OUTPUT');
const require=createRequire(path.join(root,'projects/realtime-integration-lab/package.json')),{chromium}=require('playwright-core');
const sha=b=>createHash('sha256').update(b).digest('hex');
const controls=[],trials=[],errors=[];let browser;
const tracked=['tools/run_source_experiment.py','tools/check_portfolio.py','showcase/portfolio.json','showcase/launch-browser.mjs','showcase/launch-protocol.json','north-star/field-journey/Host/Program.cs','north-star/field-journey/Host/Room.cs','north-star/field-journey/web/app.js','north-star/combat-study/Host/Program.cs','north-star/combat-study/Host/Room.cs','north-star/combat-study/Host/web/app.js','projects/realtime-integration-lab/package-lock.json'];
async function hashes(){return Object.fromEntries(await Promise.all(tracked.map(async n=>[n,sha(await fs.readFile(path.join(root,n)))])));}
function check(id,condition){assert.ok(condition,id);controls.push(id);}
const wait=ms=>new Promise(r=>setTimeout(r,ms));
async function port(){const s=createServer();await new Promise(r=>s.listen(0,'127.0.0.1',r));const p=s.address().port;await new Promise(r=>s.close(r));return p;}
async function closed(p){try{const r=await fetch(`http://127.0.0.1:${p}/`,{signal:AbortSignal.timeout(800)});await r.arrayBuffer();return false;}catch{return true;}}
await fs.mkdir(out,{recursive:false});const initial=await hashes();
try{
 browser=await chromium.launch({executablePath:process.env.CHROMIUM_PATH||'/usr/bin/chromium',headless:true});
 for(const id of ['field-journey','selected-passives']){
  const p=await port(),report=path.join(out,id+'.json');
  const args=['tools/run_source_experiment.py','run',id,'--dotnet',dotnet,'--port',String(p),'--seconds','12','--report',report];
  const child=spawn('python3',args,{cwd:root,stdio:['ignore','pipe','pipe']});let stdout='',stderr='',ready;const started=Date.now();
  child.stdout.on('data',b=>{stdout+=b;for(const line of stdout.split('\n'))try{const v=JSON.parse(line);if(v.event==='ready')ready=v;}catch{}});child.stderr.on('data',b=>stderr+=b);
  const trial={id,command:['python3',...args],port:p};trials.push(trial);
  try{
   for(let n=0;n<2400&&!ready;n++){if(child.exitCode!==null)throw Error('Launcher exited before readiness: '+stdout+stderr);await wait(25);}
   check(id+' emits observed ready event',ready?.id===id&&ready?.url===`http://127.0.0.1:${p}/`&&Number.isInteger(ready.pid));
   const page=await browser.newPage({viewport:{width:1280,height:1000}});page.on('pageerror',e=>errors.push(e.message));await page.goto(ready.url);
   const statePath=id==='field-journey'?'state':'api/state';const state=async()=>page.evaluate(async u=>{const r=await fetch(u);if(!r.ok)throw Error('Owner HTTP '+r.status);return r.json();},ready.url+statePath);
   if(id==='field-journey'){
    await page.waitForFunction(()=>window.fieldJourney?.status==='ready');trial.initial=await state();check('Field starts original unconfirmed identity without an encounter',!trial.initial.intake.confirmed&&!trial.initial.intake.state.active&&!trial.initial.intake.state.complete);
    const a=await state(),b=await state();check('Field repeated GET does not advance owner',JSON.stringify(a)===JSON.stringify(b));
    await page.fill('#handle','Aster');await page.click('#draft');await page.waitForFunction(()=>window.fieldJourney.status==='ready');await page.click('#review');await page.waitForFunction(()=>window.fieldJourney.status==='ready');await page.click('#confirm');await page.waitForFunction(()=>window.fieldJourney.status==='ready');
    const confirmed=await state();check('Launched Field visibly confirms actual named person',confirmed.intake.confirmed&&confirmed.intake.identity.handle==='Aster'&&await page.locator('#confirmed-name').textContent()==='Aster');
    await page.click('#west-help');await page.waitForFunction(()=>window.fieldJourney.status==='ready');trial.after=await state();
    check('Launched Field delegates actual paid workshop action',trial.after.accepted&&trial.after.memory.parts===confirmed.memory.parts-1&&trial.after.memory.turn===confirmed.memory.turn+1);
    check('Workshop help does not fabricate road completion',!trial.after.intake.state.complete&&!trial.after.intake.state.active);
   }else{
    await page.waitForFunction(()=>window.combatStudy?.observation()!==null);trial.initial=await state();const a=await state(),b=await state();check('Treatment repeated GET does not advance owner',JSON.stringify(a)===JSON.stringify(b));
    check('Treatment opens actual original active practice',trial.initial.state.round===0&&trial.initial.state.outcome==='active');
    await page.locator('[data-command="strike"]').click();await page.waitForFunction(()=>window.combatStudy?.observation()?.sequence===1);trial.after=await state();
    check('Launched Treatment delegates actual attack and round',trial.after.accepted&&trial.after.state.round===1&&trial.after.state.enemyHp<trial.initial.state.enemyHp);
    check('Treatment actual result stays distinct from victory',trial.after.state.outcome==='active'&&await page.locator('#stats').textContent().then(t=>t.includes('Round 1')));
   }
   await page.screenshot({path:path.join(out,id+'.png'),fullPage:true});await page.close();
   if(child.exitCode===null)await Promise.race([new Promise(r=>child.once('exit',r)),wait(18000).then(()=>{throw Error('Launcher did not expire normally');})]);
   check(id+' launcher/host exits normally',child.exitCode===0);check(id+' owned listening port closes',await closed(p));
   trial.report=JSON.parse(await fs.readFile(report,'utf8'));check(id+' final report records success',trial.report.status==='success');
  }finally{if(child.exitCode===null&&child.signalCode===null){child.kill('SIGTERM');await new Promise(r=>child.once('exit',r));}trial.stdout=stdout;trial.stderr=stderr;trial.elapsed_ms=Date.now()-started;}
 }
 check('No application exceptions',errors.length===0);const after=await hashes();check('Source and producer identities stable',JSON.stringify(initial)===JSON.stringify(after));
 await fs.writeFile(path.join(out,'browser.json'),JSON.stringify({schema:'portfolio.actual-source-launch-browser.v1',runtime:{node:process.version,chromium:browser.version()},source_sha256:initial,controls,trials,errors,limits:'Actual local launcher/HTTP/C# commands and synthetic Chromium only. No participant usability, accessibility, onboarding time, sandbox, Unity/Windows/Steam or recipient feature claim.'},null,2)+'\n');console.log(`PASS ${controls.length} actual source-launch browser controls`);
}catch(e){await fs.writeFile(path.join(out,'failure.json'),JSON.stringify({error:e.stack,source_sha256:initial,controls,trials,errors},null,2)+'\n');throw e;}finally{await browser?.close();}
