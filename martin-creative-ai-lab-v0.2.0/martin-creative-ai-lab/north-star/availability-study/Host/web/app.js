// This browser observes the C# owner. No wall clock, advertisement or picture completes a service.
'use strict';
const $ = id => document.getElementById(id);
const phaseNames = ['Day', 'Late afternoon', 'Nightfall', 'Night', 'Dawn'];
const choices = {
  'route fast': ['The rough shortcut', 'Spend one route phase and two jar integrity at departure. A weak patch breaks here; the fired repair still has to survive both actual crossings.', 'Take the rough shortcut'],
  'route sheltered': ['The sheltered path', 'Spend two route phases, with no departure wear. It fits an early patch; a three-phase fired repair leaves too little time. Actual danger remains.', 'Take the sheltered path'],
  continue: ['The second passage', 'The first crossing is won. Begin the second actual encounter; the water is still carried, not delivered.', 'Continue the actual crossing'],
  deliver: ['Water the waiting seedbeds', 'Transfer the two carried water units only after an actual living crossing with the jar intact. Arrival alone does not water them.', 'Hand over the water'],
  walk: ['Walk through the threat', 'Advance one position and recover two resolve. Walking avoids a pulse; an unprotected bolt causes harm and one jar wear.', 'Walk'],
  dash: ['Dash across a pulse', 'Advance two positions, spending one resolve. Movement avoids a pulse; a bolt can still cause harm and wear the jar.', 'Dash'],
  skill: ['Draw the bolt while moving', 'Lure advances one position and spends three resolve to protect against a bolt. It does not move you out of a pulse.', 'Use Lure'],
  promise: ['Say you will return', 'Words only. No reservation, phase cost or completed repair.', 'Make a promise'],
  reserve: ['Ask Mara to set aside the kiln', 'Commit her capacity and spend one phase. Her own batch must wait; nothing is repaired yet.', 'Reserve the work'],
  shape: ['Shape and fire the repair', 'Spend two phases on the reserved work. A ready repair still needs an actual collection.', 'Do the reserved work'],
  collect: ['Take the fired repair', 'Complete the actual handoff. An advertised closing time cannot erase work already committed.', 'Collect the repair'],
  alone: ['Patch it yourself', 'Spend two remaining phases for a temporary repair with lower durability. Mara’s batch remains unfinished.', 'Make a temporary patch'],
  wait: ['Let one phase pass', 'Advance exactly one explicit phase. No service, handoff or return is inferred.', 'Advance one phase'],
  leave: ['Leave the reserved work', 'Leave the counter with any reservation still outstanding. No work or handoff is completed; a later opening does not confirm Mara’s return.', 'Leave without a handoff'],
  withdraw: ['Withdraw the reservation', 'Leave the service unfinished. Used time is not refunded and no repair is collected.', 'Withdraw explicitly']
};
let current = null;
let connected = false;
let busy = false;
let epoch = 0;
let pending = null;
function text(id, value) { $(id).textContent = String(value); }
function enable() {
  for (const b of document.querySelectorAll('[data-command]')) b.disabled = busy || !connected;
  $('restart').disabled = busy || !connected;
  $('reconnect').disabled = busy && connected;
}
function render(observation) {
  const s = observation.state;
  if (!s || !Array.isArray(s.commands) || !Number.isInteger(s.phase) || s.phase < 0 || s.phase > 4) throw new Error('Unrecognized workshop observation');
  current = observation;
  connected = true;
  document.body.dataset.connected = 'true';
  document.body.dataset.authority = String(s.authority).toLowerCase();
  document.body.dataset.outcome = String(s.outcome);
  document.body.dataset.collected = String(s.collected);
  text('connection', 'LIVE · current attempt observed');
  const onJourney = s.journey && s.journey.stage !== 'workshop';
  document.body.dataset.journeyActive = String(Boolean(onJourney));
  text('scene-title', onJourney ? 'WORKSHOP RECORD · BEFORE DEPARTURE' : 'AT THE WORKSHOP');
  text('authority-label', onJourney ? 'MARA’S WORKSHOP RECORD' : 'MARA’S ACTUAL STATE');
  text('phase', `${onJourney ? 'Workshop ' : ''}Phase ${s.phase} / 4 · ${phaseNames[s.phase]}`);
  text('remaining', `${s.remaining} workshop phase(s) ${onJourney ? 'remained at departure' : 'remain'}`);
  text('advertised', s.advertised ? 'Advertised open' : 'Outside the advertised window');
  $('advertised').dataset.value = String(s.advertised);
  text('authority', s.authority);
  $('authority').dataset.value = s.authority;
  text('availability', s.authority === 'unaccounted' ? 'An outstanding reservation remains. Mara’s location and availability are not confirmed.' : s.reserved ? s.work_ready ? 'Committed work is ready. Collection is not yet observed.' : 'Capacity committed to this repair. Work is not yet ready.' : s.available ? 'Presence and capacity are confirmed by the owner.' : 'Availability is not confirmed by the owner.');
  if (onJourney) text('availability', 'This is the retained workshop observation before departure. Mara’s current location is not observed from the road.');
  text('stats', `Phase ${s.phase} · Authority ${s.authority} · Durability ${s.durability}`);
  text('outcome', s.outcome);
  $('outcome').dataset.value = s.outcome;
  text('durability', `${onJourney ? 'Repair durability at departure' : 'Observed durability'}: ${s.durability}. ${s.collected ? 'Actual collection recorded.' : 'No collected repair recorded.'}`);
  text('potter-work', `Mara's own work remaining: ${s.potter_work_remaining}`);
  $('potter-work').dataset.value = String(s.potter_work_remaining);
  text('account-title', onJourney ? 'The workshop record before departure.' : 'What has actually happened.');
  text('last', s.last);
  text('command-result', `${observation.accepted ? 'Accepted observation' : 'Refused action'} · ${observation.command}`);
  const actualPresence = String(s.authority).toLowerCase() === 'present' || String(s.authority).toLowerCase() === 'committed';
  // SVG elements require an actual attribute/CSS rule, not a JavaScript expando.
  $('mara').toggleAttribute('hidden', !actualPresence);
  $('empty-place').toggleAttribute('hidden', actualPresence);
  $('fired-tile').toggleAttribute('hidden', !s.collected);
  $('patched-tile').toggleAttribute('hidden', !(s.durability > 0 && !s.collected));
  $('cracked-tile').toggleAttribute('hidden', s.durability > 0);
  const workshopCaption = s.authority === 'unaccounted' ? 'Reservation outstanding. No presence, completed service or handoff is confirmed.' : s.collected ? 'A fired repair was actually handed over. Mara’s own batch is still unfinished.' : s.durability > 0 ? 'A temporary patch is in place. The potter’s work was not completed for her.' : s.work_ready ? s.reserved ? 'Ready at the workshop. No collection has happened yet.' : 'A shaped repair remains unfinished. Neither Mara’s presence nor a handoff is confirmed.' : s.reserved ? 'The kiln is reserved. Time and capacity are spent; the repair is not completed.' : 'The opening notice and the observed person are separate facts.';
  text('scene-caption', onJourney ? `Before departure: ${workshopCaption} This retained workshop record is not a fresh observation of Mara from the road.` : workshopCaption);
  text('drawing-description', `${onJourney ? 'Historical workshop record before departure. ' : ''}Phase ${s.phase}: ${phaseNames[s.phase]}. Advertised ${s.advertised ? 'open' : 'closed'}. Actual authority: ${s.authority}. Repair: ${s.outcome}, durability ${s.durability}. Mara's work remaining: ${s.potter_work_remaining}. ${s.last}`);
  renderJourney(s);
  const grid = $('choices');
  grid.replaceChildren();
  for (const command of s.commands) {
    if (command === 'restart') continue;
    const info = command === 'wait' && onJourney
      ? ['Wait through this threat', 'Spend one actual encounter beat without moving. Waiting does not avoid a pulse and can cause harm and jar wear.', 'Wait one beat']
      : command === 'leave' && !s.reserved
      ? ['Leave the counter', 'Leave without a reservation or repair. A later opening time cannot confirm Mara’s return.', 'Leave the counter']
      : choices[command] || [command, 'An explicit action offered by the current C# owner.', command];
    const card = document.createElement('article');card.className = 'choice';
    const title = document.createElement('h3');title.textContent = info[0];
    const detail = document.createElement('p');detail.textContent = info[1];
    const button = document.createElement('button');button.type = 'button';button.dataset.command = command;button.textContent = info[2];button.addEventListener('click', () => send(command));
    card.append(title, detail, button);grid.append(card);
  }
  if (!grid.children.length) { const p = document.createElement('p');p.className = 'empty-choice';p.textContent = 'No further action is offered in this attempt. Read the recorded outcome or begin a separate new attempt.';grid.append(p); }
  enable();
}
function renderJourney(s) {
  const j = s.journey;
  $('journey-panel').toggleAttribute('hidden', !j);
  if (!j) return;
  const e = j.encounter;
  text('journey-stage', j.stage);
  $('journey-stage').dataset.value = j.stage;
  text('journey-route', j.route === 'none' ? 'Not departed' : j.route);
  for (const [id, value] of [['journey-phase', j.total_phase], ['journey-integrity', j.integrity], ['journey-water', j.water], ['journey-delivered', j.delivered]]) {
    text(id, id === 'journey-phase' ? `Total phase ${value} / 4 · ${4 - value} local phase(s) remain` : value);
    $(id).dataset.value = String(value);
  }
  text('journey-last', j.last);
  $('journey-encounter').toggleAttribute('hidden', !e || j.stage === 'workshop');
  text('journey-health', e ? e.health : '—');
  $('journey-health').dataset.value = e ? String(e.health) : '';
  text('encounter-detail', e ? ` / ${e.maximum_health} health · ${e.resolve} / ${e.maximum_resolve} resolve · position ${e.position} / ${e.required_position} · beat ${e.beat} / ${e.maximum_beats}` : 'No actual encounter');
  text('journey-threat', e ? e.threat : 'No threat observed.');
  const departed = j.stage !== 'workshop';
  $('road-traveler').toggleAttribute('hidden', !departed);
  $('journey-jar').toggleAttribute('hidden', !departed || j.integrity <= 0);
  $('road-broken-jar').toggleAttribute('hidden', !departed || j.integrity > 0);
  $('road-water').toggleAttribute('hidden', j.water <= 0);
  const bothBedsWatered = Array.isArray(j.watered_beds) && j.watered_beds.length === 2 && j.watered_beds.every(value => value === true);
  $('watered-beds').toggleAttribute('hidden', !bothBedsWatered);
  $('watered-beds').dataset.value = String(bothBedsWatered);
  $('dry-seedbeds').toggleAttribute('hidden', bothBedsWatered);
  $('route-goal').toggleAttribute('hidden', !e || !e.active);
  if (departed) {
    const progress = e ? Math.max(0, Math.min(1, e.position / e.required_position)) : 0;
    const x = j.stage === 'delivered' ? 816 : j.stage === 'arrival' ? 710 : j.stage === 'interlude' ? 460 : e && e.stage === 1 ? 460 + progress * 250 : 250 + progress * 210;
    $('road-traveler').setAttribute('transform', `translate(${x} ${212 - Math.sin(progress * Math.PI) * 15})`);
  }
  const captions = {
    workshop: 'Repair first; an accepted departure fills the jar at the well. No water is delivered yet.',
    crossing: 'The jar is carried through an actual encounter. Neither paid time nor a route promise completes it.',
    interlude: 'The first passage was won. The second still needs an explicit start; the seedbeds remain dry.',
    arrival: 'You reached the far side with water still carried. The handoff has not happened.',
    broken: 'The jar broke. Its water is lost; the seedbeds remain dry. This says nothing about Mara’s return.',
    failed: 'The actual passage failed. No water delivery is recorded; no fate is invented for Mara.',
    delivered: 'Two water units were actually transferred. The seedbeds are watered; Mara’s own two pots are still unfinished.'
  };
  text('road-caption', captions[j.stage] || 'Read the actual journey account.');
  text('road-description', `Journey ${j.stage}. Route ${j.route}. Total phase ${j.total_phase}. Jar integrity ${j.integrity}. Water carried ${j.water}. Water actually delivered ${j.delivered}. ${j.last}`);
  text('choices-title', j.stage === 'workshop' ? s.durability > 0 ? 'A repaired jar. Choose its path.' : 'Preparation, path and handoff.' : j.stage === 'arrival' ? 'Arrival is not a handoff.' : j.stage === 'interlude' ? 'One passage is still ahead.' : j.stage === 'crossing' ? 'Keep yourself and the jar intact.' : 'The account stands.');
}
function quarantine(message) {
  epoch++;
  if (pending) pending.abort();
  pending = null;busy = false;connected = false;
  document.body.dataset.connected = 'false';
  text('connection', 'STALE · read the current attempt');
  text('last', message);
  if (current && current.state.journey) text('journey-last', message);
  text('command-result', 'Outcome uncertain · no automatic replay');
  enable();
}
async function request(path, command) {
  if (busy) return null;
  if (command !== undefined && !connected) return null;
  const owner = epoch;
  busy = true;pending = new AbortController();enable();
  try {
    const options = { signal: pending.signal };
    if (command !== undefined) Object.assign(options, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ command }) });
    const response = await fetch(path, options);
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const observed = await response.json();
    if (owner !== epoch) return null;
    render(observed);
    return observed;
  } catch (error) {
    if (owner === epoch) quarantine(command === undefined ? 'The workshop could not be read. Retained facts are stale. Read again before choosing.' : 'The action may have reached the workshop. Its outcome is uncertain. Read the current state before choosing; the action will not be replayed.');
    return null;
  } finally {
    if (owner === epoch) { busy = false;pending = null;enable(); }
  }
}
function send(command) {
  if (!connected || busy) return Promise.resolve(null);
  if (command !== 'restart' && !current.state.commands.includes(command)) return Promise.resolve(null);
  return request('/command', command);
}
function refresh() { if (busy && connected) return Promise.resolve(null);return request('/state'); }
$('reconnect').addEventListener('click', refresh);
$('restart').addEventListener('click', () => send('restart'));
window.addEventListener('blur', () => { if (busy) quarantine('Focus changed during an uncertain request. Read the actual workshop; no late response or old intent will be replayed.'); });
document.addEventListener('visibilitychange', () => { if (document.hidden && busy) quarantine('The workshop was hidden during a request. Its outcome remains uncertain until explicitly read.'); });
window.addEventListener('offline', () => quarantine('Connection lost. Current presence and outcome are uncertain; read before acting again.'));
window.availabilityStudy = Object.freeze({ snapshot: () => current ? current.state : null, command: send, refresh });
enable();refresh();
