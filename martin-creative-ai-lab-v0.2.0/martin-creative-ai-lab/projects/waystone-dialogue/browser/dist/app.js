import {Campaign as Adventure,serialize,restore} from './campaign.js';
import {renderMorning} from './morning-ui.js';
import {renderHandover} from './handover-ui.js';
const $=id=>document.getElementById(id), KEY='waystone-crossing-v1';
let game=new Adventure(), candidate=null, active=false, replacement=null;
const titles={pack:'What can you carry?',workshop:'The Keeper’s workshop',route:'Two ways to the mill',causeway:'A gap in the stones',ferry:'The river keeps moving'};
const endingTitles={FULL_RESCUE:'Four names. Four answers.',PEOPLE_SAFE:'All four, before the water.',PARTIAL_CROSSING:'Names for the morning crew.',SHELTERED:'Above the flood, until morning.',BOAT_LOST:'The bow gives way.'};
const itemNotes={rope:'One use: speed a rescue, secure the ferry, or lash a temporary road.',timber:'Repair a permanent road, or add buoyancy to the ferry. It will not waterproof cargo.',oil:'Signal the roof workers when the Waystone is dark. Consumed when used.'};
function p(text,parent,className='') {const node=document.createElement('p');node.textContent=text;if(className)node.className=className;parent.append(node);return node;}
function say(message) {$('notice').textContent=message;}
function paragraphs(text,parent) {for(const block of text.split('\n\n'))p(block.replace(/\n/g,' '),parent);}
function persist() {
  let data;
  try {data=JSON.stringify(serialize(game));}catch(e){$('save-status').textContent=e.message;return;}
  try {localStorage.setItem(KEY,data);$('save-status').textContent='Crossing saved in this browser. Save file to keep a portable copy.';}
  catch {$('save-status').textContent='Browser save is unavailable. Use Save file before leaving.';}
}
function activate(next) {
  game=next;active=true;candidate=null;$('cover').hidden=true;$('play').hidden=false;
  $('situation').hidden=false;$('export').hidden=false;$('restart').hidden=false;$('toggle-map').hidden=false;
  document.querySelector('.layout').classList.add('playing');render();persist();focusScene();
}
function focusScene() {$('scene-title').focus({preventScroll:true});$('scene-title').scrollIntoView({block:'start',behavior:'instant'});}
function requestReplace(next) {
  if((active && game.history.length) || candidate) {replacement=next;$('replacement').showModal();}
  else {say('');activate(next);}
}
function row(parent,label,value,className='') {
  const div=document.createElement('div'),dt=document.createElement('dt'),dd=document.createElement('dd');
  dt.textContent=label;dd.textContent=value;dd.className=className;div.append(dt,dd);parent.append(div);
}
function renderSituation() {
  const s=game.state;
  $('remaining').textContent=s.time;$('clock').replaceChildren();
  for(let beat=1;beat<=9;beat++) {
    const li=document.createElement('li');li.textContent=beat;
    if(beat<=s.elapsed)li.classList.add('spent');
    if(beat===s.elapsed+1)li.classList.add('current');
    if(beat===5 || beat===6)li.classList.add('deadline');
    li.title=`Beat ${beat}${beat===5?' · Iven deadline':beat===6?' · roof deadline':''}`;
    $('clock').append(li);
  }
  $('clock').setAttribute('aria-label',`${s.elapsed} beats spent, ${s.time} remaining. Iven deadline 5; roof deadline 6.`);
  $('roster').replaceChildren();
  row($('roster'),'High-road arrivals',`${s.saved} of 4 villagers`,s.saved===4?'safe':'');
  row($('roster'),'Lio & Senn',s.roof==='rescued'?'Off the roof':s.roof==='sheltered'?'North loft · stranded':s.ending?'Mill roof · stranded':'Roof · leave at beat 6',s.roof==='rescued'?'safe':'');
  row($('roster'),'Iven',s.iven==='rescued'?'With the crew':s.iven==='sheltered'?'North shoal · stranded':s.ending?'Jetty · stranded':'Jetty · leaves at beat 5',s.iven==='rescued'?'safe':'');
  row($('roster'),'Clinic medicine',{waiting:'At the mill',aboard:'Aboard the ferry',delivered:'Delivered · dry',spoiled:'Spoiled by water'}[s.medicine],s.medicine==='delivered'?'safe':s.medicine==='spoiled'?'warning':'');
  $('equipment').textContent=`Equipment: ${s.kit.length?s.kit.join(' · '):s.phase==='pack'?'choose two items':'none left'}`;
  $('river').hidden=s.route!=='ferry' || !!s.ending;
  $('forecast').replaceChildren();
  for(let i=0;i<3;i++) {
    const li=document.createElement('li'),small=document.createElement('small');
    const current=game.current(i);li.className=current;li.append(document.createTextNode(current));
    small.textContent=`${['now','next','in 2 beats'][i]} · ${s.line?'protected':current==='slack'?'no damage':current==='pull'?'−1 hull':'−2 hull; wets medicine'}`;
    li.append(small);$('forecast').append(li);
  }
  const capacity=s.iven==='rescued'?3:2;
  $('boat-info').textContent=`${s.bank==='mill'?'Mill':'Road'} bank · ${s.hull} hull · ${s.aboard+Number(s.medicine==='aboard')}/${capacity} cargo slots · ${s.iven==='rescued'?1:2} beat(s) per trip${s.line?' · guide line rigged':''}`;
  const position=s.phase==='pack'||s.phase==='workshop'?[118,327]:s.phase==='causeway'?[252,121]:s.bank==='road'?[471,278]:[228,293];
  $('party-marker').setAttribute('transform',`translate(${position.join(' ')})`);
  $('party-marker').setAttribute('opacity',s.ending?'0':'1');
  $('boat-marker').setAttribute('transform',`translate(${s.bank==='road'?445:260} 293)`);
  $('lantern-glow').setAttribute('opacity',s.light?'1':'0');
  $('causeway-line').setAttribute('opacity',s.light?'1':'.3');
  $('causeway-line').setAttribute('stroke-dasharray',s.bridge==='stable'?'none':s.bridge?'4 9':'15 9');
  $('guide-line').setAttribute('opacity',s.line?'1':'0');
  $('map-people').setAttribute('opacity',s.roof==='waiting'?'1':'0');
  $('map-counts').setAttribute('visibility','visible');
  $('yard-count').textContent=`${s.waiting} in yard`;$('road-count').textContent=`${s.saved} arrived`;
  $('map-desc').textContent=`Workshop and mill on the west bank, high road across the river. Waystone ${s.light?'lit':'dark'}. Causeway ${s.bridge||'broken'}. Ferry on ${s.bank} bank. ${s.saved} villagers delivered; ${s.waiting} waiting in the mill yard; ${s.aboard} aboard. Roof workers ${s.roof}; Iven ${s.iven}; medicine ${s.medicine}.`;
  $('map-caption').textContent=s.ending?'The crossing leaves a morning.':s.route==='causeway'?`Waystone lit · ${s.bridge==='stable'?'permanent road':s.bridge==='temporary'?'temporary footline':s.bridge==='waded'?'wet footpath':'missing boards'}`:s.route==='ferry'?`Ferry on the ${s.bank} bank · ${s.waiting} waiting in the yard`:'Two ways across. Neither can carry a promise.';
}
function renderContext() {
  const s=game.state,w=game.workshop.state,c=$('context');c.replaceChildren();c.hidden=!!s.ending;
  if(s.phase==='pack') p(`Two slots. ${s.kit.length}/2 packed. A resource used for a rescue will not be available to build or protect the crossing.`,c);
  else if(s.phase==='workshop') {
    p(s.time?'Every reply costs one flood beat. Leaving opens the ferry route; agreement supplies light for the causeway.':'The landing has flooded. You can leave or finish this conversation, but no crossing can begin tonight.',c);
    if(w.cooldown)p(`The Keeper is recovering from the outburst. ${w.cooldown} quiet moments remain; the flood is still rising.`,c);
    else if(w.apology_due)p('The false council order is still uncorrected.',c);
    else if(w.herbs_sorted)p('The bench is clear. The loose rune is within reach.',c);
  } else if(s.phase==='route') {
    p(`${s.light?'The lit causeway is closer, but its boards still need repair. ':'The dark causeway cannot be used. '}The ferry needs no agreement. Travel also spends the flood window.`,c);
  } else {
    p(`${s.waiting} villagers waiting in the yard${s.aboard?`; ${s.aboard} aboard`:''}. Rescue deadlines count the completion beat. People left behind seek refuge; they are stranded tonight.`,c);
    if(s.phase==='ferry')p(s.line?'The guide line prevents both hull damage and spoiled medicine.':'People and medicine share cargo slots. A surge spoils exposed medicine; extra timber only protects the hull.',c);
    else p(s.bridge==='stable'?'The stable road can carry the medicine cart with the people.':s.bridge==='waded'?'The wet footpath cannot carry the medicine.':s.bridge?'The temporary crossing is slower without Iven. Carry medicine separately.':'Light reveals the route; it does not replace the missing boards.',c);
  }
}
function renderNarrative() {
  const s=game.state,last=game.history.at(-1),n=$('narrative');n.replaceChildren();
  if(s.phase==='pack') {
    paragraphs("Mara's cart has stopped outside the workshop. Two mill workers are on its roof; two more wait with the clinic's medicine below. Iven's ferry is pinned against the jetty.\n\nYou have room for two items. Leave the rest on the cart.",n);
    return;
  }
  if(last?.workshop_trace) {
    const t=last.workshop_trace;p(t.speaker,n,'speaker');paragraphs(t.text,n);
    const rest=last.text.slice(`${t.speaker}: ${t.text}`.length).trim();if(rest)paragraphs(rest,n);
  } else if(last) paragraphs(last.text.replace(/^The Last Waystone\n/,''),n);
}
function choiceDetail(choice) {
  const s=game.state;
  let detail=choice.label.match(/\[(.+)\]/)?.[1]||'';
  if(s.phase==='pack' && itemNotes[choice.name])return itemNotes[choice.name];
  if(choice.name==='row') {
    const currents=Array.from({length:choice.cost},(_,i)=>game.current(i));
    const damage=s.line?0:currents.reduce((n,x)=>n+({slack:0,pull:1,surge:2}[x]),0);
    detail+=` · projected hull ${Math.max(0,s.hull-damage)}`;
    if(!s.line && currents.includes('surge') && s.medicine==='aboard')detail+=' · medicine will spoil';
    if(damage>=s.hull)detail+=' · ferry will fail';
  }
  return detail;
}
function render() {
  if(game.handover){renderHandover(game,{p,row,paragraphs,onAction:morningAction});return;}
  if(game.morning){renderMorning(game,{p,row,paragraphs,onAction:morningAction});return;}
  document.querySelector('.layout').classList.remove('morning','handover');
  $('continue-handover').hidden=true;
  $('chapters').hidden=false;$('flood-title').textContent='The flood window';$('time-unit').textContent='beats left';
  $('clock-note').textContent='Your choices move the water. Reading takes no time.';
  $('ending-note').textContent='There is no single score. People, medicine and tomorrow’s route have separate outcomes.';
  $('boat-marker').setAttribute('opacity','1');
  const s=game.state,stage=s.ending?4:s.phase==='pack'?0:s.phase==='workshop'?1:s.phase==='route'?2:3;
  $('play').dataset.phase=s.phase;$('play').dataset.ending=s.ending||'';
  [...$('chapters').children].forEach((li,i)=>{li.classList.toggle('done',i<stage);if(i===stage)li.setAttribute('aria-current','step');else li.removeAttribute('aria-current');});
  $('chapter').textContent=`0${stage+1} / ${s.ending?'THE MORNING LIST':s.phase==='pack'?'PREPARATION':s.phase==='workshop'?'THE LOOSE RUNE':s.phase==='route'?'THE DEPARTURE':'THE CROSSING'}`;
  $('scene-title').textContent=s.ending?endingTitles[s.ending]:titles[s.phase];
  renderNarrative();renderContext();renderSituation();
  $('continue-morning').hidden=!s.ending;
  $('choices').replaceChildren();$('choices-area').hidden=!!s.ending;$('ending').hidden=!s.ending;
  $('decision-title').textContent=s.phase==='pack'?'Choose your equipment':'What will you do?';
  $('decision-note').textContent=s.phase==='pack'?'No time spent packing':'Costs shown before you choose';
  for(const choice of game.choices()) {
    const b=document.createElement('button');b.className='choice';b.dataset.action=choice.name;
    if(s.phase==='pack' && s.kit.includes(choice.name)) {b.classList.add('packed');b.setAttribute('aria-pressed','true');}
    else if(s.phase==='pack' && itemNotes[choice.name])b.setAttribute('aria-pressed','false');
    if(['finish','retreat','leave'].includes(choice.name))b.classList.add('exit');
    const label=document.createElement('span');label.className='label';label.textContent=choice.label.replace(/ \[.*\]$/,'');
    const cost=document.createElement('span');cost.className='cost';cost.textContent=s.phase==='pack' && s.kit.includes(choice.name)?'Packed':s.phase==='workshop'&&!s.time?'1 reply':choice.cost?`${choice.cost} beat${choice.cost===1?'':'s'}`:'No time';
    b.append(label,cost);const detail=choiceDetail(choice);
    if(detail){const span=document.createElement('span');span.className='detail';span.textContent=detail;b.append(span);}
    b.addEventListener('click',()=>{
      try {game.act(choice.name);say('');render();persist();
        // Keep packing focus at the equipment; changed scenes begin at their heading.
        if(game.state.phase==='pack') ($('choices').querySelector(`[data-action="${choice.name}"]`)||$('choices').lastElementChild)?.focus({preventScroll:true});
        else focusScene();
      }catch(e){say(e.message);}
    });$('choices').append(b);
  }
  if(s.ending) {
    $('outcome').replaceChildren();row($('outcome'),'Villagers on the high road',`${s.saved} / 4`);
    row($('outcome'),'Clinic medicine',{delivered:'Dry & delivered',spoiled:'Water-damaged',waiting:'Left at the mill',aboard:'Still aboard'}[s.medicine]);
    row($('outcome'),'Iven',s.iven==='rescued'?'With the party':'Stranded tonight');
    row($('outcome'),"Tomorrow’s route",s.bridge==='stable'?'Repaired causeway':s.bridge?'Temporary crossing':s.route==='ferry'&&s.hull&&s.iven==='rescued'?'Ferry retained':'Recovery needed');
    $('epilogue').replaceChildren();paragraphs(game.epilogue().split('\n\n').slice(2).join('\n\n'),$('epilogue'));
  }
  $('journal-count').textContent=`${game.history.length} decisions`;$('journal-entries').replaceChildren();
  for(const entry of game.history) {
    const li=document.createElement('li');p(`Beat ${entry.after.expedition.elapsed} · ${entry.action} · ${entry.cost?`${entry.cost} spent`:'no time'}`,li,'entry-heading');
    p(entry.text,li);$('journal-entries').append(li);
  }
}
function morningAction(action){try{game.act(action);say('');render();persist();focusScene();}catch(e){say(e.message);}}
$('continue-morning').addEventListener('click',()=>morningAction('morning'));
$('continue-handover').addEventListener('click',()=>morningAction('handover'));
$('begin').addEventListener('click',()=>requestReplace(new Adventure()));
$('resume').addEventListener('click',()=>{say('');activate(candidate);});
$('restart').addEventListener('click',()=>requestReplace(new Adventure()));
$('replay').addEventListener('click',()=>requestReplace(new Adventure()));
$('cancel-replacement').addEventListener('click',()=>{$('replacement').close();replacement=null;});
$('replacement').addEventListener('cancel',()=>{replacement=null;});
$('confirm-replacement').addEventListener('click',()=>{const next=replacement;replacement=null;$('replacement').close();if(next){say('');activate(next);}});
$('help').addEventListener('click',()=>$('instructions').showModal());
$('toggle-map').addEventListener('click',()=>{
  const open=document.querySelector('.layout').classList.toggle('map-open');
  $('toggle-map').setAttribute('aria-expanded',String(open));$('toggle-map').textContent=open?'Hide crossing map':'Show crossing map';
});
document.querySelectorAll('[data-close]').forEach(b=>b.addEventListener('click',()=>$(b.dataset.close).close()));
$('export').addEventListener('click',()=>{
  let data;try {data=JSON.stringify(serialize(game),null,2)+'\n';}catch(e){say(e.message);return;}
  const blob=new Blob([data],{type:'application/json'}),url=URL.createObjectURL(blob),a=document.createElement('a');
  a.href=url;a.download='waystone-crossing.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);say('Save file downloaded. It contains your decisions, not personal information.');
});
$('import').addEventListener('click',()=>$('save-input').click());
$('save-input').addEventListener('change',async()=>{
  const file=$('save-input').files[0];$('save-input').value='';if(!file)return;
  try {
    if(file.size>65536)throw new Error('This save is too large. Choose a Waystone save file.');
    const next=restore(JSON.parse(await file.text()));say('');requestReplace(next);
  }catch{say('That file could not be restored. Choose a compatible Waystone save; your current crossing is unchanged.');}
});
try {
  const text=localStorage.getItem(KEY);
  if(text) {
    if(text.length>65536)throw new Error('Oversized save');
    candidate=restore(JSON.parse(text));$('resume').hidden=false;$('begin').classList.remove('primary');
    $('begin').textContent='Begin a new crossing';$('resume-note').hidden=false;
    $('resume-note').textContent=candidate.handover?`Saved handover · ${candidate.handover.state.ending?'receipt complete':candidate.handover.state.stage}.`:candidate.morning?`Saved morning · ${candidate.morning.state.time} shifts left.`:candidate.state.ending?`Saved ending: ${endingTitles[candidate.state.ending]}`:`Saved at ${candidate.state.phase} · ${candidate.state.time} beats left.`;
    $('export').hidden=false;
    // A recovered save can be exported before deciding to replace it.
    game=candidate;
  }
}catch{say('Browser progress could not be read. You can begin a new crossing or load a save file.');}
