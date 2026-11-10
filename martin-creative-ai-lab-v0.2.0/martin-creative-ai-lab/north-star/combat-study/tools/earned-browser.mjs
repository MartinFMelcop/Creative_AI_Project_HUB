import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';

// One causal acquisition journey; no new combat-policy or initiative matrix.
export async function earnedControls({check,browser,start,study,out,negative}) {
 const controls=[],states={},negatives=[];let complete=false,failure=null,scratch;
 const verify=(id,yes)=>{check(id,yes);controls.push(id);};
 async function owner(web=path.join(study,'Host/web')) {
  const url=await start(web),page=await browser.newPage();await page.goto(url);await page.waitForFunction(()=>window.combatStudy?.snapshot());
  const state=async()=>{const r=await fetch(url+'/api/state');assert.equal(r.status,200);return r.json();};
  const act=c=>page.evaluate(c=>window.combatStudy.command(c),c);
  const post=command=>fetch(url+'/api/command',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({command})});
  return {url,page,state,act,post};
 }
 async function fidelity(page,actual) {
  assert.equal(await page.locator('#earned-progress').getAttribute('data-unlocked'),String(actual.earned?.unlocked===true),'Earned availability follows actual owner');
  assert.equal(await page.locator('#earned-progress').getAttribute('data-mode'),String(actual.earned?.mode??''),'Earned mode follows actual owner');
 }
 try {
  const o=await owner(),{page,state,act,post}=o;
  verify('Fresh Room has no earned receipt',!(await state()).earned?.unlocked);
  await page.locator('#prepare-earned-toxic').click();await page.waitForFunction(()=>document.querySelector('#begin-passive')?.disabled===false);
  let current=await state();states.locked=current;
  verify('Earned entry is classic None draft with no acquisition',current.phase==='preparation'&&current.preparation.passive==='none'&&!current.preparation.responses&&!current.preparation.controls&&!current.preparation.initiative&&!current.earned.unlocked&&current.earned.receipt===null);
  const locked=JSON.stringify(current),forged=await post('equip lining heavy');verify('Forged locked passive refuses before sequence or preparation mutation',forged.status===400&&JSON.stringify(await state())===locked);
  await act('begin');const active=JSON.stringify(await state());
  for(const command of ['prepare toxic','prepare earned heated','restart toxic']) {const r=await post(command);verify('Active earned attempt refuses '+command+' atomically',r.status===400&&JSON.stringify(await state())===active);}
  await act('guard');verify('Actual unearned None guard retains 81 HP',(await state()).state.hp===81);
  await act('retreat');verify('Withdrawal cannot acquire practice ability',!(await state()).earned.unlocked&&(await state()).earned.receipt===null);
  await act('prepare earned toxic');await act('begin');for(let i=0;i<3;i++)await act('strike');
  const before=await state();await page.locator('#inspect-action').selectOption('strike');await page.locator('#inspect').click();await page.waitForFunction(()=>window.combatStudy.forecastSnapshot()!==null);
  const forecast=await page.evaluate(()=>window.combatStudy.forecastSnapshot());states.forecast={before,forecast};
  verify('Forecasted first clear cannot grant acquisition or mutate owner',forecast.forecast.state.outcome==='secured'&&!before.earned.unlocked&&JSON.stringify(await state())===JSON.stringify(before));
  let sent=0;await page.route('**/api/command',async route=>{sent++;await route.fetch();await route.abort('failed');});await page.locator('#confirm-forecast').click();await page.locator('#reconnect').waitFor({state:'visible'});await page.waitForFunction(()=>!document.querySelector('#reconnect').disabled);
  const won=await state();states.won=won;
  verify('Actual first None clear acquires once despite lost receipt',sent===1&&won.state.outcome==='secured'&&won.earned.unlocked&&won.earned.receipt?.kind==='earned-practice-clear'&&won.earned.receipt.sequence===won.sequence&&won.earned.receipt.attempt===won.earned.attempt&&won.earned.receipt.profile==='toxic');
  await page.unroute('**/api/command');await page.evaluate(()=>window.combatStudy.reconnect());await fidelity(page,won);
  verify('Reconnect observes acquisition without replaying confirmed strike',sent===1&&JSON.stringify(await state())===JSON.stringify(won));
  const receipt=JSON.stringify(won.earned.receipt);await page.reload();await page.waitForFunction(()=>window.combatStudy?.snapshot());await fidelity(page,await state());
  verify('Redraw preserves exact earned receipt',JSON.stringify((await state()).earned.receipt)===receipt);
  await act('prepare earned toxic');current=await state();verify('Later earned preparation keeps receipt but starts with None',current.preparation.passive==='none'&&JSON.stringify(current.earned.receipt)===receipt);
  await page.locator('#passive-select').selectOption('lining');await page.locator('#armor-select').selectOption('heavy');await page.locator('#equip-passive').click();await page.waitForFunction(()=>document.querySelector('#passive-state').textContent.includes('Lining'));await act('begin');await act('guard');states.earnedGuard=await state();
  verify('Acquired chosen Lining reaches actual owner and changes same guard to82',states.earnedGuard.state.passive==='lining'&&states.earnedGuard.state.armor==='heavy'&&states.earnedGuard.state.hp===82&&JSON.stringify(states.earnedGuard.earned.receipt)===receipt);
  await act('retreat');await act('prepare earned toxic');await act('begin');for(let i=0;i<4;i++)await act('strike');verify('Later clear cannot replace first acquisition receipt',JSON.stringify((await state()).earned.receipt)===receipt);await page.close();
  const defeat=await owner();await defeat.act('prepare earned toxic');await defeat.act('begin');for(let i=0;i<12&&(await defeat.state()).state.outcome==='active';i++)await defeat.act('guard');const lost=await defeat.state();states.defeat=lost;
  verify('Actual fresh earned defeat has no receipt or unlock',lost.state.outcome==='defeated'&&!lost.earned.unlocked&&lost.earned.receipt===null);await defeat.page.close();
  const preset=await owner();for(let i=0;i<4;i++)await preset.act('strike');const free=await preset.state();states.preset=free;verify('Free preset victory does not qualify as earned acquisition',free.state.outcome==='secured'&&!free.earned?.unlocked&&!free.earned?.receipt);await preset.page.close();
  scratch=await fs.mkdtemp(path.join(os.tmpdir(),'earned-render-'));await fs.cp(path.join(study,'Host/web'),scratch,{recursive:true});const script=path.join(scratch,'app.js'),source=await fs.readFile(script,'utf8'),seam='const earnedUnlockedObserved = earned?.unlocked === true;';assert.equal(source.split(seam).length,2);await fs.writeFile(script,source.replace(seam,'const earnedUnlockedObserved = true;'));
  const bad=await owner(scratch);await bad.act('prepare earned toxic');const actualBad=await bad.state();let detected=false;try{await fidelity(bad.page,actualBad);}catch(error){if(error.code!=='ERR_ASSERTION'||!error.message.includes('Earned availability follows actual owner'))throw error;detected=true;negatives.push({id:'false-earned-unlock-renderer',detected,actual_unlocked:actualBad.earned.unlocked,assertion:error.message});}
  verify('False acquired renderer is detected against actual source owner',detected);negative.push(...negatives);await bad.page.close();complete=true;
 } catch(error){failure=error.stack;throw error;}
 finally {await fs.writeFile(path.join(out,'earned-browser.json'),JSON.stringify({complete,failure,controls,states,negatives,scope:'Original room-owned practice acquisition through existing Chromium consumer; no historical class acquisition, persistence, human meaning or balance claim.'},null,2)+'\n');if(scratch)await fs.rm(scratch,{recursive:true,force:true});}
}
