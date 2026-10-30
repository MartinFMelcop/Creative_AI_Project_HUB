'use strict';
(() => {
 const $=id=>document.getElementById(id);
 let state=null,busy=false,uncertain=false,generation=0;
 const api={get state(){return state;},get status(){return uncertain?'read-required':busy?'pending':'ready';},send,read,render};window.memoryStudy=api;
 function render(s){
  if(!s||!Array.isArray(s.benches))throw Error('Incomplete owner observation');state=s;
  for(const k of ['parts','coins','turn','sequence'])$(k).textContent=String(s[k]);$('notice').textContent=s.text;
  document.body.dataset.complete=String(s.complete);document.body.dataset.policy=s.policy;$('policy-note').textContent=s.policy==='ordered'?'Ordered commission: the east fitting also requires actual west delivery. No expression supplies a fitting or waives its cost.':'Independent commissions: either bench may supply its own fitting after actual local work and payment.';
  for(const b of s.benches){
   const eligibleObserved = Boolean(b.eligible);
   const recentObserved = Boolean(b.recent);
   const deliveredObserved = Boolean(b.delivered);
   $(b.id).dataset.recent=String(recentObserved);$(b.id).dataset.fitted=String(deliveredObserved);$(b.id).dataset.eligible=String(eligibleObserved);
   $(b.id+'-condition').textContent=`Authored condition: ${b.condition_expression} · ${b.condition_complete?'known facts':'incomplete facts'} · ${b.condition_satisfied?'satisfied':'not satisfied'}. Eligibility is not acquired custody.`;
   $(b.id+'-help').textContent=b.helped?'Yes':'No';$(b.id+'-support').textContent=b.support?'Yes':'No';$(b.id+'-recent').textContent=recentObserved?'Yes':'No';$(b.id+'-fitted').textContent=deliveredObserved?'Yes':'No';
   $(b.id+'-status').textContent=deliveredObserved?'FITTING ACQUIRED':eligibleObserved?'WINDOW OPEN':b.helped?'PAST WORK RETAINED':'NO OBSERVED HELP';
   $(b.id+'-window').textContent=deliveredObserved?'The actual fitting remains acquired after any later expiry or withdrawal.':eligibleObserved?`This exact bench can act now. Demonstration expires at turn ${b.expires}; the service checks before its one-turn cost.`:b.recent?`Demonstration current until turn ${b.expires}, but the full service conditions are not met.`:b.helped?'Past help is still recorded. The recent demonstration is absent or expired; a fresh demonstration costs a part and a turn.':'No local help or demonstration has been observed. Another bench cannot supply either fact.';
   $(b.id+'-help-button').textContent=b.helped?'Demonstrate again · 1 part':'Help here · 1 part';
   $(b.id+'-picture').textContent=`${b.id} bench: past help ${b.helped?'observed':'not observed'}, current demonstration ${recentObserved?'present':'absent'}, fitting ${deliveredObserved?'acquired':'not acquired'}.`;
  }
  $('history').replaceChildren(...s.history.map(f=>{const li=document.createElement('li');li.textContent=`Turn ${f.turn}: ${f.command}${f.bench?' at '+f.bench:''}. Remaining ${f.parts} parts, ${f.coins} coins; actual fittings ${f.fittings}.`;return li;}));
  controls();
 }
 function controls(){for(const b of document.querySelectorAll('button'))b.disabled=busy||uncertain;$('read').disabled=busy;if(!state)return;for(const b of state.benches){$(b.id+'-help-button').disabled=busy||uncertain||b.delivered||state.parts<1;$(b.id+'-fit-button').disabled=busy||uncertain||!b.eligible;$(b.id+'-decline-button').disabled=busy||uncertain||(!b.support&&!b.recent);}}
 async function read(){if(busy)return;busy=true;controls();const g=++generation;try{const r=await fetch('/state',{cache:'no-store'});if(!r.ok)throw Error('Read refused');const s=await r.json();if(g!==generation)return;uncertain=false;render(s);$('connection').textContent='Current facts read. No command retried.';}catch(e){uncertain=true;$('connection').textContent=e.message+' Read current facts before acting.';}finally{busy=false;controls();}}
 async function send(command,bench){if(busy||uncertain||!state)throw Error('Read current facts before acting');busy=true;controls();const g=generation;const data={command,revision:state.sequence};if(bench!==undefined)data.bench=bench;try{const r=await fetch('/command',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)});if(!r.ok)throw Error('Receipt unavailable');const s=await r.json();if(g!==generation)throw Error('Interrupted response quarantined');render(s);$('connection').textContent='Actual owner response. No automatic retries.';return s;}catch(e){uncertain=true;$('connection').textContent='Outcome uncertain: '+e.message+'. Read current facts; do not repeat blindly.';throw e;}finally{busy=false;controls();}}
 function invoke(command,bench){send(command,bench).catch(()=>{});}
 for(const id of ['west','east']){$(id+'-help-button').onclick=()=>invoke(state.benches.find(b=>b.id===id).helped?'demonstrate':'help',id);$(id+'-fit-button').onclick=()=>invoke('serve',id);$(id+'-decline-button').onclick=()=>invoke('decline',id);}
 $('wait').onclick=()=>invoke('wait');$('read').onclick=read;
 function interrupt(){if(busy){generation++;uncertain=true;$('connection').textContent='Interrupted. An action may have committed; explicitly read current facts.';controls();}}
 window.addEventListener('blur',interrupt);window.addEventListener('offline',interrupt);document.addEventListener('visibilitychange',()=>{if(document.hidden)interrupt();});read();
})();
