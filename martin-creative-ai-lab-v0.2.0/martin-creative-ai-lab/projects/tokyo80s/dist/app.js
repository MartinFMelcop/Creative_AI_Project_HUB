import { RhythmRun, adjustedTime, calibrationOffset } from './core.js';
import { phrases, makeSession, phraseResults, backingFor } from './rehearsal.js';
const $=id=>document.getElementById(id);
const canvas=$('board'), context=canvas.getContext('2d');
const pads=[...document.querySelectorAll('[data-lane]')];
const colors=['#83e9e5','#b6a1e5','#fe8ca8','#ffd0a0'];
const held=new Set();
let track, tracks=[], run, audioContext, gain, buffer, source;
let mode='ready', started=0, frozen=0, epoch=0, selected='practice', offset=0;
let flash={text:'',color:'#fff',until:0}, bursts=[];
let calibrating=false, calibrationStart=0, calibrationSamples=[], calibrationBeat=-1, calibrationToken=0;
let lastExport;
let calibrationNodes=[];
let storeOK=true;
let session, countNodes=[], previousTake;
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
  $('song').disabled=active||!tracks.length;
  $('calibrate').disabled=active;
  $('phrase').disabled=active||!track;
  $('rate').disabled=active||$('phrase').value==='full';
  $('full-run').disabled=['pausing','loading'].includes(mode);
  $('restart').disabled=!run||['pausing','loading'].includes(mode);
  $('pause').disabled=!['playing','paused'].includes(mode);
  $('pause').textContent=mode==='paused'?'Resume':'Pause';
  $('pulse').disabled=mode!=='playing'||!run||run.aura<100;
  pads.forEach((p,lane)=>p.disabled=mode!=='playing'&&!(mode==='paused'&&run?.notes.some(n=>n.lane===lane&&n.state==='holding')));
}
function message(text) { $('status').textContent=text; }
function center(title,subtitle='') {
  $('center').hidden=false;
  $('center').querySelector('strong').textContent=title;
  $('center').querySelector('p').textContent=subtitle;
  $('center').querySelector('span').textContent=`TOKYO 80s / ${track?.title.toUpperCase()||'NIGHT SHIFT'}`;
}
function stamp(seconds) {const sec=Math.floor(seconds);return `${String(Math.floor(sec/60)).padStart(2,'0')}:${String(sec%60).padStart(2,'0')}`;}
function chooseTrack(id) {
  if(['playing','paused','pausing','loading'].includes(mode))return;
  const next=tracks.find(t=>t.id===id);if(!next)return;
  epoch++;stopSource();clearHeld();track=next;buffer=null;run=null;lastExport=null;frozen=0;session=null;
  flash={text:'',color:'#fff',until:0};bursts=[];
  $('shield').textContent='Build a combo. Protect your next difficult phrase.';
  $('results').hidden=true;document.title=`Tokyo 80s — ${track.title}`;
  const [first,...rest]=track.title.toUpperCase().split(' ');
  $('title').replaceChildren(document.createTextNode(first),document.createElement('br'));
  const titleEnd=document.createElement('span');titleEnd.textContent=rest.join(' ')+'.';$('title').append(titleEnd);
  document.querySelector('.intro').textContent=track.intro;
  document.querySelector('.eyebrow').lastChild.textContent=` ORIGINAL TRACK · ${track.bpm} BPM`;
  document.querySelector('.edition').textContent=track.side;
  document.querySelector('.track-meta span').textContent=`${stamp(track.duration)} / INSTRUMENTAL`;
  $('progress').max=track.duration;$('stage').dataset.track=track.id;$('section').textContent=track.sections[0].name.toUpperCase();
  $('score').textContent='000000';$('combo').textContent='0';$('accuracy').textContent='—';$('aura').value=0;
  $('phrase').replaceChildren(...[{id:'full',label:'Full run'},...phrases(track)].map(p=>{
    const option=document.createElement('option');option.value=p.id;option.textContent=p.label;return option;
  }));
  rehearsalInfo();
  setMode('ready');center('Hit play.',`${track.title} · ${stamp(track.duration)} · ${track.id==='rain-circuit'?'Carry the long notes to their tails.':'Tap the instrumental attacks.'}`);
  message('Choose Practice or Arcade. Selecting a track does not start sound.');
}
function position() {
  if(!audioContext) return 0;
  if(['paused','loading','error','results','ready'].includes(mode)) return frozen;
  return Math.max(0,Math.min(session?.duration||track?.duration||69,audioContext.currentTime-started));
}
function rehearsalInfo() {
  const chosen=phrases(track).find(p=>p.id===$('phrase').value);
  if(!chosen)$('rate').value='1';
  const rate=Number($('rate').value);
  $('rate').disabled=!chosen;
  $('full-run').hidden=!chosen;
  $('start').firstChild.textContent=chosen?'Start rehearsal ':'Start run ';
  $('rehearsal-info').textContent=chosen?`${chosen.label} · ${Math.round(track.bpm*rate*10)/10} BPM · original pitch · four-click entrance · no full-run best.`:'Full track · original tempo.';
  if(!run) {
    session=makeSession(track,$('difficulty').value,$('phrase').value,rate);
    $('progress').max=session.duration;
    center(chosen?'Phrase ready.':'Hit play.',chosen?`${chosen.label} · ${rate*100}% speed · four clicks before the first note.`:`${track.title} · ${stamp(track.duration)} · full track at original tempo.`);
  }
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
async function loadTrackAudio(backing, token) {
  if(buffer?.url===backing.url) return buffer.data;
  const response=await fetch(backing.url);
  if(!response.ok) throw new Error('The backing could not load. Check the connection and try again.');
  const data=await audioContext.decodeAudioData(await response.arrayBuffer());
  if(Math.abs(data.duration-backing.bufferDuration)>.1) throw new Error('Backing duration does not match this speed.');
  if(token===epoch)buffer={url:backing.url,data};
  return data;
}
function clearHeld() { held.clear();pads.forEach(p=>p.classList.remove('down')); }
function stopSource() {
  if(source) { source.onended=null;try{source.stop();}catch{}source.disconnect();source=null; }
  for(const node of countNodes){try{node.stop();}catch{}node.disconnect();}countNodes=[];
}
function countIn() {
  if(session.mode!=='rehearsal')return;
  const beat=60/track.bpm/session.rate;
  for(let i=0;i<4;i++) {
    const when=started+session.headStart-(4-i)*beat;
    const oscillator=audioContext.createOscillator(),volume=audioContext.createGain();
    oscillator.frequency.value=i===0?1000:700;
    volume.gain.setValueAtTime(.12,when);volume.gain.exponentialRampToValueAtTime(.001,when+.05);
    oscillator.connect(volume);volume.connect(gain);oscillator.start(when);oscillator.stop(when+.06);
    oscillator.onended=()=>volume.disconnect();countNodes.push(oscillator);
  }
}
async function startRun() {
  const token=++epoch;
  calibrationToken++;
  stopSource();clearHeld();
  selected=$('difficulty').value;
  session=makeSession(track,selected,$('phrase').value,Number($('rate').value));
  run=new RhythmRun(session.notes);
  flash={text:'',color:'#fff',until:0};bursts=[];frozen=0;
  $('results').hidden=true;lastExport=null;
  $('progress').max=session.duration;
  $('stage').dataset.session=session.mode;$('stage').dataset.rate=String(session.rate);
  setMode('loading');updateStats();$('stage').dataset.position='0';$('progress').value=0;$('timer').textContent=`00:00 / ${stamp(track.duration)}`;center('Tuning in…','Preparing the backing for this speed.');message('Preparing sound.');
  try {
    await ensureAudio();
    if(token!==epoch)return;
    session.backing=backingFor(track,session);
    const decoded=await loadTrackAudio(session.backing,token);
    if(token!==epoch) return;
    source=audioContext.createBufferSource();source.buffer=decoded;source.connect(gain);
    source.playbackRate.value=session.backing.playbackRate;
    started=audioContext.currentTime+.06;
    source.onended=()=>{ if(token===epoch&&mode==='playing') completeRun(); };
    source.start(started,session.backing.offset,session.backing.duration);
    countIn();
    setMode('playing');
    $('center').hidden=true;
    if(window.matchMedia('(max-width: 800px)').matches)$('stage').scrollIntoView({block:'center',behavior:'instant'});
    message(session.mode==='rehearsal'?`${session.phrase.label} at ${session.rate*100}% · follow four clicks, carry every tail. Each take stops for review.`:'D F J K / touch pads · P or Escape to pause · Space for Pulse.');
  } catch(error) {
    if(token!==epoch)return;
    stopSource();
    setMode('error');center('Signal lost.',error.message);message(error.message);
  }
}
async function togglePause(reason='Paused. The song and notes are frozen.') {
  if(mode==='playing') {
    setMode('pausing');clearHeld();
    await audioContext.suspend();
    if(mode!=='pausing')return;
    frozen=Math.max(0,audioContext.currentTime-started);
    run.pause(adjustedTime(frozen,offset));
    setMode('paused');center('Take a breath.','Re-hold lit lanes before Resume, or within 200 ms after. No notes pass while paused.');message(reason);
  } else if(mode==='paused') {
    const token=epoch;
    await audioContext.resume();
    if(token!==epoch||mode!=='paused')return;
    run.resume(adjustedTime(frozen,offset),[...held].map(id=>Number(id.split(':').at(-1))));
    setMode('playing');$('center').hidden=true;message('Back on the night line.');
  }
}
function hit(lane) {
  if(mode!=='playing')return;
  const time=position();
  // The lead-in permits learning the controls without ghost-input penalties.
  if(time<(session?.headStart??track.leadIn)-.145)return;
  const note=run.hit(lane,adjustedTime(time,offset));
  if(!note)return;
  flash={text:note.state==='holding'?'HOLD':note.state==='stray'?'OFF BEAT':note.state.toUpperCase(),
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
  frozen=session.duration;
  const stats=run.finish(adjustedTime(session.duration,offset));
  setMode('results');stopSource();clearHeld();
  const rehearsal=session.mode==='rehearsal';
  center(rehearsal?'Phrase complete.':'Last stop.',`${stats.rank} rank · ${stats.accuracy.toFixed(1)}% accuracy`);
  $('result-label').textContent=rehearsal?`REHEARSAL / ${session.phrase.label.toUpperCase()} / ${session.rate*100}%`:'LAST STOP / RUN COMPLETE';
  $('rank').textContent=stats.rank;
  for(const name of ['perfect','good','ok','miss'])$(name).textContent=String(stats.counts[name]);
  $('result-summary').textContent=`${stats.score.toLocaleString()} points · best combo ${stats.maxCombo} · ${stats.strays} off-beat inputs · ${stats.pulses} Pulse use(s).`;
  $('timing-result').textContent=stats.meanErrorMs===null?'No scored hits yet. Try Practice and tap with the drum.':`Average timing: ${stats.meanErrorMs>0?'+':''}${stats.meanErrorMs.toFixed(1)} ms (${stats.meanErrorMs>15?'late':stats.meanErrorMs< -15?'early':'close to the beat'}). Input offset used: ${offset} ms. Adjust timing between runs if hits consistently feel displaced.`;
  if(rehearsal) {
    const key=`${track.id}/${selected}/${session.phrase.id}/${session.rate}/${offset}`;
    const comparison=previousTake?.key===key?` Previous identical setup: ${previousTake.accuracy.toFixed(1)}%. Change: ${(stats.accuracy-previousTake.accuracy).toFixed(1)} percentage points.`:'';
    $('best').textContent=`${session.phrase.label} · ${session.rate*100}% speed. Rehearsals do not update full-run bests.${comparison}`;
    previousTake={key,accuracy:stats.accuracy};
  } else {
    let best=stats.score,newBest=false;
    try {
      const key=track.id==='midnight-signal'?`tokyo80s-best-v1-${selected}`:`tokyo80s-best-v2-${track.id}-${selected}`;
      const old=Number(localStorage.getItem(key))||0;
      best=Math.max(old,stats.score);newBest=stats.score>old;
      localStorage.setItem(key,String(best));
    } catch {storeOK=false;}
    $('best').textContent=storeOK?`${newBest?'New best. ':''}${selected==='practice'?'Practice':'Arcade'} best in this browser: ${best.toLocaleString()}.`:'Browser storage is unavailable; this run still counts and can be exported.';
  }
  const breakdown=phraseResults(track,run.notes);
  lastExport={game:'Tokyo 80s',version:'0.4.0',track:track.id,chart:selected,offsetMs:offset,...stats,
    mode:session.mode,playbackRate:session.rate,backing:session.backing,
    ...(rehearsal?{phrase:session.phrase,cueStart:session.cueStart,audioEnd:session.audioEnd}:{}),
    timeUnit:'performance-seconds',phrases:breakdown,
    notes:run.notes.map(({id,time,lane,state,error,duration,sourceTime,sourceDuration,protected:shield})=>({id,time,lane,state,duration:duration||0,
      ...(rehearsal?{sourceTime,sourceDuration}:{}),errorMs:error===null?null:Math.round(error*10000)/10,comboProtected:shield}))};
  $('phrase-results').replaceChildren(...breakdown.map(p=>{
    const row=document.createElement('div');row.className='phrase-row';
    const info=document.createElement('p');info.textContent=`${p.label}\n${p.accuracy}% note accuracy · ${p.counts.miss}/${p.notes} missed · ${p.lostHolds} lost holds`;
    const button=document.createElement('button');button.textContent='Rehearse';button.dataset.phrase=p.id;
    button.setAttribute('aria-label',`Rehearse ${p.label}`);
    button.addEventListener('click',()=>{$('phrase').value=p.id;rehearsalInfo();startRun();});row.append(info,button);return row;
  }));
  $('replay').textContent=rehearsal?'Repeat phrase':'Ride again';
  const next=tracks[(tracks.indexOf(track)+1)%tracks.length];$('next-stage').textContent=`Play ${next.title}`;
  $('results').hidden=false;$('results').focus({preventScroll:true});
  message(rehearsal?'Take complete. Repeat, change speed between takes, or return to a full run.':'Run complete. Review each phrase, rehearse a difficult passage, or save your actual run data.');updateStats();
}
function press(lane,id) { if(held.has(id))return;const already=[...held].some(k=>k.endsWith(`:${lane}`));held.add(id);pads[lane].classList.add('down');if(!already)hit(lane); }
function release(lane,id) {
  if(!held.delete(id))return;
  if([...held].some(k=>k.endsWith(`:${lane}`)))return;
  pads[lane].classList.remove('down');
  if(mode==='playing'){
    const note=run.release(lane,adjustedTime(position(),offset));
    if(note?.state==='miss')flash={text:note.protected?'COMBO SAVED':'HOLD LOST',color:'#fe8ca8',until:position()+.38};
    updateStats();
  }
}
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
function interruptPlayback(reason) {
  clearHeld();
  if(mode==='loading') {
    epoch++;stopSource();run=null;session=null;frozen=0;
    setMode('ready');rehearsalInfo();
    message('Loading interrupted. Press Start when you are ready; no playback was started.');
  } else if(mode==='playing')togglePause(reason);
}
window.addEventListener('blur',()=>interruptPlayback('Paused after leaving this window. Resume when you return.'));
document.addEventListener('visibilitychange',()=>{if(document.hidden)interruptPlayback('Paused while the page was hidden. Resume when you return.');});
$('start').addEventListener('click',startRun);$('restart').addEventListener('click',startRun);$('replay').addEventListener('click',startRun);
$('pause').addEventListener('click',()=>togglePause());$('pulse').addEventListener('click',pulse);
$('song').addEventListener('change',()=>chooseTrack($('song').value));
$('phrase').addEventListener('change',rehearsalInfo);$('rate').addEventListener('change',rehearsalInfo);$('difficulty').addEventListener('change',rehearsalInfo);
$('full-run').addEventListener('click',()=>{
  epoch++;stopSource();clearHeld();run=null;session=null;frozen=0;lastExport=null;
  flash={text:'',color:'#fff',until:0};bursts=[];
  $('results').hidden=true;$('phrase').value='full';rehearsalInfo();
  $('progress').max=track.duration;$('stage').dataset.session='full';setMode('ready');
  $('score').textContent='000000';$('combo').textContent='0';$('accuracy').textContent='—';$('aura').value=0;
  center('Hit play.',`${track.title} · full track at original tempo.`);message('Full run ready. Choose Start run when you want sound.');
});
$('next-stage').addEventListener('click',()=>{const next=tracks[(tracks.indexOf(track)+1)%tracks.length];$('song').value=next.id;chooseTrack(next.id);startRun();});
$('volume').addEventListener('input',()=>{if(gain)gain.gain.setTargetAtTime(Number($('volume').value)/100,audioContext.currentTime,.02);});
$('export').addEventListener('click',()=>{
  if(!lastExport)return;
  const url=URL.createObjectURL(new Blob([JSON.stringify(lastExport,null,2)+'\n'],{type:'application/json'}));
  const a=document.createElement('a');a.href=url;a.download=lastExport.mode==='rehearsal'?`${track.id}-${selected}-phrase-${lastExport.phrase.id}-${lastExport.playbackRate*100}.json`:`${track.id}-${selected}-run.json`;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
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
      if(!['pending','holding'].includes(note.state))continue;
      const delta=note.time-time;
      if(delta>2||(note.state!=='holding'&&delta<-.25))continue;
      const y=hitY-delta/2*(hitY-25),x=note.lane*laneW+14;
      if(note.duration) {
        const bottom=note.state==='holding'?hitY:y;
        const top=hitY-(note.time+note.duration-time)/2*(hitY-25);
        context.fillStyle=colors[note.lane]+(note.engaged?'b0':'55');
        context.fillRect(x+laneW*.2,top,laneW*.6-28,Math.max(0,bottom-top));
        context.strokeStyle=colors[note.lane];context.strokeRect(x+laneW*.2,top,laneW*.6-28,Math.max(0,bottom-top));
      }
      context.fillStyle=colors[note.lane];context.shadowColor=colors[note.lane];context.shadowBlur=8;
      const headY=note.state==='holding'?hitY:y;
      context.fillRect(x,headY-4,laneW-28,8);context.shadowBlur=0;
      context.fillStyle='#ffffff70';context.fillRect(x,headY-4,laneW-28,2);
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
    if(time<session.headStart){
      const beat=60/track.bpm/session.rate;
      center(String(Math.max(1,Math.ceil((session.headStart-time)/(session.mode==='rehearsal'?beat:1)))),session.mode==='rehearsal'?'Four clicks. First note lands after the fourth.':'Listen to the clicks. First note lands on the downbeat.');
    }
    else $('center').hidden=true;
    const songTime=session.cueStart+time*session.rate;
    const section=[...track.sections].reverse().find(s=>songTime>=s.time);
    $('section').textContent=session.mode==='rehearsal'?`BARS ${Number(session.phrase.id)*4+1}–${Number(session.phrase.id)*4+4} · ${session.rate*100}% SPEED`:(section?.name||'COUNT IN').toUpperCase();
    if(time>=session.duration)completeRun();
    updateStats();
  }
  $('stage').dataset.position=String(time);
  $('stage').dataset.songPosition=String(session?session.cueStart+time*session.rate:time);
  $('progress').value=time;
  const duration=session?.duration||track?.duration||69;
  $('timer').textContent=`${stamp(Math.min(duration,time))} / ${stamp(duration)}`;
  pads.forEach((p,lane)=>p.classList.toggle('sustaining',!!run?.notes.some(n=>n.lane===lane&&n.state==='holding')));
  $('judgment').textContent=time<flash.until?flash.text:'';$('judgment').style.color=flash.color;
  draw(time);
  if(calibrating&&audioContext.currentTime>calibrationStart+6)finishCalibration();
  requestAnimationFrame(frame);
}
setMode('ready');requestAnimationFrame(frame);
fetch('setlist.json').then(r=>{if(!r.ok)throw new Error('Could not load the setlist.');return r.json();}).then(list=>Promise.all(list.map(async item=>{
  const response=await fetch(item.score);if(!response.ok)throw new Error('Could not load the chart.');
  const data=await response.json();if(data.id!==item.id)throw new Error('Setlist and chart disagree.');
  return {...data,...item};
}))).then(data=>{
  tracks=data;$('song').replaceChildren(...tracks.map(t=>{const option=document.createElement('option');option.value=t.id;option.textContent=`${t.title} · ${t.bpm} BPM`;return option;}));
  chooseTrack(tracks[0].id);
}).catch(error=>{setMode('error');center('Signal lost.',error.message);message(error.message);});
