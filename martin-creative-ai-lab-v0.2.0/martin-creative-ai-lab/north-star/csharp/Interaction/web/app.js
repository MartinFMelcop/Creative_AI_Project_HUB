// Rendering observes actual C# state. No work timers, rewards or shadow gameplay rules live here.
const $=id=>document.getElementById(id), held=new Set();let queue=Promise.resolve(),state=null,live=false;
function command(op,extra={}){
 queue=queue.then(async()=>{const r=await fetch('/command',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({op,...extra})});if(!r.ok)throw Error(`Room refused ${op}`);render(await r.json());live=true;}).catch(error=>{live=false;$('connection').textContent='Room disconnected';$('notice').textContent=error.message;document.body.dataset.disconnected='true';});return queue;
}
function render(s){
 state=s;document.body.dataset.disconnected='false';document.body.dataset.terminal=String(s.won||s.lost);
 $('connection').textContent='LIVE · C# room';$('connection').dataset.live='true';
 const names={'catch-a':'Catch A',ground:'Grounding relay','catch-b':'Catch B'};
 $('target-name').textContent=names[s.target];$('target-description').textContent=s.target==='ground'?'A full 1.5 s hold trades one integrity for ward shutdown.':'A full 1 s hold raises this catch. Movement or harm interrupts.';
 $('health').textContent=`${s.health} / 3`;$('integrity').textContent=`${s.integrity} / 3`;
 $('phase').textContent=s.won?'PASSAGE COMPLETE':s.lost?'ATTEMPT LOST':s.paused?'PAUSED':s.need_neutral?'RELEASE TO REARM':s.working?'WORKING':(s.target==='ground'?s.grounded:s.target==='catch-a'?s.catch_a:s.catch_b)?'STATION COMPLETE':'READY';
 $('room-state').textContent=$('phase').textContent;$('progress').max=s.required_ms;$('progress').value=s.progress_ms;$('progress-value').textContent=`${(s.progress_ms/1000).toFixed(2)} / ${(s.required_ms/1000).toFixed(1)} s`;
 $('cost').textContent=s.target==='ground'?`Grounding costs 1 integrity and requires at least 2. Paid so far: ${s.paid}.`:'Catch work costs no integrity. Both catches and an actual living exit are required.';
 $('notice').textContent=s.last;$('last-cause').textContent=s.last_cause==='none'?'No completed or interrupted attempt.':`${s.last_cause.toUpperCase()} · ${(s.last_progress_ms/1000).toFixed(2)} s`;$('last-cost').textContent=`Last work cost: ${s.last_cost} integrity. Total paid: ${s.paid}.`;
 const terminal=s.won||s.lost;$('work').disabled=terminal||s.paused||s.need_neutral||(s.target==='ground'?(s.grounded||s.integrity<2):s.target==='catch-a'?s.catch_a:s.catch_b);$('work').dataset.held=String(s.held);
 $('pause').disabled=s.paused||terminal;$('resume').disabled=!s.paused||terminal;$('exit').disabled=terminal||s.paused||!s.catch_a||!s.catch_b;
 $('hit').disabled=terminal||s.grounded;$('move').disabled=terminal;$('restart').disabled=false;
 for(const b of document.querySelectorAll('[data-target]')){b.disabled=terminal;b.setAttribute('aria-pressed',String(b.dataset.target===s.target));const art=$(b.dataset.target+'-art');art.dataset.selected=String(b.dataset.target===s.target);art.dataset.working=String(s.working&&b.dataset.target===s.target);art.dataset.complete=String(b.dataset.target==='ground'?s.grounded:b.dataset.target==='catch-a'?s.catch_a:s.catch_b);}
 $('catch-a-caption').textContent=s.catch_a?'RAISED':'WAITING';$('catch-b-caption').textContent=s.catch_b?'RAISED':'WAITING';$('ground-caption').textContent=s.grounded?'GROUNDED · PAID 1':'WARD ACTIVE';$('ward-caption').textContent=s.grounded?'WARD DISABLED':'WARD ACTIVE';$('ward-art').style.opacity=s.grounded?'.3':'1';$('exit-bars').style.display=s.catch_a&&s.catch_b?'none':'';$('exit-caption').textContent=s.won?'PASSED':s.catch_a&&s.catch_b?'OPEN':'LOCKED';
}
function input(source,down){down?held.add(source):held.delete(source);return command('heartbeat',{held:held.size>0});}
$('work').addEventListener('pointerdown',e=>{e.preventDefault();$('work').setPointerCapture(e.pointerId);input('pointer',true);});
for(const event of ['pointerup','pointercancel','lostpointercapture'])$('work').addEventListener(event,()=>{if(held.has('pointer'))input('pointer',false);});
document.addEventListener('keydown',e=>{if(e.code==='KeyE'){e.preventDefault();if(!e.repeat&&!held.has('key'))input('key',true);}if(e.code==='Escape'&&!e.repeat){e.preventDefault();command('pause');}});
document.addEventListener('keyup',e=>{if(e.code==='KeyE'){e.preventDefault();input('key',false);}});
for(const b of document.querySelectorAll('[data-target]'))b.onclick=()=>command('select',{target:b.dataset.target});
$('pause').onclick=()=>command('pause');$('resume').onclick=()=>command('resume');$('move').onclick=()=>command('select',{target:state?.target||'catch-a'});$('hit').onclick=()=>command('hit');$('exit').onclick=()=>command('exit');$('restart').onclick=()=>{held.clear();command('restart');};
function suspend(){held.clear();command('pause');}
window.addEventListener('blur',suspend);document.addEventListener('visibilitychange',()=>{if(document.hidden)suspend();});
setInterval(()=>{if(!document.hidden)command('heartbeat',{held:held.size>0});},100);command('heartbeat',{held:false});
