export function renderAfternoon(game,ui) {
  const {p,row,paragraphs,onAction}=ui,$=id=>document.getElementById(id),day=game.afternoon,s=day.state,r=day.route,reviewing=day.reviewActive(),commitment=day.commitment();
  document.querySelector('.layout').classList.add('morning');
  document.querySelector('.layout').classList.remove('handover');
  $('continue-handover').hidden=true;
  $('continue-afternoon').hidden=true;
  $('play').dataset.phase='afternoon';$('play').dataset.ending=s.ending||'';
  $('chapters').hidden=true;$('chapter').textContent=reviewing?'DAY TWO / THE DEFERRED REQUEST':s.ending?'DAY TWO / THE DUSK LIST':'DAY TWO / THE AFTERNOON CREW';
  $('scene-title').textContent=reviewing?{table:'The request comes back.',decision:'What can leave now?',terms:'Agree the loan’s terms.'}[day.review.state.stage]:s.ending?'The light is going.':'Four shifts with what remains.';
  $('narrative').replaceChildren();paragraphs(day.history.at(-1)?.text||day.opening(),$('narrative'));
  $('flood-title').textContent='Afternoon work';$('remaining').textContent=s.time;$('time-unit').textContent='shifts left';
  $('clock-note').textContent=reviewing?'The remaining light stays in view. Discussion spends no work shifts.':'Four shifts until dusk. Agreed loans stay unavailable.';
  $('clock').replaceChildren();
  for(let shift=1;shift<=4;shift++) {
    const li=document.createElement('li');li.textContent=shift;li.className=shift<=s.elapsed?'spent':shift===s.elapsed+1?'current':'';
    if(shift===4)li.classList.add('deadline');li.title=`Shift ${shift}${shift===4?' · dusk':''}`;$('clock').append(li);
  }
  $('clock').setAttribute('aria-label',`${s.elapsed} shifts worked, ${s.time} remaining. Dusk after shift 4.`);
  $('roster').replaceChildren();
  row($('roster'),'Mill party',`${s.people} of 4 at the clinic`,s.people===4?'safe':'');
  row($('roster'),'Iven',s.iven?'With the crew':commitment.decision==='send-guide'?'Volunteering upstream':'Still across the channel',s.iven?'safe':'');
  row($('roster'),'Clinic',s.medicine==='supplied'?(s.timely?'Supplied on time':'Supplied late'):s.medicine==='ready'?'Chest awaiting delivery':'Dry supplies needed',s.medicine==='supplied'?'safe':'warning');
  row($('roster'),'Kitchen grain',`${s.grain} / 4 crates`,s.grain===4?'safe':'');
  row($('roster'),'Sowing seed',{loft:'Still in the loft',saved:'Dry in the yard',sown:'Planted · harvest unknown'}[s.seed],s.seed!=='loft'?'safe':'');
  if(day.receipt.handover.term==='review-later')row($('roster'),'Upstream request',day.review?.state.ending?(commitment.decision==='keep-crossing'?'Refused this afternoon':`${commitment.decision==='lend-ferry'?'Ferry':'Iven'} left after shift ${commitment.openedAt}`):'Deferred · no loan promised');
  $('river').hidden=true;$('equipment').textContent=`${r.route} · ${r.grain_per_trip} crate(s) / ${r.shifts_per_trip} shift(s)`;
  $('party-marker').setAttribute('opacity','0');$('map-people').setAttribute('opacity','0');$('lantern-glow').setAttribute('opacity','0');
  $('causeway-line').setAttribute('opacity',r.road?'1':'.3');$('causeway-line').setAttribute('stroke-dasharray',r.road?'none':'15 9');
  $('boat-marker').setAttribute('transform','translate(445 293)');
  $('boat-marker').setAttribute('opacity',r.ferry?'1':'.3');$('guide-line').setAttribute('opacity','0');
  $('yard-count').textContent=`${4-s.people} still across`;$('road-count').textContent=`${s.people} at clinic`;
  $('map-caption').textContent=`Afternoon: ${r.route} · ${s.grain}/4 grain crates received`;
  $('map-desc').textContent=`Afternoon route: ${r.route}. ${s.people} villagers at the clinic. ${s.grain} grain crates received; seed ${s.seed}.`;
  $('context').replaceChildren();$('context').hidden=!!s.ending;
  p(`${r.route}: ${r.grain_per_trip} crate(s) per ${r.shifts_per_trip} shift(s). ${day.review?.state.ending?'Afternoon decision recorded; noon receipt unchanged.':'Noon commitments stay in force.'} Work competes for the remaining light; reading takes no time.`,$('context'));
  if(s.medicine==='supplied'&&!s.timely)p(s.recall?'Morning callers contacted; original late delivery retained.':'Dry supplies are here; the morning callers still need contacting.',$('context'));
  if(s.seed==='saved'&&s.people<4)p('The seed is safe; bring the whole mill party back before Senn’s planting crew can work.',$('context'));
  if(reviewing)p('This is a new consultation with the crew present now. The noon receipt and earlier deliveries stay unchanged; no asset leaves before terms are accepted.',$('context'));
  $('decision-title').textContent=reviewing?(day.review.state.stage==='table'?'Who do you hear now?':day.review.state.stage==='decision'?'What can the crew spare?':'What limit do you agree?'):'What takes the next shift?';$('decision-note').textContent=reviewing?'No work shifts spent':'Costs and loads shown before work';
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
    row($('outcome'),'Local transport',r.route);
    if(day.review?.state.ending)row($('outcome'),'Afternoon upstream decision',commitment.decision==='keep-crossing'?'Request refused':`${commitment.decision==='lend-ferry'?'Ferry':'Iven'} sent · ${commitment.term==='return-at-dusk'?'due at dusk, unverified':'no return time agreed'}`);
    row($('outcome'),'Morning callers',s.timely?'Morning care opened on time':s.recall?'Contacted for afternoon care':'Recall still needed');
    row($('outcome'),'Depot reserve',s.reserve_used?'Needs replenishing':'Untouched');
    $('epilogue').replaceChildren();paragraphs(day.epilogue(),$('epilogue'));
  }
  $('ending-note').textContent='Local work is observed. An upstream rescue or return is not.';
  $('journal-count').textContent=`${game.history.length} campaign decisions`;$('journal-entries').replaceChildren();
  for(const entry of game.history) {
    const li=document.createElement('li'),clock=entry.after.morning,late=entry.after.afternoon;
    p(`${late?`Afternoon shift ${late.elapsed}`:entry.after.handover?'Handover':clock?`Morning shift ${clock.elapsed}`:`Night beat ${entry.after.expedition.elapsed}`} · ${entry.action}`,li,'entry-heading');p(entry.text,li);$('journal-entries').append(li);
  }
}
