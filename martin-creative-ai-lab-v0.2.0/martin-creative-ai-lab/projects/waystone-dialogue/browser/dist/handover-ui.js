import {renderMorning} from './morning-ui.js';
export function renderHandover(game,ui) {
  // Reuse the morning's factual roster; override only the current conversation/loan.
  renderMorning(game,ui);
  const {p,row,paragraphs,onAction}=ui,$=id=>document.getElementById(id),scene=game.handover,s=scene.state,a=scene.afternoon();
  document.querySelector('.layout').classList.add('handover');
  $('play').dataset.phase='handover';$('play').dataset.ending=s.ending||'';
  $('chapter').textContent='DAY TWO / THE RECEIPT';
  $('scene-title').textContent={table:'A request, not an order.',decision:'What can the village spare?',terms:'Write the limit.',ended:'What leaves. What stays.'}[s.stage];
  $('narrative').replaceChildren();paragraphs(scene.history.at(-1)?.text||scene.opening(),$('narrative'));
  $('flood-title').textContent='At the table';$('remaining').textContent={table:1,decision:2,terms:3,ended:3}[s.stage];$('time-unit').textContent='of 3 parts';
  $('clock-note').textContent='The morning is finished. Reading and speaking take no work shifts.';
  $('clock').replaceChildren();
  for(const [index,label] of ['Listen','Choose','Terms'].entries()) {
    const li=document.createElement('li');li.textContent=label;
    li.className=index+1<Number($('remaining').textContent)?'spent':index+1===Number($('remaining').textContent)?'current':'';$('clock').append(li);
  }
  $('clock').setAttribute('aria-label',`Conversation: ${s.stage}. No running clock.`);
  $('equipment').textContent='Morning work and deliveries stay on this list. The handover records a separate loan.';
  $('roster').children[1].querySelector('dt').textContent='Iven after morning';
  $('map-caption').textContent=s.ending?`Local afternoon route: ${a.route}`:'The local crossing before a loan is agreed';
  if(s.ending) {
    row($('roster'),'Iven locally now',a.iven?'With the local crew':'Unavailable');
    row($('roster'),'Ferry locally now',a.ferry?'Retained':'Unavailable');
    $('boat-marker').setAttribute('opacity',a.ferry?'1':'.3');
    $('map-desc').textContent=`Afternoon: ${a.route}; local ferry ${a.ferry?'retained':'unavailable'}; Iven ${a.iven?'present':'unavailable'}. Past deliveries remain unchanged.`;
  }
  $('context').replaceChildren();$('context').hidden=!!s.ending;
  if(s.stage==='table') {
    p('Hear anyone present, or go straight to the request. No resource is handed over until you choose it and write the terms.',$('context'));
    p(`Council record: ${s.order==='clear'?'crossing crew’s request':'disputed; no council authority established'}.`,$('context'));
  } else if(s.stage==='decision')p('A boat and a boat hand are separate offers. Dain’s crew can take a ready ferry without taking Iven. A guide leaves only after offering to go.',$('context'));
  else if(!s.ending)p('Choose the scope of this commitment. A return deadline is an obligation to check later; it does not make anyone return now.',$('context'));
  $('decision-title').textContent=s.stage==='table'?'Who do you hear?':s.stage==='decision'?'What do you offer?':'What goes on the receipt?';
  $('decision-note').textContent='No work shifts spent';$('continue-morning').hidden=true;$('continue-handover').hidden=true;
  $('choices').replaceChildren();$('choices-area').hidden=!!s.ending;$('ending').hidden=!s.ending;
  for(const choice of scene.choices()) {
    const b=document.createElement('button');b.className='choice';b.dataset.action=choice.name;
    const label=document.createElement('span'),detail=document.createElement('span');label.className='label';label.textContent=choice.label;detail.className='detail';detail.textContent=choice.detail;
    b.append(label,detail);b.addEventListener('click',()=>onAction(choice.name));$('choices').append(b);
  }
  if(s.ending) {
    $('outcome').replaceChildren();
    row($('outcome'),'Sent upstream',{ 'lend-ferry':'Ferry with Dain’s boat hands','send-guide':'Iven, by his own offer','keep-crossing':'No local boat or guide'}[s.decision]);
    row($('outcome'),'Receipt',{decline:'Request refused','review-later':'Later review requested','return-at-dusk':'Return due at dusk · not yet verified','open-return':'Return after recovery · no time agreed'}[s.term]);
    row($('outcome'),'Local afternoon route',a.route);row($('outcome'),'Local grain capacity',`${a.grain_per_trip} crate(s) / ${a.shifts_per_trip} shift(s)`);
    row($('outcome'),'Council record',s.order==='clear'?'Crossing crew’s request':'Disputed authority');
    $('epilogue').replaceChildren();paragraphs(scene.epilogue(),$('epilogue'));
  }
  $('ending-note').textContent='The afternoon crew inherits the remaining work and any agreed return deadline.';
}
