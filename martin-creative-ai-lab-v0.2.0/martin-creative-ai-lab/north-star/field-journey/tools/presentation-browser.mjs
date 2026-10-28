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
async function baseFidelity(page,s){
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
async function fidelity(page,s){
 await baseFidelity(page,s);const v=s.encounter_view,p=v.person,e=v.encounter,a=v.action;const actor=page.locator('#field-actor'),board=page.locator('#field-encounter-board');
 assert.equal(await actor.getAttribute('data-handle'),p.handle??'','Actual actor identity');
 assert.equal(await actor.getAttribute('data-rig'),p.rig,'Actual actor rig');assert.equal(await actor.getAttribute('data-class'),p.class_id??'');assert.equal(await actor.getAttribute('data-accent'),p.accent??'copper');
 assert.equal(await board.getAttribute('data-complete'),String(e.complete),'Actual encounter completion');assert.equal(await board.getAttribute('data-threshold-reached'),String(e.threshold_reached));assert.equal(await board.getAttribute('data-threat'),e.threat_kind);
 assert.equal(await actor.getAttribute('data-contact'),a.contact);assert.equal(await actor.getAttribute('data-event-sequence'),String(a.event_sequence));assert.equal(await actor.getAttribute('data-kind'),a.kind);
 assert.equal(await page.locator('#field-actor-shape').getAttribute('transform'),`translate(${85+830*e.position/e.world_end} 320)`,'Position uses full display bound');
 const visibility=await actor.evaluate(el=>Object.fromEntries(['field-plate','field-trail','field-anchor','field-lure','field-contact-hurt','field-contact-protected','field-contact-evaded'].map(c=>[c,getComputedStyle(el.querySelector('.'+c)).display!=='none'])));
 assert.deepEqual(visibility,{'field-plate':p.rig==='plate','field-trail':p.rig==='trail','field-anchor':p.class_id==='anchor','field-lure':p.class_id==='lure','field-contact-hurt':a.contact==='hurt','field-contact-protected':a.contact==='protected','field-contact-evaded':a.contact==='evaded'});
 const color={teal:'#5c9997',copper:'#ae794f',violet:'#9b88b1'};assert.equal(await page.locator('#field-cloth').getAttribute('fill'),color[p.accent]??color.copper);
 const response=await page.locator('#field-response').textContent();if(['walk','dash','skill','wait'].includes(a.kind))for(const text of [`HP lost ${a.health_lost}`,`resolve spent ${a.resolve_spent}`,`gained ${a.resolve_gained}`,`contact ${a.contact}`])assert.ok(response.includes(text),text);
 if(e.active&&e.threshold_reached){assert.match(await page.locator('#field-threshold-note').textContent(),/actual beats remain/);assert.equal(await board.getAttribute('data-complete'),'false');}
}
await fs.mkdir(output,{recursive:false});
try{
 const url=await start(web);browser=await chromium.launch({executablePath:process.env.CHROMIUM_PATH||'/usr/bin/chromium',headless:true,args:['--no-sandbox']});const page=await open(url);
 check('Unconfirmed actor is not depicted as a confirmed person',await page.locator('#field-actor').evaluate(el=>getComputedStyle(el).display==='none'));
 await confirm(page,url,'Neri');check('Same confirmed identity and cosmetic accent reach the actual board',(await actual(url)).encounter_view.person.handle==='Neri');
 for(const bench of ['west','east']){await serve(page,url,bench);await craft(page,url,bench);}
 await begin(page,url);check('Actual acquired Trail entry supplies the depicted outfit',(await actual(url)).encounter_view.person.rig==='trail');
 await refusal(page,url,'slot',{slot:4},'Empty slot refuses without an accepted encounter response');check('Refusal has no damage cost movement or new event',(await actual(url)).encounter_view.action.kind==='refused'&&(await actual(url)).encounter_view.action.event_sequence===0);
 states.first=await act(page,url,'slot',{slot:1},'use-slot1');check('Actual Lure response spends resolve and protects actual bolt',states.first.encounter_view.action.contact==='protected'&&states.first.encounter_view.action.resolve_spent===3&&states.first.encounter_view.action.to_position===1);
 states.threshold=await act(page,url,'slot',{slot:1},'use-slot1');check('Survey position threshold stays active while two actual beats remain',states.threshold.encounter_view.encounter.threshold_reached&&states.threshold.encounter_view.encounter.active&&!states.threshold.encounter_view.encounter.complete&&states.threshold.encounter_view.encounter.beat===2);await page.locator('#field-encounter-board').screenshot({path:path.join(output,'threshold-not-complete.png')});
 states.evaded=await act(page,url,'walk',{},'walk');check('Actual pulse movement evades and reports resolve gained',states.evaded.encounter_view.action.contact==='evaded'&&states.evaded.encounter_view.action.resolve_gained===2);
 states.survey=await act(page,url,'slot',{slot:1},'use-slot1');check('Ended survey keeps its actual resolved objective apart from next owner stage',states.survey.encounter_view.encounter.phase==='survey-won'&&states.survey.encounter_view.encounter.stage===0&&states.survey.encounter_view.encounter.owner_stage===1&&!states.survey.encounter_view.encounter.complete);
 await begin(page,url);await run(page,url,crossing);states.complete=await actual(url);check('Same actual person and used outfit complete both owned encounters',states.complete.encounter_view.encounter.complete&&states.complete.encounter_view.person.handle==='Neri'&&states.complete.intake.state.consumed_rigs===2);await page.locator('#field-encounter-board').screenshot({path:path.join(output,'actual-same-person-complete.png')});
 const last=JSON.stringify(await actual(url));await page.waitForTimeout(150);await page.reload();await page.waitForFunction(()=>window.fieldJourney?.status==='ready');await fidelity(page,await actual(url));check('Reads elapsed time and reentry retain exact facts and event identity',JSON.stringify(await actual(url))===last);
 const lossUrl=await start(web),loss=await open(lossUrl);await confirm(loss,lossUrl,'Sela');await serve(loss,lossUrl,'west');await craft(loss,lossUrl,'west');await begin(loss,lossUrl);states.hurt=await act(loss,lossUrl,'wait',{},'wait');check('Actual damaging wait depicts harm not protection',states.hurt.encounter_view.action.health_lost===4&&states.hurt.encounter_view.action.contact==='hurt');
 while((await actual(lossUrl)).intake.state.active)await act(loss,lossUrl,'wait',{},'wait');states.loss=await actual(lossUrl);check('Actual loss retains spent rig and depicts no invented victory',states.loss.encounter_view.encounter.phase==='failed'&&!states.loss.encounter_view.encounter.complete&&states.loss.intake.state.consumed_rigs===1);await loss.locator('#field-encounter-board').screenshot({path:path.join(output,'actual-harm-and-loss.png')});
 scratch=await fs.mkdtemp(path.join(os.tmpdir(),'field-picture-negative-'));
 for(const [id,target,replacement,message]of [['false-complete','const fieldCompleteObserved = v.encounter.complete;','const fieldCompleteObserved = true;','Actual encounter completion'],['false-person','const fieldHandleObserved = v.person.handle;','const fieldHandleObserved = "Another person";','Actual actor identity']]){
  const copy=path.join(scratch,id);await fs.cp(web,copy,{recursive:true});const file=path.join(copy,'app.js'),source=await fs.readFile(file,'utf8');assert.equal(source.split(target).length,2);const changed=source.replace(target,replacement);await fs.writeFile(file,changed);const u=await start(copy),p=await browser.newPage();await p.goto(u);await p.waitForFunction(()=>window.fieldJourney?.status==='ready');await p.evaluate(async()=>{await window.fieldJourney.send('review');await window.fieldJourney.send('confirm',{draft_revision:window.fieldJourney.state.intake.draft_revision});});assert.equal((await actual(u)).encounter_view.person.confirmed,true);let detection;try{await fidelity(p,await actual(u));}catch(e){if(e.code!=='ERR_ASSERTION'||!e.message.includes(message))throw e;detection={message:e.message,code:e.code};}assert.ok(detection,'Specific false renderer detected');negatives.push({id,detected:true,mutation:{target,replacement,original_sha256:hash(source),mutated_sha256:hash(changed)},assertion:detection,actual:await actual(u)});check('Actual isolated '+id+' renderer is detected',true);await p.close();
 }
 check('No uncaught actual page errors',errors.length===0);assert.deepEqual(await identities(),before);check('Actual source closure stays stable',true);
 await fs.writeFile(path.join(output,'browser.json'),JSON.stringify({schema_version:1,checks:{passed:controls.length,failed:0},controls,states,negatives,source_sha256:before,source_stable:true,runtime:{node:process.version,chromium:browser.version(),playwright:require('playwright-core/package.json').version},limits:'Overlapping actual software controls, not human recognition, comprehension, balance, source integration, Unity, new Windows or Steam.'},null,2)+'\n');console.log(`PASS: ${controls.length} actual encounter presentation controls`);
}catch(e){await fs.writeFile(path.join(output,'failure.json'),JSON.stringify({error:{message:e.message,stack:e.stack},controls,states,source_sha256:before},null,2)+'\n');throw e;}finally{for(const child of children)await stop(child);await browser?.close();if(scratch)await fs.rm(scratch,{recursive:true,force:true});await fs.writeFile(path.join(output,'hosts.json'),JSON.stringify(logs,null,2)+'\n');}
