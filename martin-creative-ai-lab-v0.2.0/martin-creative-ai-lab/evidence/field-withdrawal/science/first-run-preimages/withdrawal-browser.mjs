import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';
import {spawn} from 'node:child_process';
import {createRequire} from 'node:module';
import {createServer} from 'node:net';
import {createHash} from 'node:crypto';
import {fileURLToPath} from 'node:url';

const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../../..');
const study=path.join(root,'north-star/field-journey'),web=path.join(study,'web');
const dotnet=process.argv[2],out=process.argv[3]&&path.resolve(process.argv[3]);
if(!dotnet||!out||out===root||out.startsWith(root+path.sep))throw Error('Usage: withdrawal-browser.mjs DOTNET NEW_EXTERNAL_OUTPUT');
const require=createRequire(path.join(root,'projects/realtime-integration-lab/package.json'));
const {chromium}=require('playwright-core');
const sha=b=>createHash('sha256').update(b).digest('hex');
const controls=[],trace=[],states={},negatives=[],logs=[],children=[],errors=[];
let browser;
async function inputs(){
 const result={};
 async function scan(relative){for(const e of await fs.readdir(path.join(root,relative),{withFileTypes:true})){if(['bin','obj','node_modules','__pycache__'].includes(e.name))continue;const n=path.join(relative,e.name);if(e.isDirectory())await scan(n);else if(e.isFile()&&/\.(cs|csproj|js|mjs|html|css|json|py)$/.test(n))result[n]=sha(await fs.readFile(path.join(root,n)));}}
 for(const n of ['field-journey','intake','memory-study','csharp/Domain','csharp/Portable','csharp/Loadout','csharp/Forge','csharp/Crossing'])await scan('north-star/'+n);
 for(const n of ['north-star/csharp/global.json','projects/realtime-integration-lab/package.json','projects/realtime-integration-lab/package-lock.json'])result[n]=sha(await fs.readFile(path.join(root,n)));
 return Object.fromEntries(Object.entries(result).sort(([a],[b])=>a.localeCompare(b)));
}
const before=await inputs();
function check(id,condition){assert.ok(condition,id);controls.push(id);}
const facts=s=>JSON.stringify({intake:s.intake,memory:s.memory,fittings:s.fittings,assembly:s.assembly_receipts});
async function start(){const server=createServer();await new Promise(r=>server.listen(0,'127.0.0.1',r));const port=server.address().port;await new Promise(r=>server.close(r));const command=[dotnet,path.join(study,'Host/bin/Release/net10.0/NorthStar.FieldJourney.dll'),'--serve',String(port),web,'--seconds','180'];const c=spawn(command[0],command.slice(1),{cwd:root,stdio:['ignore','pipe','pipe']});children.push(c);const log={command,stdout:'',stderr:''};logs.push(log);c.stdout.on('data',b=>log.stdout+=b);c.stderr.on('data',b=>log.stderr+=b);for(let n=0;n<240&&!log.stdout.includes('READY');n++){if(c.exitCode!==null)throw Error(JSON.stringify(log));await new Promise(r=>setTimeout(r,25));}assert.match(log.stdout,/READY/);return`http://127.0.0.1:${port}/`;}
async function get(url){const r=await fetch(url+'state',{signal:AbortSignal.timeout(5000)});assert.equal(r.status,200);return r.json();}
async function open(url,mutant){const page=await browser.newPage({viewport:{width:1400,height:1100}});page.on('pageerror',e=>errors.push(e.message));if(mutant)await page.route('**/app.js',r=>r.fulfill({contentType:'text/javascript',body:mutant}));await page.goto(url);await page.waitForFunction(()=>window.fieldJourney?.status==='ready');return page;}
async function act(page,url,command,fields={},button){if(button){const b=await get(url);await page.locator('#'+button).click();await page.waitForFunction(n=>window.fieldJourney.status==='ready'&&window.fieldJourney.state.sequence>n,b.sequence);}else await page.evaluate(async p=>window.fieldJourney.send(p.command,p.fields),{command,fields});const s=await get(url);trace.push({command,fields,state:s});assert.deepEqual(await page.evaluate(()=>window.fieldJourney.state),s);return s;}
async function prepare(page,url,name){
 await act(page,url,'draft',{handle:name,accent:'teal',class_id:'lure',background_id:'trailborn',slots:['draw',null,null,null]});await act(page,url,'review');await act(page,url,'confirm',{draft_revision:(await get(url)).intake.draft_revision});
 for(const bench of ['west','east']){await act(page,url,'help',{bench});await act(page,url,'serve',{bench});await act(page,url,'craft',{bench,rig:'trail'});}
 return act(page,url,'begin',{rig:'trail'});
}
async function refusal(page,url,command,fields,id){const b=await get(url),s=await act(page,url,command,fields);check(id,!s.accepted&&facts(b)===facts(s)&&JSON.stringify(b.sample_case)===JSON.stringify(s.sample_case)&&JSON.stringify(b.withdrawal_receipt)===JSON.stringify(s.withdrawal_receipt));return s;}
async function fidelity(page,s){
 assert.equal(await page.locator('#completion').isVisible(),Boolean(s.intake.state.complete),'Visible completion cannot be fabricated by withdrawal');
 assert.equal(await page.locator('#field-encounter-board').getAttribute('data-historical'),String(s.encounter_historical),'Encounter picture is explicitly historical');
 assert.equal(await page.locator('#field-phase').textContent(),'WITHDRAWN / HISTORICAL ENCOUNTER','Actual visible outer phase');
 for(const id of ['field-bolt','field-pulse'])assert.equal(await page.locator('#'+id).evaluate(el=>getComputedStyle(el).display),'none','Historical picture cannot show active threat '+id);
 assert.equal(await page.locator('#withdrawal-summary').isVisible(),true,'Accepted withdrawal summary is visible');
 assert.equal(await page.locator('#withdraw-expedition').isVisible(),false,'Already accepted withdrawal cannot offer another confirmation');
 for(const value of await page.locator('.field-sample-site').evaluateAll(xs=>xs.map(x=>getComputedStyle(x).display)))assert.equal(value,'none','Historical sampling sites are not active opportunities');
 assert.equal(await page.locator('#field-sample-cargo').evaluate(el=>getComputedStyle(el).display),'none','Forfeited or never acquired cargo cannot remain visibly carried');
 assert.ok(await page.locator('button,input,select').evaluateAll(xs=>xs.every(x=>x.id==='read'||x.disabled)),'Every mutating form control remains disabled');
 assert.equal(await page.locator('body').getAttribute('data-withdrawn'),String(s.withdrawn),'Visible outer withdrawal follows actual owner');
 assert.equal(await page.locator('body').getAttribute('data-complete'),String(s.intake.state.complete),'Withdrawal cannot fabricate final completion');
 assert.equal((await page.locator('#confirmed-name').textContent()).trim(),s.intake.identity.handle,'Confirmed person remains the same');
 assert.equal(Number(await page.locator('#consumed-rigs').textContent()),s.intake.state.consumed_rigs,'Withdrawal cannot refund actual consumed rig');
 assert.equal(await page.locator('#field-sampling').getAttribute('data-status'),s.sample_case.status,'Visible sample custody follows actual owner');
 assert.equal(await page.locator('#notice').textContent(),s.text,'Actual withdrawal receipt remains visible');
 for(const id of ['walk','wait','use-slot1','use-slot2','use-slot3','use-slot4','begin','assemble','review','confirm','focus','vitality'])assert.equal(await page.locator('#'+id).isEnabled(),false,'Closed outer trial cannot expose enabled mutation '+id);
 assert.equal(await page.locator('#read').isEnabled(),true,'History remains readable');
}
await fs.mkdir(out,{recursive:false});
try{
 browser=await chromium.launch({executablePath:process.env.CHROMIUM_PATH||'/usr/bin/chromium',headless:true});
 const url=await start(),page=await open(url);
 await refusal(page,url,'withdraw',{},'No pre-entry outer withdrawal can end an unstarted journey');
 states.active=await prepare(page,url,'Neri');await act(page,url,'slot',{slot:1});states.carried=await act(page,url,'sample',{site:'ridge'});
 check('Actual active child and paid acquired sample exist before withdrawal',states.carried.intake.state.active&&states.carried.sample_case.status==='carried'&&states.carried.sample_case.acquired);
 const b=await get(url);
 for(const payload of [{command:'withdraw',revision:b.sequence-1},{command:'withdraw',revision:b.sequence,complete:true},{command:'withdraw',revision:'bad'}]){
  const response=await fetch(url+'command',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload),signal:AbortSignal.timeout(5000)});
  if(payload.revision===b.sequence-1){assert.equal(response.status,200);assert.equal((await response.json()).accepted,false);}else assert.equal(response.status,400);
  check('Stale or malformed withdrawal preserves exact current owner '+JSON.stringify(payload),JSON.stringify(await get(url))===JSON.stringify(b));
 }
 states.withdrawn=await act(page,url,'withdraw',{},'withdraw-expedition');
 check('Actual withdrawal preserves entire child/memory/fitting facts',states.withdrawn.accepted&&states.withdrawn.withdrawn&&states.withdrawn.encounter_historical&&facts(states.carried)===facts(states.withdrawn));
 check('Carried sample is lost but its actual acquisition and receipt remain',states.withdrawn.sample_case.status==='lost'&&states.withdrawn.sample_case.acquired&&JSON.stringify(states.withdrawn.sample_case.receipt)===JSON.stringify(states.carried.sample_case.receipt)&&states.withdrawn.sample_case.loss_reason==='withdrawn');
 check('Historical active child is neither defeated completed nor returned',states.withdrawn.intake.state.active&&!states.withdrawn.intake.state.complete&&!states.withdrawn.withdrawal_receipt.complete&&!states.withdrawn.withdrawal_receipt.returned);
 await fidelity(page,states.withdrawn);check('Actual withdrawn controls and identity match owner',true);await page.screenshot({path:path.join(out,'active-withdrawal.png'),fullPage:true});
 for(const [cmd,fields]of [['walk',{}],['wait',{}],['slot',{slot:1}],['begin',{rig:'trail'}],['craft',{bench:'east',rig:'trail'}],['review',{}],['withdraw',{}]])await refusal(page,url,cmd,fields,'Closed outer refuses '+cmd+' without child/custody mutation');
 const after=await get(url);await new Promise(r=>setTimeout(r,150));await page.locator('#read').click();await page.waitForFunction(()=>window.fieldJourney.status==='ready');check('Reads and elapsed time cannot resolve historical encounter',JSON.stringify(await get(url))===JSON.stringify(after));
 const surveyUrl=await start(),surveyPage=await open(surveyUrl);await prepare(surveyPage,surveyUrl,'Mira');for(const [cmd,fields]of [['slot',{slot:1}],['slot',{slot:1}],['walk',{}],['slot',{slot:1}]])await act(surveyPage,surveyUrl,cmd,fields);
 states.survey=await get(surveyUrl);assert.ok(states.survey.intake.state.won&&!states.survey.intake.state.complete);states.surveyWithdrawn=await act(surveyPage,surveyUrl,'withdraw',{},'withdraw-expedition');
 check('Survey withdrawal retains earned XP unused rig and exact child facts',states.surveyWithdrawn.withdrawn&&facts(states.survey)===facts(states.surveyWithdrawn)&&!states.surveyWithdrawn.intake.state.complete);await fidelity(surveyPage,states.surveyWithdrawn);await surveyPage.screenshot({path:path.join(out,'survey-withdrawal.png'),fullPage:true});
 // Actual isolated rendering defect: lie about completion while keeping actual C# facts intact.
 const source=await fs.readFile(path.join(web,'app.js'),'utf8');const target='const completeObserved = Boolean(s.intake.state.complete);';assert.equal(source.split(target).length,2,'Exact current completion projection mutation target');
 const mutated=source.replace(target,'const completeObserved = Boolean(s.intake.state.complete) || Boolean(s.withdrawn);');const mutant=await open(surveyUrl,mutated);let rejected=false;try{await fidelity(mutant,await get(surveyUrl));}catch(e){assert.match(e.message,/Visible completion cannot be fabricated by withdrawal/);rejected=true;negatives.push({id:'actual-false-completion-renderer',source_sha256:sha(source),mutated_sha256:sha(mutated),error:e.message,detected:true});}
 check('Actual isolated false-completion renderer is detected',rejected);await mutant.screenshot({path:path.join(out,'detected-false-completion.png'),fullPage:true});
 check('No application browser exceptions',errors.length===0);check('All actual source and producer identities remain stable',JSON.stringify(before)===JSON.stringify(await inputs()));
 await fs.writeFile(path.join(out,'withdrawal-browser.json'),JSON.stringify({schema:'north-star.actual-field-withdrawal-browser.v1',runtime:{node:process.version,chromium:browser.version()},identities:before,controls,states,trace,negatives,logs,limits:'Actual outer trial termination and historical child/UI ownership only; no world retreat, physical return, human agency/balance/accessibility, Unity, Windows or Steam validation.'},null,2)+'\n');console.log(`PASS ${controls.length} actual withdrawal browser controls; ${negatives.length} actual renderer negative`);
}catch(error){await fs.writeFile(path.join(out,'withdrawal-failure.json'),JSON.stringify({error:error.stack,identities:before,controls,states,trace,negatives,logs,errors},null,2)+'\n');throw error;
}finally{await browser?.close();for(const c of children){if(c.exitCode===null&&c.signalCode===null){c.kill();await new Promise(r=>c.once('exit',r));}}}
