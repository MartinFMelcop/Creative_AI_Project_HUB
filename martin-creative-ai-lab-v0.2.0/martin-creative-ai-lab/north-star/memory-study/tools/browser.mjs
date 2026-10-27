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
async function identities(){const directories=['memory-study'];const names=(await Promise.all(directories.map(d=>files(path.join(root,'north-star',d))))).flat();names.push(path.join(root,'north-star/csharp/global.json'),path.join(root,'projects/realtime-integration-lab/package.json'),path.join(root,'projects/realtime-integration-lab/package-lock.json'));return Object.fromEntries(await Promise.all(names.sort().map(async p=>[path.relative(root,p),hash(await fs.readFile(p))])));}
const before=await identities(),controls=[],httpControls=[],states={},negatives=[],logs=[],children=[],errors=[];
let browser,scratch,complete=false;
function check(id,condition){assert.ok(condition,id);assert.ok(!controls.includes(id),'Unique browser control');controls.push(id);}
async function start(webroot){const server=createServer();await new Promise((resolve,reject)=>{server.once('error',reject);server.listen(0,'127.0.0.1',resolve);});const port=server.address().port;await new Promise(resolve=>server.close(resolve));const command=[path.join(study,'Host/bin/Release/net10.0/NorthStar.MemoryStudy.dll'),'--serve',String(port),webroot,'--seconds','120'];const child=spawn(dotnet,command,{cwd:root,stdio:['ignore','pipe','pipe']});children.push(child);const log={command:[dotnet,...command],stdout:'',stderr:''};logs.push(log);child.stdout.on('data',b=>log.stdout+=b);child.stderr.on('data',b=>log.stderr+=b);child.on('error',e=>log.stderr+=e.message);for(let i=0;i<240&&!log.stdout.includes('READY');i++){if(child.exitCode!==null)throw Error(JSON.stringify(log));await new Promise(resolve=>setTimeout(resolve,25));}assert.match(log.stdout,/READY/,'Actual bounded C# host starts');return`http://127.0.0.1:${port}/`;}
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
  assert.equal(await page.locator('#'+b.id+'-fit-button').isEnabled(),b.eligible,'Named service button follows eligibility');
 }
 assert.equal(await page.locator('#history li').count(),s.history.length,'Actual accepted action history remains visible');
 assert.equal(await page.locator('#notice').textContent(),s.text,'Actual receipt rendered');
}
async function open(url){const page=await browser.newPage({viewport:{width:1280,height:1100}});page.on('pageerror',e=>errors.push(e.message));await page.goto(url);await page.waitForFunction(()=>window.memoryStudy?.state&&window.memoryStudy.status==='ready');await fidelity(page,await actual(url));return page;}
async function act(page,url,command,bench,button){if(button){const before=await actual(url);await page.locator('#'+button).click();await page.waitForFunction(n=>window.memoryStudy?.state?.sequence>n&&window.memoryStudy.status==='ready',before.sequence);}else await page.evaluate(async({command,bench})=>window.memoryStudy.send(command,bench),{command,bench});const s=await actual(url);await fidelity(page,s);return s;}
const bench=(s,id)=>s.benches.find(b=>b.id===id);
async function refusal(page,url,command,recipient,id){const before=await actual(url),after=await act(page,url,command,recipient);const facts=s=>JSON.stringify({turn:s.turn,parts:s.parts,coins:s.coins,benches:s.benches,history:s.history});check(id,!after.accepted&&facts(before)===facts(after));negatives.push({id,before,after});return after;}
await fs.mkdir(output,{recursive:false});
try{
 const url=await start(web);const invalid=[
  {id:'forged witness field',body:'{"command":"help","revision":0,"bench":"west","recent":true}'},
  {id:'duplicate command',body:'{"command":"wait","command":"wait","revision":0}'},
  {id:'unknown recipient',body:'{"command":"help","revision":0,"bench":"other"}'},
  {id:'malformed JSON',body:'{'},
  {id:'cross-origin',body:'{"command":"wait","revision":0}',headers:{'Content-Type':'application/json',Origin:'http://untrusted.invalid'}},
  {id:'wrong media',body:'{"command":"wait","revision":0}',headers:{'Content-Type':'text/plain'}},
  {id:'oversized body',body:' '.repeat(4097)}];
 for(const input of invalid){const prior=await actual(url);const response=await fetch(url+'command',{method:'POST',body:input.body,headers:input.headers??{'Content-Type':'application/json'},signal:AbortSignal.timeout(5000)});assert.equal(response.status,400,input.id);assert.deepEqual(await actual(url),prior);httpControls.push(input.id);}
 browser=await chromium.launch({executablePath:process.env.CHROMIUM_PATH||'/usr/bin/chromium',headless:true,args:['--no-sandbox']});const page=await open(url);
 states.initial=await actual(url);check('Neither bench begins witnessed or supplied',states.initial.parts===4&&states.initial.coins===2&&states.initial.benches.every(b=>!b.helped&&!b.recent&&!b.delivered));
 await refusal(page,url,'serve','west','Unobserved service cannot spend coin or fabricate fitting');
 states.help=await act(page,url,'help','west','west-help-button');check('Actual local help pays part and turn then records only west',states.help.parts===3&&states.help.turn===1&&bench(states.help,'west').eligible&&!bench(states.help,'east').helped&&!bench(states.help,'east').recent);
 await refusal(page,url,'serve','east','West witness cannot authorize east service');await page.screenshot({path:path.join(output,'west-observed.png'),fullPage:true});
 await act(page,url,'wait',undefined,'wait');await act(page,url,'wait',undefined,'wait');states.beforeExpiry=await actual(url);check('Named opportunity remains before exact expiry',states.beforeExpiry.turn===3&&bench(states.beforeExpiry,'west').recent);
 states.expired=await act(page,url,'wait',undefined,'wait');check('Exact expiry removes opportunity but retains actual help and history',states.expired.turn===4&&!bench(states.expired,'west').recent&&!bench(states.expired,'west').eligible&&bench(states.expired,'west').helped&&states.expired.history.length===4);await page.screenshot({path:path.join(output,'expired-not-erased.png'),fullPage:true});
 const unchanged=JSON.stringify(await actual(url));await page.waitForTimeout(120);await page.reload();await page.waitForFunction(()=>window.memoryStudy?.state&&window.memoryStudy.status==='ready');await fidelity(page,await actual(url));check('Wall time reads and redraw cannot renew opportunity',JSON.stringify(await actual(url))===unchanged);
 await refusal(page,url,'serve','west','Expired service refuses without charge or output');
 states.renew=await act(page,url,'demonstrate','west','west-help-button');check('Fresh demonstration costs another part and actual action',states.renew.turn===5&&states.renew.parts===2&&bench(states.renew,'west').eligible);
 states.decline=await act(page,url,'decline','west','west-decline-button');check('Withdrawal preserves actual work without consuming turn',states.decline.turn===5&&bench(states.decline,'west').helped&&!bench(states.decline,'west').support&&!bench(states.decline,'west').recent);
 await act(page,url,'demonstrate','west','west-help-button');states.first=await act(page,url,'serve','west','west-fit-button');check('Explicit paid renewal then actual service produces exactly west fitting',states.first.turn===7&&states.first.parts===1&&states.first.coins===1&&bench(states.first,'west').delivered&&!bench(states.first,'east').delivered);
 for(let n=0;n<3;n++)await act(page,url,'wait',undefined,'wait');states.afterExpiry=await actual(url);check('Later expiry cannot erase acquired fitting',!bench(states.afterExpiry,'west').recent&&bench(states.afterExpiry,'west').delivered&&bench(states.afterExpiry,'west').helped);
 await act(page,url,'help','east','east-help-button');states.complete=await act(page,url,'serve','east','east-fit-button');check('Actual independent second service spends last coin and final part',states.complete.complete&&states.complete.parts===0&&states.complete.coins===0&&states.complete.benches.every(b=>b.delivered));await page.screenshot({path:path.join(output,'two-actual-fittings.png'),fullPage:true});
 await refusal(page,url,'serve','east','Completed fitting cannot be minted twice');
 const failedUrl=await start(web),failed=await open(failedUrl);await act(failed,failedUrl,'help','west','west-help-button');for(let n=0;n<3;n++)await act(failed,failedUrl,'demonstrate','west','west-help-button');for(let n=0;n<3;n++)await act(failed,failedUrl,'wait',undefined,'wait');states.losing=await actual(failedUrl);check('Repeated demonstrations can exhaust parts with both outputs absent',states.losing.parts===0&&states.losing.coins===2&&states.losing.benches.every(b=>!b.delivered)&&!bench(states.losing,'west').recent);
 await refusal(failed,failedUrl,'help','east','Spent parts cannot be refunded into other bench work');await refusal(failed,failedUrl,'demonstrate','west','A promise cannot replace an exhausted demonstration part');await failed.screenshot({path:path.join(output,'exhausted-window.png'),fullPage:true});
 scratch=await fs.mkdtemp(path.join(os.tmpdir(),'memory-render-mutants-'));
 for(const [label,target,replacement,message] of [['false-witness','const recentObserved = Boolean(b.recent);','const recentObserved = true;','Named recent picture follows actual owner'],['false-fitting','const deliveredObserved = Boolean(b.delivered);','const deliveredObserved = true;','Named fitting picture follows actual owner']]){
  const copy=path.join(scratch,label);await fs.cp(web,copy,{recursive:true});const file=path.join(copy,'app.js'),source=await fs.readFile(file,'utf8');assert.equal(source.split(target).length,2);const changed=source.replace(target,replacement);await fs.writeFile(file,changed);const mutantUrl=await start(copy),mutant=await browser.newPage({viewport:{width:1280,height:1100}});await mutant.goto(mutantUrl);await mutant.waitForFunction(()=>window.memoryStudy?.state&&window.memoryStudy.status==='ready');const actualState=await actual(mutantUrl);let detection;try{await fidelity(mutant,actualState);}catch(e){if(e.code!=='ERR_ASSERTION'||!e.message.includes(message))throw e;detection={name:e.name,code:e.code,message:e.message};}assert.ok(detection,label+' must be rejected');negatives.push({id:label,detected:true,mutation:{target,replacement,original_sha256:hash(source),mutated_sha256:hash(changed)},actual:actualState,assertion:detection});check('Actual isolated '+label+' renderer is detected',true);await mutant.close();
 }
 check('Actual browser has no uncaught script errors',errors.length===0);assert.deepEqual(await identities(),before);check('Actual consumer source identities remain stable',true);complete=true;
 await fs.writeFile(path.join(output,'browser.json'),JSON.stringify({schema_version:1,kind:'actual_browser_scoped_memory',checks:{passed:controls.length,failed:0},http_checks:{passed:httpControls.length,failed:0},controls,http_controls:httpControls,states,negatives,source_sha256:before,source_stable:true,runtime:{node:process.version,chromium:browser.version(),playwright:require('playwright-core/package.json').version},limits:'Synthetic software controls, overlapping outcomes, not people, independent studies, full NPC schedules, source fiction, Ruby/RGSS, Unity, Windows, Steam or human testimony.'},null,2)+'\n');console.log(`PASS: ${controls.length} Chromium and ${httpControls.length} HTTP memory controls`);
}catch(e){await fs.writeFile(path.join(output,'failure.json'),JSON.stringify({complete:false,error:{name:e.name,code:e.code??null,message:e.message,stack:e.stack},controls,http_controls:httpControls,states,source_sha256:before},null,2)+'\n');throw e;}finally{for(const child of children)await stop(child);await browser?.close();if(scratch)await fs.rm(scratch,{recursive:true,force:true});await fs.writeFile(path.join(output,'hosts.json'),JSON.stringify({complete,logs},null,2)+'\n');}
