import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';
import os from 'node:os';
import {spawn} from 'node:child_process';
import {createRequire} from 'node:module';
import {createServer} from 'node:net';
import {createHash} from 'node:crypto';
import {fileURLToPath} from 'node:url';

// Observe actual passive selection and resolved contacts, separately from end-round DOT.
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../../..');
const study=path.join(root,'north-star/combat-study'),web=path.join(study,'Host/web');
const dotnet=process.argv[2],output=process.argv[3]&&path.resolve(process.argv[3]);
if(!dotnet||!output||output===root||output.startsWith(root+path.sep))throw Error('Usage: response-browser.mjs DOTNET NEW_OUTPUT_OUTSIDE_MAINTAINED_TREE');
const require=createRequire(path.join(root,'projects/realtime-integration-lab/package.json'));
const {chromium}=require('playwright-core');
const hash=data=>createHash('sha256').update(data).digest('hex');
async function files(directory){let names=[];for(const entry of await fs.readdir(directory,{withFileTypes:true})){if(['bin','obj','node_modules','__pycache__'].includes(entry.name))continue;const p=path.join(directory,entry.name);if(entry.isDirectory())names.push(...await files(p));else if(entry.isFile()&&/\.(cs|csproj|js|mjs|html|css|json|py)$/.test(p))names.push(p);}return names;}
async function identities(){const names=[...await files(study),path.join(root,'projects/realtime-integration-lab/package.json'),path.join(root,'projects/realtime-integration-lab/package-lock.json'),path.join(root,'north-star/csharp/global.json')];return Object.fromEntries(await Promise.all(names.sort().map(async p=>[path.relative(root,p),hash(await fs.readFile(p))])));}
const before=await identities(),controls=[],httpControls=[],states={},negatives=[],logs=[],children=[],errors=[];
let browser,scratch,complete=false;
function check(id,condition){assert.ok(condition,id);assert.ok(!controls.includes(id),'Unique control');controls.push(id);}
async function start(webroot){const server=createServer();await new Promise((resolve,reject)=>{server.once('error',reject);server.listen(0,'127.0.0.1',resolve);});const port=server.address().port;await new Promise(resolve=>server.close(resolve));const command=[path.join(study,'Host/bin/Release/net10.0/NorthStar.CombatStudy.dll'),'--serve',String(port),webroot,'--seconds','180'];const child=spawn(dotnet,command,{cwd:root,stdio:['ignore','pipe','pipe']});children.push(child);const log={command:[dotnet,...command],stdout:'',stderr:''};logs.push(log);child.stdout.on('data',b=>log.stdout+=b);child.stderr.on('data',b=>log.stderr+=b);child.on('error',e=>log.stderr+=e.message);for(let i=0;i<240&&!log.stdout.includes('READY');i++){if(child.exitCode!==null)throw Error(JSON.stringify(log));await new Promise(resolve=>setTimeout(resolve,25));}assert.match(log.stdout,/READY/,'Actual bounded host starts');return`http://127.0.0.1:${port}`;}
async function stop(child){if(child.exitCode!==null||child.signalCode!==null)return;child.kill('SIGTERM');await Promise.race([new Promise(resolve=>child.once('exit',resolve)),new Promise(resolve=>setTimeout(resolve,1200))]);if(child.exitCode===null&&child.signalCode===null){child.kill('SIGKILL');await new Promise(resolve=>child.once('exit',resolve));}}
async function actual(url){const r=await fetch(url+'/api/state',{signal:AbortSignal.timeout(5000)});assert.equal(r.status,200);return r.json();}
async function fidelity(page,o){
 assert.deepEqual(await page.evaluate(()=>window.combatStudy.observation()),o,'Actual complete observation remains visible');
 const s=o.state,p=s??o.preparation,spent=s?.rescueSpent??false;
 assert.equal(await page.locator('#passive-glyph').getAttribute('data-passive'),p.passive,'Actual selected passive glyph follows owner');
 assert.equal(await page.locator('#passive-glyph').getAttribute('data-spent'),String(spent),'Actual spent rescue glyph follows owner');
 const glyph=await page.locator('#passive-glyph').evaluate(el=>Object.fromEntries(['passive-none','lining-glyph','thread-ready-glyph','thread-spent-glyph'].map(name=>[name,getComputedStyle(el.querySelector('.'+name)).display!=='none'])));
 assert.deepEqual(glyph,{'passive-none':p.passive==='none','lining-glyph':p.passive==='lining','thread-ready-glyph':p.passive==='last-thread'&&!spent,'thread-spent-glyph':p.passive==='last-thread'&&spent},'Computed glyph visibility follows actual passive and spent state');
 assert.equal(await page.locator('#equip-passive').isEnabled(),o.phase==='preparation','Only actual preparation enables passive replacement');
 assert.equal(await page.locator('#begin-passive').isEnabled(),o.phase==='preparation','Actual explicit Begin belongs to preparation');
 if(s){const text=await page.locator('#stats').textContent();for(const fact of [`Round ${s.round}`,`HP ${s.hp}/${s.maxHp}`,`Target ${s.enemyHp}`,`Charges ${s.charges}`,`Outcome ${s.outcome}`])assert.ok(text.includes(fact),'Actual '+fact);assert.equal(await page.locator('#player-hp').evaluate(e=>e.value),s.hp,'Actual final HP after contact AND DOT');assert.equal(await page.locator('#target-hp').evaluate(e=>e.value),s.enemyHp);assert.deepEqual(await page.locator('#events li').allTextContents(),s.events,'Actual event order remains visible');assert.deepEqual(await page.evaluate(()=>window.combatStudy.snapshot()),s,'Retained state-only observer stays exact');}
 else assert.equal(await page.evaluate(()=>window.combatStudy.snapshot()),null,'Preparation is not an actual encounter');
}
async function open(url){const page=await browser.newPage({viewport:{width:1280,height:1250}});page.on('pageerror',e=>errors.push(e.message));await page.goto(url);await page.waitForFunction(()=>window.combatStudy?.observation());await fidelity(page,await actual(url));return page;}
async function action(page,url,command,button){if(button){const prior=await actual(url);await page.locator(button).click();await page.waitForFunction(n=>window.combatStudy.observation()?.sequence>n,prior.sequence);}else await page.evaluate(command=>window.combatStudy.command(command),command);const o=await actual(url);await page.waitForFunction(o=>JSON.stringify(window.combatStudy.observation())===JSON.stringify(o),o);await fidelity(page,o);return o;}
async function setup(page,url,passive,armor='light',profile='toxic'){await action(page,url,'prepare '+profile,'#prepare-'+profile);await page.locator('#passive-select').selectOption(passive);await page.locator('#armor-select').selectOption(armor);await action(page,url,`equip ${passive} ${armor}`,'#equip-passive');return action(page,url,'begin','#begin-passive');}
async function play(page,url,commands){let o;for(const command of commands){o=await action(page,url,command,`[data-command="${command}"]`);assert.equal(o.accepted,true,'Actual action '+command);}return o;}
await fs.mkdir(output,{recursive:false});
async function responseSetup(page,url,profile='toxic'){
 await action(page,url,'prepare responses '+profile,`[data-command="prepare responses ${profile}"]`);
 assert.match(await page.locator('#response-state').textContent(),/prepared/);
 return action(page,url,'begin','#begin-passive');
}
async function responseFidelity(page,o){
 await fidelity(page,o);const s=o.state;if(!s)return;
 assert.equal(await page.locator('#response-state').getAttribute('data-pending'),String(s.responsePractice&&s.pending!==null));
 assert.equal(await page.locator('[data-command="commit"]').isEnabled(),o.phase==='active'&&s.responsePractice&&!s.pending&&s.charges>0);
 assert.equal(await page.locator('[data-command="release"]').isEnabled(),o.phase==='active'&&s.responsePractice&&s.pending!==null);
 assert.equal(await page.locator('[data-command="break-ward"]').isEnabled(),o.phase==='active'&&s.responsePractice&&s.pending!==null&&s.pending.ward&&s.charges>0);
 assert.deepEqual(await page.locator('#response-resolution li').allTextContents(),s.resolution);
 if(s.pending)for(const cmd of ['strike','bash','guard','treat','cleanse','retreat'])assert.equal(await page.locator(`[data-command="${cmd}"]`).isEnabled(),false,'Pending locks '+cmd);
}
async function doResponse(page,url,cmd){const o=await action(page,url,cmd,`[data-command="${cmd}"]`);await responseFidelity(page,o);return o;}
try{
 const url=await start(web);browser=await chromium.launch({headless:true});const page=await open(url);
 let o=await actual(url);await responseFidelity(page,o);check('Classic practice has no response commands',!o.state.responsePractice&&await page.locator('[data-command="commit"]').isDisabled());
 await responseSetup(page,url);o=await doResponse(page,url,'commit');states.pending=o;
 check('Actual paid cast waits without damage or round',o.accepted&&o.state.charges===1&&o.state.round===0&&o.state.hp===100&&o.state.enemyHp===96&&o.state.pending.ward&&!o.state.wardAvailable);
 check('Pending text refuses premature hit or refund',(await page.locator('#response-state').textContent()).includes('No strike damage'));
 const frozen=await actual(url);await page.waitForTimeout(80);await page.evaluate(()=>window.combatStudy.reconnect());check('Reads and elapsed time do not resolve',JSON.stringify(await actual(url))===JSON.stringify(frozen));
 o=await action(page,url,'strike');check('Owner refuses unrelated pending action',!o.accepted&&o.state.round===0&&o.state.charges===1&&o.state.enemyHp===96&&o.state.pending.ward);
 o=await action(page,url,'equip lining heavy');check('Pending cast cannot swap passive',!o.accepted&&o.state.passive==='none'&&o.state.charges===1);
 await page.screenshot({path:path.join(output,'paid-pending.png'),fullPage:true});
 o=await doResponse(page,url,'release');states.countered=o;
 check('Released ward counters real cast without refund',o.accepted&&o.state.round===1&&o.state.charges===1&&o.state.enemyHp===96&&o.state.pending===null&&o.state.hp<100);
 check('Actual reversed two-item resolution',JSON.stringify(o.state.resolution)===JSON.stringify(['Ward:applied','CommittedStrike:cancelled']));
 await page.screenshot({path:path.join(output,'countered-no-refund.png'),fullPage:true});
 await responseSetup(page,url);await doResponse(page,url,'commit');o=await doResponse(page,url,'break-ward');states.broken=o;
 check('Counter costs remaining shared charge',o.state.charges===0&&o.state.enemyHp===48&&o.state.round===1&&o.state.pending===null);
 check('Actual LIFO counter resolves before ward and strike',JSON.stringify(o.state.resolution)===JSON.stringify(['BreakWard:applied','Ward:cancelled','CommittedStrike:applied']));
 o=await action(page,url,'treat');check('Spent counter cannot also heal',!o.accepted&&o.state.charges===0&&o.state.round===1);
 await doResponse(page,url,'strike');o=await doResponse(page,url,'strike');states.secured=o;check('Actual paid counter route secures original encounter',o.state.outcome==='secured'&&o.state.enemyHp===0&&o.state.round===3&&o.state.charges===0&&o.state.hp>0);
 await page.screenshot({path:path.join(output,'actual-counter-secured.png'),fullPage:true});
 await responseSetup(page,url);await doResponse(page,url,'commit');await doResponse(page,url,'release');
 for(let n=0;n<4;n++){o=await actual(url);if(o.state.outcome!=='active')break;await doResponse(page,url,'strike');}
 o=await actual(url);states.losing=o;check('Actual losing release policy retains spent charge',o.state.outcome==='defeated'&&o.state.charges===1&&o.state.enemyHp>0);
 await responseSetup(page,url,'heated');o=await action(page,url,'commit');check('Disarm refuses cast without charge or pending window',!o.accepted&&o.state.charges===2&&o.state.round===0&&o.state.pending===null);
 await doResponse(page,url,'bash');await doResponse(page,url,'guard');await doResponse(page,url,'commit');o=await doResponse(page,url,'break-ward');states.burn=o;check('Actual existing burn modifies committed damage',o.state.enemyHp===52&&o.state.round===3&&o.state.charges===0);
 for(const body of [{command:'commit',damage:999},{command:'break-ward',charges:2},{command:'release',target:'forged'}]){const before=await actual(url);const response=await fetch(url+'/api/command',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});assert.equal(response.status,400);assert.deepEqual(await actual(url),before);httpControls.push(body.command+'-forged-field');}
 await page.close();
 scratch=await fs.mkdtemp(path.join(os.tmpdir(),'response-renderer-'));
 for(const [id,from,to] of [
 ['false-refund','Charges ${s.charges}','Charges ${2}'],
 ['premature-hit',"$('target-hp').value=s.enemyHp;","$('target-hp').value=s.pending?48:s.enemyHp;"]]){
  const dest=path.join(scratch,id);await fs.cp(web,dest,{recursive:true});let source=await fs.readFile(path.join(dest,'app.js'),'utf8');assert.ok(source.includes(from));source=source.replace(from,to);await fs.writeFile(path.join(dest,'app.js'),source);
  const mutantUrl=await start(dest),mp=await open(mutantUrl);await responseSetup(mp,mutantUrl);let detected=false;
  try{await doResponse(mp,mutantUrl,'commit');}catch(error){detected=true;negatives.push({id,detected:true,reason:String(error)});}
  assert.ok(detected,'Actual isolated renderer mutant detected');await mp.close();
 }
 check('Both actual isolated false renderers rejected',negatives.length===2);assert.deepEqual(errors,[]);assert.deepEqual(await identities(),before,'Producer closure stable');complete=true;
 await fs.writeFile(path.join(output,'browser.json'),JSON.stringify({schema_version:1,kind:'actual_response_browser',checks:{passed:controls.length,failed:0},http_checks:{passed:httpControls.length,failed:0},controls,httpControls,states,negatives,input_hashes:before,source_stable:true,limits:'Overlapping software controls, not participants, balance, Ruby, Unity/Windows/Steam or canon.'},null,2)+'\n');
 console.log('PASS: '+controls.length+' actual response Chromium controls and '+httpControls.length+' HTTP negatives');
}finally{
 if(browser)await browser.close();for(const child of children)await stop(child);if(scratch)await fs.rm(scratch,{recursive:true,force:true});await fs.writeFile(path.join(output,'hosts.json'),JSON.stringify({complete,logs,errors},null,2)+'\n');
}
