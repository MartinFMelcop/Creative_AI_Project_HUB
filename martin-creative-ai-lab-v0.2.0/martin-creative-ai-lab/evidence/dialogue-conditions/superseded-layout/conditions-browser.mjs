import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';
import os from 'node:os';
import {spawn} from 'node:child_process';
import {createRequire} from 'node:module';
import {createServer} from 'node:net';
import {createHash} from 'node:crypto';
import {fileURLToPath} from 'node:url';

// Observe one real named witness and its actual owner; never infer play from a draft.
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../../..');
const study=path.join(root,'north-star/memory-study'),web=path.join(study,'web');
const dotnet=process.argv[2],output=process.argv[3]&&path.resolve(process.argv[3]);
if(!dotnet||!output||output===root||output.startsWith(root+path.sep))throw Error('Usage: browser.mjs DOTNET NEW_OUTPUT_OUTSIDE_MAINTAINED_TREE');
const require=createRequire(path.join(root,'projects/realtime-integration-lab/package.json'));
const {chromium}=require('playwright-core');
const hash=data=>createHash('sha256').update(data).digest('hex');
async function files(directory){let names=[];for(const entry of await fs.readdir(directory,{withFileTypes:true})){if(['bin','obj','node_modules','__pycache__'].includes(entry.name))continue;const p=path.join(directory,entry.name);if(entry.isDirectory())names.push(...await files(p));else if(entry.isFile()&&/\.(cs|csproj|js|mjs|html|css|json|py)$/.test(p))names.push(p);}return names;}
async function identities(){const directories=['memory-study','field-journey','intake','csharp/Domain','csharp/Crossing','csharp/Forge','csharp/Loadout'];const names=(await Promise.all(directories.map(d=>files(path.join(root,'north-star',d))))).flat();names.push(path.join(root,'north-star/csharp/global.json'),path.join(root,'projects/realtime-integration-lab/package.json'),path.join(root,'projects/realtime-integration-lab/package-lock.json'));return Object.fromEntries(await Promise.all(names.sort().map(async p=>[path.relative(root,p),hash(await fs.readFile(p))])));}
const before=await identities(),controls=[],httpControls=[],states={},negatives=[],logs=[],children=[],errors=[];
let browser,scratch,complete=false;
function check(id,condition){assert.ok(condition,id);assert.ok(!controls.includes(id),'Unique browser control');controls.push(id);}
async function start(webroot,policy="independent"){const server=createServer();await new Promise((resolve,reject)=>{server.once('error',reject);server.listen(0,'127.0.0.1',resolve);});const port=server.address().port;await new Promise(resolve=>server.close(resolve));const command=[path.join(study,'Host/bin/Release/net10.0/NorthStar.MemoryStudy.dll'),'--serve',String(port),webroot,'--seconds','120','--policy',policy];const child=spawn(dotnet,command,{cwd:root,stdio:['ignore','pipe','pipe']});children.push(child);const log={command:[dotnet,...command],stdout:'',stderr:''};logs.push(log);child.stdout.on('data',b=>log.stdout+=b);child.stderr.on('data',b=>log.stderr+=b);child.on('error',e=>log.stderr+=e.message);for(let i=0;i<240&&!log.stdout.includes('READY');i++){if(child.exitCode!==null)throw Error(JSON.stringify(log));await new Promise(resolve=>setTimeout(resolve,25));}assert.match(log.stdout,/READY/,'Actual bounded C# host starts');return`http://127.0.0.1:${port}/`;}
async function stop(child){if(child.exitCode!==null||child.signalCode!==null)return;child.kill('SIGTERM');await Promise.race([new Promise(resolve=>child.once('exit',resolve)),new Promise(resolve=>setTimeout(resolve,1200))]);if(child.exitCode===null&&child.signalCode===null){child.kill('SIGKILL');await new Promise(resolve=>child.once('exit',resolve));}}
async function actual(url){const response=await fetch(url+'state',{signal:AbortSignal.timeout(5000)});assert.equal(response.status,200);return response.json();}
async function fidelity(page,s){
 assert.deepEqual(await page.evaluate(()=>window.memoryStudy.state),s,'Browser snapshot equals actual C# owner');
 for(const k of ['turn','parts','coins','sequence'])assert.equal(Number(await page.locator('#'+k).textContent()),s[k],'Actual '+k+' follows owner');
 for(const b of s.benches){
  assert.equal(await page.locator('#'+b.id).getAttribute('data-recent'),String(b.recent),'Named recent picture follows actual owner');
  assert.equal(await page.locator('#'+b.id).getAttribute('data-fitted'),String(b.delivered),'Named fitting picture follows actual owner');
  assert.equal((await page.locator('#'+b.id+'-help').textContent()).trim(),b.helped?'Yes':'No');
  assert.equal((await page.locator('#'+b.id+'-support').textContent()).trim(),b.support?'Yes':'No');
  const visible=await page.locator('#'+b.id).evaluate(el=>({recent:getComputedStyle(el.querySelector('.recent-mark')).display!=='none',fitting:getComputedStyle(el.querySelector('.fitted-piece')).display!=='none'}));
  assert.deepEqual(visible,{recent:b.recent,fitting:b.delivered},'Actual computed named witness/output SVG visibility');
  assert.equal(await page.locator('#'+b.id).getAttribute('data-eligible'),String(b.eligible),'Named eligibility picture follows actual owner');
  assert.equal(await page.locator('#'+b.id+'-fit-button').isEnabled(),b.eligible,'Named service button follows eligibility');
  assert.ok((await page.locator('#'+b.id+'-condition').textContent()).includes(b.condition_expression),'Actual expression is displayed');
  assert.equal(typeof b.condition_satisfied,'boolean');assert.equal(b.condition_complete,true,'Actual known context is complete');
 }
 assert.ok((await page.locator('#policy-note').textContent()).toLowerCase().includes(s.policy),'Actual startup policy displayed');
 assert.equal(await page.locator('#history li').count(),s.history.length,'Actual accepted action history remains visible');
 assert.equal(await page.locator('#notice').textContent(),s.text,'Actual receipt rendered');
}
async function open(url){const page=await browser.newPage({viewport:{width:1280,height:1100}});page.on('pageerror',e=>errors.push(e.message));await page.goto(url);await page.waitForFunction(()=>window.memoryStudy?.state&&window.memoryStudy.status==='ready');await fidelity(page,await actual(url));return page;}
async function act(page,url,command,bench,button){if(button){const before=await actual(url);await page.locator('#'+button).click();await page.waitForFunction(n=>window.memoryStudy?.state?.sequence>n&&window.memoryStudy.status==='ready',before.sequence);}else await page.evaluate(async({command,bench})=>window.memoryStudy.send(command,bench),{command,bench});const s=await actual(url);await fidelity(page,s);return s;}
const bench=(s,id)=>s.benches.find(b=>b.id===id);
async function refusal(page,url,command,recipient,id){const before=await actual(url),after=await act(page,url,command,recipient);const facts=s=>JSON.stringify({turn:s.turn,parts:s.parts,coins:s.coins,benches:s.benches,history:s.history});check(id,!after.accepted&&facts(before)===facts(after));negatives.push({id,before,after});return after;}
async function startField(){
 const server=createServer();await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));const port=server.address().port;await new Promise(resolve=>server.close(resolve));
 const command=[path.join(root,'north-star/field-journey/Host/bin/Release/net10.0/NorthStar.FieldJourney.dll'),'--serve',String(port),path.join(root,'north-star/field-journey/web'),'--seconds','120','--policy','ordered'];const child=spawn(dotnet,command,{cwd:root,stdio:['ignore','pipe','pipe']});children.push(child);const log={command:[dotnet,...command],stdout:'',stderr:''};logs.push(log);child.stdout.on('data',b=>log.stdout+=b);child.stderr.on('data',b=>log.stderr+=b);child.on('error',e=>log.stderr+=e.message);for(let i=0;i<240&&!log.stdout.includes('READY');i++){if(child.exitCode!==null)throw Error(JSON.stringify(log));await new Promise(resolve=>setTimeout(resolve,25));}assert.match(log.stdout,/READY/);return`http://127.0.0.1:${port}/`;
}
await fs.mkdir(output,{recursive:false});
try{
 browser=await chromium.launch({executablePath:process.env.CHROMIUM_PATH||'/usr/bin/chromium',headless:true,args:['--no-sandbox']});
 const independentUrl=await start(web,'independent'),independent=await open(independentUrl);
 check('Explicit independent startup is observed without a fitting',(await actual(independentUrl)).policy==='independent'&&(await actual(independentUrl)).benches.every(b=>!b.delivered));
 await act(independent,independentUrl,'help','east','east-help-button');states.independent=await act(independent,independentUrl,'serve','east','east-fit-button');
 check('Independent East help then service pays actual costs and supplies East only',states.independent.turn===2&&states.independent.parts===3&&states.independent.coins===1&&bench(states.independent,'east').delivered&&!bench(states.independent,'west').delivered);
 const url=await start(web,'ordered'),page=await open(url);states.initial=await actual(url);
 check('Ordered startup declares its actual immutable East condition',states.initial.policy==='ordered'&&bench(states.initial,'east').condition_expression.includes('OtherDelivered=true')&&!bench(states.initial,'west').condition_expression.includes('OtherDelivered'));
 await act(page,url,'help','east','east-help-button');states.eastHelp=await actual(url);
 check('Actual East help cannot replace West delivery in ordered context',states.eastHelp.turn===1&&states.eastHelp.parts===3&&bench(states.eastHelp,'east').helped&&bench(states.eastHelp,'east').support&&bench(states.eastHelp,'east').recent&&!bench(states.eastHelp,'east').condition_satisfied&&!bench(states.eastHelp,'east').eligible);
 await refusal(page,url,'serve','east','Same East service is actually refused without cost under ordered policy');
 for(const [id,extra]of [['forged OtherDelivered fact',{OtherDelivered:true}],['forged startup policy',{policy:'independent'}]]){
  const before=await actual(url);const response=await fetch(url+'command',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({command:'serve',revision:before.sequence,bench:'east',...extra}),signal:AbortSignal.timeout(5000)});assert.equal(response.status,400,id);assert.deepEqual(await actual(url),before,id+' cannot mutate actual owner');httpControls.push(id);
 }
 check('Client facts and policy cannot bypass actual ordered condition',httpControls.length===2);
 await act(page,url,'help','west','west-help-button');states.west=await act(page,url,'serve','west','west-fit-button');
 check('Actual West service changes East condition without acquiring East fitting',states.west.turn===3&&states.west.coins===1&&bench(states.west,'west').delivered&&bench(states.west,'east').condition_satisfied&&bench(states.west,'east').eligible&&!bench(states.west,'east').delivered);
 await page.screenshot({path:path.join(output,'condition-true-not-delivered.png'),fullPage:true});
 const stable=JSON.stringify(await actual(url));await page.waitForTimeout(120);await page.reload();await page.waitForFunction(()=>window.memoryStudy?.state&&window.memoryStudy.status==='ready');await fidelity(page,await actual(url));check('Read redraw wall time and reentry cannot turn condition truth into service',JSON.stringify(await actual(url))===stable);
 states.complete=await act(page,url,'serve','east','east-fit-button');
 check('Explicit eligible East service pays before output and can complete at expiry boundary',states.complete.turn===4&&states.complete.coins===0&&states.complete.complete&&states.complete.benches.every(b=>b.delivered));
 await refusal(page,url,'serve','east','Actual acquired East fitting cannot be minted again');await page.screenshot({path:path.join(output,'ordered-actual-delivery.png'),fullPage:true});
 const expiryUrl=await start(web,'ordered'),expiry=await open(expiryUrl);await act(expiry,expiryUrl,'help','east','east-help-button');await act(expiry,expiryUrl,'wait',undefined,'wait');await act(expiry,expiryUrl,'help','west','west-help-button');states.expired=await act(expiry,expiryUrl,'serve','west','west-fit-button');
 check('Observed West output does not bypass expired East demonstration',states.expired.turn===4&&bench(states.expired,'west').delivered&&bench(states.expired,'east').helped&&!bench(states.expired,'east').recent&&!bench(states.expired,'east').condition_satisfied&&!bench(states.expired,'east').eligible);
 await refusal(expiry,expiryUrl,'serve','east','Expired ordered service refuses without coin turn or fitting');
 states.renewed=await act(expiry,expiryUrl,'demonstrate','east','east-help-button');check('Paid fresh demonstration can make full ordered condition true',states.renewed.turn===5&&states.renewed.parts===1&&bench(states.renewed,'east').condition_satisfied&&bench(states.renewed,'east').eligible&&!bench(states.renewed,'east').delivered);
 states.withdrawn=await act(expiry,expiryUrl,'decline','east','east-decline-button');check('Withdrawal keeps prior outputs but removes current required support',states.withdrawn.turn===5&&bench(states.withdrawn,'west').delivered&&!bench(states.withdrawn,'east').support&&!bench(states.withdrawn,'east').recent&&!bench(states.withdrawn,'east').condition_satisfied&&!bench(states.withdrawn,'east').delivered);
 await refusal(expiry,expiryUrl,'serve','east','True historical West delivery cannot replace withdrawn East support');await expiry.screenshot({path:path.join(output,'ordered-withdrawn-refusal.png'),fullPage:true});
 scratch=await fs.mkdtemp(path.join(os.tmpdir(),'conditions-render-mutants-'));
 for(const [id,target,replacement,message]of [
  ['false-eligible','const eligibleObserved = Boolean(b.eligible);',"const eligibleObserved = b.id==='east'?true:Boolean(b.eligible);",'Named eligibility picture follows actual owner'],
  ['false-delivered','const deliveredObserved = Boolean(b.delivered);',"const deliveredObserved = b.id==='east'?true:Boolean(b.delivered);",'Named fitting picture follows actual owner']]){
  const copy=path.join(scratch,id);await fs.cp(web,copy,{recursive:true});const file=path.join(copy,'app.js'),source=await fs.readFile(file,'utf8');assert.equal(source.split(target).length,2,'One declared mutation seam');const changed=source.replace(target,replacement);await fs.writeFile(file,changed);const u=await start(copy,'ordered'),p=await browser.newPage({viewport:{width:1280,height:1100}});await p.goto(u);await p.waitForFunction(()=>window.memoryStudy?.state&&window.memoryStudy.status==='ready');
  await p.evaluate(()=>window.memoryStudy.send('help','east'));const s=await actual(u);assert.equal(bench(s,'east').condition_satisfied,false);assert.equal(bench(s,'east').delivered,false);let detection;try{await fidelity(p,s);}catch(e){if(e.code!=='ERR_ASSERTION'||!e.message.includes(message))throw e;detection={name:e.name,code:e.code,message:e.message};}assert.ok(detection,'Specific actual renderer negative detected');negatives.push({id,detected:true,mutation:{target,replacement,original_sha256:hash(source),mutated_sha256:hash(changed)},actual:s,assertion:detection});check('Actual isolated '+id+' renderer is detected',true);await p.close();
 }
 const fieldUrl=await startField(),field=await browser.newPage({viewport:{width:1380,height:1160}});field.on('pageerror',e=>errors.push(e.message));await field.goto(fieldUrl);await field.waitForFunction(()=>window.fieldJourney?.state&&window.fieldJourney.status==='ready');
 async function fieldState(){const s=await actual(fieldUrl);assert.deepEqual(await field.evaluate(()=>window.fieldJourney.state),s,'Actual composed field observation');return s;}
 async function fieldAct(command,fields={},button){const before=await fieldState();if(button){await field.locator('#'+button).click();await field.waitForFunction(n=>window.fieldJourney?.state?.sequence>n&&window.fieldJourney.status==='ready',before.sequence);}else await field.evaluate(async({command,fields})=>window.fieldJourney.send(command,fields),{command,fields});return fieldState();}
 check('Actual field host passes ordered policy into its private Memory owner',(await fieldState()).memory.policy==='ordered');
 await fieldAct('review',{},'review');await fieldAct('confirm',{},'confirm');await fieldAct('help',{bench:'east'},'east-help');const fieldBefore=await fieldState();states.fieldRefusal=await fieldAct('serve',{bench:'east'});
 check('Actual field East service refuses ordered bypass without fitting or payment',!states.fieldRefusal.accepted&&states.fieldRefusal.memory.turn===fieldBefore.memory.turn&&states.fieldRefusal.memory.coins===fieldBefore.memory.coins&&!states.fieldRefusal.fittings.find(f=>f.bench==='east').acquired);
 await fieldAct('help',{bench:'west'},'west-help');await fieldAct('serve',{bench:'west'},'west-serve');states.fieldWindow=await fieldState();check('West field service can unlock East without fabricating its component',states.fieldWindow.memory.benches.find(b=>b.id==='east').condition_satisfied&&!states.fieldWindow.fittings.find(f=>f.bench==='east').acquired);
 await fieldAct('serve',{bench:'east'},'east-serve');for(const benchName of ['west','east']){await field.locator('#benchselect').selectOption(benchName);await field.locator('#fittingrig').selectOption('trail');await fieldAct('craft',{bench:benchName,rig:'trail'},'assemble');}
 states.fieldEntry=await fieldAct('begin',{rig:'trail'},'begin');check('Actual conditional components fund real assembly and consumed field entry',states.fieldEntry.workshop_closed&&states.fieldEntry.intake.state.active&&states.fieldEntry.intake.state.consumed_rigs===1&&states.fieldEntry.fittings.every(f=>f.acquired&&f.spent));
 const workshopTurn=states.fieldEntry.memory.turn;await fieldAct('walk',{},'walk');await fieldAct('slot',{slot:1},'use-slot1');await fieldAct('walk',{},'walk');states.fieldSurvey=await fieldAct('slot',{slot:1},'use-slot1');check('Actual ordered field survey remains distinct from final completion and workshop time',states.fieldSurvey.intake.state.won&&!states.fieldSurvey.intake.state.complete&&states.fieldSurvey.memory.turn===workshopTurn);await field.locator('.road').screenshot({path:path.join(output,'ordered-actual-field-survey.png')});
 check('No actual uncaught browser errors',errors.length===0);assert.deepEqual(await identities(),before);check('Actual consumer source closure remains stable',true);complete=true;
 await fs.writeFile(path.join(output,'browser.json'),JSON.stringify({schema_version:1,kind:'actual_browser_conditions_service',checks:{passed:controls.length,failed:0},http_checks:{passed:httpControls.length,failed:0},controls,http_controls:httpControls,states,negatives,source_sha256:before,source_stable:true,runtime:{node:process.version,chromium:browser.version(),playwright:require('playwright-core/package.json').version},limits:'Actual deterministic software controls overlap outcomes; not people, independent studies, full dialogue/scoring/quest catalogs, Ruby/RGSS/RMXP, Unity, Windows/Steam, human testimony, balance or commercial clearance.'},null,2)+'\n');console.log(`PASS: ${controls.length} actual condition-service Chromium and ${httpControls.length} HTTP controls`);
}catch(e){await fs.writeFile(path.join(output,'failure.json'),JSON.stringify({complete:false,error:{name:e.name,code:e.code??null,message:e.message,stack:e.stack},controls,http_controls:httpControls,states,source_sha256:before},null,2)+'\n');throw e;}finally{for(const child of children)await stop(child);await browser?.close();if(scratch)await fs.rm(scratch,{recursive:true,force:true});await fs.writeFile(path.join(output,'hosts.json'),JSON.stringify({complete,logs},null,2)+'\n');}
