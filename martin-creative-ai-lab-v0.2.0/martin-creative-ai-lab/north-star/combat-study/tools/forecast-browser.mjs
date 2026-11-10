import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';

export async function forecastControls({page,url,state,check,browser,start,study,out,negative}){
 const controls=[],states={},negatives=[];let complete=false,failure=null,scratch;
 const verify=(id,yes)=>{check(id,yes);controls.push(id);};
 const act=c=>page.evaluate(c=>window.combatStudy.command(c),c);
 async function inspect(command){await page.locator('#inspect-action').selectOption(command);await page.locator('#inspect').click();await page.waitForFunction(()=>window.combatStudy.forecastSnapshot()!==null);return page.evaluate(()=>window.combatStudy.forecastSnapshot());}
 async function confirm(){await page.locator('#confirm-forecast').click();await page.waitForFunction(()=>window.combatStudy.forecastSnapshot()===null&&!document.querySelector('#reconnect').hidden||window.combatStudy.forecastSnapshot()===null&&!document.querySelector('#inspect').disabled);}
 try{
  await act('restart toxic');const before=await state();const projected=await inspect('guard');states.inspected={before,projected};
  verify('Forecast is conditional while complete live observation remains exact',JSON.stringify(await state())===JSON.stringify(before)&&projected.forecast.state.hp===81&&projected.forecast.state.round===1&&await page.locator('#stats').textContent().then(t=>t.includes('HP 100/100')));
  assert.equal(Number(await page.locator('#forecast-state').getAttribute('data-hp')),projected.forecast.state.hp,'Forecast HP follows actual branch');
  await inspect('guard');verify('Repeated inspection leaves sequence and costs exact',JSON.stringify(await state())===JSON.stringify(before));
  await page.screenshot({path:path.join(out,'forecast.png'),fullPage:true});
  await confirm();states.confirmed=await state();verify('Explicit confirmation equals the one inspected action',JSON.stringify(states.confirmed.state)===JSON.stringify(projected.forecast.state)&&states.confirmed.sequence===before.sequence+1);
  const stale=await inspect('guard');await fetch(url+'/api/command',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({command:'guard'})});const externallyChanged=await state();await confirm();
  await page.locator('#reconnect').waitFor({state:'visible'});verify('Stale inspection confirmation refuses without owner mutation',JSON.stringify(await state())===JSON.stringify(externallyChanged)&&await page.locator('#confirm-forecast').isDisabled()&&stale.sequence!==externallyChanged.sequence);
  await page.evaluate(()=>window.combatStudy.reconnect());verify('Explicit read discards stale projection without replay',JSON.stringify(await state())===JSON.stringify(externallyChanged)&&await page.evaluate(()=>window.combatStudy.forecastSnapshot()===null));
  await act('restart toxic');await inspect('guard');let sent=0;
  await page.route('**/api/command',async route=>{sent++;await route.fetch();await route.abort('failed');});await page.locator('#confirm-forecast').click();await page.locator('#reconnect').waitFor({state:'visible'});await page.waitForFunction(()=>!document.querySelector('#reconnect').disabled);const lost=await state();
  verify('Lost confirmed receipt spends once and quarantines confirmation',sent===1&&lost.state.hp===81&&lost.state.round===1&&await page.locator('#confirm-forecast').isDisabled());
  await page.unroute('**/api/command');await page.evaluate(()=>window.combatStudy.reconnect());verify('Lost confirmation is observed and never replayed',sent===1&&JSON.stringify(await state())===JSON.stringify(lost));
  await act('prepare responses toxic');await act('begin');const pendingBefore=await state();const cast=await inspect('commit');
  verify('Commit forecast stops at response choice without free release',cast.forecast.boundary==='response'&&cast.forecast.state.round===0&&cast.forecast.state.charges===1&&cast.forecast.state.enemyHp===96&&JSON.stringify(await state())===JSON.stringify(pendingBefore));
  await confirm();const pending=await state();const released=await inspect('release');const broken=await inspect('break-ward');states.response={pending,released,broken};
  verify('One pending owner supports distinct conditional response costs',released.forecast.state.charges===1&&released.forecast.state.enemyHp===96&&broken.forecast.state.charges===0&&broken.forecast.state.enemyHp===48&&JSON.stringify(await state())===JSON.stringify(pending));
  await confirm();verify('Confirming inspected break resolves only that actual chain',JSON.stringify((await state()).state)===JSON.stringify(broken.forecast.state));
  await act('restart toxic');await inspect('guard');const interrupted=await state();await page.evaluate(()=>window.dispatchEvent(new Event('blur')));
  verify('Interruption discards inspection without action',await page.evaluate(()=>window.combatStudy.forecastSnapshot()===null)&&await page.locator('#confirm-forecast').isDisabled()&&JSON.stringify(await state())===JSON.stringify(interrupted));
  await page.evaluate(async()=>{const pending=window.combatStudy.forecast('guard');window.dispatchEvent(new Event('blur'));await pending;});
  verify('Late inspection reply cannot rearm interrupted confirmation',await page.evaluate(()=>window.combatStudy.forecastSnapshot()===null)&&await page.locator('#confirm-forecast').isDisabled()&&JSON.stringify(await state())===JSON.stringify(interrupted));
  for(const c of [
   {id:'extra forecast field',endpoint:'forecast',body:'{"command":"guard","hp":100}'},
   {id:'duplicate forecast command',endpoint:'forecast',body:'{"command":"guard","command":"strike"}'},
   {id:'forecast lifecycle command',endpoint:'forecast',body:'{"command":"restart toxic"}'},
   {id:'unknown reviewed field',endpoint:'command',body:'{"command":"guard","reviewed_sequence":0,"hp":100}'},
   {id:'malformed reviewed sequence',endpoint:'command',body:'{"command":"guard","reviewed_sequence":"0"}'},
  ]){const original=await state();const response=await fetch(url+'/api/'+c.endpoint,{method:'POST',headers:{'Content-Type':'application/json'},body:c.body});verify('HTTP refuses '+c.id+' without mutation',response.status===400&&JSON.stringify(await state())===JSON.stringify(original));}
  scratch=await fs.mkdtemp(path.join(os.tmpdir(),'forecast-render-'));await fs.cp(path.join(study,'Host/web'),scratch,{recursive:true});const script=path.join(scratch,'app.js'),source=await fs.readFile(script,'utf8'),target='const forecastHpObserved = f.state.hp;';assert.equal(source.split(target).length,2);await fs.writeFile(script,source.replace(target,'const forecastHpObserved = 100;'));
  const badUrl=await start(scratch),bad=await browser.newPage();await bad.goto(badUrl);await bad.waitForFunction(()=>window.combatStudy?.snapshot());const genuine=await bad.evaluate(()=>window.combatStudy.forecast('guard'));let detected=false;
  try{assert.equal(Number(await bad.locator('#forecast-state').getAttribute('data-hp')),genuine.forecast.state.hp,'Forecast HP follows actual branch');}catch(error){if(error.code!=='ERR_ASSERTION'||!error.message.includes('Forecast HP follows actual branch'))throw error;detected=true;negatives.push({id:'false-forecast-hp-renderer',detected,actual_projected_hp:genuine.forecast.state.hp,drawn_hp:100,assertion:error.message});}
  verify('False conditional HP renderer is detected against actual branch',detected);negative.push(...negatives);await bad.close();complete=true;
 }catch(error){failure=error.stack;throw error;}
 finally{await fs.writeFile(path.join(out,'forecast-browser.json'),JSON.stringify({complete,failure,controls,states,negatives,scope:'Actual existing C# owner through Chromium; bounded conditional information, not independent player understanding or balance.'},null,2)+'\n');if(scratch)await fs.rm(scratch,{recursive:true,force:true});}
}
