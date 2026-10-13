export function renderMorning(game,ui) {
  const {p,row,paragraphs,onAction}=ui,$=id=>document.getElementById(id),day=game.morning,s=day.state;
  document.querySelector('.layout').classList.add('morning');
  document.querySelector('.layout').classList.remove('handover');
  $('continue-handover').hidden=!s.ending;
  $('play').dataset.phase='morning';$('play').dataset.ending=s.ending||'';
  $('chapters').hidden=true;$('chapter').textContent=s.ending?'DAY TWO / THE AFTERNOON LIST':'DAY TWO / THE MORNING CREW';
  $('scene-title').textContent=s.ending?(s.ending==='READY_FOR_NOON'?'The kitchen gate is open.':'Work for the next crew.'):'Six shifts before noon.';
  $('narrative').replaceChildren();paragraphs(day.history.at(-1)?.text||day.opening(),$('narrative'));
  $('flood-title').textContent='Morning work';$('remaining').textContent=s.time;$('time-unit').textContent='shifts left';
  $('clock-note').textContent='Clinic supplies due at shift 3. Noon wagon leaves at shift 6.';
  $('clock').replaceChildren();
  for(let shift=1;shift<=6;shift++) {
    const li=document.createElement('li');li.textContent=shift;li.className=shift<=s.elapsed?'spent':shift===s.elapsed+1?'current':'';
    if(shift===3)li.classList.add('deadline');li.title=`Shift ${shift}${shift===3?' · clinic deadline':''}`;$('clock').append(li);
  }
  $('clock').setAttribute('aria-label',`${s.elapsed} shifts worked, ${s.time} remaining. Clinic deadline 3, wagon departure 6.`);
  $('roster').replaceChildren();
  row($('roster'),'Mill party',`${s.people} of 4 at the clinic`,s.people===4?'safe':'');
  row($('roster'),'Iven',s.iven?'With the crew':'Still across the channel',s.iven?'safe':'');
  row($('roster'),'Clinic',s.medicine==='supplied'?(s.timely?'Supplied on time':'Supplied late'):s.medicine==='ready'?'Chest awaiting delivery':'Dry supplies needed',s.medicine==='supplied'?'safe':'warning');
  row($('roster'),'Kitchen grain',`${s.grain} / 4 crates`,s.grain===4?'safe':'');
  row($('roster'),'Sowing seed',{loft:'Still in the loft',saved:'Dry in the yard',sown:'Planted · harvest unknown'}[s.seed],s.seed!=='loft'?'safe':'');
  $('river').hidden=true;$('equipment').textContent=`${s.timber} timber bundle(s) · ${s.road?(s.ferry?'cart-bearing road + standby ferry':'cart-bearing road'):s.ferry?'ferry ready':'ridge trail only'}`;
  $('party-marker').setAttribute('opacity','0');$('map-people').setAttribute('opacity','0');$('lantern-glow').setAttribute('opacity','0');
  $('causeway-line').setAttribute('opacity',s.road?'1':'.3');$('causeway-line').setAttribute('stroke-dasharray',s.road?'none':'15 9');
  $('boat-marker').setAttribute('opacity',s.ferry?'1':'.3');$('guide-line').setAttribute('opacity','0');
  $('yard-count').textContent=`${4-s.people} still across`;$('road-count').textContent=`${s.people} at clinic`;
  $('map-caption').textContent=`Morning supplies via the ${day.transport()} · ${s.grain}/4 grain crates delivered`;
  $('map-desc').textContent=`Morning: ${s.people} villagers at the clinic; Iven ${s.iven?'present':'stranded'}. ${s.road?'Repaired causeway. ':''}${s.ferry?'Ferry ready. ':''}Clinic ${s.medicine}; ${s.grain} grain crates delivered; seed ${s.seed}. Ridge trail remains a slow fallback.`;
  $('context').replaceChildren();$('context').hidden=!!s.ending;
  p(`${s.road?'The road carries four crates in one shift.':s.ferry?`The ferry carries two crates per ${s.iven?'one shift':'two shifts'}.`:'The ridge trail carries one crate per two shifts.'} Loads and repairs compete with clinical care, stranded people and planting. Reading costs no shifts.`,$('context'));
  if(s.seed==='saved'&&s.people<4)p('The seed is safe; bring the whole mill party back before Senn’s planting crew can work.',$('context'));
  $('decision-title').textContent='What takes the next shift?';$('decision-note').textContent='Costs and loads shown before work';
  $('choices').replaceChildren();$('choices-area').hidden=!!s.ending;$('ending').hidden=!s.ending;$('continue-morning').hidden=true;
  for(const choice of day.choices()) {
    const b=document.createElement('button');b.className='choice'+(choice.name==='close'?' exit':'');b.dataset.action=choice.name;
    const label=document.createElement('span'),cost=document.createElement('span'),detail=document.createElement('span');
    label.className='label';label.textContent=choice.label;cost.className='cost';cost.textContent=choice.cost?`${choice.cost} shift${choice.cost===1?'':'s'}`:'No time';detail.className='detail';detail.textContent=choice.detail;
    b.append(label,cost,detail);b.addEventListener('click',()=>onAction(choice.name));$('choices').append(b);
  }
  if(s.ending) {
    $('outcome').replaceChildren();row($('outcome'),'Mill party at clinic',`${s.people} / 4`);
    row($('outcome'),'Clinic supplies',s.medicine==='supplied'?(s.timely?'On time':'Late'):s.medicine==='ready'?'Awaiting delivery':'Missing');
    row($('outcome'),'Kitchen grain',`${s.grain} / 4 crates`);row($('outcome'),'Sowing seed',{loft:'In the loft',saved:'Kept dry',sown:'Planted'}[s.seed]);
    row($('outcome'),'Afternoon transport',s.road?(s.ferry?'Causeway + ferry':'Causeway'):s.ferry?'Ferry':'Ridge trail');
    row($('outcome'),'Depot reserve',s.reserve_used?'Needs replenishing':'Untouched');
    $('epilogue').replaceChildren();paragraphs(day.epilogue(),$('epilogue'));
  }
  $('ending-note').textContent='Clinical timing, people, food, seed and afternoon transport keep their separate outcomes.';
  $('journal-count').textContent=`${game.history.length} campaign decisions`;$('journal-entries').replaceChildren();
  for(const entry of game.history) {
    const li=document.createElement('li'),clock=entry.after.morning;
    p(`${entry.after.handover?'Handover':clock?`Morning shift ${clock.elapsed}`:`Night beat ${entry.after.expedition.elapsed}`} · ${entry.action}`,li,'entry-heading');p(entry.text,li);$('journal-entries').append(li);
  }
}
