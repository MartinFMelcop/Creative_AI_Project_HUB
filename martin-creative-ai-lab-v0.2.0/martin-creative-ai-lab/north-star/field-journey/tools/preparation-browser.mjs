import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';
import os from 'node:os';
import {spawn} from 'node:child_process';
import {createRequire} from 'node:module';
import {createServer} from 'node:net';
import {createHash} from 'node:crypto';
import {fileURLToPath} from 'node:url';

// Observe strict authored content through the existing proposal and gameplay owners.
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../../..');
const study=path.join(root,'north-star/field-journey'),web=path.join(study,'web');
const dotnet=process.argv[2],output=process.argv[3]&&path.resolve(process.argv[3]);
if(!dotnet||!output||output===root||output.startsWith(root+path.sep))throw Error('Usage: browser.mjs DOTNET NEW_OUTPUT_OUTSIDE_MAINTAINED_TREE');
const require=createRequire(path.join(root,'projects/realtime-integration-lab/package.json'));
const {chromium}=require('playwright-core');
const hash=data=>createHash('sha256').update(data).digest('hex');
async function files(directory){let names=[];for(const entry of await fs.readdir(directory,{withFileTypes:true})){if(['bin','obj','node_modules','__pycache__'].includes(entry.name))continue;const p=path.join(directory,entry.name);if(entry.isDirectory())names.push(...await files(p));else if(entry.isFile()&&/\.(cs|csproj|js|mjs|html|css|json|py)$/.test(p))names.push(p);}return names;}
async function identities(){const directories=['field-journey','intake','memory-study','csharp/Domain','csharp/Portable','csharp/Loadout','csharp/Forge','csharp/Crossing'];const names=(await Promise.all(directories.map(d=>files(path.join(root,'north-star',d))))).flat();names.push(path.join(root,'evidence/preparation-authoring/protocol.json'),path.join(root,'north-star/csharp/global.json'),path.join(root,'projects/realtime-integration-lab/package.json'),path.join(root,'projects/realtime-integration-lab/package-lock.json'));return Object.fromEntries(await Promise.all(names.sort().map(async p=>[path.relative(root,p),hash(await fs.readFile(p))])));}
const before=await identities(),controls=[],httpControls=[],trace=[],states={},negatives=[],logs=[],children=[],errors=[];
let browser,scratch,complete=false;
function check(id,condition){assert.ok(condition,id);assert.ok(!controls.includes(id),'Unique browser control');controls.push(id);}
async function port(){const server=createServer();await new Promise((resolve,reject)=>{server.once('error',reject);server.listen(0,'127.0.0.1',resolve);});const p=server.address().port;await new Promise(resolve=>server.close(resolve));return p;}
async function launch(webroot,pack=null){const p=await port();const command=[path.join(study,'Host/bin/Release/net10.0/NorthStar.FieldJourney.dll'),'--serve',String(p),webroot,'--seconds','180'];if(pack)command.push('--preparations',pack);const child=spawn(dotnet,command,{cwd:root,stdio:['ignore','pipe','pipe']});children.push(child);const log={command:[dotnet,...command],stdout:'',stderr:''};logs.push(log);child.stdout.on('data',b=>log.stdout+=b);child.stderr.on('data',b=>log.stderr+=b);child.on('error',e=>log.stderr+=e.message);return{child,log,url:`http://127.0.0.1:${p}/`};}
async function start(webroot,pack=null){const host=await launch(webroot,pack);for(let i=0;i<240&&!host.log.stdout.includes('READY');i++){if(host.child.exitCode!==null)throw Error(JSON.stringify(host.log));await new Promise(resolve=>setTimeout(resolve,25));}assert.match(host.log.stdout,/READY/,'Actual bounded C# host starts');return host.url;}
async function refusedStartup(id,file){const {child,log}=await launch(web,file);await Promise.race([new Promise(resolve=>child.once('exit',resolve)),new Promise((_,reject)=>setTimeout(()=>reject(Error('Bad-content host did not refuse within5s')),5000))]);assert.ok(child.exitCode!==0||child.signalCode!==null,'Malformed book rejected');assert.ok(!log.stdout.includes('READY'),'No listener exposed before whole-book validation');return{id,detected:true,exit_code:child.exitCode,signal:child.signalCode,stderr:log.stderr};}
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
 const s=await actual(url);trace.push({command,fields,state:s});await fidelity(page,s);return s;
}
const fitting=(s,id)=>s.fittings.find(f=>f.bench===id);
const facts=s=>JSON.stringify({sample_case:s.sample_case,intake:s.intake.state,identity:s.intake.identity,memory:s.memory,workshop_closed:s.workshop_closed,fittings:s.fittings,assembly_receipts:s.assembly_receipts});
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
 await baseFidelity(page,s);const book=s.preparation_book;assert.ok(book&&Array.isArray(book.cards));
 assert.equal(await page.locator('#preparation-book').getAttribute('data-draft-card'),book.draft_card_id||'','Actual draft preparation source');
 assert.equal(await page.locator('#preparation-book').getAttribute('data-confirmed-card'),book.confirmed_card_id||'','Actual confirmed preparation source');
 const names=await page.locator('#preparation-cards article').evaluateAll(nodes=>nodes.map(n=>n.dataset.cardId));assert.deepEqual(names,book.cards.map(c=>c.id),'Actual authored card identities');
 for(const card of book.cards){const node=page.locator(`#preparation-cards article[data-card-id="${card.id}"]`);assert.equal(await node.getAttribute('data-minimum-level'),String(card.minimum_level));assert.equal(await page.locator('#propose-card-'+card.id).isEnabled(),card.eligible,'Actual earned-card eligibility');const text=await node.textContent();for(const literal of [card.title,card.description,card.class_id,card.background_id,card.slots.map(x=>x||'empty').join(' / '),card.recommended_rig])assert.ok(text.includes(literal),'Exact authored content is rendered');}
}
const childFacts=s=>JSON.stringify({intake:s.intake,memory:s.memory,fittings:s.fittings,assembly_receipts:s.assembly_receipts,sample:s.sample_case});
async function propose(page,url,id,button=true){return act(page,url,'propose-card',{card_id:id},button?'propose-card-'+id:null);}
async function confirmCurrent(page,url){await act(page,url,'review',{},'review');return act(page,url,'confirm',{},'confirm');}
async function supplies(page,url){for(const b of ['west','east']){await serve(page,url,b);await craft(page,url,b);}}
async function raw(url,command,fields={}){const prior=await actual(url);const r=await fetch(url+'command',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({command,revision:prior.sequence,...fields}),signal:AbortSignal.timeout(5000)});assert.equal(r.status,200);const s=await r.json();trace.push({raw:true,command,fields,state:s});return s;}
await fs.mkdir(output,{recursive:false});
try{
 browser=await chromium.launch({executablePath:process.env.CHROMIUM_PATH||'/usr/bin/chromium',headless:true,args:['--no-sandbox']});scratch=await fs.mkdtemp(path.join(os.tmpdir(),'preparation-content-'));
 const rawBook=await fs.readFile(path.join(study,'preparations.json')),book=JSON.parse(rawBook);
 const url=await start(web),page=await open(url),initial=await actual(url);
 check('Startup exposes the exact original book identity and four cards',initial.preparation_book.sha256===hash(rawBook)&&initial.preparation_book.cards.length===4&&!initial.intake.confirmed&&initial.intake.state.xp===0&&initial.intake.state.attempts===0);
 const early=childFacts(initial);await refusal(page,url,'propose-card',{card_id:'lure-dash'},'An early earned Dash card refuses without actual gameplay mutation');check('Early card refusal leaves all child observations exact',childFacts(await actual(url))===early);
 const prior=await actual(url);states.proposed=await propose(page,url,'lure-start');
 check('Actual base-card button proposes a full draft without confirming it',states.proposed.intake.draft.class_id==='lure'&&states.proposed.intake.draft.slots[0]==='draw'&&!states.proposed.intake.confirmed&&states.proposed.preparation_book.draft_card_id==='lure-start'&&states.proposed.preparation_book.confirmed_card_id===null);
 check('Proposal cannot grant resources start an encounter or change the current owner',JSON.stringify(states.proposed.intake.state)===JSON.stringify(prior.intake.state)&&JSON.stringify(states.proposed.memory)===JSON.stringify(prior.memory));
 await refusal(page,url,'confirm',{draft_revision:states.proposed.intake.draft_revision},'Unreviewed actual card cannot become confirmed preparation');
 await page.locator('#preparation-book').screenshot({path:path.join(output,'proposed-not-confirmed.png')});
 states.confirmed=await confirmCurrent(page,url);check('Explicit review and confirmation commit actual card preparation',states.confirmed.intake.confirmed&&states.confirmed.intake.identity.class_id==='lure'&&states.confirmed.intake.state.slots[0]==='draw'&&states.confirmed.preparation_book.confirmed_card_id==='lure-start');
 await supplies(page,url);await begin(page,url);await run(page,url,survey);states.survey=await actual(url);check('Confirmed authored card spends actual rigs and earns survey progression',states.survey.intake.state.won&&!states.survey.intake.state.complete&&states.survey.intake.state.level===2&&states.survey.intake.state.xp===10&&states.survey.intake.state.consumed_rigs===1);
 const beforeAmend=await actual(url);states.amendment=await propose(page,url,'lure-dash');check('Actually earned level unlocks proposed Dash without applying it',states.amendment.intake.pending&&states.amendment.intake.draft.slots[1]==='dash'&&states.amendment.intake.state.slots[1]===null&&states.amendment.preparation_book.confirmed_card_id==='lure-start');
 check('Earned proposal cannot heal refund or grant XP',JSON.stringify(states.amendment.intake.state)===JSON.stringify(beforeAmend.intake.state));
 const reviewed=await act(page,url,'review',{},'review');await propose(page,url,'lure-start');check('Changing authored draft expires the exact old review',(await actual(url)).intake.reviewed_revision===null);await refusal(page,url,'confirm',{draft_revision:reviewed.intake.draft_revision},'Superseded reviewed card cannot confirm after a new proposal');
 await propose(page,url,'lure-dash');states.amended=await confirmCurrent(page,url);check('Actual confirmation equips earned Dash without changing health XP or stock',states.amended.intake.state.slots[1]==='dash'&&states.amended.preparation_book.confirmed_card_id==='lure-dash'&&states.amended.intake.state.health===beforeAmend.intake.state.health&&states.amended.intake.state.xp===10);
 await page.locator('#preparation-book').screenshot({path:path.join(output,'earned-amendment.png')});await begin(page,url);states.dash=await act(page,url,'slot',{slot:2},'use-slot2');check('Actually equipped authored Dash executes the unchanged paid action',states.dash.intake.state.position===2&&states.dash.encounter_view.action.kind==='dash'&&states.dash.encounter_view.action.resolve_spent===1&&states.dash.encounter_view.action.health_lost===6);
 const stable=JSON.stringify(await actual(url));await page.waitForTimeout(100);await page.reload();await page.waitForFunction(()=>window.fieldJourney?.status==='ready');await fidelity(page,await actual(url));check('Reload and elapsed time cannot reapply a card or alter actual state',JSON.stringify(await actual(url))===stable);
 // A separately authored content variant changes real slots with the SAME compiled host.
 const variant=JSON.parse(rawBook);variant.cards.find(c=>c.id==='lure-start').slots=[null,'draw',null,null];const variantBytes=Buffer.from(JSON.stringify(variant,null,2)+'\n');const variantPath=path.join(scratch,'variant.json');await fs.writeFile(variantPath,variantBytes);await fs.writeFile(path.join(output,'valid-variant.json'),variantBytes);
 const vu=await start(web,variantPath),vp=await open(vu);check('Separate valid content has its exact distinct active identity',(await actual(vu)).preparation_book.sha256===hash(variantBytes)&&hash(variantBytes)!==hash(rawBook));await propose(vp,vu,'lure-start');await confirmCurrent(vp,vu);await supplies(vp,vu);await begin(vp,vu);await refusal(vp,vu,'slot',{slot:1},'Authored empty slot1 refuses through the real owner');states.variant=await act(vp,vu,'slot',{slot:2},'use-slot2');check('Content-only slot change drives actual slot2 Draw with unchanged engine',states.variant.intake.state.slots[0]===null&&states.variant.intake.state.slots[1]==='draw'&&states.variant.intake.state.position===1&&states.variant.encounter_view.action.kind==='skill'&&states.variant.encounter_view.action.resolve_spent===3);await vp.locator('#preparation-book').screenshot({path:path.join(output,'actual-content-variant.png')});
 const malformed=[];
 function bad(id,edit){const obj=JSON.parse(rawBook);edit(obj);malformed.push([id,JSON.stringify(obj)]);}
 bad('missing-cards',o=>delete o.cards);bad('duplicate-card-id',o=>o.cards.push({...o.cards[0]}));bad('unknown-root-field',o=>o.xp=100);bad('unsupported-class',o=>o.cards[0].class_id='unknown');bad('premature-dash',o=>o.cards.find(c=>c.id==='lure-dash').minimum_level=1);bad('unsupported-resource-grant',o=>o.cards[1].gold=200);bad('wrong-slot-count',o=>o.cards[1].slots=['draw']);bad('wrong-integer-type',o=>o.cards[0].minimum_level='1');malformed.push(['duplicate-json-field',rawBook.toString().replace('"schema_version": 1','"schema_version": 1, "schema_version": 1')]);
 for(const [id,bytes]of malformed){const file=path.join(scratch,id+'.json');await fs.writeFile(file,bytes);const result=await refusedStartup(id,file);result.source_sha256=hash(bytes);result.source=bytes;negatives.push(result);check('Whole invalid pack refuses before READY: '+id,true);}
 // The actual browser receives a false proposed-as-confirmed renderer after real manual confirmation.
 const copy=path.join(scratch,'false-confirmed');await fs.cp(web,copy,{recursive:true});const file=path.join(copy,'app.js'),src=await fs.readFile(file,'utf8');const target='const confirmedCardObserved = s.preparation_book.confirmed_card_id;',replacement='const confirmedCardObserved = s.preparation_book.draft_card_id;';assert.equal(src.split(target).length,2);const changed=src.replace(target,replacement);await fs.writeFile(file,changed);const mu=await start(copy);await raw(mu,'review');await raw(mu,'confirm',{draft_revision:(await actual(mu)).intake.draft_revision});await raw(mu,'propose-card',{card_id:'lure-start'});const mp=await browser.newPage();await mp.goto(mu);await mp.waitForFunction(()=>window.fieldJourney?.status==='ready');let detected;try{await fidelity(mp,await actual(mu));}catch(e){if(e.code!=='ERR_ASSERTION'||!e.message.includes('Actual confirmed preparation source'))throw e;detected=e.message;}assert.ok(detected,'Actual false confirmed source detected');negatives.push({id:'false-confirmed-renderer',detected,original_sha256:hash(src),mutated_sha256:hash(changed),target,replacement,actual:await actual(mu)});check('Actual proposed-as-confirmed renderer is rejected',true);await mp.close();
 for(const [id,payload]of [['forged-card-state',{command:'propose-card',revision:0,card_id:'lure-start',confirmed:true}],['unknown-card',{command:'propose-card',revision:(await actual(url)).sequence,card_id:'missing'}]]){const beforeState=JSON.stringify(await actual(url));const response=await fetch(url+'command',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});assert.equal(response.status,400);assert.equal(JSON.stringify(await actual(url)),beforeState);httpControls.push(id);}
 check('No uncaught browser errors',errors.length===0);assert.deepEqual(await identities(),before);check('Actual authoring source closure stable',true);
 await fs.writeFile(path.join(output,'browser.json'),JSON.stringify({schema_version:1,checks:{passed:controls.length,failed:0},http_checks:httpControls,controls,states,trace,negatives,source_sha256:before,source_stable:true,runtime:{node:process.version,chromium:browser.version(),playwright:require('playwright-core/package.json').version},limits:'Overlapping actual software controls, not people, author productivity, validated build diversity, historical Ruby/creation integration, approved canon or Unity/Windows/Steam.'},null,2)+'\n');console.log(`PASS: ${controls.length} preparation Chromium controls and ${httpControls.length} HTTP negatives`);
}catch(e){await fs.writeFile(path.join(output,'failure.json'),JSON.stringify({error:{message:e.message,stack:e.stack},controls,states,trace,source_sha256:before},null,2)+'\n');throw e;}finally{for(const child of children)await stop(child);await browser?.close();if(scratch)await fs.rm(scratch,{recursive:true,force:true});await fs.writeFile(path.join(output,'hosts.json'),JSON.stringify(logs,null,2)+'\n');}
