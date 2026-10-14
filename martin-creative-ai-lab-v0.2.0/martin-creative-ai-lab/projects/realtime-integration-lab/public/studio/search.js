/* Read-only snapshots and context stay separate from timeline/action drafts. */
window.RecordSearch = (() => {
  let active = null, back = [], next = null, cursor, busy = false, epoch = 0, contextEpoch = 0;
  let arrivals = 0;
  const names = { todo: 'To do', doing: 'In progress', blocked: 'Blocked', done: 'Done' };
  const paragraph = (text, className = '') => { const p = document.createElement('p'); p.textContent = text; p.className = className; return p; };
  function controls() {
    byId('search-tab').disabled = !room || joining;
    for (const id of ['search-query', 'search-kind', 'search-submit']) byId(id).disabled = !room || joining || busy;
    byId('search-next').disabled = !next || busy || joining;
    byId('search-prev').disabled = !back.length || busy || joining;
    byId('search-refresh').disabled = busy || joining;
    for (const b of byId('search-results').querySelectorAll('button')) b.disabled = busy || joining;
  }
  function hide() { byId('search-panel').hidden = true; byId('search-tab').setAttribute('aria-pressed', 'false'); }
  function open() {
    if (!room || joining) return;
    byId('discussion').hidden = true; byId('action-panel').hidden = true; byId('search-panel').hidden = false;
    for (const id of ['conversation-tab', 'actions-tab']) byId(id).setAttribute('aria-pressed', 'false');
    byId('search-tab').setAttribute('aria-pressed', 'true'); byId('search-query').focus();
  }
  function reset() {
    epoch++; contextEpoch++; busy = false; active = null; back = []; next = null; cursor = undefined; arrivals = 0;
    byId('search-results').replaceChildren(); byId('search-context-body').replaceChildren();
    byId('search-context').hidden = true; byId('search-stale').hidden = true;
    byId('search-query').value = ''; byId('search-kind').value = 'all';
    byId('search-status').textContent = 'Start a search to find records beyond the loaded timeline.';
    if (!byId('search-panel').hidden) { byId('discussion').hidden = false; byId('conversation-tab').setAttribute('aria-pressed', 'true'); }
    hide(); controls();
  }
  function revisionElement(e) {
    const a = e.action, article = document.createElement('article');
    article.append(paragraph(`Revision ${e.revision} · ${e.author} · ${new Date(e.created_at).toLocaleString()}`, 'entry-meta'),
      paragraph(a.title, 'record-title'), paragraph(`${names[a.status]} · ${a.owner_name ?? 'Unassigned'}`, 'muted'), paragraph(a.note, 'entry-body'));
    return article;
  }
  async function showContext(hit, origin) {
    const target = room?.id, generation = joinGeneration, ticket = ++contextEpoch, searchEpoch = epoch;
    try {
      const value = await api(`/rooms/${target}/context/${hit.kind === 'action' ? 'action' : 'entry'}/${hit.id}`);
      if (target !== room?.id || generation !== joinGeneration || ticket !== contextEpoch || searchEpoch !== epoch) return;
      const body = byId('search-context-body'); body.replaceChildren();
      if (value.kind === 'entry') for (const e of value.entries) {
        const element = entryElement(e); element.dataset.selected = String(e.id === value.selectedId);
        if (e.id === value.selectedId) element.prepend(paragraph('Matched record', 'record-title')); body.append(element);
      }
      else {
        if (value.decision) { body.append(paragraph('Original decision', 'record-title'), entryElement(value.decision)); }
        for (const e of value.events) {
          const element = revisionElement(e); element.dataset.selected = String(e.id === value.selectedId);
          if (e.id === value.selectedId) element.prepend(paragraph('Matched revision', 'record-title')); body.append(element);
        }
      }
      if (value.actions.length) body.append(paragraph('Linked work · current when opened', 'record-title'));
      for (const a of value.actions) {
        const card = document.createElement('article'); card.className = 'context-action';
        const button = document.createElement('button'); button.textContent = 'Open current action';
        button.onclick = () => window.WorkBoard?.openCurrent(a);
        card.append(paragraph(a.title, 'record-title'), paragraph(`${names[a.status]} · ${a.owner_name ?? 'Unassigned'} · revision ${a.revision}`, 'muted'), paragraph(a.note, 'entry-body'), button); body.append(card);
      }
      byId('search-context-title').textContent = value.kind === 'entry' ? `Saved context · entry #${hit.id}` : `Saved context · action revision ${hit.revision}`;
      byId('search-context-back').onclick = () => { origin.focus(); origin.scrollIntoView({ block: 'center' }); };
      byId('search-context').hidden = false; byId('search-context-title').focus();
    } catch (e) { if (target === room?.id && ticket === contextEpoch && searchEpoch === epoch) notice(e.message); }
  }
  async function run(query, pageCursor, previous) {
    if (!room || joining) return;
    const target = room.id, generation = joinGeneration, ticket = ++epoch, observedArrivals = arrivals, wasStale = !byId('search-stale').hidden; contextEpoch++;
    busy = true; controls(); byId('search-status').textContent = 'Searching the saved record…';
    try {
      const params = new URLSearchParams(query); if (pageCursor !== undefined) params.set('cursor', pageCursor);
      const value = await api(`/rooms/${target}/search?${params}`);
      if (target !== room?.id || generation !== joinGeneration || ticket !== epoch) return;
      active = query; cursor = value.cursor; back = previous; next = value.next;
      byId('search-context').hidden = true; byId('search-context-body').replaceChildren();
      byId('search-stale').hidden = !value.stale && observedArrivals === arrivals && (pageCursor === undefined || !wasStale);
      byId('search-results').replaceChildren(...value.results.map(hit => {
        const li = document.createElement('li'); li.dataset.kind = hit.kind; li.dataset.id = hit.id;
        li.append(paragraph(`${hit.kind === 'action' ? `Action revision ${hit.revision} · ${names[hit.status]}` : hit.kind === 'decision' ? 'Decision' : 'Discussion note'} · ${hit.author} · ${new Date(hit.created_at).toLocaleString()}`, 'entry-meta'));
        if (hit.title) li.append(paragraph(hit.title, 'record-title'));
        li.append(paragraph(hit.body, 'entry-body'));
        const button = document.createElement('button'); button.textContent = 'Open saved context'; button.onclick = () => showContext(hit, button); li.append(button); return li;
      }));
      byId('search-status').textContent = value.total
        ? `${value.offset + 1}–${value.offset + value.results.length} of ${value.total} matches for “${query.q}”. Action matches describe saved revisions.`
        : `No matches for “${query.q}” in this project.`;
    } catch (e) { if (target === room?.id && ticket === epoch) byId('search-status').textContent = e.message; }
    finally { if (ticket === epoch) { busy = false; controls(); } }
  }
  byId('search-tab').onclick = open;
  byId('search-form').onsubmit = e => { e.preventDefault(); run({ q: byId('search-query').value, kind: byId('search-kind').value }, undefined, []); };
  byId('search-next').onclick = () => { if (next && active && !busy) run(active, next, [...back, cursor]); };
  byId('search-prev').onclick = () => { if (back.length && active && !busy) run(active, back.at(-1), back.slice(0, -1)); };
  byId('search-refresh').onclick = () => { if (active && !busy) run(active, undefined, []); };
  controls();
  return { controls, hide, reset, arrived() { arrivals++; if (active) byId('search-stale').hidden = false; } };
})();
