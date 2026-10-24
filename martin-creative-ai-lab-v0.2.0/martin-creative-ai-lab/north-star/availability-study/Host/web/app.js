// This browser observes the C# owner. No wall clock, advertisement or picture completes a service.
'use strict';
const $ = id => document.getElementById(id);
const phaseNames = ['Day', 'Late afternoon', 'Nightfall', 'Night', 'Dawn'];
const choices = {
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
  text('connection', 'LIVE · current workshop observed');
  text('phase', `Phase ${s.phase} / 4 · ${phaseNames[s.phase]}`);
  text('remaining', `${s.remaining} phase(s) remain`);
  text('advertised', s.advertised ? 'Advertised open' : 'Outside the advertised window');
  $('advertised').dataset.value = String(s.advertised);
  text('authority', s.authority);
  $('authority').dataset.value = s.authority;
  text('availability', s.authority === 'unaccounted' ? 'An outstanding reservation remains. Mara’s location and availability are not confirmed.' : s.reserved ? s.work_ready ? 'Committed work is ready. Collection is not yet observed.' : 'Capacity committed to this repair. Work is not yet ready.' : s.available ? 'Presence and capacity are confirmed by the owner.' : 'Availability is not confirmed by the owner.');
  text('stats', `Phase ${s.phase} · Authority ${s.authority} · Durability ${s.durability}`);
  text('outcome', s.outcome);
  $('outcome').dataset.value = s.outcome;
  text('durability', `Observed durability: ${s.durability}. ${s.collected ? 'Actual collection recorded.' : 'No collected repair recorded.'}`);
  text('potter-work', `Mara's own work remaining: ${s.potter_work_remaining}`);
  $('potter-work').dataset.value = String(s.potter_work_remaining);
  text('last', s.last);
  text('command-result', `${observation.accepted ? 'Accepted observation' : 'Refused action'} · ${observation.command}`);
  const actualPresence = String(s.authority).toLowerCase() === 'present' || String(s.authority).toLowerCase() === 'committed';
  // SVG elements require an actual attribute/CSS rule, not a JavaScript expando.
  $('mara').toggleAttribute('hidden', !actualPresence);
  $('empty-place').toggleAttribute('hidden', actualPresence);
  $('fired-tile').toggleAttribute('hidden', !s.collected);
  $('patched-tile').toggleAttribute('hidden', !(s.durability > 0 && !s.collected));
  $('cracked-tile').toggleAttribute('hidden', s.durability > 0);
  const caption = s.authority === 'unaccounted' ? 'Reservation outstanding. No presence, completed service or handoff is confirmed.' : s.collected ? 'A fired repair was actually handed over. Mara’s own batch is still unfinished.' : s.durability > 0 ? 'A temporary patch is in place. The potter’s work was not completed for her.' : s.work_ready ? s.reserved ? 'Ready at the workshop. No collection has happened yet.' : 'A shaped repair remains unfinished. Neither Mara’s presence nor a handoff is confirmed.' : s.reserved ? 'The kiln is reserved. Time and capacity are spent; the repair is not completed.' : 'The opening notice and the observed person are separate facts.';
  text('scene-caption', caption);
  text('drawing-description', `Phase ${s.phase}: ${phaseNames[s.phase]}. Advertised ${s.advertised ? 'open' : 'closed'}. Actual authority: ${s.authority}. Repair: ${s.outcome}, durability ${s.durability}. Mara's work remaining: ${s.potter_work_remaining}. ${s.last}`);
  const grid = $('choices');
  grid.replaceChildren();
  for (const command of s.commands) {
    if (command === 'restart') continue;
    const info = command === 'leave' && !s.reserved
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
function quarantine(message) {
  epoch++;
  if (pending) pending.abort();
  pending = null;busy = false;connected = false;
  document.body.dataset.connected = 'false';
  text('connection', 'STALE · read the current workshop');
  text('last', message);
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
