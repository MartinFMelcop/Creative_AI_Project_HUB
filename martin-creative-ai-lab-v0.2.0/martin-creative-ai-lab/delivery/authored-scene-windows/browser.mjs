import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';
import {spawn,spawnSync} from 'node:child_process';
import {createRequire} from 'node:module';
import {createServer} from 'node:net';
import {fileURLToPath} from 'node:url';
const here=path.dirname(fileURLToPath(import.meta.url)),root=path.resolve(here,'../..');
if(process.platform!=='win32'||process.arch!=='x64')throw Error('Actual Windows x64 required; cross-compilation is insufficient');
const bundle=path.resolve(process.argv[2]),out=path.resolve(process.argv[3]);
if([bundle,out].some(p=>p===root||p.startsWith(root+path.sep)))throw Error('External relocated bundle/output required');
const require=createRequire(path.join(root,'projects/realtime-integration-lab/package.json'));
const {chromium}=require('playwright-core');
const shell=process.env.PWSH_EXE;
if(!shell||!path.isAbsolute(shell))throw Error('Explicit installed PowerShell executable required');
const controls=[],states={},logs=[],negatives=[],children=[],errors=[];
let browser,browserVersion=null,complete=false,failure=null,request=0;
const refused=r=>Number.isInteger(r.status)&&r.status!==0&&!r.error&&!r.signal;
const check=(id,ok)=>{assert.ok(ok,id);assert.ok(!controls.includes(id));controls.push(id);};
await fs.mkdir(out,{recursive:false});
const cwd=path.join(out,'unrelated directory'),minimal=path.join(out,'empty PATH');await fs.mkdir(cwd);await fs.mkdir(minimal);
// Keep OS necessities, remove SDK/Node resolution from the recipient environment.
const environment={...process.env,PATH:minimal,DOTNET_ROOT:'Z:\\unavailable',DOTNET_ROOT_X64:'Z:\\unavailable',DOTNET_MULTILEVEL_LOOKUP:'0'};
delete environment.DOTNET_ADDITIONAL_DEPS;delete environment.DOTNET_SHARED_STORE;delete environment.NUGET_PACKAGES;
const launcher=path.join(bundle,'run-demo.ps1');
const shellArgs=['-NoLogo','-NoProfile','-NonInteractive','-File',launcher];
async function port(){const s=createServer();await new Promise((r,j)=>{s.once('error',j);s.listen(0,'127.0.0.1',r);});const p=s.address().port;await new Promise(r=>s.close(r));return p;}
async function stop(child){if(child.exitCode!==null||child.signalCode!==null)return;spawnSync(path.join(process.env.SystemRoot,'System32/taskkill.exe'),['/PID',String(child.pid),'/T','/F'],{encoding:'utf8'});await Promise.race([new Promise(r=>child.once('exit',r)),new Promise(r=>setTimeout(r,3000))]);assert.ok(child.exitCode!==null||child.signalCode!==null,'Owned process tree must stop');}
async function start(save,seconds='90'){
 const p=await port(),url=`http://127.0.0.1:${p}/`,log={port:p,stdout:'',stderr:''};logs.push(log);
 const child=spawn(shell,[...shellArgs,String(p),seconds],{cwd,env:{...environment,NORTH_STAR_SAVE_DIR:save},stdio:['ignore','pipe','pipe']});children.push(child);child.stdout.on('data',d=>log.stdout+=d);child.stderr.on('data',d=>log.stderr+=d);child.on('error',e=>log.stderr+=e.message);
 for(let i=0;i<400;i++){if(child.exitCode!==null)throw Error(JSON.stringify(log));try{const r=await fetch(url+'state',{signal:AbortSignal.timeout(500)});if(r.ok)return {url,child};}catch{}await new Promise(r=>setTimeout(r,50));}throw Error('Windows host failed to become ready: '+JSON.stringify(log));
}
async function observation(url){const r=await fetch(url+'state',{signal:AbortSignal.timeout(5000)});assert.equal(r.status,200);return r.json();}
async function command(url,c){const o=await observation(url);const r=await fetch(url+'command',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({command:c,request_id:'windows-'+(++request),revision:o.continuity.revision,run_id:o.continuity.run_id}),signal:AbortSignal.timeout(5000)});assert.equal(r.status,200);const a=await r.json();assert.ok(a.accepted,c);return a;}
async function fidelity(page,o){assert.equal(await page.locator('body').getAttribute('data-returned'),String(o.state.returned));assert.equal(await page.locator('body').getAttribute('data-delivered'),String(o.state.delivered));assert.equal(Number.parseInt(await page.locator('#remaining').textContent()),o.state.remaining);assert.equal(Number.parseInt(await page.locator('#crates').textContent()),o.state.crates);assert.deepEqual(await page.evaluate(()=>window.authoredScene.snapshot()),o);}
try{
 const resolution=spawnSync(shell,['-NoLogo','-NoProfile','-NonInteractive','-Command',"if(Get-Command dotnet,node -ErrorAction SilentlyContinue){exit 1}else{exit 0}"],{cwd,env:environment,encoding:'utf8'});check('Recipient PATH resolves neither dotnet nor Node',resolution.status===0);
 const runtime=spawnSync(path.join(bundle,'runtime/dotnet.exe'),['--info'],{cwd,env:environment,encoding:'utf8'});check('Actual private runtime is Windows x64 10.0.12',runtime.status===0&&runtime.stdout.includes('10.0.12')&&runtime.stdout.includes('win-x64'));
 const sdks=spawnSync(path.join(bundle,'runtime/dotnet.exe'),['--list-sdks'],{cwd,env:environment,encoding:'utf8'});check('Private runtime contains no SDK',sdks.status===0&&sdks.stdout.trim()==='');
 const save=path.join(out,'saved choices');let host=await start(save);check('Actual relocated Windows package starts from unrelated cwd without URLACL modification',true);
 browser=await chromium.launch({headless:true});browserVersion=browser.version();const page=await browser.newPage({viewport:{width:1280,height:1120}});page.on('pageerror',e=>errors.push(e.message));await page.goto(host.url);await page.waitForFunction(()=>window.authoredScene?.snapshot()?.state);
 async function action(c){const before=await observation(host.url);await page.locator(`[data-command=${JSON.stringify(c)}]`).click();await page.waitForFunction(n=>window.authoredScene.snapshot().sequence>n,before.sequence);const a=await observation(host.url);await fidelity(page,a);return a;}
 states.initial=await observation(host.url);await fidelity(page,states.initial);check('Windows browser observes unfinished work and secured guide',states.initial.state.remaining===4&&!states.initial.state.returned&&!states.initial.state.delivered);
 await action('open');states.refusal=await action('decline');check('Actual refusal preserves guide and cannot fabricate delivery',states.refusal.state.status==='declined'&&states.refusal.state.guide_available&&!states.refusal.state.delivered);
 await action('restart');for(const c of ['survey','skill','skill','walk','skill','open','hear','offer','terms dusk'])await action(c);states.preparing=await action('confirm');check('Private heard consent and agreement spend actual guide capacity',states.preparing.state.guide_location==='local-preparing'&&states.preparing.state.capacity===1&&!states.preparing.state.returned);
 states.departed=await action('depart guided');states.mid=await action('skill');check('Real nested Crossing is in progress after paid departure',states.mid.state.encounter.active&&states.mid.state.remaining===1&&!states.mid.state.returned&&!states.mid.state.delivered);
 await page.screenshot({path:path.join(out,'departed.png'),fullPage:true});await stop(host.child);host=await start(save);await page.goto(host.url);await page.waitForFunction(()=>window.authoredScene?.snapshot()?.state);states.resumed=await observation(host.url);check('Windows process reentry preserves actual in-progress encounter, costs and consent',JSON.stringify(states.resumed.state)===JSON.stringify(states.mid.state)&&states.resumed.continuity.revision===states.mid.continuity.revision);
 const stable=JSON.stringify(await observation(host.url));await page.waitForTimeout(100);await page.reload();await page.waitForFunction(()=>window.authoredScene?.snapshot()?.state);check('Offline reentry, time and redraw cannot manufacture return or delivery',stable===JSON.stringify(await observation(host.url)));
 for(const c of ['skill','walk','skill','walk','skill'])states.returned=await action(c);check('Actual final encounter permits observed guided return and delivery',states.returned.state.returned&&states.returned.state.delivered&&states.returned.state.guide_available);
 states.finished=await action('work');check('Delivered request leaves three actual crates unfinished',states.finished.state.crates===2&&states.finished.state.crates_required===5&&states.finished.state.remaining===0);await page.screenshot({path:path.join(out,'delivered.png'),fullPage:true});await stop(host.child);
 const linux=path.join(out,'Linux journal on Windows');await fs.mkdir(linux);await fs.copyFile(path.join(here,'fixtures/linux-scene.json'),path.join(linux,'scene.json'));host=await start(linux);states.imported=await observation(host.url);const expected=JSON.parse(await fs.readFile(path.join(here,'fixtures/linux-state.json'),'utf8'));check('Exact unchanged managed assemblies replay the actual Linux journal on Windows',JSON.stringify(states.imported.state)===JSON.stringify(expected.state)&&states.imported.continuity.run_id===expected.continuity.run_id&&states.imported.continuity.revision===expected.continuity.revision);await stop(host.child);
 for(const file of ['runtime/ThirdPartyNotices.txt','web/app.js']){const target=path.join(bundle,file),original=await fs.readFile(target);await fs.unlink(target);try{const r=spawnSync(shell,[...shellArgs,'8768','1'],{cwd,env:environment,encoding:'utf8',timeout:20000});check('Actual Windows launcher rejects missing '+file,refused(r)&&!r.stdout.includes('READY'));negatives.push({file,exit_code:r.status,stdout:r.stdout,stderr:r.stderr});}finally{await fs.writeFile(target,original);}}
 const corrupt=path.join(out,'corrupt save');await fs.mkdir(corrupt);const corruptPath=path.join(corrupt,'scene.json');await fs.writeFile(corruptPath,'{broken');const bad=spawnSync(shell,[...shellArgs,'8768','1'],{cwd,env:{...environment,NORTH_STAR_SAVE_DIR:corrupt},encoding:'utf8',timeout:20000});check('Actual Windows corrupt save refuses without reset',refused(bad)&&!bad.stdout.includes('READY')&&await fs.readFile(corruptPath,'utf8')==='{broken');negatives.push({kind:'corrupt save',exit_code:bad.status,stdout:bad.stdout,stderr:bad.stderr});
 const invalid=spawnSync(shell,[...shellArgs,'1023','1'],{cwd,env:environment,encoding:'utf8',timeout:20000});check('Windows launcher refuses invalid port',refused(invalid)&&!invalid.stdout.includes('READY'));
 const expires=await start(save,'1');await new Promise((r,j)=>{const t=setTimeout(()=>j(Error('Bounded Windows host did not expire')),15000);expires.child.once('exit',()=>{clearTimeout(t);r();});});check('Actual Windows host lifetime ends successfully',expires.child.exitCode===0);
 check('No Windows browser script exceptions',errors.length===0);complete=true;
 await fs.writeFile(path.join(out,'results.json'),JSON.stringify({complete,browser_version:browserVersion,controls,passed:controls.length,states,negatives,errors,scope:'Actual hosted Windows x64 software controls. Same unchanged scene; no participant, Unity, Steam or normal-user-device claim.'},null,2)+'\n');console.log(controls.length+' actual Windows recipient controls passed');
}catch(e){failure=e.stack;throw e;}finally{if(browser)await browser.close();for(const c of children)await stop(c);await fs.writeFile(path.join(out,'execution.json'),JSON.stringify({complete,browser_version:browserVersion,failure,controls,states,negatives,errors,logs},null,2)+'\n');}
