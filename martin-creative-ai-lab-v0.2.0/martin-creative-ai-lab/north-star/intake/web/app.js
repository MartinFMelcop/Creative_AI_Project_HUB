'use strict';
(() => {
  const $ = id => document.getElementById(id);
  let current = null, busy = false, quarantined = false, generation = 0;
  const colors = {copper:'#b7794c',teal:'#518d89',violet:'#9180ad'};
  const api = {get state(){return current;},get pending(){return busy;},get status(){return quarantined?'read-required':busy?'pending':'ready';},read,send,render};
  window.intake = api;
  function formDraft(){return {handle:$('handle').value,accent:$('accent').value,class_id:$('class_id').value,background_id:$('background_id').value,slots:[1,2,3,4].map(n=>$('slot'+n).value||null)};}
  function adoptDraft(d){if(!d)return;for(const k of ['handle','accent','class_id','background_id'])$(k).value=d[k];d.slots.forEach((v,i)=>$('slot'+(i+1)).value=v||'');}
  function render(s){
    if(!s||!s.state)throw new Error('Incomplete owner observation.');
    current=s;const e=s.state;
    const identityObserved = s.identity;
    const id=identityObserved;
    const completeObserved = Boolean(s.state.complete);
    document.body.dataset.confirmed=String(Boolean(s.confirmed));document.body.dataset.complete=String(completeObserved);
    $('confirmed-name').textContent=id?id.handle:'Not confirmed';$('confirmed-class').textContent=id?id.class_id:'No discipline';$('confirmed-background').textContent=id?id.background_id:'No background';
    $('identity-detail').textContent=id?`${id.accent} accent · ${id.slots.map(x=>x||'empty').join(' / ')}`:'The drawing is a preview until you confirm.';
    $('card-status').textContent=s.confirmed?(s.pending?'DRAFT PENDING':'COMMITTED'):'UNCONFIRMED';
    $('draft-status').textContent=`Draft ${s.draft_revision} · review ${s.reviewed_revision===null?'none':s.reviewed_revision}`;
    $('review-text').textContent=s.reviewed_revision===s.draft_revision?`Reviewed: ${s.draft.handle}, ${s.draft.accent}, ${s.draft.class_id} / ${s.draft.background_id}; slots ${s.draft.slots.map(x=>x||'empty').join(', ')}. Confirmation applies this whole card without refunding supplies or restoring resources.`:'Review the whole submitted proposal. Unsaved form edits are not part of that review.';
    $('avatar-accent').setAttribute('fill',colors[id?.accent]||colors.copper);
    $('portrait-title').textContent=id?`${id.handle}, ${id.class_id}, ${id.accent} accent, ${e.rig} outfit. Committed identity.`:'Unconfirmed traveler, no committed identity';
    $('plate-shape').style.display=id&&e.rig==='Plate'?'':'none';$('trail-shape').style.display=id&&e.rig==='Trail'?'':'none';
    $('brace-shape').style.display=id?.class_id==='anchor'?'':'none';$('draw-shape').style.display=id?.class_id==='lure'?'':'none';
    $('stage').textContent=completeObserved?'COMPLETE':e.active?`ENCOUNTER ${e.stage+1} / BEAT ${e.beat}`:e.attempts?e.won?'BETWEEN ENCOUNTERS':'ATTEMPT ENDED':'NOT DEPARTED';
    $('health').textContent=e.attempts?String(e.health):'—';$('resolve').textContent=e.attempts?String(e.resolve):'—';$('progression').textContent=`${e.level} / ${e.xp}`;$('spent').textContent=String(e.consumed_rigs);
    $('supplies').textContent=Object.entries(e.inventory).map(([k,v])=>`${k.replaceAll('_',' ')}: ${v}`).join(' · ')+` · ${e.transactions} inventory transactions`;
    $('earned-text').textContent=`Unspent earned points: ${e.unspent}. Vitality ${e.vitality}; Focus ${e.focus}. Earned levels permit a fresh explicit proposal between encounters.`;
    $('threat').textContent=e.active?s.threat:completeObserved?'Both actual encounters are complete. No further entry, preparation or reward is available in this session.':!s.confirmed?'Confirm your identity before preparing a departure.':e.attempts&&e.won?'Survey complete. Earned points and a fresh confirmed proposal may prepare the next encounter; final arrival still requires the actual road.':e.attempts?'The actual attempt ended in loss. Its rig remains spent. Only remaining supplies can fund another attempt.':'Prepare supplies, choose an acquired outfit, and enter. Survey victory is not final expedition completion.';
    const ratio=Math.max(0,Math.min(1,e.position/Math.max(1,s.required_position)));$('road-traveler').style.left=`${ratio*100}%`;
    $('outcome').hidden=!completeObserved;$('outcome').textContent='Actual expedition complete. This person crossed both encounters; used rigs and remaining supplies stay accounted for.';
    $('sequence').textContent=String(s.sequence);$('notice').textContent=s.text;
    updateControls();
  }
  function updateControls(){
    const s=current,e=s?.state;for(const b of document.querySelectorAll('button'))b.disabled=busy||quarantined;
    $('read').disabled=busy;
    if(!s)return;
    const locked=e.active||e.complete;
    for(const x of $('draft-form').elements)x.disabled=busy||quarantined||locked;
    $('handle').readOnly=Boolean(s.confirmed);
    $('review').disabled=busy||quarantined||locked;
    $('confirm').disabled=busy||quarantined||locked||s.reviewed_revision!==s.draft_revision;
    for(const k of ['craft-plate','craft-trail','begin'])$(k).disabled=busy||quarantined||!s.confirmed||s.pending||locked;
    for(const k of ['walk','wait','use-slot1','use-slot2','use-slot3','use-slot4'])$(k).disabled=busy||quarantined||!e.active;
    for(const k of ['focus','vitality'])$(k).disabled=busy||quarantined||e.active||e.complete||e.unspent<1;
  }
  async function read(){if(busy)return;busy=true;updateControls();const g=++generation;try{const r=await fetch('/state',{cache:'no-store'});if(!r.ok)throw new Error('Read refused.');const s=await r.json();if(g!==generation)return;quarantined=false;render(s);adoptDraft(s.draft);$('connection').textContent='Current facts read from the C# owner. No command was retried.';}catch(err){quarantined=true;$('connection').textContent=`Unable to read current facts: ${err.message}`;}finally{busy=false;updateControls();}}
  async function send(command,fields={}){if(busy||quarantined||!current)throw new Error('Read current facts before another command.');busy=true;updateControls();const g=generation;const body={command,revision:current.sequence,...fields};try{const r=await fetch('/command',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});if(!r.ok)throw new Error('Command receipt unavailable.');const s=await r.json();if(g!==generation){quarantined=true;throw new Error('Response quarantined after interruption. Read current facts.');}render(s);if(command==='draft')adoptDraft(s.draft);$('connection').textContent='Observed response from the actual owner. No automatic retries.';return s;}catch(err){quarantined=true;$('connection').textContent=`Outcome uncertain: ${err.message} Read current facts before acting.`;throw err;}finally{busy=false;updateControls();}}
  function invoke(command,fields={}){send(command,fields).catch(()=>{});}
  $('draft-form').addEventListener('submit',e=>{e.preventDefault();invoke('draft',formDraft());});
  $('review').onclick=()=>invoke('review');$('confirm').onclick=()=>invoke('confirm',{draft_revision:current.draft_revision});
  for(const rig of ['plate','trail'])$('craft-'+rig).onclick=()=>invoke('craft',{request_id:crypto.randomUUID(),recipe_id:rig+'_rig'});
  $('begin').onclick=()=>invoke('begin',{rig:$('rig').value});for(const a of ['walk','wait'])$(a).onclick=()=>invoke(a);
  for(let n=1;n<=4;n++)$('use-slot'+n).onclick=()=>invoke('slot',{slot:n});for(const axis of ['focus','vitality'])$(axis).onclick=()=>invoke('allocate',{axis,points:1});$('read').onclick=read;
  function interrupt(){if(busy){generation++;quarantined=true;$('connection').textContent='Interrupted while a command may have committed. Read current facts; no automatic retry.';updateControls();}}
  window.addEventListener('blur',interrupt);document.addEventListener('visibilitychange',()=>{if(document.hidden)interrupt();});window.addEventListener('offline',interrupt);
  read();
})();
