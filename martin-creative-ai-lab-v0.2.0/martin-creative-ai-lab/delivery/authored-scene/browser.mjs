import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';
import {spawn,spawnSync} from 'node:child_process';
import {createRequire} from 'node:module';
import {createServer} from 'node:net';
import {fileURLToPath} from 'node:url';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../..');
const bundle=process.argv[2]&&path.resolve(process.argv[2]),out=process.argv[3]&&path.resolve(process.argv[3]);
if(!bundle||!out||[bundle,out].some(p=>p===root||p.startsWith(root+path.sep)))throw Error('Bundle and new output must be outside maintained workspace');
const require=createRequire(path.join(root,'projects/realtime-integration-lab/package.json'));
const {chromium}=require('playwright-core');
const controls=[],states={},negatives=[],logs=[],children=[],errors=[];
let browser,complete=false,failure=null;
const check=(id,ok)=>{assert.ok(ok,id);assert.ok(!controls.includes(id));controls.push(id);};
await fs.mkdir(out,{recursive:false});
const minimal=path.join(out,'minimal tools'),cwd=path.join(out,'unrelated directory');await fs.mkdir(minimal);await fs.mkdir(cwd);
for(const tool of ['sha256sum','dirname'])await fs.symlink('/usr/bin/'+tool,path.join(minimal,tool));
const environment={PATH:minimal,DOTNET_CLI_TELEMETRY_OPTOUT:'1',DOTNET_MULTILEVEL_LOOKUP:'0',DOTNET_ROOT:'/nonexistent',DOTNET_ROOT_X64:'/nonexistent',LANG:'C.UTF-8'};
const launcher=path.join(bundle,'run-demo.sh');
async function port(){const server=createServer();await new Promise((r,j)=>{server.once('error',j);server.listen(0,'127.0.0.1',r);});const value=server.address().port;await new Promise(r=>server.close(r));return value;}
async function stop(child){if(child.exitCode!==null||child.signalCode!==null)return;child.kill('SIGTERM');await Promise.race([new Promise(r=>child.once('exit',r)),new Promise(r=>setTimeout(r,1200))]);if(child.exitCode===null&&child.signalCode===null){child.kill('SIGKILL');await new Promise(r=>child.once('exit',r));}}
async function start(seconds='120'){const p=await port();const log={port:p,stdout:'',stderr:''};logs.push(log);const child=spawn(launcher,[String(p),seconds],{cwd,env:environment,stdio:['ignore','pipe','pipe']});children.push(child);child.stdout.on('data',d=>log.stdout+=d);child.stderr.on('data',d=>log.stderr+=d);child.on('error',e=>log.stderr+=e.message);for(let i=0;i<200&&!log.stdout.includes('READY');i++){if(child.exitCode!==null)throw Error(JSON.stringify(log));await new Promise(r=>setTimeout(r,25));}assert.match(log.stdout,/READY/,'Extracted actual package must start');return {url:`http://127.0.0.1:${p}/`,child};}
async function fidelity(page,o){const s=o.state;assert.equal(await page.locator('body').getAttribute('data-returned'),String(s.returned));assert.equal(await page.locator('body').getAttribute('data-delivered'),String(s.delivered));assert.equal(Number.parseInt(await page.locator('#crates').textContent(),10),s.crates);assert.equal(Number.parseInt(await page.locator('#remaining').textContent(),10),s.remaining);assert.ok((await page.locator('#notice').textContent()).includes(o.text));assert.deepEqual(await page.evaluate(()=>window.authoredScene.snapshot()),o);}
try{
 const unavailable=spawnSync('/bin/sh',['-c','command -v dotnet || command -v node'],{cwd,env:environment,encoding:'utf8'});check('Recipient process PATH contains neither SDK/dotnet nor Node',unavailable.status!==0&&unavailable.stdout==='');
 const sdk=spawnSync(path.join(bundle,'runtime/dotnet'),['--list-sdks'],{cwd,env:environment,encoding:'utf8'});check('Bundled runtime has no installed SDK',sdk.status===0&&sdk.stdout.trim()==='');
 const runtimes=spawnSync(path.join(bundle,'runtime/dotnet'),['--list-runtimes'],{cwd,env:environment,encoding:'utf8'});check('Only bundled pinned Microsoft.NETCore.App10.0.12 runtime is available',runtimes.status===0&&runtimes.stdout.includes('Microsoft.NETCore.App 10.0.12')&&!runtimes.stdout.includes('AspNetCore'));
 const {url,child}=await start();check('Actual relocated package starts from unrelated cwd and restricted PATH',true);
 browser=await chromium.launch({executablePath:process.env.CHROMIUM_PATH||'/usr/bin/chromium',headless:true,args:['--no-sandbox']});const page=await browser.newPage({viewport:{width:1280,height:1120}});page.on('pageerror',e=>errors.push(e.message));await page.goto(url);await page.waitForFunction(()=>window.authoredScene?.snapshot()?.state);
 const actual=async()=>{const r=await fetch(url+'state',{signal:AbortSignal.timeout(5000)});assert.equal(r.status,200);return r.json();};
 async function action(command){const before=await actual();await page.locator(`[data-command=${JSON.stringify(command)}]`).click();await page.waitForFunction(n=>window.authoredScene?.snapshot()?.sequence>n,before.sequence);const after=await actual();await fidelity(page,after);return after;}
 states.initial=await actual();await fidelity(page,states.initial);check('Package starts with actual unfinished work and secured guide',states.initial.state.crates===0&&states.initial.state.remaining===4&&!states.initial.state.returned&&!states.initial.state.delivered);
 await action('open');states.refusal=await action('decline');check('Packaged owner preserves actual final refusal',states.refusal.state.status==='declined'&&!states.refusal.state.delivered&&!states.refusal.state.returned&&states.refusal.state.guide_available);
 await action('restart');for(const c of ['survey','skill','skill','walk','skill','open','hear','offer','terms dusk'])await action(c);states.preparing=await action('confirm');check('Actual agreement spends guide capacity before departure',states.preparing.state.guide_location==='local-preparing'&&states.preparing.state.capacity===1&&!states.preparing.state.delivery_started);
 const unchanged=JSON.stringify(await actual());await page.waitForTimeout(100);await page.reload();await page.waitForFunction(()=>window.authoredScene?.snapshot()?.state);check('Packaged redraw and elapsed time cannot invent departure or return',unchanged===JSON.stringify(await actual()));
 states.departed=await action('depart guided');check('Actual package pays travel cost and starts nested Crossing',states.departed.state.remaining===1&&states.departed.state.encounter.active&&!states.departed.state.returned);
 for(const c of ['skill','skill','walk','skill','walk','skill'])states.returned=await action(c);check('Packaged actual encounter produces observed guided return and delivery',states.returned.state.returned&&states.returned.state.delivered&&states.returned.state.guide_available);
 states.finished=await action('work');check('Packaged completed handoff leaves three crates unfinished',states.finished.state.crates===2&&states.finished.state.crates_required===5&&states.finished.state.remaining===0);await page.screenshot({path:path.join(out,'delivered.png'),fullPage:true});
 await browser.close();browser=null;await stop(child);check('Owned packaged host stops explicitly',child.exitCode!==null||child.signalCode!==null);
 for(const file of ['web/app.js','runtime/ThirdPartyNotices.txt']){const target=path.join(bundle,file),saved=await fs.readFile(target);await fs.unlink(target);try{const r=spawnSync(launcher,['8768','1'],{cwd,env:environment,encoding:'utf8',timeout:5000});check('Launcher rejects missing '+file+' before starting',r.status!==0&&!r.stdout.includes('READY')&&r.stderr.includes('payload is missing or changed'));negatives.push({file,exit_code:r.status,stderr:r.stderr,ready:false});}finally{await fs.writeFile(target,saved);}}
 const invalid=spawnSync(launcher,['1023','1'],{cwd,env:environment,encoding:'utf8',timeout:5000});check('Actual launcher rejects out-of-range port before start',invalid.status!==0&&!invalid.stdout.includes('READY'));
 const expires=await start('1');await new Promise((resolve,reject)=>{const timer=setTimeout(()=>reject(Error('Bounded host failed to expire')),6000);expires.child.once('exit',()=>{clearTimeout(timer);resolve();});});check('Actual packaged lifetime expires successfully',expires.child.exitCode===0);
 check('No browser script exception',errors.length===0);complete=true;
 await fs.writeFile(path.join(out,'results.json'),JSON.stringify({complete,controls,passed:controls.length,states,negatives,errors,scope:'Actual same-machine Debian13/Linuxx64 extracted package; source filesystem is not sandboxed. No new independent participant or prior full scene matrix.'},null,2)+'\n');console.log(controls.length+' extracted-package controls passed');
}catch(e){failure=e.stack;throw e;}finally{if(browser)await browser.close();for(const child of children)await stop(child);await fs.writeFile(path.join(out,'execution.json'),JSON.stringify({complete,failure,controls,states,negatives,errors,logs},null,2)+'\n');}
