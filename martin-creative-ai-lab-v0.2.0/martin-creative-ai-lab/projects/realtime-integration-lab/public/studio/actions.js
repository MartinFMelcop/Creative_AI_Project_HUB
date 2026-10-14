/* Action drafts and immutable attempts share the existing per-participant room storage. */
window.WorkBoard=(()=>{
  let actions=new Map(),members=[],queued=[],latest=null;
  const names={todo:'To do',doing:'In progress',blocked:'Blocked',done:'Done'};
  const fields=['action-title','action-owner','action-status','action-note'];
  const ready=()=>!!room&&online&&!joining;
  function state() {
    const d=draft();if(!d.work||typeof d.work!=='object')d.work={fields:null,attempt:null,dirty:false};
    return d.work;
  }
  function persist() {saveDrafts();}
  function view(work) {
    window.RecordSearch?.hide();
    byId('action-panel').hidden=!work;byId('discussion').hidden=work;
    byId('actions-tab').setAttribute('aria-pressed',String(work));byId('conversation-tab').setAttribute('aria-pressed',String(!work));
  }
  function ownerOptions() {
    const selected=room?state().fields?.ownerId:null;
    const option=(id,label)=>{const o=document.createElement('option');o.value=id??'';o.textContent=label;return o;};
    const duplicates=new Set(members.filter(m=>members.filter(n=>n.name===m.name).length>1).map(m=>m.name));
    byId('action-owner').replaceChildren(option(null,'Unassigned'),...members.map(m=>option(m.id,duplicates.has(m.name)?`${m.name} (${m.id.slice(0,8)})`:m.name)));
    byId('action-owner').value=selected??'';
  }
  function controls() {
    const w=room?state():null,pending=!!w?.attempt;
    byId('actions-tab').disabled=!room;byId('new-action').disabled=!ready()||pending||!!w?.dirty;
    byId('action-save').disabled=!ready()||pending||!!latest;
    byId('action-retry').disabled=!ready();byId('action-pending').hidden=!pending;
    for(const id of fields)byId(id).disabled=pending||!room;
    byId('action-status').disabled=pending||!room||!w?.fields?.actionId;
    for(const b of byId('action-board').querySelectorAll('[data-edit]'))b.disabled=!ready()||pending||!!w?.dirty;
    byId('action-discard').disabled=pending;
    byId('action-resume').hidden=!w?.fields||!byId('action-editor').hidden;
    byId('action-use-latest').disabled=pending;byId('action-rebase').disabled=pending;
    const current=w?.fields?.actionId&&actions.get(w.fields.actionId);
    byId('action-note').required=['blocked','done'].includes(byId('action-status').value)||!!(current?.status==='done'&&byId('action-status').value!=='done');
  }
  function draw() {
    const filter=byId('action-filter').value;
    const visible=[...actions.values()].filter(a=>filter==='all'||(filter==='mine'?a.owner_id===identity?.id:a.owner_id===null));
    byId('action-count').textContent=`${actions.size} actions · ${[...actions.values()].filter(a=>a.status!=='done').length} open · ${visible.length} shown`;
    byId('action-board').replaceChildren(...Object.entries(names).map(([status,name])=>{
      const lane=document.createElement('section');lane.className='action-lane';lane.dataset.status=status;
      const h=document.createElement('h3'),items=visible.filter(a=>a.status===status);h.textContent=`${name} (${items.length})`;lane.append(h);
      for(const a of items) {
        const card=document.createElement('article');card.className='action-card';card.dataset.id=a.id;card.dataset.status=status;
        const title=document.createElement('h4');title.textContent=a.title;
        const owner=document.createElement('p');owner.textContent=a.owner_name?`Responsible: ${a.owner_name}`:'Unassigned';
        const note=document.createElement('p');note.textContent=a.note;
        const meta=document.createElement('p');meta.className='muted';meta.textContent=`Revision ${a.revision} · ${a.source_id?'Linked to decision #'+a.source_id:'Independent action'}`;
        const edit=document.createElement('button');edit.textContent='Edit action';edit.dataset.edit='true';edit.onclick=()=>editAction(a);
        const history=document.createElement('button');history.textContent='History';history.onclick=()=>showHistory(a).catch(e=>notice(e.message));
        card.append(title,owner,note,meta,edit,history);lane.append(card);
      }
      if(!items.length){const empty=document.createElement('p');empty.className='muted';empty.textContent='No actions in this view.';lane.append(empty);}
      return lane;
    }));controls();
  }
  function fill() {
    const f=state().fields;byId('action-editor').hidden=!f;if(!f)return;
    ownerOptions();byId('action-title').value=f.title;byId('action-owner').value=f.ownerId??'';
    byId('action-status').value=f.status;byId('action-note').value=f.note;
    byId('action-source').textContent=f.sourceId?`Decision #${f.sourceId}: ${f.sourceBody}`:'Independent action · add a concrete outcome to deliver.';
    byId('action-editor-title').textContent=f.actionId?`Edit action · revision ${f.expectedRevision}`:'New action';
    conflict(null);controls();
  }
  function editAction(a,reveal=true) {
    if(state().attempt)return;
    const wasHidden=byId('action-editor').hidden;
    state().fields={actionId:a.id,expectedRevision:a.revision,sourceId:a.source_id,sourceBody:a.decision_body,title:a.title,ownerId:a.owner_id,status:a.status,note:a.note};
    state().dirty=false;persist();fill();
    if(reveal){view(true);byId('action-editor').scrollIntoView({block:'nearest'});}else byId('action-editor').hidden=wasHidden;
    controls();
  }
  function newAction(source) {
    if(!ready()||state().attempt){notice('Reconnect and resolve any pending action first.');return;}
    if(state().dirty){view(true);byId('action-editor').hidden=false;controls();notice('Save or discard this action draft before starting another.');return;}
    state().fields={actionId:null,sourceId:source?.id??null,sourceBody:source?.body??'',title:'',ownerId:identity.id,status:'todo',note:''};
    state().dirty=false;persist();view(true);fill();byId('action-title').focus();
  }
  function conflict(a) {
    latest=a;byId('action-conflict').hidden=!a;
    byId('action-latest').textContent=a?`${a.title}\n${names[a.status]} · ${a.owner_name??'Unassigned'} · revision ${a.revision}\n${a.note}`:'';
    controls();
  }
  function merge(a) {
    if(a.room_id!==room?.id)return;
    const old=actions.get(a.id);if(old&&old.revision>=a.revision)return;
    actions.set(a.id,a);
    const w=state();
    if(w.fields?.actionId===a.id&&!w.attempt&&w.fields.expectedRevision!==a.revision) {
      if(w.dirty)conflict(a);else editAction(a,false);
    }
  }
  function settle(result) {
    if(!room||result.action.room_id!==room.id)return;
    merge(result.action);
    if(state().attempt?.clientId===result.clientId&&result.sessionId===identity.id) {
      state().attempt=null;editAction(actions.get(result.action.id),false);notice('Action saved; its change history is recorded.');
    }
    draw();
  }
  function receive(result) {if(result.action?.room_id===room?.id)window.RecordSearch?.arrived();if(joining){queued.push(result);return;}settle(result);}
  function flush() {const events=queued;queued=[];for(const e of events)settle(e);}
  async function load(result) {
    byId('action-history').hidden=true;
    actions=new Map((result.actions??[]).map(a=>[a.id,a]));members=result.members??[];latest=null;ownerOptions();draw();fill();
    const w=state(),current=w.fields?.actionId&&actions.get(w.fields.actionId);
    if(current&&current.revision!==w.fields.expectedRevision&&!w.attempt)conflict(current);
    if(w.attempt) {
      const target=room.id,attempt=w.attempt;
      try {const receipt=await api(`/rooms/${target}/action-attempts/${attempt.clientId}`);if(room?.id===target&&receipt.accepted)settle(receipt);}
      catch {notice('Action receipt unavailable. Keep the exact attempt and retry after reconnecting.');}
    }
  }
  async function send(attempt) {
    const target=attempt.roomId;
    try {const result=await request('project action',attempt);if(room?.id===target)settle(result);}
    catch(e) {
      if(e.rejected&&drafts[target]?.work?.attempt?.clientId===attempt.clientId) {drafts[target].work.attempt=null;persist();}
      if(room?.id===target&&e.code==='conflict') {merge(e.action);conflict(e.action);draw();}
      notice(e.message);
    }
    controls();
  }
  async function showHistory(a) {
    const target=room.id,result=await api(`/rooms/${target}/actions/${a.id}/history`);if(room?.id!==target)return;
    byId('action-history').hidden=false;byId('action-history-title').textContent=`History · ${a.title}`;
    byId('action-events').replaceChildren(...result.events.map(e=>{
      const li=document.createElement('li');li.textContent=`Revision ${e.revision} · ${e.author} · ${new Date(e.created_at).toLocaleString()}\n${e.action.title}\n${names[e.action.status]} · ${e.action.owner_name??'Unassigned'}\n${e.action.note}`;return li;
    }));byId('action-history-limit').textContent=result.hasMore?'Latest 50 changes. Export the project for the complete history.':'Complete action history.';
  }
  byId('conversation-tab').onclick=()=>view(false);byId('actions-tab').onclick=()=>view(true);
  byId('new-action').onclick=()=>newAction();byId('action-filter').onchange=draw;
  byId('action-close').onclick=()=>{byId('action-editor').hidden=true;controls();};
  byId('action-resume').onclick=()=>{byId('action-editor').hidden=false;controls();};
  byId('action-discard').onclick=()=>{if(!state().attempt){state().fields=null;state().dirty=false;persist();fill();draw();}};
  for(const id of fields)byId(id).addEventListener('input',()=>{
    if(!room||!state().fields||state().attempt)return;
    const current=state().fields.actionId&&actions.get(state().fields.actionId);
    if(id==='action-status'&&current?.status==='done'&&byId('action-status').value!=='done'&&byId('action-note').value===current.note)byId('action-note').value='';
    Object.assign(state().fields,{title:byId('action-title').value,ownerId:byId('action-owner').value||null,status:byId('action-status').value,note:byId('action-note').value});
    state().dirty=true;persist();controls();
  });
  byId('action-use-latest').onclick=()=>{if(latest)editAction(latest);};
  byId('action-rebase').onclick=()=>{
    if(!latest)return;state().fields.expectedRevision=latest.revision;persist();conflict(null);
    byId('action-editor-title').textContent=`Review draft · revision ${state().fields.expectedRevision}`;
    notice('Draft retained against the latest revision. Review and Save action to apply it.');
  };
  byId('action-editor').onsubmit=async e=>{
    e.preventDefault();if(!ready()||latest||state().attempt||!state().fields)return;
    const f=state().fields;
    state().attempt={op:f.actionId?'update':'create',roomId:room.id,clientId:crypto.randomUUID(),title:f.title,ownerId:f.ownerId,status:f.status,note:f.note,
      ...(f.actionId?{actionId:f.actionId,expectedRevision:f.expectedRevision}:{sourceId:f.sourceId})};
    persist();controls();await send(state().attempt);
  };
  byId('action-retry').onclick=()=>{if(ready()&&state().attempt)send(state().attempt);};
  function reset() {actions=new Map();members=[];queued=[];latest=null;byId('action-board').replaceChildren();byId('action-editor').hidden=true;byId('action-history').hidden=true;view(false);}
  // A remembered identity can finish joining before this deferred script arrives.
  if(room) {
    const initial=room.id;
    api(`/rooms/${initial}/actions`).then(result=>{if(room?.id===initial)return load(result);}).then(controls).catch(e=>notice(e.message));
  }
  return {load,receive,flush,controls,newAction,reset,openCurrent(a){merge(a);byId('action-filter').value='all';draw();view(true);const card=[...byId('action-board').querySelectorAll('.action-card')].find(c=>c.dataset.id===a.id);if(card){card.tabIndex=-1;card.focus();card.scrollIntoView({block:'nearest'});}},members(result){if(room?.id===result.roomId){members=result.members;ownerOptions();}}};
})();
