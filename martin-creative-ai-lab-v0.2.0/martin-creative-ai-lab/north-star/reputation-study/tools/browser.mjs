import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';
import os from 'node:os';
import {spawn} from 'node:child_process';
import {createRequire} from 'node:module';
import {createServer} from 'node:net';
import {createHash} from 'node:crypto';
import {fileURLToPath} from 'node:url';

// Observe accepted C# events; browser text and drawings do not own standing or service.
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../../..');
const study=path.join(root,'north-star/reputation-study'),web=path.join(study,'web');
const dotnet=process.argv[2],output=process.argv[3]&&path.resolve(process.argv[3]);
if(!dotnet||!output||output===root||output.startsWith(root+path.sep))throw Error('Usage: browser.mjs DOTNET NEW_OUTPUT_OUTSIDE_MAINTAINED_TREE');
const require=createRequire(path.join(root,'projects/realtime-integration-lab/package.json'));
const {chromium}=require('playwright-core');
const hash=data=>createHash('sha256').update(data).digest('hex');
async function files(directory){let names=[];for(const entry of await fs.readdir(directory,{withFileTypes:true})){if(['bin','obj','node_modules','__pycache__'].includes(entry.name))continue;const p=path.join(directory,entry.name);if(entry.isDirectory())names.push(...await files(p));else if(entry.isFile()&&/\.(cs|csproj|js|mjs|html|css|json)$/.test(p))names.push(p);}return names;}
async function identities(){const names=[...await files(study),path.join(root,'north-star/csharp/global.json'),path.join(root,'projects/realtime-integration-lab/package.json'),path.join(root,'projects/realtime-integration-lab/package-lock.json')];return Object.fromEntries(await Promise.all(names.sort().map(async p=>[path.relative(root,p),hash(await fs.readFile(p))])));}
const before=await identities(),controls=[],httpControls=[],states={},negatives=[],logs=[],children=[],errors=[];
let browser,scratch,complete=false;
function check(id,condition){assert.ok(condition,id);assert.ok(!controls.includes(id),'Unique browser control');controls.push(id);}
async function start(webroot){const server=createServer();await new Promise((resolve,reject)=>{server.once('error',reject);server.listen(0,'127.0.0.1',resolve);});const port=server.address().port;await new Promise(resolve=>server.close(resolve));const command=[path.join(study,'Host/bin/Release/net10.0/NorthStar.ReputationStudy.dll'),'--serve',String(port),webroot,'--seconds','120'];const child=spawn(dotnet,command,{cwd:root,stdio:['ignore','pipe','pipe']});children.push(child);const log={command:[dotnet,...command],stdout:'',stderr:''};logs.push(log);child.stdout.on('data',b=>log.stdout+=b);child.stderr.on('data',b=>log.stderr+=b);child.on('error',e=>log.stderr+=e.message);for(let i=0;i<200&&!log.stdout.includes('READY');i++){if(child.exitCode!==null)throw Error(JSON.stringify(log));await new Promise(resolve=>setTimeout(resolve,25));}assert.match(log.stdout,/READY/,'Actual bounded C# host starts');return`http://127.0.0.1:${port}/`;}
async function stop(child){if(child.exitCode!==null||child.signalCode!==null)return;child.kill('SIGTERM');await Promise.race([new Promise(resolve=>child.once('exit',resolve)),new Promise(resolve=>setTimeout(resolve,1200))]);if(child.exitCode===null&&child.signalCode===null){child.kill('SIGKILL');await new Promise(resolve=>child.once('exit',resolve));}}
const region=(o,id)=>o.state.regions.find(r=>r.id===id);
async function actual(url){const response=await fetch(url+'state',{signal:AbortSignal.timeout(5000)});assert.equal(response.status,200);return response.json();}
async function snapshot(page){return page.evaluate(()=>window.reputationStudy.snapshot());}
async function fidelity(page,observed){
 const state=observed.state;
 assert.equal(Number.parseInt(await page.locator('#time').textContent(),10),state.time,'Visible time follows actual owner');
 assert.equal(Number.parseInt(await page.locator('#coins').textContent(),10),state.coins,'Visible coins follow actual owner');
 assert.ok((await page.locator('#notice').textContent()).includes(observed.text),'Actual accepted/refused event text is rendered');
 for(const value of state.regions){
  const card=page.locator(`[data-region="${value.id}"]`);
  assert.equal(await card.count(),1,'One independently observed regional card');
  assert.equal(Number(await card.getAttribute('data-standing')),value.standing,'Standing follows actual region');
  assert.equal(await card.getAttribute('data-custody'),String(value.custody),'Custody follows actual region');
  assert.equal(await card.getAttribute('data-returned'),String(value.returned),'Return follows actual region');
  assert.equal(await card.getAttribute('data-service'),String(value.service),'Service must follow actual owner');
  assert.equal((await card.locator('[data-role="service"]').textContent()).trim(),value.service?'Service actually received here':'Service not received here','Visible service text follows actual owner');
  assert.equal(Number.parseInt(await card.locator('[data-role="standing"]').textContent(),10),value.standing,'Visible standing follows actual region');
 }
 assert.deepEqual(await snapshot(page),observed,'Observed browser snapshot is exact C# envelope');
}
async function action(page,url,command){const prior=await actual(url);await page.locator(`[data-command=${JSON.stringify(command)}]`).click();await page.waitForFunction(sequence=>window.reputationStudy?.snapshot()?.sequence>sequence,prior.sequence);const observed=await actual(url);await fidelity(page,observed);return observed;}
async function expectRefusal(page,url,command,label){const before=await actual(url),after=await action(page,url,command);check(label,!after.accepted&&JSON.stringify(before.state)===JSON.stringify(after.state));negatives.push({id:label,before,after});return after;}
await fs.mkdir(output,{recursive:false});
try{
 const url=await start(web);
 const invalid=[
  {id:'extra client standing',body:'{"command":"help","standing":3}',headers:{'Content-Type':'application/json'}},
  {id:'duplicate command key',body:'{"command":"help","command":"service"}',headers:{'Content-Type':'application/json'}},
  {id:'fabricated return command',body:'{"command":"complete"}',headers:{'Content-Type':'application/json'}},
  {id:'malformed JSON',body:'{',headers:{'Content-Type':'application/json'}},
  {id:'cross-origin request',body:'{"command":"help"}',headers:{'Content-Type':'application/json',Origin:'http://untrusted.invalid'}},
  {id:'wrong content type',body:'{"command":"help"}',headers:{'Content-Type':'text/plain'}},
  {id:'oversized body',body:' '.repeat(1025),headers:{'Content-Type':'application/json'}}];
 for(const input of invalid){const before=await actual(url);const response=await fetch(url+'command',{method:'POST',body:input.body,headers:input.headers,signal:AbortSignal.timeout(5000)});assert.equal(response.status,400,input.id);assert.deepEqual(await actual(url),before,input.id+' leaves observation unchanged');httpControls.push(input.id);}
 browser=await chromium.launch({executablePath:process.env.CHROMIUM_PATH||'/usr/bin/chromium',headless:true,args:['--no-sandbox']});const page=await browser.newPage({viewport:{width:1280,height:1120}});page.on('pageerror',e=>errors.push(e.message));await page.goto(url);await page.waitForFunction(()=>window.reputationStudy?.snapshot()?.state);
 states.initial=await actual(url);await fidelity(page,states.initial);check('Both independent regions begin at explicit experimental minus one',states.initial.state.regions.length===2&&states.initial.state.regions.every(r=>r.standing===-1&&!r.custody&&!r.returned&&!r.service)&&states.initial.state.time===4&&states.initial.state.coins===3);
 const unchanged=JSON.stringify(await actual(url));await page.waitForTimeout(120);await page.reload();await page.waitForFunction(()=>window.reputationStudy?.snapshot()?.state);await fidelity(page,await actual(url));check('Actual reads redraw and elapsed time cannot create standing return or service',JSON.stringify(await actual(url))===unchanged);
 await expectRefusal(page,url,'service','Insufficient standing refuses real service without charge');
 await expectRefusal(page,url,'return','Return without actual custody refuses without time or standing');
 states.borrowed=await action(page,url,'borrow');check('Borrowing creates custody without reputational improvement',states.borrowed.accepted&&region(states.borrowed,'quay').custody&&region(states.borrowed,'quay').standing===-1&&states.borrowed.state.time===4&&states.borrowed.state.coins===3&&!region(states.borrowed,'quay').returned);
 await expectRefusal(page,url,'borrow','A second loan cannot manufacture another held tool');
 await action(page,url,'visit orchard');await expectRefusal(page,url,'return','A tool held at Quay cannot be returned at Orchard');
 states.separate=await actual(url);check('Visiting another region leaves the first actual custody independent',region(states.separate,'quay').custody&&!region(states.separate,'orchard').custody&&region(states.separate,'orchard').standing===-1);
 await action(page,url,'visit quay');states.returned=await action(page,url,'return');check('Actual return consumes custody and two finite time units before crossing sign',states.returned.accepted&&!region(states.returned,'quay').custody&&region(states.returned,'quay').returned&&region(states.returned,'quay').standing===1&&states.returned.state.time===2&&states.returned.state.coins===3);
 check('A returned Quay loan does not improve Orchard standing',region(states.returned,'orchard').standing===-1&&!region(states.returned,'orchard').returned&&!region(states.returned,'orchard').service);
 await expectRefusal(page,url,'return','Repeated return cannot improve standing or repay an event');
 states.served=await action(page,url,'service');check('Eligible service actually consumes two coins and one time unit',states.served.accepted&&region(states.served,'quay').service&&states.served.state.coins===1&&states.served.state.time===1&&states.served.state.receipts.some(r=>r.kind==='service'&&r.region==='quay'&&r.coin_cost===2&&r.time_cost===1));
 await page.screenshot({path:path.join(output,'service.png'),fullPage:true});
 await expectRefusal(page,url,'service','A completed service cannot charge or grant twice');
 await action(page,url,'visit orchard');states.unreturned=await action(page,url,'borrow');await expectRefusal(page,url,'return','Insufficient remaining time cannot erase custody or invent return');check('An unfinished other-region loan remains visibly held',region(await actual(url),'orchard').custody&&!region(await actual(url),'orchard').returned&&!region(await actual(url),'orchard').service);await page.screenshot({path:path.join(output,'unfinished-loan.png'),fullPage:true});
 await action(page,url,'restart');for(let i=0;i<4;i++)states.minor=await action(page,url,'help');check('Four actually paid minor helps retain the source negative sign counterexample',states.minor.state.time===0&&region(states.minor,'quay').standing===-1&&region(states.minor,'quay').work===4&&states.minor.state.coins===3&&!region(states.minor,'quay').service);await expectRefusal(page,url,'help','Exhausted work cannot spend negative time');await expectRefusal(page,url,'service','Minor-help losing policy cannot purchase an unearned service');await page.screenshot({path:path.join(output,'minor-help-stall.png'),fullPage:true});
 const beforeQueued=await actual(url);await page.evaluate(async()=>{const restart=window.reputationStudy.command('restart');const oldBorrow=window.reputationStudy.command('borrow');await Promise.all([restart,oldBorrow]);});states.newTrialQueue=await actual(url);await fidelity(page,states.newTrialQueue);check('Accepted new trial discards older queued borrowing intent',states.newTrialQueue.sequence===beforeQueued.sequence+1&&states.newTrialQueue.state.time===4&&states.newTrialQueue.state.coins===3&&states.newTrialQueue.state.receipts.length===0&&states.newTrialQueue.state.regions.every(r=>!r.custody));negatives.push({id:'queued-intent-after-new-trial',before:beforeQueued,after:states.newTrialQueue,classification:'Actual accepted restart changes browser generation; the queued old-view loan does not execute.'});
 // A separate web copy changes the actual renderer, never the C# owner.
 scratch=await fs.mkdtemp(path.join(os.tmpdir(),'reputation-render-mutant-'));await fs.cp(web,path.join(scratch,'web'),{recursive:true});const filename=path.join(scratch,'web/app.js'),source=await fs.readFile(filename,'utf8'),target='const serviceObserved = Boolean(place.service);';assert.equal(source.split(target).length,2,'One declared false-service renderer mutation target');const changed=source.replace(target,'const serviceObserved = true;');await fs.writeFile(filename,changed);const mutantUrl=await start(path.join(scratch,'web')),mutant=await browser.newPage({viewport:{width:1280,height:1120}});await mutant.goto(mutantUrl);await mutant.waitForFunction(()=>window.reputationStudy?.snapshot()?.state);const mutantActual=await actual(mutantUrl);assert.ok(mutantActual.state.regions.every(r=>!r.service));let detection;try{await fidelity(mutant,mutantActual);}catch(error){if(error.code!=='ERR_ASSERTION'||!error.message.includes('Service must follow actual owner'))throw error;detection={name:error.name,code:error.code,message:error.message};}assert.ok(detection,'Specific false-service renderer must be rejected');negatives.push({id:'forced-service-renderer',detected:true,mutation:{target,replacement:'const serviceObserved = true;',original_sha256:hash(source),mutated_sha256:hash(changed)},actual:mutantActual,assertion:detection});check('An isolated actual false-service renderer is detected against its unchanged owner',Boolean(detection));await mutant.close();
 check('Actual browser has no uncaught script errors',errors.length===0);assert.deepEqual(await identities(),before,'Consumer and instrument input closure stays exact');check('Consumer source identities remain stable through execution',true);complete=true;
 await fs.writeFile(path.join(output,'browser.json'),JSON.stringify({schema_version:1,kind:'actual_browser_csharp_reputation',runtime:{node:process.version,chromium:browser.version(),playwright:require('playwright-core/package.json').version},checks:{passed:controls.length,failed:0},http_checks:{passed:httpControls.length,failed:0},controls,http_controls:httpControls,states,negatives,source_sha256:before,source_stable:true,scope:'Finite original trusted-local ephemeral C# service experiment using selected standing arithmetic. Synthetic software actions and rendered fidelity, not people, source effect execution, morality, broad social trust, Unity, Windows, Steam or human balance/quality.'},null,2)+'\n');console.log(`PASS: ${controls.length} actual reputation Chromium controls, ${httpControls.length} HTTP controls and false-service detection`);
}catch(error){await fs.writeFile(path.join(output,'failure.json'),JSON.stringify({complete:false,error:{name:error.name,code:error.code??null,message:error.message,stack:error.stack},completed_controls:controls,http_controls:httpControls,states,source_sha256:before},null,2)+'\n');throw error;}finally{for(const child of children)await stop(child);await browser?.close();if(scratch)await fs.rm(scratch,{recursive:true,force:true});await fs.writeFile(path.join(output,'hosts.json'),JSON.stringify({complete,logs},null,2)+'\n');}
