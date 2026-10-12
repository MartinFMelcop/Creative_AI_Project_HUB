import { RhythmRun, adjustedTime, calibrationOffset } from './core.js';
const $=id=>document.getElementById(id);
const canvas=$('board'), context=canvas.getContext('2d');
const pads=[...document.querySelectorAll('[data-lane]')];
const colors=['#83e9e5','#b6a1e5','#fe8ca8','#ffd0a0'];
const held=new Set();
let track, run, audioContext, gain, buffer, source;
let mode='ready', started=0, frozen=0, epoch=0, selected='practice', offset=0;
let flash={text:'',color:'#fff',until:0}, bursts=[];
let calibrating=false, calibrationStart=0, calibrationSamples=[], calibrationBeat=-1, calibrationToken=0;
let lastExport;
let calibrationNodes=[];
let storeOK=true;
try {
  const remembered=JSON.parse(localStorage.getItem('tokyo80s-settings')||'{}');
  if(Number.isFinite(remembered.offset)&&Math.abs(remembered.offset)<=150) offset=Math.round(remembered.offset/5)*5;
} catch { storeOK=false; }
$('offset').value=offset;
$('offset-value').textContent=`${offset>0?'+':''}${offset} ms`;
function setMode(next) {
  mode=next;
  $('stage').dataset.mode=mode;
  const active=['playing','paused','pausing','loading'].includes(mode);
  $('start').disabled=active||!track;
  $('difficulty').disabled=active;
  $('calibrate').disabled=active;
  $('restart').disabled=!run||['pausing','loading'].includes(mode);
  $('pause').disabled=!['playing','paused'].includes(mode);
  $('pause').textContent=mode==='paused'?'Resume':'Pause';
  $('pulse').disabled=mode!=='playing'||!run||run.aura<100;
  pads.forEach(p=>p.disabled=mode!=='playing');
}
function message(text) { $('status').textContent=text; }
function center(title,subtitle='') {
  $('center').hidden=false;
  $('center').querySelector('strong').textContent=title;
  $('center').querySelector('p').textContent=subtitle;
  $('center').querySelector('span').textContent='TOKYO 80s / MIDNIGHT SIGNAL';
}
function position() {
  if(!audioContext) return 0;
  if(['paused','loading','error','results','ready'].includes(mode)) return frozen;
  return Math.max(0,Math.min(track?.duration||69,audioContext.currentTime-started));
}
async function ensureAudio() {
  if(!audioContext) {
    const Audio=window.AudioContext||window.webkitAudioContext;
    if(!Audio) throw new Error('This browser does not support Web Audio. Try a current browser.');
    audioContext=new Audio();
    gain=audioContext.createGain();gain.gain.value=Number($('volume').value)/100;
    gain.connect(audioContext.destination);
  }
  await audioContext.resume();
}
async function loadTrackAudio() {
  if(buffer) return buffer;
  const response=await fetch(track.audio);
  if(!response.ok) throw new Error('The track could not load. Check the connection and try again.');
  buffer=await audioContext.decodeAudioData(await response.arrayBuffer());
  if(Math.abs(buffer.duration-track.duration)>.1) throw new Error('Track duration does not match the chart.');
  return buffer;
}
function clearHeld() { held.clear();pads.forEach(p=>p.classList.remove('down')); }
function stopSource() { if(source) { source.onended=null;try{source.stop();}catch{}source.disconnect();source=null; } }
async function startRun() {
  const token=++epoch;
  calibrationToken++;
  stopSource();clearHeld();
  selected=$('difficulty').value;
  run=new RhythmRun(track.charts[selected]);
  flash={text:'',color:'#fff',until:0};bursts=[];frozen=0;
  $('results').hidden=true;lastExport=null;
  setMode('loading');updateStats();$('stage').dataset.position='0';$('progress').value=0;$('timer').textContent='00:00 / 01:09';center('Tuning in…','Loading the original soundtrack.');message('Preparing sound.');
  try {
    await ensureAudio();
    const decoded=await loadTrackAudio();
    if(token!==epoch) return;
    source=audioContext.createBufferSource();source.buffer=decoded;source.connect(gain);
    started=audioContext.currentTime+.06;
    source.onended=()=>{ if(token===epoch&&mode==='playing') completeRun(); };
    source.start(started);
    setMode('playing');
    $('center').hidden=true;
    if(window.matchMedia('(max-width: 800px)').matches)$('stage').scrollIntoView({block:'center',behavior:'instant'});
    message('D F J K / touch pads · P or Escape to pause · Space for Pulse.');
  } catch(error) {
    if(token!==epoch)return;
    setMode('error');center('Signal lost.',error.message);message(error.message);
  }
}
async function togglePause(reason='Paused. The song and notes are frozen.') {
  if(mode==='playing') {
    setMode('pausing');clearHeld();
    await audioContext.suspend();
    if(mode!=='pausing')return;
    frozen=Math.max(0,audioContext.currentTime-started);
    setMode('paused');center('Take a breath.','Resume when you are ready. No notes pass while paused.');message(reason);
  } else if(mode==='paused') {
    const token=epoch;
    await audioContext.resume();
    if(token!==epoch||mode!=='paused')return;
    setMode('playing');$('center').hidden=true;message('Back on the night line.');
  }
}
function hit(lane) {
  if(mode!=='playing')return;
  const time=position();
  // The lead-in permits learning the controls without ghost-input penalties.
  if(time<track.leadIn-.145)return;
  const note=run.hit(lane,adjustedTime(time,offset));
  if(!note)return;
  flash={text:note.state==='stray'?'OFF BEAT':note.state.toUpperCase(),
    color:note.state==='perfect'?colors[lane]:note.state==='stray'?'#9498ae':'#eee',until:time+.38};
  if(note.state!=='stray')bursts.push({lane,time});
  updateStats();
}
function pulse() {
  if(mode==='playing'&&run.pulse(adjustedTime(position(),offset))) {
    message('Pulse active: the next two misses keep your combo for eight seconds. Accuracy still records them.');
    flash={text:'PULSE',color:'#fe8ca8',until:position()+.7};updateStats();
  }
}
function updateStats() {
  if(!run)return;
  const s=run.summary();
  $('score').textContent=String(run.score).padStart(6,'0');
  $('combo').textContent=String(run.combo);
  $('accuracy').textContent=s.counts.pending===run.notes.length?'—':`${s.accuracy.toFixed(1)}%`;
  $('aura').value=run.aura;
  $('pulse').disabled=mode!=='playing'||run.aura<100;
  const left=Math.max(0,run.shieldUntil-adjustedTime(position(),offset));
  $('shield').textContent=left>0&&run.shields?`Pulse: ${run.shields} combo protection(s) · ${left.toFixed(1)}s remaining`:run.aura===100?'Aura full. Choose when to protect your next difficult phrase.':'Build a combo. Protect your next difficult phrase.';
}
function completeRun() {
  if(!run||mode!=='playing')return;
  frozen=track.duration;
  const stats=run.finish(adjustedTime(track.duration,offset));
  setMode('results');stopSource();clearHeld();
  center('Last stop.',`${stats.rank} rank · ${stats.accuracy.toFixed(1)}% accuracy`);
  $('rank').textContent=stats.rank;
  for(const name of ['perfect','good','ok','miss'])$(name).textContent=String(stats.counts[name]);
  $('result-summary').textContent=`${stats.score.toLocaleString()} points · best combo ${stats.maxCombo} · ${stats.strays} off-beat inputs · ${stats.pulses} Pulse use(s).`;
  $('timing-result').textContent=stats.meanErrorMs===null?'No scored hits yet. Try Practice and tap with the drum.':`Average timing: ${stats.meanErrorMs>0?'+':''}${stats.meanErrorMs.toFixed(1)} ms (${stats.meanErrorMs>15?'late':stats.meanErrorMs< -15?'early':'close to the beat'}). Input offset used: ${offset} ms. Adjust timing between runs if hits consistently feel displaced.`;
  let best=stats.score,newBest=false;
  try {
    const key=`tokyo80s-best-v1-${selected}`;
    const old=Number(localStorage.getItem(key))||0;
    best=Math.max(old,stats.score);newBest=stats.score>old;
    localStorage.setItem(key,String(best));
  } catch {storeOK=false;}
  $('best').textContent=storeOK?`${newBest?'New best. ':''}${selected==='practice'?'Practice':'Arcade'} best in this browser: ${best.toLocaleString()}.`:'Browser storage is unavailable; this run still counts and can be exported.';
  lastExport={game:'Tokyo 80s',version:'0.1.0',track:track.id,chart:selected,offsetMs:offset,...stats,
    notes:run.notes.map(({id,time,lane,state,error,protected:shield})=>({id,time,lane,state,errorMs:error===null?null:Math.round(error*10000)/10,comboProtected:shield}))};
  $('results').hidden=false;$('results').focus({preventScroll:true});
  message('Run complete. Replay, try the other chart, or save your actual run data.');updateStats();
}
function press(lane,id) { if(held.has(id))return;held.add(id);pads[lane].classList.add('down');hit(lane); }
function release(lane,id) { held.delete(id);if(![...held].some(k=>k.endsWith(`:${lane}`)))pads[lane].classList.remove('down'); }
pads.forEach((pad,lane)=>{
  pad.addEventListener('pointerdown',e=>{e.preventDefault();pad.setPointerCapture(e.pointerId);press(lane,`pointer${e.pointerId}:${lane}`);});
  for(const name of ['pointerup','pointercancel','lostpointercapture'])pad.addEventListener(name,e=>release(lane,`pointer${e.pointerId}:${lane}`));
});
const keys={KeyD:0,KeyF:1,KeyJ:2,KeyK:3,ArrowLeft:0,ArrowDown:1,ArrowUp:2,ArrowRight:3};
document.addEventListener('keydown',e=>{
  if(/INPUT|SELECT|TEXTAREA/.test(e.target.tagName))return;
  if($('calibration').open) {
    if(e.code==='KeyF'&&!e.repeat){e.preventDefault();tapCalibration();}return;
  }
  if(e.repeat)return;
  if(e.code in keys){e.preventDefault();press(keys[e.code],`${e.code}:${keys[e.code]}`);}
  if(e.code==='Space'&&mode==='playing'){e.preventDefault();pulse();}
  if(['Escape','KeyP'].includes(e.code)&&['playing','paused'].includes(mode)){e.preventDefault();togglePause();}
});
document.addEventListener('keyup',e=>{if(e.code in keys)release(keys[e.code],`${e.code}:${keys[e.code]}`);});
window.addEventListener('blur',()=>{clearHeld();if(mode==='playing')togglePause('Paused after leaving this window. Resume when you return.');});
document.addEventListener('visibilitychange',()=>{if(document.hidden&&mode==='playing')togglePause('Paused while the page was hidden. Resume when you return.');});
$('start').addEventListener('click',startRun);$('restart').addEventListener('click',startRun);$('replay').addEventListener('click',startRun);
$('pause').addEventListener('click',()=>togglePause());$('pulse').addEventListener('click',pulse);
$('volume').addEventListener('input',()=>{if(gain)gain.gain.setTargetAtTime(Number($('volume').value)/100,audioContext.currentTime,.02);});
$('export').addEventListener('click',()=>{
  if(!lastExport)return;
  const url=URL.createObjectURL(new Blob([JSON.stringify(lastExport,null,2)+'\n'],{type:'application/json'}));
  const a=document.createElement('a');a.href=url;a.download=`midnight-signal-${selected}-run.json`;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
});
$('calibrate').addEventListener('click',()=>{$('calibration').showModal();$('offset').value=offset;});
$('offset').addEventListener('input',()=>{$('offset-value').textContent=`${Number($('offset').value)>0?'+':''}${$('offset').value} ms`;});
$('apply').addEventListener('click',()=>{
  offset=Number($('offset').value);
  try{localStorage.setItem('tokyo80s-settings',JSON.stringify({offset}));}catch{storeOK=false;}
  stopCalibration();$('calibration').close();message(`Input offset set to ${offset} ms. Timing changes apply to the next run.`);
});
function stopCalibration() {for(const node of calibrationNodes){try{node.stop();}catch{}node.disconnect();}calibrationNodes=[];calibrating=false;calibrationToken++;$('tap').disabled=true;$('clicks').disabled=false;}
$('calibration').addEventListener('close',stopCalibration);
$('calibration').addEventListener('cancel',stopCalibration);
$('calibration').querySelector('form').addEventListener('submit',stopCalibration);
$('clicks').addEventListener('click',async()=>{
  const token=++calibrationToken;
  try {
    await ensureAudio();
    if(token!==calibrationToken||!$('calibration').open)return;
    calibrationStart=audioContext.currentTime+.8;calibrationSamples=[];calibrationBeat=-1;calibrating=true;
    $('tap').disabled=false;$('clicks').disabled=true;
    $('cal-status').textContent='Tap F or the pad once per click. First two clicks are warm-up.';
    for(let i=0;i<12;i++){
      const osc=audioContext.createOscillator(),env=audioContext.createGain();
      osc.frequency.value=i<2?900:1200;osc.connect(env);env.connect(gain);
      const t=calibrationStart+i*.5;env.gain.setValueAtTime(.0001,t);env.gain.exponentialRampToValueAtTime(.22,t+.003);env.gain.exponentialRampToValueAtTime(.0001,t+.07);
      osc.start(t);osc.stop(t+.08);calibrationNodes.push(osc);
    }
  } catch(error){stopCalibration();$('cal-status').textContent=error.message;}
});
function tapCalibration() {
  if(!calibrating)return;
  const elapsed=audioContext.currentTime-calibrationStart;
  const beat=Math.round(elapsed/.5);
  if(beat<2||beat>11||beat===calibrationBeat)return;
  calibrationBeat=beat;
  calibrationSamples.push(elapsed-beat*.5);
  $('cal-status').textContent=`${calibrationSamples.length} timing taps recorded. Keep tapping with the click.`;
}
$('tap').addEventListener('pointerdown',e=>{e.preventDefault();tapCalibration();});
function finishCalibration() {
  stopCalibration();
  if(calibrationSamples.length<6){$('cal-status').textContent='Not enough taps. Try again, or choose an offset manually.';return;}
  const suggestion=calibrationOffset(calibrationSamples);
  $('offset').value=suggestion;$('offset-value').textContent=`${suggestion>0?'+':''}${suggestion} ms`;
  $('cal-status').textContent=`Suggested offset: ${suggestion} ms from ${calibrationSamples.length} taps. Apply it, or adjust manually.`;
}
let width=1,height=1;
new ResizeObserver(()=>{
  const dpr=Math.min(2,window.devicePixelRatio||1);width=canvas.clientWidth;height=canvas.clientHeight;
  canvas.width=Math.round(width*dpr);canvas.height=Math.round(height*dpr);context.setTransform(dpr,0,0,dpr,0,0);
}).observe(canvas);
function draw(time) {
  context.clearRect(0,0,width,height);
  const laneW=width/4,hitY=height-44;
  for(let lane=0;lane<4;lane++){
    context.fillStyle=lane%2?'#171726':'#141422';context.fillRect(lane*laneW,0,laneW,height);
    context.strokeStyle='#ffffff08';context.beginPath();context.moveTo(lane*laneW,0);context.lineTo(lane*laneW,height);context.stroke();
    context.fillStyle=colors[lane]+'40';context.fillRect(lane*laneW+6,hitY-2,laneW-12,3);
    context.fillStyle=colors[lane]+'15';context.fillRect(lane*laneW+6,hitY+1,laneW-12,35);
  }
  context.strokeStyle='#ffffff08';
  for(let j=0;j<8;j++){const y=((j/8+time/4)%1)*hitY;context.beginPath();context.moveTo(0,y);context.lineTo(width,y);context.stroke();}
  if(run){
    for(const note of run.notes){
      if(note.state!=='pending')continue;
      const delta=note.time-time;
      if(delta>2||delta<-.25)continue;
      const y=hitY-delta/2*(hitY-25),x=note.lane*laneW+14;
      context.fillStyle=colors[note.lane];context.shadowColor=colors[note.lane];context.shadowBlur=8;
      context.fillRect(x,y-4,laneW-28,8);context.shadowBlur=0;
      context.fillStyle='#ffffff70';context.fillRect(x,y-4,laneW-28,2);
    }
  }
  if(!window.matchMedia('(prefers-reduced-motion: reduce)').matches){
    bursts=bursts.filter(b=>time-b.time<.4);
    for(const b of bursts){
      const life=time-b.time;context.strokeStyle=colors[b.lane]+Math.round(255*(1-life/.4)).toString(16).padStart(2,'0');
      context.strokeRect(b.lane*laneW+10-life*16,hitY-6-life*18,laneW-20+life*32,12+life*36);
    }
  }
}
function frame() {
  let time=run?position():0;
  if(mode==='results')time=frozen;
  if(mode==='playing'){
    const misses=run.advance(adjustedTime(time,offset));
    if(misses.length)flash={text:misses.every(n=>n.protected)?'COMBO SAVED':'MISS',color:'#a4a7b7',until:time+.38};
    if(time<track.leadIn){center(String(Math.max(1,Math.ceil(track.leadIn-time))),'Listen to the clicks. First note lands on the downbeat.');}
    else $('center').hidden=true;
    const section=[...track.sections].reverse().find(s=>time>=s.time);
    $('section').textContent=(section?.name||'COUNT IN').toUpperCase();
    if(time>=track.duration)completeRun();
    updateStats();
  }
  $('stage').dataset.position=String(time);
  $('progress').value=time;
  const sec=Math.min(69,Math.floor(time));$('timer').textContent=`${String(Math.floor(sec/60)).padStart(2,'0')}:${String(sec%60).padStart(2,'0')} / 01:09`;
  $('judgment').textContent=time<flash.until?flash.text:'';$('judgment').style.color=flash.color;
  draw(time);
  if(calibrating&&audioContext.currentTime>calibrationStart+6)finishCalibration();
  requestAnimationFrame(frame);
}
setMode('ready');requestAnimationFrame(frame);
fetch('track.json').then(r=>{if(!r.ok)throw new Error('Could not load the chart.');return r.json();}).then(data=>{
  track=data;setMode('ready');
}).catch(error=>{setMode('error');center('Signal lost.',error.message);message(error.message);});
