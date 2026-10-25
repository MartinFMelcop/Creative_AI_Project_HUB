'use strict';
// The owner supplies inventory, custody and actual encounters. This page supplies no clock or outcome.
const $ = id => document.getElementById(id);
let observation = null;
let connected = false;
let busy = false;
let generation = 0;
let request = null;
let queue = Promise.resolve();
function text(id, value) { $(id).textContent = String(value); }
function controls() {
  for (const button of document.querySelectorAll('[data-command]')) button.disabled = busy || !connected;
  $('refresh').disabled = busy && connected;
}
function render(next) {
  observation = next;
  const state = next.state;
  const encounter = state.encounter;
  const active = Boolean(encounter && encounter.active);
  const complete = Boolean(encounter && encounter.complete);
  const gaugeObserved = state.inventory.gauge;
  const gaugeHeld = gaugeObserved > 0;
  connected = true;
  document.body.dataset.connected = 'true';
  document.body.dataset.active = String(active);
  document.body.dataset.complete = String(complete);
  document.body.dataset.gauge = String(gaugeObserved);
  $('gauge-card').dataset.gaugeHeld = String(gaugeHeld);
  text('connection', 'LIVE · actual bench and crossing');
  text('preset', state.mode === 'missing' ? 'MISSING-GAUGE TRIAL · explicit fresh setup' : 'EQUIPPED TRIAL · explicit initial ownership');
  for (const id of ['fiber', 'binder']) text(id, state.inventory[id]);
  text('gauge', gaugeObserved);
  text('trail-rig', state.inventory.trail_rig);
  text('gauge-status', gaugeHeld ? 'Required gauge is actually owned. Making a rig does not consume it.' : 'Required gauge is missing. A recipe or promise cannot supply ownership.');
  text('transactions', state.transactions);
  text('consumed-rigs', state.consumed_rigs);
  text('attempts', state.attempts);
  text('notice', next.text);
  text('command-result', next.command === 'initial' ? 'NO ACTION TAKEN' : `${next.accepted ? 'ACCEPTED' : 'REFUSED'} · ${next.command}`);
  $('command-result').dataset.accepted = String(next.accepted);
  $('encounter').hidden = !active;
  $('route-traveler').toggleAttribute('hidden', !encounter);
  const position = encounter ? encounter.position : 0;
  const required = encounter ? encounter.required_position : 1;
  const fraction = required > 0 ? Math.max(0, Math.min(1, position / required)) : 0;
  $('route-traveler').setAttribute('transform', `translate(${90 + fraction * 810} 95)`);
  text('route-description', encounter ? `Actual crossing stage ${encounter.stage}. Position ${position} of ${required}. ${active ? 'Active; no result inferred.' : complete ? `Complete; won ${encounter.won}.` : 'Not final completion.'}` : 'No actual encounter has begun. A made rig is not an entry or a completed journey.');
  text('journey-phase', !encounter ? 'NO ACTUAL ENTRY YET' : active ? `ACTUAL CROSSING · STAGE ${encounter.stage}` : complete ? encounter.won ? 'ACTUAL EXPEDITION COMPLETED' : 'ACTUAL EXPEDITION ENDED' : encounter.won ? 'THIS CROSSING WON · EXPLICIT NEXT ENTRY REQUIRED' : 'THIS ATTEMPT ENDED · NO RIG REFUND');
  text('journey-status', !encounter ? 'Crafting creates an inventory output. Only an accepted entry spends it and starts the actual Crossing.' : active ? 'The announced threat and your next accepted action own contact and movement.' : complete ? encounter.won ? 'The actual final encounter completed. The gauge and remaining supplies are still separate inventory facts.' : 'The owner reports a completed failed outcome; preparation cannot erase spent rigs.' : encounter.won ? 'Survey victory is not final arrival. Make the next choice explicitly; the page will not enter for you.' : 'Failure retains the rig expenditure. A future permitted entry needs another actual output.');
  text('next-entry', complete ? 'Final completion comes only from the actual owner. No browser label or elapsed time can supply it.' : 'A successful survey is not final completion. Continue only through an explicit next entry.');
  const enter = $('enter');
  enter.firstChild.textContent = encounter && encounter.won && !complete ? 'Enter the next actual crossing' : 'Enter the actual crossing';
  text('beat', encounter ? `Beat ${encounter.beat} / ${encounter.maximum_beats}` : 'No beat observed');
  text('health', encounter ? encounter.health : '—');
  text('resolve', encounter ? encounter.resolve : '—');
  text('position', encounter ? `${position} / ${required}` : '—');
  text('threat', active ? encounter.threat : 'No active threat.');
  controls();
}
function quarantine(message) {
  generation++;
  if (request) request.abort();
  request = null;
  connected = false;
  busy = false;
  document.body.dataset.connected = 'false';
  text('connection', 'STALE · read before choosing');
  text('notice', message);
  text('command-result', 'NO NEW OUTCOME DISPLAYED');
  controls();
}
function command(value) {
  const intent = typeof value === 'string' ? value : value.command;
  const queuedGeneration = generation;
  queue = queue.then(async () => {
    if (!connected || queuedGeneration !== generation) return null;
    const owner = generation;
    busy = true;
    request = new AbortController();
    controls();
    try {
      const response = await fetch('/command', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ command: intent }), signal: request.signal });
      if (!response.ok) throw new Error(`The response could not be read (HTTP ${response.status}).`);
      const next = await response.json();
      if (owner === generation) {
        if (next.accepted && (intent === 'restart equipped' || intent === 'restart missing')) {
          generation++;
          busy = false;
          request = null;
        }
        render(next);
      }
      return next;
    } catch (error) {
      if (owner === generation) quarantine('The action may already have been accepted. Read the actual bench before making another choice; no request is automatically repeated.');
      return null;
    } finally {
      if (owner === generation) { busy = false; request = null; controls(); }
    }
  });
  return queue;
}
async function refresh() {
  generation++;
  if (request) request.abort();
  const owner = generation;
  connected = false;
  busy = true;
  document.body.dataset.connected = 'false';
  request = new AbortController();
  controls();
  try {
    const response = await fetch('/state', { cache: 'no-store', signal: request.signal });
    if (!response.ok) throw new Error('The bench could not be read.');
    const next = await response.json();
    if (owner === generation) render(next);
    return next;
  } catch (error) {
    if (owner === generation) quarantine('Current facts are unavailable. Retained inventory and encounter pictures are stale; no outcome is inferred. Read again when the host is available.');
    return null;
  } finally {
    if (owner === generation) { busy = false; request = null; controls(); }
  }
}
for (const button of document.querySelectorAll('[data-command]')) button.addEventListener('click', () => command(button.dataset.command));
$('refresh').addEventListener('click', refresh);
window.addEventListener('blur', () => quarantine('Focus changed. An action may already have reached the owner. Read current facts before choosing again.'));
window.addEventListener('pagehide', () => quarantine('This view is stale. Read the actual bench before choosing.'));
window.toolingStudy = Object.freeze({ snapshot: () => observation, command, refresh });
controls();
refresh();
