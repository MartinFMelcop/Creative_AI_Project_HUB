'use strict';
let current=null;let observation=null;let pending=false;let uncertain=true;
const $=id=>document.getElementById(id);
const buttons=()=>document.querySelectorAll('[data-command]');
const passiveNames={none:'None',lining:'Lining','last-thread':'Last thread'};
function availability(){
 buttons().forEach(b=>b.disabled=pending||uncertain||(observation?.phase==='preparation'&&['strike','bash','guard','treat','cleanse','retreat'].includes(b.dataset.command))||(b.dataset.command==='begin'&&observation?.phase!=='preparation'));
 const response=current?.responsePractice===true;const waiting=current?.pending!==null&&current?.pending!==undefined;
 buttons().forEach(b=>{const c=b.dataset.command;if(['commit','release','break-ward'].includes(c))b.disabled=pending||uncertain||observation?.phase!=='active'||!response||(c==='commit'?waiting||current.charges<1:!waiting||(c==='break-ward'&&(!current.pending.ward||current.charges<1)));else if(waiting&&['strike','bash','guard','treat','cleanse','retreat'].includes(c))b.disabled=true;});
 $('reconnect').hidden=!uncertain;$('reconnect').disabled=pending;
 for(const id of ['passive-select','armor-select','equip-passive'])$(id).disabled=pending||uncertain||observation?.phase!=='preparation';
}
function valid(s){return s&&['toxic','heated'].includes(s.profile)&&Number.isInteger(s.round)&&s.round>=0&&Number.isInteger(s.hp)&&s.hp>=0&&s.hp<=100&&s.maxHp===100&&Number.isInteger(s.enemyHp)&&s.enemyHp>=0&&s.enemyHp<=96&&Number.isInteger(s.charges)&&s.charges>=0&&s.charges<=2&&Array.isArray(s.effects)&&s.effects.every(e=>['Poison','Bleed','Burn','Disarm'].includes(e.effect)&&Number.isInteger(e.remaining)&&e.remaining>0)&&Array.isArray(s.events)&&s.events.every(e=>typeof e==='string')&&['active','secured','defeated','withdrawn'].includes(s.outcome)&&typeof s.last==='string'&&typeof s.threat==='string'&&Object.hasOwn(passiveNames,s.passive)&&['light','heavy'].includes(s.armor)&&typeof s.rescueSpent==='boolean'&&typeof s.responsePractice==='boolean'&&typeof s.wardAvailable==='boolean'&&(s.pending===null||(s.pending&&typeof s.pending.ward==='boolean'&&Number.isInteger(s.pending.items)&&s.pending.items>=1&&s.pending.items<=3))&&Array.isArray(s.resolution)&&s.resolution.every(x=>typeof x==='string');}
function passiveView(passive,armor,spent,hit,preparing){
 if(!Object.hasOwn(passiveNames,passive)||!['light','heavy'].includes(armor)||typeof spent!=='boolean')throw Error('Invalid passive observation');
 $('passive-glyph').dataset.passive=passive;$('passive-glyph').dataset.spent=String(spent);
 $('passive-picture').textContent=passive==='last-thread'?`Last thread, ${preparing?'prepared for next encounter':spent?'already spent in this encounter':'unused in this encounter'}.`:passive==='lining'?`Lining, ${armor} armor context.`:'No passive selected.';
 $('passive-state').textContent=passiveNames[passive]+(preparing?' · prepared':'');$('armor-state').textContent=(armor==='heavy'?'Heavy':'Light')+' context'+(passive==='lining'?(armor==='heavy'?' · Lining eligible for physical direct contact':' · Lining does not apply in light context'):'');
 const rescueText=passive!=='last-thread'?'No rescue passive selected.':preparing?'One interception becomes available only when the prepared encounter begins.':spent?'Spent this encounter. No further fatal direct hit can be intercepted.':'Unused this encounter. One qualifying fatal direct hit may leave 1 HP.';
 $('rescue-spent').textContent=rescueText;$('rescue-spent').dataset.spent=String(spent);
 if(preparing)$('contact-detail').textContent='No encounter is running. Preparation has not received a hit or spent a rescue.';
 else if(!hit)$('contact-detail').textContent='No direct contact is recorded for this observation.';
 else {
  const fields=['incoming','effectiveDamage','hpBefore','hpAfter','damageReduced','actualHpLost','avoidedHpLoss'];if(hit.kind!=='PhysicalDirect'||fields.some(k=>!Number.isInteger(hit[k])||hit[k]<0)||typeof hit.rescued!=='boolean')throw Error('Invalid direct-contact observation');
  $('contact-detail').textContent=`Last physical direct contact: incoming ${hit.incoming}; effective damage ${hit.effectiveDamage}; reduction ${hit.damageReduced}; actual HP lost ${hit.actualHpLost}; avoided HP loss ${hit.avoidedHpLoss}; HP at that hit ${hit.hpBefore} → ${hit.hpAfter}.`+(hit.rescued?' Last thread intercepted this hit. Later DOT still resolves; this is not a survival or victory receipt.':' No fatal-hit interception occurred.');
 }
}
function responseView(s){
 if(s===null){$('response-state').textContent=observation.preparation.responses?'Response practice prepared; no encounter or cast exists yet.':'Classic practice prepared; no encounter exists yet.';$('response-state').dataset.pending='false';$('ward-state').textContent=observation.preparation.responses?'One ward reserve will be issued only when this new practice begins.':'';$('response-resolution').replaceChildren();return;}
 const enabled=s?.responsePractice===true,waiting=enabled&&s.pending!==null;
 const pendingObserved=s?.pending??null;
 $('response-state').textContent=!enabled?'Classic practice. No response window.':waiting?'Cast paid; response pending. No strike damage, contact, DOT or round has resolved yet.':s.outcome==='active'?'Response practice active. A committed strike spends one shared charge before its effect.':'Response practice ended. Resolution log is historical.';
 $('response-state').dataset.pending=String(waiting);
 $('ward-state').textContent=!enabled?'No ward policy in classic practice.':s.outcome!=='active'?'Encounter ended; the ward reserve is historical, not a new opportunity.':waiting&&pendingObserved.ward?'Ward queued; its one reserve is spent. Choose Release or pay to Break ward.':s.wardAvailable?'Target has one ward reserve.':'Target ward reserve spent. No new ward is supplied.';
 $('response-resolution').replaceChildren(...(s?.resolution??[]).map(t=>{const e=document.createElement('li');e.textContent=t;return e;}));
}
function render(s){
 responseView(s);document.body.dataset.phase=observation.phase;$('phase-state').textContent=observation.phase==='preparation'?'PREPARATION / NO ENCOUNTER':observation.phase==='ended'?'ENCOUNTER ENDED':'ACTIVE / PREPARATION LOCKED';
 if(s===null){
  current=null;const p=observation.preparation;passiveView(p.passive,p.armor,false,null,true);
  $('stats').replaceChildren(...[`Prepared profile ${p.profile}`,'No encounter begun','No damage or rounds resolved'].map(t=>{const n=document.createElement('span');n.textContent=t;return n;}));$('effects').replaceChildren();document.querySelector('.arena').className='arena preparation';$('player-hp').value=0;$('target-hp').value=0;$('threat').textContent='No encounter yet. Apply one whole preparation, then explicitly Begin.';$('last').textContent='Prepared state only. Begin creates a fresh encounter with its actual initial effects and resources.';$('events').replaceChildren();return;
 }
 if(!valid(s))throw new Error('Invalid state response');
 current=s;
 const passiveObserved = s.passive;
 const rescueObserved = s.rescueSpent;
 passiveView(passiveObserved,s.armor,rescueObserved,s.lastHit,false);
 $('stats').replaceChildren(...[`Profile ${s.profile}`,`Round ${s.round}`,`HP ${s.hp}/${s.maxHp}`,`Target ${s.enemyHp}`,`Charges ${s.charges}`,`Outcome ${s.outcome}`].map(t=>{const n=document.createElement('span');n.textContent=t;return n;}));$('effects').replaceChildren(...(s.effects.length?s.effects.map(e=>`${e.effect} · ${e.remaining} rounds`):['No active effects.']).map(t=>{const n=document.createElement('span');n.textContent=t;return n;}));document.querySelector('.arena').className='arena '+s.outcome+' '+s.effects.map(e=>e.effect.toLowerCase()).join(' ');$('player-hp').value=s.hp;$('target-hp').value=s.enemyHp;$('threat').textContent='Next: '+s.threat;$('last').textContent=s.last;$('events').replaceChildren(...s.events.map(t=>{const n=document.createElement('li');n.textContent=t;return n;}));
}
async function request(path,options){const controller=new AbortController();const timer=setTimeout(()=>controller.abort(),8000);try{const response=await fetch(path,{...options,signal:controller.signal});if(!response.ok)throw new Error(`Response ${response.status}`);return await response.json();}finally{clearTimeout(timer);}}
async function run(command){if(pending||(command!==null&&uncertain))return null;pending=true;availability();try{const result=command===null?await request('/api/state'):await request('/api/command',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({command})});if(command!==null&&(typeof result.accepted!=='boolean'||result.command!==command||!Number.isInteger(result.sequence)))throw new Error('Invalid command receipt');if(!['preparation','active','ended'].includes(result.phase)||!result.preparation||!Object.hasOwn(passiveNames,result.preparation.passive)||!['light','heavy'].includes(result.preparation.armor)||!['toxic','heated'].includes(result.preparation.profile)||(result.phase==='preparation')!==(result.state===null))throw Error('Invalid lifecycle observation');observation=result;render(result.state);$('passive-select').value=result.preparation.passive;$('armor-select').value=result.preparation.armor;uncertain=false;return result;}catch(error){uncertain=true;$('last').textContent='Result unknown. Actions paused. Reconnect observes current state without retrying the command. '+error.message;throw error;}finally{pending=false;availability();}}
async function command(value){return run(value);}
document.querySelectorAll('[data-command]').forEach(button=>button.addEventListener('click',()=>{command(button.dataset.command).catch(()=>{});}));$('equip-passive').addEventListener('click',()=>command('equip '+$('passive-select').value+' '+$('armor-select').value).catch(()=>{}));$('reconnect').addEventListener('click',()=>run(null).catch(()=>{}));
window.combatStudy={snapshot:()=>current?JSON.parse(JSON.stringify(current)):null,observation:()=>observation?JSON.parse(JSON.stringify(observation)):null,command,reconnect:()=>run(null)};
availability();run(null).catch(()=>{});
