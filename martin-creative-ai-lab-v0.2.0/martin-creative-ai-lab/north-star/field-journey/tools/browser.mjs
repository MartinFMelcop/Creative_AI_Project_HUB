import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';
import os from 'node:os';
import {spawn} from 'node:child_process';
import {createRequire} from 'node:module';
import {createServer} from 'node:net';
import {createHash} from 'node:crypto';
import {fileURLToPath} from 'node:url';

// Observe one real confirmed person and actual fitting custody through one journey.
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../../..');
const study=path.join(root,'north-star/field-journey'),web=path.join(study,'web');
const dotnet=process.argv[2],output=process.argv[3]&&path.resolve(process.argv[3]);
if(!dotnet||!output||output===root||output.startsWith(root+path.sep))throw Error('Usage: browser.mjs DOTNET NEW_OUTPUT_OUTSIDE_MAINTAINED_TREE');
const require=createRequire(path.join(root,'projects/realtime-integration-lab/package.json'));
const {chromium}=require('playwright-core');
const hash=data=>createHash('sha256').update(data).digest('hex');
async function files(directory){let names=[];for(const entry of await fs.readdir(directory,{withFileTypes:true})){if(['bin','obj','node_modules','__pycache__'].includes(entry.name))continue;const p=path.join(directory,entry.name);if(entry.isDirectory())names.push(...await files(p));else if(entry.isFile()&&/\.(cs|csproj|js|mjs|html|css|json|py)$/.test(p))names.push(p);}return names;}
async function identities(){const directories=['field-journey','intake','memory-study','csharp/Domain','csharp/Loadout','csharp/Forge','csharp/Crossing'];const names=(await Promise.all(directories.map(d=>files(path.join(root,'north-star',d))))).flat();names.push(path.join(root,'north-star/csharp/global.json'),path.join(root,'projects/realtime-integration-lab/package.json'),path.join(root,'projects/realtime-integration-lab/package-lock.json'));return Object.fromEntries(await Promise.all(names.sort().map(async p=>[path.relative(root,p),hash(await fs.readFile(p))])));}
const before=await identities(),controls=[],httpControls=[],states={},negatives=[],logs=[],children=[],errors=[];
let browser,scratch,complete=false;
function check(id,condition){assert.ok(condition,id);assert.ok(!controls.includes(id),'Unique browser control');controls.push(id);}
async function start(webroot){const server=createServer();await new Promise((resolve,reject)=>{server.once('error',reject);server.listen(0,'127.0.0.1',resolve);});const port=server.address().port;await new Promise(resolve=>server.close(resolve));const command=[path.join(study,'Host/bin/Release/net10.0/NorthStar.FieldJourney.dll'),'--serve',String(port),webroot,'--seconds','120'];const child=spawn(dotnet,command,{cwd:root,stdio:['ignore','pipe','pipe']});children.push(child);const log={command:[dotnet,...command],stdout:'',stderr:''};logs.push(log);child.stdout.on('data',b=>log.stdout+=b);child.stderr.on('data',b=>log.stderr+=b);child.on('error',e=>log.stderr+=e.message);for(let i=0;i<240&&!log.stdout.includes('READY');i++){if(child.exitCode!==null)throw Error(JSON.stringify(log));await new Promise(resolve=>setTimeout(resolve,25));}assert.match(log.stdout,/READY/,'Actual bounded C# host starts');return`http://127.0.0.1:${port}/`;}
async function stop(child){if(child.exitCode!==null||child.signalCode!==null)return;child.kill('SIGTERM');await Promise.race([new Promise(resolve=>child.once('exit',resolve)),new Promise(resolve=>setTimeout(resolve,1200))]);if(child.exitCode===null&&child.signalCode===null){child.kill('SIGKILL');await new Promise(resolve=>child.once('exit',resolve));}}
async function actual(url){const response=await fetch(url+'state',{signal:AbortSignal.timeout(5000)});assert.equal(response.status,200);return response.json();}
async function fidelity(page,s){
 assert.deepEqual(await page.evaluate(()=>window.fieldJourney.state),s,'Browser snapshot equals actual composed owner');
 assert.equal(await page.locator('body').getAttribute('data-complete'),String(Boolean(s.intake.state.complete)),'Overall completion follows actual Crossing');
 assert.equal(await page.locator('body').getAttribute('data-workshop-closed'),String(s.workshop_closed),'Workshop historical boundary follows actual departure');
 assert.equal((await page.locator('#confirmed-name').textContent()).trim(),s.intake.identity?.handle??'Not confirmed','Actual confirmed identity remains visible');
 assert.equal(Number(await page.locator('#workshop-turn').textContent()),s.memory.turn,'Separate workshop action turn follows owner');
 assert.equal(Number(await page.locator('#beat').textContent()),s.intake.state.beat,'Separate encounter beat follows owner');
 const stock=s.intake.state.inventory;const rigText=await page.locator('#rig-stock').textContent();assert.equal(rigText,`Actual stock: ${stock.trail_rig??0} Trail rigs · ${stock.plate_rig??0} Plate rigs`,'Actual assembled rig stock follows owner');
 assert.equal(Number(await page.locator('#consumed-rigs').textContent()),s.intake.state.consumed_rigs,'Actual consumed rig count follows owner');
 for(const f of s.fittings){
  const card=page.locator('#'+f.bench+'-fitting');
  for(const k of ['acquired','spent','available'])assert.equal(await card.getAttribute('data-'+k),String(f[k]),'Actual fitting '+k+' follows owner');
  const visible=await card.evaluate(el=>({available:getComputedStyle(el.querySelector('.fitting-available')).display!=='none',spent:getComputedStyle(el.querySelector('.fitting-spent')).display!=='none'}));
  assert.deepEqual(visible,{available:f.available,spent:f.spent},'Actual fitting SVG shows current custody');
 }
 const workers=await page.locator('.worker-live').evaluateAll(elements=>elements.map(e=>getComputedStyle(e).display!=='none'));
 assert.ok(workers.length>0,'Original workshop pictures exist');assert.ok(workers.every(visible=>visible===!s.workshop_closed),'Worker visibility cannot imply fresh remote presence');
 assert.equal(await page.locator('#notice').textContent(),s.text,'Actual composed receipt is rendered');
}
async function open(url){const page=await browser.newPage({viewport:{width:1380,height:1160}});page.on('pageerror',e=>errors.push(e.message));await page.goto(url);await page.waitForFunction(()=>window.fieldJourney?.state&&window.fieldJourney.status==='ready');await fidelity(page,await actual(url));return page;}
async function act(page,url,command,fields={},button){
 if(button){const prior=await actual(url);await page.locator('#'+button).click();await page.waitForFunction(n=>window.fieldJourney?.state?.sequence>n&&window.fieldJourney.status==='ready',prior.sequence);}
 else await page.evaluate(async({command,fields})=>window.fieldJourney.send(command,fields),{command,fields});
 const s=await actual(url);await fidelity(page,s);return s;
}
const fitting=(s,id)=>s.fittings.find(f=>f.bench===id);
const facts=s=>JSON.stringify({intake:s.intake.state,identity:s.intake.identity,memory:s.memory,workshop_closed:s.workshop_closed,fittings:s.fittings,assembly_receipts:s.assembly_receipts});
async function refusal(page,url,command,fields,id){const before=await actual(url),after=await act(page,url,command,fields);check(id,!after.accepted&&facts(before)===facts(after));negatives.push({id,before,after});return after;}
async function confirm(page,url,name){
 await page.locator('#handle').fill(name);await page.locator('#accent').selectOption('teal');await page.locator('#class_id').selectOption('lure');await page.locator('#background_id').selectOption('trailborn');await page.locator('#slot1').selectOption('draw');
 await act(page,url,'draft',{},'draft');await act(page,url,'review',{},'review');return act(page,url,'confirm',{},'confirm');
}
async function serve(page,url,bench){await act(page,url,'help',{bench},bench+'-help');return act(page,url,'serve',{bench},bench+'-serve');}
async function craft(page,url,bench){await page.locator('#benchselect').selectOption(bench);await page.locator('#fittingrig').selectOption('trail');return act(page,url,'craft',{bench,rig:'trail'},'assemble');}
async function begin(page,url,rig='trail'){await page.locator('#rig').selectOption(rig);return act(page,url,'begin',{rig},'begin');}
const survey=[['slot',{slot:1},'use-slot1'],['slot',{slot:1},'use-slot1'],['walk',{},'walk'],['slot',{slot:1},'use-slot1']];
const crossing=[['slot',{slot:1},'use-slot1'],['slot',{slot:1},'use-slot1'],['walk',{},'walk'],['slot',{slot:1},'use-slot1'],['walk',{},'walk'],['slot',{slot:1},'use-slot1']];
async function run(page,url,steps){let s;for(const [command,fields,button]of steps){s=await act(page,url,command,fields,button);assert.equal(s.accepted,true,'Actual journey '+command);}return s;}
await fs.mkdir(output,{recursive:false});
try{
 const url=await start(web);const invalid=[
  {id:'forged unused fitting',body:'{"command":"craft","revision":0,"bench":"west","rig":"trail","available":true}'},
  {id:'client child revision',body:'{"command":"help","revision":0,"bench":"west","memory_revision":0}'},
  {id:'duplicate command',body:'{"command":"review","command":"review","revision":0}'},
  {id:'unknown fitting provenance',body:'{"command":"craft","revision":0,"bench":"other","rig":"trail"}'},
  {id:'cross-origin',body:'{"command":"review","revision":0}',headers:{'Content-Type':'application/json',Origin:'http://untrusted.invalid'}},
  {id:'wrong media',body:'{"command":"review","revision":0}',headers:{'Content-Type':'text/plain'}},
  {id:'oversized body',body:' '.repeat(4097)}];
 for(const input of invalid){const prior=await actual(url);const response=await fetch(url+'command',{method:'POST',body:input.body,headers:input.headers??{'Content-Type':'application/json'},signal:AbortSignal.timeout(5000)});assert.equal(response.status,400,input.id);assert.deepEqual(await actual(url),prior,input.id+' cannot mutate either child');httpControls.push(input.id);}
 browser=await chromium.launch({executablePath:process.env.CHROMIUM_PATH||'/usr/bin/chromium',headless:true,args:['--no-sandbox']});const page=await open(url);states.initial=await actual(url);
 check('Original proposed person owns no acquired fitting or encounter',!states.initial.intake.confirmed&&!states.initial.workshop_closed&&states.initial.fittings.every(f=>!f.acquired&&!f.spent)&&states.initial.intake.state.attempts===0);
 await refusal(page,url,'help',{bench:'west'},'Unconfirmed person cannot spend workshop resources');states.confirmed=await confirm(page,url,'Neri');check('Actual form review and confirmation precede paid preparation',states.confirmed.accepted&&states.confirmed.intake.identity.handle==='Neri'&&states.confirmed.intake.identity.class_id==='lure'&&states.confirmed.memory.parts===4&&states.confirmed.intake.state.inventory.fiber===4);
 await refusal(page,url,'craft',{bench:'west',rig:'trail'},'Otherwise valid rig production needs actual acquired unused fitting');
 states.firstFitting=await serve(page,url,'west');check('Actual observed service acquires exactly west fitting',states.firstFitting.memory.turn===2&&states.firstFitting.memory.parts===3&&states.firstFitting.memory.coins===1&&fitting(states.firstFitting,'west').available&&!fitting(states.firstFitting,'east').acquired);
 await act(page,url,'wait-window',{},'wait-window');await act(page,url,'wait-window',{},'wait-window');await act(page,url,'decline',{bench:'west'},'west-decline');states.expired=await actual(url);
 check('Acquired fitting survives workshop recency expiry and withdrawal',!states.expired.memory.benches.find(b=>b.id==='west').recent&&!states.expired.memory.benches.find(b=>b.id==='west').support&&fitting(states.expired,'west').available);
 states.firstCraft=await craft(page,url,'west');check('Actual assembly allocates one fitting and spends existing fiber and binder',states.firstCraft.accepted&&fitting(states.firstCraft,'west').spent&&!fitting(states.firstCraft,'west').available&&states.firstCraft.intake.state.inventory.fiber===2&&states.firstCraft.intake.state.inventory.binder===1&&states.firstCraft.intake.state.inventory.trail_rig===1&&states.firstCraft.assembly_receipts.length===1);
 await refusal(page,url,'craft',{bench:'west',rig:'trail'},'Historical delivered receipt cannot allocate a second rig');
 await serve(page,url,'east');states.prepared=await craft(page,url,'east');check('Both service receipts and spent fittings are preparation not Crossing completion',states.prepared.memory.complete&&states.prepared.fittings.every(f=>f.acquired&&f.spent)&&!states.prepared.intake.state.complete&&states.prepared.intake.state.attempts===0&&states.prepared.intake.state.inventory.trail_rig===2);
 await page.screenshot({path:path.join(output,'two-allocated-fittings.png'),fullPage:true});
 const unchanged=JSON.stringify(await actual(url));await page.waitForTimeout(120);await page.reload();await page.waitForFunction(()=>window.fieldJourney?.state&&window.fieldJourney.status==='ready');await fidelity(page,await actual(url));check('Reads redraw and wall time cannot recreate fitting custody or produce victory',JSON.stringify(await actual(url))===unchanged);
 states.departed=await begin(page,url);const departureTurn=states.departed.memory.turn;
 check('First actual prepared entry consumes rig and permanently closes workshop',states.departed.accepted&&states.departed.workshop_closed&&states.departed.intake.state.active&&states.departed.intake.state.inventory.trail_rig===1&&states.departed.intake.state.consumed_rigs===1);
 states.survey=await run(page,url,survey);check('Survey victory preserves named person and historical workshop without final completion',states.survey.intake.identity.handle==='Neri'&&states.survey.intake.state.won&&!states.survey.intake.state.complete&&!states.survey.intake.state.active&&states.survey.memory.turn===departureTurn&&states.survey.workshop_closed);
 await refusal(page,url,'wait-window',{},'Between encounters cannot reopen historical workshop or advance its clock');
 await begin(page,url);states.complete=await run(page,url,crossing);check('Actual harder encounter completes with two allocated fittings and two consumed rigs',states.complete.intake.state.complete&&states.complete.intake.state.won&&states.complete.intake.state.consumed_rigs===2&&states.complete.fittings.every(f=>f.spent)&&states.complete.intake.identity.handle==='Neri'&&states.complete.memory.turn===departureTurn);
 await page.screenshot({path:path.join(output,'actual-named-completion.png'),fullPage:true});
 const earlyUrl=await start(web),early=await open(earlyUrl);await confirm(early,earlyUrl,'Ivo');await serve(early,earlyUrl,'west');await craft(early,earlyUrl,'west');await begin(early,earlyUrl);states.earlySurvey=await run(early,earlyUrl,survey);
 check('Premature departure can finish survey with east fitting never acquired',states.earlySurvey.intake.state.won&&!states.earlySurvey.intake.state.complete&&!fitting(states.earlySurvey,'east').acquired&&states.earlySurvey.intake.state.inventory.trail_rig===0);
 await refusal(early,earlyUrl,'help',{bench:'east'},'An unfunded later stage cannot manufacture remote workshop help');
 states.unfunded=await refusal(early,earlyUrl,'begin',{rig:'trail'},'Consumed first rig leaves harder prepared entry unfunded');await early.screenshot({path:path.join(output,'premature-unfunded.png'),fullPage:true});
 const lossUrl=await start(web),loss=await open(lossUrl);await confirm(loss,lossUrl,'Sela');await serve(loss,lossUrl,'west');await craft(loss,lossUrl,'west');await begin(loss,lossUrl);for(let n=0;n<20&&(await actual(lossUrl)).intake.state.active;n++)states.loss=await act(loss,lossUrl,'wait',{},'wait');
 check('Actual losing contact policy retains spent fitting and consumed rig without reward',!states.loss.intake.state.active&&!states.loss.intake.state.won&&!states.loss.intake.state.complete&&states.loss.intake.state.xp===0&&fitting(states.loss,'west').spent&&states.loss.intake.state.consumed_rigs===1&&states.loss.intake.state.inventory.trail_rig===0);
 await refusal(loss,lossUrl,'craft',{bench:'west',rig:'trail'},'Actual loss cannot refund allocation into another rig');await loss.screenshot({path:path.join(output,'actual-loss-no-refund.png'),fullPage:true});
 // Isolate an actual picture mutation after real allocation; historical acquisition stays true.
 scratch=await fs.mkdtemp(path.join(os.tmpdir(),'field-fitting-mutant-'));const copy=path.join(scratch,'web');await fs.cp(web,copy,{recursive:true});const file=path.join(copy,'app.js'),source=await fs.readFile(file,'utf8'),target='const availableObserved = Boolean(f.available);';assert.equal(source.split(target).length,2,'One declared false available-fitting target');const changed=source.replace(target,'const availableObserved = Boolean(f.acquired);');await fs.writeFile(file,changed);
 const mutantUrl=await start(copy),mutant=await browser.newPage({viewport:{width:1380,height:1160}});await mutant.goto(mutantUrl);await mutant.waitForFunction(()=>window.fieldJourney?.state&&window.fieldJourney.status==='ready');
 // Operate through actual owner commands without invoking fidelity until the allocated state.
 async function raw(command,fields={}){await mutant.evaluate(async({command,fields})=>window.fieldJourney.send(command,fields),{command,fields});}
 await raw('review');await raw('confirm',{draft_revision:(await actual(mutantUrl)).intake.draft_revision});await raw('help',{bench:'west'});await raw('serve',{bench:'west'});await raw('craft',{bench:'west',rig:'trail'});
 const observed=await actual(mutantUrl);assert.ok(fitting(observed,'west').acquired&&fitting(observed,'west').spent&&!fitting(observed,'west').available);let detection;
 try{await fidelity(mutant,observed);}catch(e){if(e.code!=='ERR_ASSERTION'||!e.message.includes('Actual fitting available follows owner'))throw e;detection={name:e.name,code:e.code,message:e.message};}
 assert.ok(detection,'Historical acquired-as-available renderer must be rejected');negatives.push({id:'historical-fitting-reused-by-renderer',detected:true,actual:observed,mutation:{target,replacement:'const availableObserved = Boolean(f.acquired);',original_sha256:hash(source),mutated_sha256:hash(changed)},assertion:detection});check('Actual isolated acquired-as-unused renderer is detected after real allocation',true);await mutant.close();
 // A complete workshop means two actual acquisitions, never completed Crossing.
 const completionCopy=path.join(scratch,'completion-web');await fs.cp(web,completionCopy,{recursive:true});const completionFile=path.join(completionCopy,'app.js'),completionSource=await fs.readFile(completionFile,'utf8'),completionTarget='const completeObserved = Boolean(s.intake.state.complete);';assert.equal(completionSource.split(completionTarget).length,2,'One declared false overall-completion target');const completionChanged=completionSource.replace(completionTarget,'const completeObserved = Boolean(s.memory.complete);');await fs.writeFile(completionFile,completionChanged);
 const completionUrl=await start(completionCopy),completionPage=await browser.newPage({viewport:{width:1380,height:1160}});await completionPage.goto(completionUrl);await completionPage.waitForFunction(()=>window.fieldJourney?.state&&window.fieldJourney.status==='ready');
 async function rawComplete(command,fields={}){await completionPage.evaluate(async({command,fields})=>window.fieldJourney.send(command,fields),{command,fields});}
 await rawComplete('review');await rawComplete('confirm',{draft_revision:(await actual(completionUrl)).intake.draft_revision});for(const bench of ['west','east']){await rawComplete('help',{bench});await rawComplete('serve',{bench});}
 const completionActual=await actual(completionUrl);assert.ok(completionActual.memory.complete&&!completionActual.intake.state.complete&&completionActual.intake.state.attempts===0);let completionDetection;
 try{await fidelity(completionPage,completionActual);}catch(e){if(e.code!=='ERR_ASSERTION'||!e.message.includes('Overall completion follows actual Crossing'))throw e;completionDetection={name:e.name,code:e.code,message:e.message};}
 assert.ok(completionDetection,'Workshop-acquisition-as-road-completion renderer must be rejected');negatives.push({id:'workshop-acquisition-as-road-completion',detected:true,actual:completionActual,mutation:{target:completionTarget,replacement:'const completeObserved = Boolean(s.memory.complete);',original_sha256:hash(completionSource),mutated_sha256:hash(completionChanged)},assertion:completionDetection});check('Actual isolated workshop-complete-as-road-complete renderer is detected',true);await completionPage.close();
 check('Actual browser has no uncaught script errors',errors.length===0);assert.deepEqual(await identities(),before,'Actual source closure remains stable');check('Actual composed consumer and all referenced owner identities remain exact',true);complete=true;
 await fs.writeFile(path.join(output,'browser.json'),JSON.stringify({schema_version:1,kind:'actual_browser_fitting_owned_journey',checks:{passed:controls.length,failed:0},http_checks:{passed:httpControls.length,failed:0},controls,http_controls:httpControls,states,negatives,source_sha256:before,source_stable:true,runtime:{node:process.version,chromium:browser.version(),playwright:require('playwright-core/package.json').version},limits:'One original composition per ephemeral host of unchanged intake, memory and prepared-expedition owners. Synthetic controls overlap outcomes; no participant, independent population study, new source consumption, full creation, persistence, Unity, Windows, Steam or human experience.'},null,2)+'\n');console.log(`PASS: ${controls.length} field journey Chromium and ${httpControls.length} HTTP controls`);
}catch(e){await fs.writeFile(path.join(output,'failure.json'),JSON.stringify({complete:false,error:{name:e.name,code:e.code??null,message:e.message,stack:e.stack},controls,http_controls:httpControls,states,source_sha256:before},null,2)+'\n');throw e;}finally{for(const child of children)await stop(child);await browser?.close();if(scratch)await fs.rm(scratch,{recursive:true,force:true});await fs.writeFile(path.join(output,'hosts.json'),JSON.stringify({complete,logs},null,2)+'\n');}
