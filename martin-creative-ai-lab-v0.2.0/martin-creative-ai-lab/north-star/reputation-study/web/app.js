'use strict';
// Read actual owner facts. No clock, picture or displayed account creates an action.
const $ = id => document.getElementById(id);
let observation = null;
let connected = false;
let busy = false;
let generation = 0;
let request = null;
let queue = Promise.resolve();
const names = { quay: 'Quay', orchard: 'Orchard' };
function text(id, value) { $(id).textContent = String(value); }
function controls() {
  for (const button of document.querySelectorAll('[data-command]')) button.disabled = busy || !connected;
  $('refresh').disabled = busy && connected;
}
function render(next) {
  observation = next;
  const state = next.state;
  connected = true;
  document.body.dataset.connected = 'true';
  document.body.dataset.activeRegion = state.region;
  text('connection', 'LIVE · actual local accounts');
  text('time', state.time);
  text('coins', state.coins);
  text('selected-region', names[state.region] || state.region);
  text('notice', next.text);
  text('command-result', next.command === 'initial' ? 'NO ACTION TAKEN' : `${next.accepted ? 'ACCEPTED' : 'REFUSED'} · ${next.command}`);
  $('command-result').dataset.accepted = String(next.accepted);
  for (const place of state.regions) {
    const id = place.id;
    const serviceObserved = Boolean(place.service);
    const card = $('place-' + id);
    if (!card) continue;
    card.dataset.selected = String(state.region === id);
    card.dataset.standing = String(place.standing);
    card.dataset.custody = String(place.custody);
    card.dataset.returned = String(place.returned);
    card.dataset.service = String(serviceObserved);
    text('standing-' + id, place.standing > 0 ? '+' + place.standing : place.standing);
    text('tool-' + id, place.custody ? 'Tool held by you · still owed here' : 'Tool at this store · not in your custody');
    text('return-' + id, place.returned ? 'Return actually recorded here' : 'No completed return recorded here');
    text('service-' + id, serviceObserved ? 'Service actually received here' : 'Service not received here');
    text('work-' + id, `Accepted help here: ${place.work}`);
    card.querySelector('.tool-label').textContent = place.custody ? 'HELD BY YOU · OWED HERE' : "THE STORE'S TOOL";
  }
  const list = $('receipts');
  list.replaceChildren();
  if (!state.receipts.length) {
    const row = document.createElement('li');
    row.textContent = 'No recorded receipt. Borrowing or asking does not claim a completed service.';
    list.append(row);
  } else {
    for (const receipt of state.receipts) {
      const row = document.createElement('li');
      const title = document.createElement('strong');
      title.textContent = names[receipt.region] || receipt.region || 'Recorded local event';
      const detail = document.createElement('span');
      const labels = { borrow: 'Tool borrowed · still owed here', return: 'Actual tool return', help: 'Help completed', service: 'Service actually received' };
      const change = `${receipt.standing_before > 0 ? '+' : ''}${receipt.standing_before} → ${receipt.standing_after > 0 ? '+' : ''}${receipt.standing_after}`;
      detail.textContent = `${labels[receipt.kind] || 'Accepted local event'}. Standing ${change}. Paid ${receipt.time_cost} time and ${receipt.coin_cost} coins.`;
      row.dataset.kind = receipt.kind;
      row.dataset.regionReceipt = receipt.region;
      row.append(title, detail);
      list.append(row);
    }
  }
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
        if (next.accepted && next.command === 'restart') {
          // The new attempt cannot inherit intentions already queued for the previous one.
          generation++;
          busy = false;
          request = null;
        }
        render(next);
      }
      return next;
    } catch (error) {
      if (owner === generation) quarantine('The action may already have been accepted. Read the actual accounts before making another choice; this page will not retry it.');
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
    if (!response.ok) throw new Error('The accounts could not be read.');
    const next = await response.json();
    if (owner === generation) render(next);
    return next;
  } catch (error) {
    if (owner === generation) quarantine('Current accounts are unavailable. Retained facts are stale; no outcome is inferred. Read again when the host is available.');
    return null;
  } finally {
    if (owner === generation) { busy = false; request = null; controls(); }
  }
}
for (const button of document.querySelectorAll('[data-command]')) button.addEventListener('click', () => command(button.dataset.command));
$('refresh').addEventListener('click', refresh);
window.addEventListener('blur', () => quarantine('Focus changed. An action may already have reached the owner. Read the current accounts before choosing again.'));
window.addEventListener('pagehide', () => quarantine('This view is stale. Read current facts before choosing.'));
window.reputationStudy = Object.freeze({ snapshot: () => observation, command, refresh });
controls();
refresh();
