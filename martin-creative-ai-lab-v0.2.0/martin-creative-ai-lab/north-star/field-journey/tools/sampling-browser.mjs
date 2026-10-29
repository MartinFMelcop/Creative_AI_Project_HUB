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
const before=await identities(),controls=[],httpControls=[],trace=[],states={},negatives=[],logs=[],children=[],errors=[];
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
 await baseFidelity(page,s);const c=s.sample_case,carried=c.status==='carried',secured=c.status==='secured';
 assert.equal(await page.locator('#field-sampling').getAttribute('data-status'),c.status,'Actual sample status');
 assert.equal(await page.locator('#field-sampling').getAttribute('data-carried'),String(carried),'Actual sample carried');
 assert.equal(await page.locator('#field-sampling').getAttribute('data-secured'),String(secured),'Actual sample secured');
 const visible=await page.locator('#field-sample-cargo').evaluate(el=>getComputedStyle(el).display!=='none');
 assert.equal(visible,carried||secured,'Actual sample cargo picture');
 const seal=await page.locator('#field-sample-cargo .sample-seal').evaluate(el=>getComputedStyle(el).display!=='none');assert.equal(seal,secured,'Actual sample secured seal');
 const title=await page.locator('#sampling-picture-title').textContent();assert.match(title,c.status==='lost'?/lost/:secured?/secured/:carried?/carried/:/empty/);
 for(const site of c.sites){assert.equal(await page.locator('#sample-'+site.id).isEnabled(),site.eligible,'Actual site button eligibility');}
 if(c.receipt){const text=await page.locator('#sampling-receipt').textContent();for(const item of [`beat ${c.receipt.before_beat} → ${c.receipt.after_beat}`,`${c.receipt.health_lost} lost`])assert.ok(text.includes(item),'Actual paid sampling receipt');}
}
async function prepare(page,url,name){await confirm(page,url,name);for(const b of ['west','east']){await serve(page,url,b);await craft(page,url,b);}}
const draw=['slot',{slot:1},'use-slot1'];
async function raw(url,command,fields={}){const before=await actual(url);const r=await fetch(url+'command',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({command,revision:before.sequence,...fields}),signal:AbortSignal.timeout(5000)});assert.equal(r.status,200);const s=await r.json();trace.push({raw:true,command,fields,state:s});return s;}
async function rawPrepared(url){await raw(url,'draft',{handle:'Mira',accent:'teal',class_id:'lure',background_id:'trailborn',slots:['draw',null,null,null]});await raw(url,'review');await raw(url,'confirm',{draft_revision:(await actual(url)).intake.draft_revision});for(const bench of ['west','east']){await raw(url,'help',{bench});await raw(url,'serve',{bench});await raw(url,'craft',{bench,rig:'trail'});}await raw(url,'begin',{rig:'trail'});await raw(url,'slot',{slot:1});await raw(url,'sample',{site:'ridge'});}
await fs.mkdir(output,{recursive:false});
try{
 browser=await chromium.launch({executablePath:process.env.CHROMIUM_PATH||'/usr/bin/chromium',headless:true,args:['--no-sandbox']});
 const url=await start(web),page=await open(url);check('Initial case is disclosed setup without cargo',(await actual(url)).sample_case.status==='empty');
 await prepare(page,url,'Neri');await begin(page,url);await refusal(page,url,'sample',{site:'ridge'},'Entry without exact site cannot spend case or beat');await run(page,url,[draw]);
 await refusal(page,url,'sample',{site:'channel'},'Wrong known site leaves actual child and custody unchanged');
 const b=await actual(url);states.ridge=await act(page,url,'sample',{site:'ridge'},'sample-ridge');
 check('Ridge collection pays the actual stationary bolt and beat',states.ridge.intake.state.health===b.intake.state.health-4&&states.ridge.intake.state.beat===b.intake.state.beat+1&&states.ridge.intake.state.position===b.intake.state.position);
 check('Same confirmed person carries one acquired sample without securing it',states.ridge.sample_case.acquired&&states.ridge.sample_case.status==='carried'&&states.ridge.intake.identity.handle==='Neri'&&!states.ridge.intake.state.complete);
 check('Sampling records actual Wait harm, not free protection',states.ridge.encounter_view.action.kind==='wait'&&states.ridge.encounter_view.action.contact==='hurt'&&states.ridge.sample_case.receipt.health_lost===4);
 await page.locator('#field-sampling').screenshot({path:path.join(output,'ridge-carried.png')});await page.locator('#field-encounter-board').screenshot({path:path.join(output,'ridge-contact.png')});
 await run(page,url,[['walk',{},'walk'],draw]);states.survey=await actual(url);check('Actual survey win retains carried sample without final securing',states.survey.intake.state.won&&!states.survey.intake.state.complete&&states.survey.sample_case.status==='carried');
 await act(page,url,'allocate',{axis:'focus',points:2});await begin(page,url);await run(page,url,[draw,draw]);await refusal(page,url,'sample',{site:'channel'},'Spent case excludes later site without replacement');await run(page,url,crossing.slice(2));states.ridgeFinal=await actual(url);
 check('Actual final Crossing secures ridge without extra XP or refunded rig',states.ridgeFinal.sample_case.status==='secured'&&states.ridgeFinal.intake.state.complete&&states.ridgeFinal.intake.state.xp===25&&states.ridgeFinal.intake.state.consumed_rigs===2);
 await page.locator('#field-encounter-board').screenshot({path:path.join(output,'ridge-secured.png')});
 const held=JSON.stringify(await actual(url));await page.waitForTimeout(100);await page.reload();await page.waitForFunction(()=>window.fieldJourney?.status==='ready');await fidelity(page,await actual(url));check('Elapsed time reload and redraw cannot resupply or change securing',JSON.stringify(await actual(url))===held);
 const u=await start(web),p=await open(u);await prepare(p,u,'Iona');await begin(p,u);await run(p,u,survey);check('Deferring collection retains the same unused case',(await actual(u)).sample_case.status==='empty');await act(p,u,'allocate',{axis:'focus',points:2});await begin(p,u);await run(p,u,[draw,draw]);const ch=await actual(u);states.channel=await act(p,u,'sample',{site:'channel'},'sample-channel');
 check('Later channel collection pays actual stationary pulse',states.channel.sample_case.status==='carried'&&states.channel.intake.state.health===ch.intake.state.health-6&&states.channel.encounter_view.action.contact==='hurt');await run(p,u,[draw,['walk',{},'walk'],draw]);states.channelFinal=await actual(u);check('Exclusive channel sample can survive actual complete route',states.channelFinal.sample_case.status==='secured'&&states.channelFinal.sample_case.site==='channel'&&states.channelFinal.intake.state.health===5&&states.channelFinal.intake.state.complete);await p.locator('#field-sampling').screenshot({path:path.join(output,'channel-secured.png')});
 const lu=await start(web),lp=await open(lu);await prepare(lp,lu,'Sela');await begin(lp,lu);await run(lp,lu,[draw,['sample',{site:'ridge'},'sample-ridge'],['wait',{},'wait'],['wait',{},'wait']]);states.lost=await actual(lu);check('Actual later defeat loses cargo but retains acquisition history',states.lost.sample_case.status==='lost'&&states.lost.sample_case.acquired&&states.lost.intake.state.health===0);await lp.locator('#field-sampling').screenshot({path:path.join(output,'sample-lost.png')});await begin(lp,lu);await run(lp,lu,[draw]);await refusal(lp,lu,'sample',{site:'ridge'},'Real retry cannot refill the lost case');
 const du=await start(web),dp=await open(du);await prepare(dp,du,'Eren');await begin(dp,du);await run(dp,du,[['walk',{},'walk'],['wait',{},'wait'],['sample',{site:'ridge'},'sample-ridge']]);states.fatal=await actual(du);check('Fatal collection spends case without acquisition victory or XP',states.fatal.sample_case.status==='lost'&&!states.fatal.sample_case.acquired&&states.fatal.intake.state.xp===0&&!states.fatal.intake.state.won);
 for(const [id,payload] of [['forged-state',{command:'sample',revision:0,site:'ridge',status:'secured'}],['unknown-site',{command:'sample',revision:0,site:'elsewhere'}]]){const prior=JSON.stringify(await actual(du));const rr=await fetch(du+'command',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});assert.equal(rr.status,400);assert.equal(JSON.stringify(await actual(du)),prior);httpControls.push(id);}
 scratch=await fs.mkdtemp(path.join(os.tmpdir(),'sample-renderer-'));
 for(const [id,target,replacement,afterLoss,message] of [['false-carried',"const sampleCarriedObserved = s.sample_case.status === 'carried';",'const sampleCarriedObserved = s.sample_case.acquired;',true,'Actual sample carried'],['false-secured',"const sampleSecuredObserved = s.sample_case.status === 'secured';",'const sampleSecuredObserved = s.sample_case.acquired;',false,'Actual sample secured']]){
  const copy=path.join(scratch,id);await fs.cp(web,copy,{recursive:true});const file=path.join(copy,'app.js'),src=await fs.readFile(file,'utf8');assert.equal(src.split(target).length,2);const mutated=src.replace(target,replacement);await fs.writeFile(file,mutated);const mu=await start(copy);await rawPrepared(mu);if(afterLoss){await raw(mu,'wait');await raw(mu,'wait');}const mp=await browser.newPage();await mp.goto(mu);await mp.waitForFunction(()=>window.fieldJourney?.status==='ready');let detected;try{await fidelity(mp,await actual(mu));}catch(e){if(e.code!=='ERR_ASSERTION'||!e.message.includes(message))throw e;detected=e.message;}assert.ok(detected);negatives.push({id,detected,original_sha256:hash(src),mutated_sha256:hash(mutated),target,replacement,actual:await actual(mu)});check('Actual isolated '+id+' renderer rejected',true);await mp.close();
 }
 check('No uncaught page errors',errors.length===0);assert.deepEqual(await identities(),before);check('Actual browser source closure stable',true);
 await fs.writeFile(path.join(output,'browser.json'),JSON.stringify({schema_version:1,checks:{passed:controls.length,failed:0},http_checks:httpControls,controls,states,trace,negatives,source_sha256:before,source_stable:true,runtime:{node:process.version,chromium:browser.version(),playwright:require('playwright-core/package.json').version},limits:'Overlapping software journeys and controls, not people, source consumption, human balance, Unity/Windows/Steam or observed home delivery.'},null,2)+'\n');console.log(`PASS: ${controls.length} sampling Chromium controls and ${httpControls.length} HTTP negatives`);
}catch(e){await fs.writeFile(path.join(output,'failure.json'),JSON.stringify({error:{message:e.message,stack:e.stack},controls,states,trace,source_sha256:before},null,2)+'\n');throw e;}finally{for(const child of children)await stop(child);await browser?.close();if(scratch)await fs.rm(scratch,{recursive:true,force:true});await fs.writeFile(path.join(output,'hosts.json'),JSON.stringify(logs,null,2)+'\n');}
