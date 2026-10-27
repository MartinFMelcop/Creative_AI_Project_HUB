'use strict';
(() => {
 const $=id=>document.getElementById(id);
 let state=null,busy=false,uncertain=false,generation=0;
 const accents={copper:'#ae794f',teal:'#5c9997',violet:'#9b88b1'};
 window.fieldJourney={get state(){return state;},get status(){return uncertain?'read-required':busy?'pending':'ready';},send,read,render};
 function proposal(){return{handle:$('handle').value,accent:$('accent').value,class_id:$('class_id').value,background_id:$('background_id').value,slots:[1,2,3,4].map(n=>$('slot'+n).value||null)};}
 function adopt(d){if(!d)return;for(const key of ['handle','accent','class_id','background_id'])$(key).value=d[key];d.slots.forEach((value,i)=>$('slot'+(i+1)).value=value||'');}
 function render(s){
  if(!s?.intake?.state||!s?.memory||!Array.isArray(s.fittings))throw Error('Incomplete actual journey observation');
  state=s;const card=s.intake,e=card.state,m=s.memory,id=card.identity;
  const completeObserved = Boolean(s.intake.state.complete);
  document.body.dataset.confirmed=String(card.confirmed);document.body.dataset.workshopClosed=String(s.workshop_closed);document.body.dataset.complete=String(completeObserved);
  $('confirmed-name').textContent=id?id.handle:'Not confirmed';$('identity-discipline').textContent=id?`${id.class_id} / ${id.background_id}`:'No committed preparation';$('identity-accent').textContent=id?`${id.accent} cloth accent · expression only`:'Expression has no combat advantage.';$('identity-slots').textContent=id?`Equipped: ${id.slots.map(x=>x||'empty').join(' / ')}`:'No confirmed actions.';
  $('card-status').textContent=card.confirmed?card.pending?'AMENDMENT PENDING':'CONFIRMED':'UNCONFIRMED';$('draft-status').textContent=`Draft ${card.draft_revision} · review ${card.reviewed_revision===null?'none':card.reviewed_revision}`;
  $('review-text').textContent=card.reviewed_revision===card.draft_revision?`Reviewed: ${card.draft.handle}, ${card.draft.accent}, ${card.draft.class_id} / ${card.draft.background_id}; slots ${card.draft.slots.map(x=>x||'empty').join(', ')}. Confirmation applies this whole submitted card, not unsaved form edits, without granting supplies or restoring resources.`:'Submit a complete proposal, then review its exact current version before confirming. Unsaved form edits are not part of a review. No step creates a fitting, rig, heal or encounter.';
  $('avatar-accent').setAttribute('fill',accents[id?.accent]||accents.copper);$('portrait-title').textContent=id?`${id.handle}, ${id.class_id}, ${id.accent} accent. Actual outfit ${e.rig}.`:'Unconfirmed traveler preview';
  $('portrait-plate').style.display=id&&e.rig==='Plate'?'':'none';$('portrait-trail').style.display=id&&e.rig==='Trail'?'':'none';$('portrait-brace').style.display=id?.class_id==='anchor'?'':'none';$('portrait-draw').style.display=id?.class_id==='lure'?'':'none';
  $('workshop-stage').textContent=s.workshop_closed?'HISTORICAL / AT DEPARTURE':'WORKSHOP OPEN';
  $('workshop-context').textContent=s.workshop_closed?`${id?.handle||'This person'} has departed. These are the last workshop facts observed before leaving. The road does not observe either worker's presence, return or current support.`:card.confirmed?`${id.handle}'s local work must actually occur at each bench. An open opportunity supplies a fitting only after its own paid service.`:'Confirm your person before any paid workshop work. A draft is not permission to spend either pouch.';
  for(const key of ['parts','coins'])$(key).textContent=String(m[key]);$('workshop-turn').textContent=String(m.turn);
  for(const b of m.benches){
   const panel=$(b.id+'-bench');panel.dataset.recent=String(b.recent);panel.dataset.historical=String(s.workshop_closed);
   $(b.id+'-helped').textContent=b.helped?'Yes':'No';$(b.id+'-support').textContent=b.support?'Yes':'No';$(b.id+'-recent').textContent=b.recent?'Yes':'No';
   $(b.id+'-status').textContent=s.workshop_closed?'RECORDED BEFORE LEAVING':b.delivered?'FITTING ACQUIRED':b.eligible?'WINDOW OPEN':b.helped?'PAST WORK RETAINED':'NO OBSERVED HELP';
   $(b.id+'-window').textContent=s.workshop_closed?`Recorded at workshop turn ${m.turn}: help ${b.helped?'observed':'not observed'}, support ${b.support?'present':'absent'}, recent demonstration ${b.recent?'present':'absent'}. This is historical knowledge, not a fresh observation.`:b.delivered?'This bench already supplied its one fitting. Expiry or withdrawal cannot undo acquisition.':b.eligible?`This exact bench can supply a fitting now, before its one-turn cost. Demonstration expires at workshop turn ${b.expires}.`:b.helped?'Actual help remains known here. A fresh demonstration costs one part and one workshop turn; another bench cannot provide it.':'No actual help observed here. A different bench cannot stand in for it.';
   $(b.id+'-help').textContent=b.helped?'Demonstrate again · 1 part':'Help here · 1 part';$(b.id+'-picture').textContent=s.workshop_closed?`${b.id} workbench, historical observation at departure. Worker presence is not observed from the road.`:`${b.id} workbench, local worker and ${b.recent?'current':'absent'} recent demonstration.`;
  }
  for(const f of s.fittings){
   const availableObserved = Boolean(f.available);
   const panel=$(f.bench+'-fitting');panel.dataset.acquired=String(f.acquired);panel.dataset.spent=String(f.spent);panel.dataset.available=String(availableObserved);
   $(f.bench+'-fitting-state').textContent=f.spent?'Spent in actual assembly':availableObserved?'Acquired · available':'Not acquired';
   $(f.bench+'-fitting-history').textContent=f.acquired?f.spent?`${f.bench} supplied this fitting; it was used assembling a ${f.rig} rig. History stays true; it cannot be spent again.`:`Actually supplied by ${f.bench}. Later workshop expiry or withdrawal cannot revoke it.`:'No fitting has been supplied here.';
  }
  const quantity=name=>e.inventory[name]??0;$('field-materials').textContent=`${quantity('fiber')} FIBER / ${quantity('binder')} BINDER`;$('rig-stock').textContent=`Actual stock: ${quantity('trail_rig')} Trail rigs · ${quantity('plate_rig')} Plate rigs`;
  $('assembly-list').replaceChildren(...s.assembly_receipts.map(r=>{const li=document.createElement('li');li.textContent=`${r.bench} fitting → ${r.rig} rig. One fitting, 2 fiber and 1 binder spent.`;return li;}));
  $('road-stage').textContent=completeObserved?'ACTUAL ROAD COMPLETE':e.active?`ENCOUNTER ${e.stage+1} / BEAT ${e.beat}`:e.attempts?e.won?'SURVEY COMPLETE':'ATTEMPT ENDED':'NOT DEPARTED';
  $('departure-warning').textContent=s.workshop_closed?'The workshop is closed for this journey. Only already assembled rigs remain available; card amendments cannot reopen it or restore supplies.':'First accepted entry closes the workshop for this whole session. Assemble the rigs you need before leaving. An unfunded later encounter is a real possible consequence.';
  $('health').textContent=e.attempts?String(e.health):'—';$('resolve').textContent=e.attempts?String(e.resolve):'—';$('beat').textContent=String(e.beat);$('level-xp').textContent=`${e.level} / ${e.xp}`;$('consumed-rigs').textContent=String(e.consumed_rigs);
  $('route-person').style.left=`${Math.max(0,Math.min(1,e.position/Math.max(1,card.required_position)))*100}%`;
  $('threat').textContent=e.active?card.threat:completeObserved?'Both actual encounters are complete. Consumed fittings, used rigs and remaining supplies stay accounted for.':e.attempts?e.won?'Survey victory earned progression, not final completion. Explicitly amend earned preparation if desired, then enter with an actual remaining rig.':'The attempt ended without victory. Its rig remains spent; an unfunded retry does not create new workshop access.':'No actual encounter has begun. Your confirmed discipline and acquired outfit remain independent choices.';
  $('earned-state').textContent=`Earned points remaining: ${e.unspent}. Vitality ${e.vitality}; Focus ${e.focus}. Between encounters, a new whole proposal may equip earned Dash. Confirmation never heals, refunds or reopens the workshop.`;
  for(let n=1;n<=4;n++)$('use-slot'+n).textContent=`Slot ${n}${id?.slots[n-1]?' · '+id.slots[n-1]:''}`;
  $('completion').hidden=!completeObserved;$('completion').textContent=`${id?.handle||'This person'} completed the actual road. Workshop acquisition and assembly remain distinct from that completion.`;
  $('sequence').textContent=String(s.sequence);$('notice').textContent=s.text;controls();
 }
 function controls(){
  for(const b of document.querySelectorAll('button'))b.disabled=busy||uncertain;$('read').disabled=busy;if(!state)return;
  const c=state.intake,e=c.state,ready=c.confirmed&&!c.pending,locked=e.active||e.complete,workshop=ready&&!state.workshop_closed;
  for(const el of $('draft-form').elements)el.disabled=busy||uncertain||locked;$('handle').readOnly=Boolean(c.confirmed);
  $('review').disabled=busy||uncertain||locked;$('confirm').disabled=busy||uncertain||locked||!c.pending||c.reviewed_revision!==c.draft_revision;
  for(const b of state.memory.benches){$(''+b.id+'-help').disabled=busy||uncertain||!workshop||state.memory.parts<1||b.delivered;$(''+b.id+'-serve').disabled=busy||uncertain||!workshop||!b.eligible;$(''+b.id+'-decline').disabled=busy||uncertain||!c.confirmed||state.workshop_closed||(!b.support&&!b.recent);}
  $('wait-window').disabled=busy||uncertain||!workshop;
  $('assemble').disabled=busy||uncertain||!workshop||!state.fittings.some(f=>f.available)||(e.inventory.fiber??0)<2||(e.inventory.binder??0)<1;
  $('begin').disabled=busy||uncertain||!ready||locked;
  for(const key of ['walk','wait','use-slot1','use-slot2','use-slot3','use-slot4'])$(key).disabled=busy||uncertain||!e.active;
  for(const key of ['focus','vitality'])$(key).disabled=busy||uncertain||locked||e.unspent<1;
 }
 async function read(){if(busy)return;busy=true;controls();const g=++generation;try{const r=await fetch('/state',{cache:'no-store'});if(!r.ok)throw Error('Read refused');const s=await r.json();if(g!==generation)return;uncertain=false;render(s);adopt(s.intake.draft);$('connection').textContent='Current facts read from the owner. No action was retried.';}catch(e){uncertain=true;$('connection').textContent='Unable to read: '+e.message+'. Read again before acting.';}finally{busy=false;controls();}}
 async function send(command,fields={}){if(busy||uncertain||!state)throw Error('Read current facts before another action');busy=true;controls();const g=generation;try{const r=await fetch('/command',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({command,revision:state.sequence,...fields})});if(!r.ok)throw Error('Command receipt unavailable');const s=await r.json();if(g!==generation)throw Error('Response quarantined after interruption');render(s);if(command==='draft')adopt(s.intake.draft);$('connection').textContent='Actual owner response. No automatic retry or clock conversion.';return s;}catch(e){uncertain=true;$('connection').textContent='Outcome uncertain: '+e.message+'. Explicitly read facts before acting again.';throw e;}finally{busy=false;controls();}}
 function invoke(command,fields={}){send(command,fields).catch(()=>{});}
 $('draft-form').onsubmit=e=>{e.preventDefault();invoke('draft',proposal());};$('review').onclick=()=>invoke('review');$('confirm').onclick=()=>invoke('confirm',{draft_revision:state.intake.draft_revision});
 for(const bench of ['west','east']){$(bench+'-help').onclick=()=>invoke(state.memory.benches.find(b=>b.id===bench).helped?'demonstrate':'help',{bench});$(bench+'-serve').onclick=()=>invoke('serve',{bench});$(bench+'-decline').onclick=()=>invoke('decline',{bench});}
 $('wait-window').onclick=()=>invoke('wait-window');$('assemble').onclick=()=>invoke('craft',{bench:$('benchselect').value,rig:$('fittingrig').value});$('begin').onclick=()=>invoke('begin',{rig:$('rig').value});for(const command of ['walk','wait'])$(command).onclick=()=>invoke(command);
 for(let n=1;n<=4;n++)$('use-slot'+n).onclick=()=>invoke('slot',{slot:n});for(const axis of ['focus','vitality'])$(axis).onclick=()=>invoke('allocate',{axis,points:1});$('read').onclick=read;
 function interrupt(){if(busy){generation++;uncertain=true;$('connection').textContent='Interrupted while an action may have committed. Read actual facts; do not repeat blindly.';controls();}}
 window.addEventListener('blur',interrupt);window.addEventListener('offline',interrupt);document.addEventListener('visibilitychange',()=>{if(document.hidden)interrupt();});read();
})();
