// Observe one C# scene. No browser clock, gesture or displayed promise owns a consequence.
'use strict';
const $ = id => document.getElementById(id);
let lastObservation = null;
let connected = false;
let busy = false;
let ownership = 0;
let controller = null;
let queue = Promise.resolve();
const preference = window.matchMedia('(prefers-reduced-motion: reduce)');
$('reduced-motion').checked = preference.matches;
function applyMotion() { document.body.dataset.motion = $('reduced-motion').checked ? 'reduced' : 'full'; }
applyMotion();
$('reduced-motion').addEventListener('change', applyMotion);

function text(id, value) { $(id).textContent = String(value); }
function numeric(id, value) { $(id).dataset.value = String(value); }
function visibleCommand(command, visible) {
  const element = document.querySelector(`[data-command="${command}"]`);
  if (element) element.hidden = !visible;
}
function controls() {
  for (const button of document.querySelectorAll('[data-command]')) button.disabled = busy || !connected;
  $('reconnect').disabled = busy && connected;
}
function showReceipts(receipts) {
  const list = $('receipts');
  list.replaceChildren();
  if (!receipts.length) {
    const empty = document.createElement('li');
    empty.className = 'empty-receipt';
    empty.textContent = 'No signed commitment or journey receipt.';
    list.append(empty);
    return;
  }
  const names = { commitment: 'A commitment, signed', withdrawal: 'Withdrawal before departure', solo_departure: 'Solo departure', observed_return: 'Actual handoff and return observed', failed_crossing: 'Crossing ended without delivery' };
  for (const receipt of receipts) {
    const row = document.createElement('li');
    row.dataset.kind = receipt.kind;
    row.dataset.guide = receipt.guide;
    row.dataset.delivered = String(receipt.delivered);
    row.dataset.returned = String(receipt.returned);
    const title = document.createElement('strong');
    title.className = 'receipt-title';
    title.textContent = names[receipt.kind] || receipt.kind;
    const detail = document.createElement('span');
    detail.className = 'receipt-detail';
    const terms = { dusk: 'Return due before dark', open: 'No return time agreed', solo: 'Solo journey' };
    detail.textContent = `${terms[receipt.term] || 'No terms recorded'} · ${receipt.guide === 'Rill' ? 'Rill named on this entry' : 'No guide supplied'}.`;
    const facts = document.createElement('span');
    facts.className = 'receipt-facts';
    facts.textContent = `Shift ${receipt.shift} · crates carried ${receipt.crates} · delivery ${receipt.delivered ? 'observed' : 'unchecked'} · completed-journey return ${receipt.returned ? 'observed' : 'unchecked'}.`;
    row.append(title, detail, facts);
    list.append(row);
  }
}
function render(observation) {
  const s = observation.state;
  const e = s.encounter;
  const returnObserved = Boolean(s.returned);
  const rillReturn = s.receipts.some(receipt => receipt.kind === 'observed_return' && receipt.guide === 'Rill' && receipt.returned === true);
  const guide = s.guide_location === 'local-preparing' ? 'preparing' : s.guide_location === 'travelling' ? 'away' : s.guide_location === 'unaccounted' ? 'unaccounted' : rillReturn ? 'returned' : 'secured';
  const guideLabels = { secured: 'Local · line secured here', preparing: 'Local · preparing the coil', away: 'Away · return not observed', unaccounted: 'Unaccounted for · no return confirmed', returned: 'Returned · available locally' };
  lastObservation = observation;
  connected = true;
  document.body.dataset.connected = 'true';
  document.body.dataset.guide = guide;
  document.body.dataset.delivered = String(Boolean(s.delivered));
  document.body.dataset.returned = String(returnObserved);
  document.body.dataset.coil = s.delivered ? 'delivered' : s.delivery_started ? 'away' : 'local';
  $('guide-line').dataset.line = guide;
  $('guide-line').dataset.state = guide;
  text('connection', 'LIVE · the current day');
  text('guide-state', guideLabels[guide]);
  text('delivered', s.delivered ? 'Delivered · actual handoff observed' : s.status === 'failed' ? 'Not delivered · handoff unconfirmed' : s.delivery_started ? 'Carried · handoff not completed' : 'At the board · not delivered');
  text('returned', returnObserved ? 'Return observed · completed journey' : 'No completed-journey return observed');
  numeric('coil-status', Boolean(s.delivered));
  numeric('return-status', returnObserved);
  numeric('delivered', Boolean(s.delivered));
  numeric('returned', returnObserved);
  text('crates', `${s.crates} / ${s.crates_required}`);
  numeric('crates-status', s.crates);
  numeric('crates', s.crates);
  text('remaining', `${s.remaining} / 4`);
  numeric('daylight', s.remaining);
  numeric('remaining', s.remaining);
  text('capacity', `${s.capacity} ${s.capacity === 1 ? 'crate' : 'crates'}`);
  numeric('capacity', s.capacity);
  text('notice', observation.text);
  text('command-result', observation.command === 'initial' ? 'No action taken' : `${observation.accepted ? 'Accepted' : 'Refused'} · ${observation.command}`);
  $('command-result').dataset.accepted = String(observation.accepted);
  for (const crate of document.querySelectorAll('[data-crate]')) crate.toggleAttribute('hidden', Number(crate.dataset.crate) <= s.crates);
  for (const shutter of document.querySelectorAll('[data-shutter]')) shutter.toggleAttribute('hidden', Number(shutter.dataset.shutter) > s.crates);
  $('route-traveler').toggleAttribute('hidden', !e.active);
  $('route-goal').toggleAttribute('hidden', !e.active);
  $('route-goal').dataset.value = String(e.required_position);
  $('route-goal').setAttribute('transform', `translate(${601 + e.required_position * 61} ${373 - e.required_position * 6.5})`);
  // Position is an observed C# fact; this mapping only places its marker in the drawing.
  $('route-traveler').setAttribute('transform', `translate(${601 + e.position * 61} ${373 - e.position * 6.5})`);
  $('sun').setAttribute('opacity', String(.25 + s.remaining * .1375));
  text('scene-phase', e.active ? e.kind === 'survey' ? 'ON THE SURVEY ROUTE' : 'ON THE DELIVERY ROUTE' : s.status === 'delivered' ? 'BACK AT THE WORK BOARD' : s.status === 'failed' ? 'AN UNFINISHED ACCOUNT' : 'AT EDDA\'S BOARD');
  text('scene-scope', `${s.remaining} shifts of light · ${s.crates_required - s.crates} shutter crates remain`);
  text('scene-description', `Edda's shutters: ${s.crates} of ${s.crates_required} crates carried. ${s.remaining} shifts remain. Rill: ${guideLabels[guide]}. Coil ${s.delivered ? 'delivered' : 'not delivered'}. Completed-journey return ${returnObserved ? 'observed' : 'not observed'}. ${observation.text}`);
  const caption = e.active ? `${e.kind === 'survey' ? 'Survey' : 'Delivery'} in progress · position ${e.position} / required ${e.required_position}.` : s.status === 'failed' ? s.guide_location === 'unaccounted' ? 'Rill is unaccounted for. No handoff or return is confirmed.' : 'The handoff was not completed. Unfinished work remains.' : s.delivered ? rillReturn ? 'Actual handoff completed. Rill returned; the shutters still need work.' : 'You returned from the handoff alone. Rill stayed local.' : s.status === 'committed' ? 'Signed, still local: Rill prepares the coil. Departure has not occurred.' : s.surveyed ? 'Survey completed. A new guided trip needs a current offer and signature.' : 'The route is unchecked. The line stays here.';
  text('route-caption', caption);
  const local = !e.active;
  $('local-choices').hidden = !local;
  visibleCommand('work', local);
  visibleCommand('survey', local && !s.surveyed && !s.delivery_started);
  visibleCommand('depart solo', local && s.surveyed && !s.delivery_started && s.guide_available);
  text('route-choice-title', s.surveyed ? 'A surveyed route. Your own time.' : 'See the crossing yourself.');
  text('route-choice-copy', s.status === 'committed' && !s.delivery_started ? 'Rill is reserved for the guided trip. Withdraw that commitment before choosing to carry the coil alone.' : s.surveyed ? 'You can attempt the delivery alone without assigning Rill. Solo travel uses three shifts; the actual crossing still has to finish.' : 'A survey takes one shift and an actual passage through the announced threats. It makes no promise for Rill.');
  visibleCommand('open', local);
  $('consultation').hidden = !local || s.conversation === 'closed';
  visibleCommand('hear', local && s.conversation === 'table');
  visibleCommand('offer', local && s.conversation === 'table');
  visibleCommand('terms dusk', local && (s.conversation === 'terms' || s.conversation === 'ready'));
  visibleCommand('terms open', local && (s.conversation === 'terms' || s.conversation === 'ready'));
  visibleCommand('confirm', local && s.conversation === 'ready');
  visibleCommand('defer', local && s.conversation !== 'closed');
  visibleCommand('decline', local && s.conversation !== 'closed');
  text('consultation-title', s.conversation === 'ready' ? 'The words are written. Still unsigned.' : s.conversation === 'terms' ? 'Write the limit before signing.' : 'Hear a current answer.');
  text('consultation-note', s.conversation === 'ready' ? 'Signing reserves Rill locally. It does not depart, deliver the coil or verify a return.' : s.conversation === 'terms' ? 'A return deadline and no agreed return time are different terms. Neither is an observed result.' : 'An offer depends on the actual survey, daylight and current local work list.');
  $('commitment').hidden = !local || s.status !== 'committed' || s.delivery_started;
  visibleCommand('depart guided', local && s.status === 'committed' && !s.delivery_started);
  visibleCommand('withdraw', local && s.status === 'committed' && !s.delivery_started);
  text('decision-title', e.active ? 'The journey has not finished.' : s.status === 'delivered' ? 'The handoff is done. The work is not erased.' : s.status === 'failed' ? 'An attempt ended. Keep the account honest.' : s.remaining === 0 ? 'The light is spent. Facts remain.' : 'Two tasks. One remaining day.');
  text('decision-context', s.due_elapsed ? 'The before-dark obligation has elapsed. That does not prove a return.' : e.active ? 'Resolve the actual passage below. Watching spends no beat.' : 'Reading the board spends no daylight. Unavailable choices explain their refusal.');
  $('encounter').hidden = !e.active;
  text('encounter-kind', e.kind === 'survey' ? 'ACTUAL SURVEY / RILL REMAINS LOCAL' : e.kind === 'guided' ? 'ACTUAL DELIVERY / GUIDED JOURNEY' : 'ACTUAL DELIVERY / SOLO JOURNEY');
  text('encounter-beat', `Beat ${e.beat} / ${e.maximum_beats}`);
  text('health', e.health);
  text('resolve', e.resolve);
  text('position', `${e.position} / ${e.required_position}`);
  numeric('health', e.health);
  numeric('resolve', e.resolve);
  numeric('position', e.position);
  text('threat', e.active ? e.threat : 'No active threat.');
  for (const command of ['walk', 'dash', 'skill', 'wait']) visibleCommand(command, e.active);
  showReceipts(s.receipts);
  controls();
}
function quarantine(message) {
  ownership++;
  if (controller) controller.abort();
  controller = null;
  busy = false;
  connected = false;
  document.body.dataset.connected = 'false';
  text('connection', 'STALE · read the current board');
  text('notice', message);
  text('command-result', 'No new outcome is displayed');
  // The retained facts remain labelled stale. A late accepted reply cannot revive this view.
  controls();
}
function command(value) {
  const commandText = typeof value === 'string' ? value : value.command;
  const enqueuedOwner = ownership;
  queue = queue.then(async () => {
    if (!connected || enqueuedOwner !== ownership) return null;
    const owner = ownership;
    busy = true;
    controller = new AbortController();
    controls();
    try {
      const response = await fetch('/command', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ command: commandText }), signal: controller.signal });
      if (!response.ok) throw new Error(`The command could not be read (HTTP ${response.status}).`);
      const observation = await response.json();
      if (owner === ownership) render(observation);
      return observation;
    } catch (error) {
      if (owner === ownership) quarantine('The connection was interrupted. The action may have reached the board; its outcome is not yet shown. Read the current board before choosing again.');
      return null;
    } finally {
      if (owner === ownership) { busy = false; controller = null; controls(); }
    }
  });
  return queue;
}
async function refresh() {
  const owner = ++ownership;
  if (controller) controller.abort();
  controller = new AbortController();
  busy = true;
  connected = false;
  document.body.dataset.connected = 'false';
  text('connection', 'Reading the current day…');
  controls();
  try {
    const response = await fetch('/state', { signal: controller.signal });
    if (!response.ok) throw new Error(`The board could not be read (HTTP ${response.status}).`);
    const observation = await response.json();
    if (owner === ownership) render(observation);
    return observation;
  } catch (error) {
    if (owner === ownership) quarantine('The current board is unavailable. The last displayed facts remain stale. Read the board again to inspect what actually happened.');
    return null;
  } finally {
    if (owner === ownership) { busy = false; controller = null; controls(); }
  }
}
for (const button of document.querySelectorAll('[data-command]')) button.addEventListener('click', () => command(button.dataset.command));
$('reconnect').addEventListener('click', refresh);
function loseOwnership() {
  if (busy) quarantine('Focus changed while an action was pending. It may have reached the board; a late reply will not be displayed. Read the current board to inspect the actual outcome.');
}
window.addEventListener('blur', loseOwnership);
document.addEventListener('visibilitychange', () => { if (document.hidden) loseOwnership(); });
window.authoredScene = Object.freeze({ snapshot: () => lastObservation, command, refresh, pending: () => busy, connected: () => connected });
controls();
refresh();
