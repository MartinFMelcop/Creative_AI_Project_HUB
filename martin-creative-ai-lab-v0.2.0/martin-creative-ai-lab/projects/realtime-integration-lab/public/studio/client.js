/* Persistent rooms use a separate namespace; the legacy lab protocol is unchanged. */
const byId = (id) => document.getElementById(id);
const notice = (text) => { byId('feedback').textContent = text; };
let identity = null, socket = null, room = null, online = false, joining = false;
let rooms = [], entries = [], decisions = [], before = null, hasMore = false, unread = 0;
let drafts = {}, joinGeneration = 0, queued = [];
let readingRequest = null;
function read(key,fallback) { try { return JSON.parse(localStorage.getItem(key)) ?? fallback; } catch { return fallback; } }
function save(key,value) { try { localStorage.setItem(key,JSON.stringify(value)); } catch { byId('storage').hidden=false; } }
function draft() { return drafts[room.id] ||= { body:'', kind:'note', attempt:null }; }
function saveDrafts() { save(`p11-room-drafts-${identity.id}`,drafts); }
async function api(url,options={}) {
  const response = await fetch(`/api/studio${url}`, { ...options, headers:{ 'Content-Type':'application/json', ...(identity ? {Authorization:`Bearer ${identity.token}`} : {}), ...options.headers } });
  const value = await response.json();
  if (!response.ok) throw new Error(value.error || 'Workspace request failed.');
  return value;
}
function request(event,payload) {
  return new Promise((resolve,reject) => {
    if (!socket?.connected) return reject(new Error('Reconnect before sending.'));
    socket.timeout(4000).emit(event,payload,(error,reply) => {
      if (error) reject(new Error('Delivery could not be confirmed.'));
      else if (!reply?.ok) { const rejected=new Error(reply?.error || 'Request rejected.');rejected.rejected=true;rejected.code=reply?.code;rejected.action=reply?.action;reject(rejected); }
      else resolve(reply);
    });
    // An uncertain attempt is retried explicitly with the same ID, never replayed offline.
    socket.sendBuffer.length=0;
  });
}
function controls() {
  const ready = !!room && online && !joining;
  byId('body').disabled = !room;
  byId('send').disabled = !ready || !!(room && draft().attempt);
  byId('retry').disabled = !ready;
  byId('export').disabled = !room;
  byId('reading-export').disabled = !room || joining || !!readingRequest;
  byId('link').disabled = !room;
  byId('older').hidden = !hasMore || entries.length >= 300;
  if(room) byId('room-hint').textContent = entries.length>=300 && hasMore
    ? 'Showing the latest 300 loaded entries. Search record to find older history.'
    : 'Discussion and decisions share one saved timeline. Load earlier entries, search the saved record or export it.';
  byId('older').disabled = joining;
  byId('send').textContent = byId('kind').value === 'decision' ? 'Record decision' : 'Send note';
  window.WorkBoard?.controls();
  window.RecordSearch?.controls();
  byId('connection').textContent = joining ? 'Opening project…' : online ? 'Connected · entries saved' : 'Offline · drafts kept';
}
function meta(message) {
  return `${message.author} · ${new Date(message.created_at).toLocaleString()}${message.kind === 'decision' ? ' · Decision' : ''}`;
}
function entryElement(message) {
  const li=document.createElement('li'); li.dataset.id=message.id; li.dataset.kind=message.kind;
  const label=document.createElement('p');label.className='entry-meta';label.textContent=meta(message);
  const body=document.createElement('p');body.className='entry-body';body.textContent=message.body;
  li.append(label,body);
  if(message.kind==='decision') {const button=document.createElement('button');button.textContent='Create action';button.className='decision-action';button.onclick=()=>window.WorkBoard?.newAction(message);li.append(button);}
  return li;
}
function drawDecisions() { byId('decisions').replaceChildren(...decisions.map(entryElement)); }
function pendingView() {
  const attempt=room && draft().attempt;
  byId('pending').hidden=!attempt;
  byId('pending-body').textContent=attempt?.body || '';
  controls();
}
function accepted(message) {
  if (!room || message.room_id!==room.id) return;
  const d=draft();
  if (d.attempt?.clientId===message.client_id && message.session_id===identity.id) {
    if (d.body===d.attempt.body && d.kind===d.attempt.kind) { d.body='';byId('body').value=''; }
    d.attempt=null;saveDrafts();pendingView();
  }
}
function receive(message) {
  if (joining) { queued.push(message);return; }
  if (!room || message.room_id!==room.id) return;
  accepted(message);
  window.RecordSearch?.arrived();
  if (entries.some(e=>e.id===message.id)) return;
  const summary=rooms.find(r=>r.id===room.id);if(summary){summary.entries++;summary.latest_id=message.id;drawRooms();}
  const list=byId('entries'), follow=list.scrollHeight-list.clientHeight-list.scrollTop<24;
  const anchor=[...list.children].find(e=>e.getBoundingClientRect().bottom>list.getBoundingClientRect().top);
  const offset=anchor?.getBoundingClientRect().top;
  entries.push(message);entries.sort((a,b)=>a.id-b.id);
  if (entries.length>300) entries.shift();
  list.replaceChildren(...entries.map(entryElement));
  if (follow) list.scrollTop=list.scrollHeight;
  else if (anchor) { const replacement=list.querySelector(`[data-id="${anchor.dataset.id}"]`); if(replacement) list.scrollTop+=replacement.getBoundingClientRect().top-offset; }
  if (!follow || !document.hasFocus()) { unread++;byId('latest').hidden=false;byId('latest').textContent=`Jump to latest (${unread})`; }
  if (message.kind==='decision') { decisions.unshift(message);decisions=decisions.slice(0,100);drawDecisions(); }
  controls();
}
function drawRooms() {
  byId('rooms').replaceChildren(...rooms.map(item=>{
    const li=document.createElement('li'),button=document.createElement('button'),count=document.createElement('small');
    button.textContent=item.name;button.setAttribute('aria-current',String(item.id===room?.id));
    count.textContent=`${item.entries} saved entries`;button.append(count);button.onclick=()=>openRoom(item.id).catch(e=>notice(e.message));li.append(button);return li;
  }));
}
async function refreshRooms() { rooms=await api('/rooms');drawRooms(); }
async function openRoom(id) {
  if (!online) throw new Error('Reconnect before changing project.');
  const generation=++joinGeneration;joining=true;readingRequest=null;window.RecordSearch?.reset();controls();
  try {
    const result=await request('join project',id);
    if (generation!==joinGeneration) return;
    room=result.room;entries=result.messages;decisions=result.decisions;before=result.before;hasMore=result.hasMore;
    location.hash=room.id;byId('room-title').textContent=room.name;
    byId('room-hint').textContent='Discussion and decisions share one saved timeline. Load earlier entries, search the saved record or export it.';
    const d=draft();byId('body').value=d.body;byId('kind').value=d.kind;
    for (const message of entries) accepted(message);
    byId('entries').replaceChildren(...entries.map(entryElement));byId('entries').scrollTop=byId('entries').scrollHeight;
    await window.WorkBoard?.load(result);
    unread=0;byId('latest').hidden=true;drawDecisions();drawRooms();pendingView();
  } finally { if(generation===joinGeneration) { joining=false;const arrivals=queued;queued=[];for(const message of arrivals)receive(message);window.WorkBoard?.flush();controls(); } }
}
async function enter(saved) {
  identity=saved;await api('/me');save('p11-room-identity',identity);
  drafts=read(`p11-room-drafts-${identity.id}`,{});
  if(!drafts||typeof drafts!=='object'||Array.isArray(drafts))drafts={};
  byId('participant').textContent=identity.name;byId('change').hidden=false;byId('welcome').hidden=true;byId('workspace').hidden=false;
  socket=io('/studio',{ auth:{ token:identity.token } });
  socket.on('project entry',receive);
  socket.on('project action',r=>window.WorkBoard?.receive(r));
  socket.on('project members',r=>window.WorkBoard?.members(r));
  socket.on('rooms changed',()=>refreshRooms().catch(e=>notice(e.message)));
  socket.on('connect',async()=>{
    online=true;controls();
    try { await refreshRooms();const id=room?.id || location.hash.slice(1);if(id) await openRoom(id); }
    catch(e) { notice(e.message); }
  });
  socket.on('disconnect',()=>{online=false;controls();});
  socket.on('connect_error',e=>{online=false;controls();notice(e.message);});
}
async function sendAttempt(attempt) {
  const target=room.id;
  try {
    const result=await request('project entry',attempt);
    if(room?.id===target) receive(result.message);
    // The broadcast may already have resolved the attempt before its acknowledgement.
    if(room?.id===target) accepted(result.message);
    notice('Entry saved.');refreshRooms().catch(()=>{});
  } catch(e) {
    if(e.rejected && drafts[target]?.attempt?.clientId===attempt.clientId) { drafts[target].attempt=null;saveDrafts(); }
    notice(e.message);
  }
  pendingView();
}
byId('identity-form').onsubmit=async e=>{e.preventDefault();try { const saved=await api('/sessions',{method:'POST',body:JSON.stringify({name:byId('name').value})});await enter(saved);notice(''); }catch(e){notice(e.message);} };
byId('change').onclick=()=>{window.RecordSearch?.reset();window.WorkBoard?.reset();socket?.disconnect();identity=null;room=null;readingRequest=null;online=false;drafts={};entries=[];decisions=[];byId('entries').replaceChildren();byId('decisions').replaceChildren();save('p11-room-identity',null);byId('workspace').hidden=true;byId('welcome').hidden=false;byId('change').hidden=true;byId('participant').textContent='';byId('name').focus();};
byId('room-form').onsubmit=async e=>{e.preventDefault();try {const created=await api('/rooms',{method:'POST',body:JSON.stringify({name:byId('room-name').value})});await refreshRooms();await openRoom(created.id);byId('room-name').value='';notice('Project created.');}catch(e){notice(e.message);} };
for (const id of ['body','kind']) byId(id).addEventListener('input',()=>{if(room){draft().body=byId('body').value;draft().kind=byId('kind').value;saveDrafts();controls();}});
byId('compose').onsubmit=async e=>{e.preventDefault();if(!room||!online||joining||draft().attempt)return;
  const body=byId('body').value.trim();if(!body)return;
  const d=draft();d.body=body;d.kind=byId('kind').value;d.attempt={roomId:room.id,clientId:crypto.randomUUID(),body,kind:d.kind};saveDrafts();pendingView();await sendAttempt(d.attempt);
};
byId('retry').onclick=()=>{if(room&&draft().attempt)sendAttempt(draft().attempt);};
byId('older').onclick=async()=>{
  if(!room||joining)return;const target=room.id,generation=joinGeneration;const list=byId('entries'),height=list.scrollHeight;byId('older').disabled=true;
  try {const result=await api(`/rooms/${target}/history?before=${before}`);if(generation!==joinGeneration||room?.id!==target)return;
    entries=[...result.messages,...entries].slice(-300);before=result.before;hasMore=result.hasMore;list.replaceChildren(...entries.map(entryElement));list.scrollTop+=list.scrollHeight-height;controls();
  }catch(e){notice(e.message);controls();}
};
byId('latest').onclick=()=>{byId('entries').scrollTop=byId('entries').scrollHeight;unread=0;byId('latest').hidden=true;byId('entries').focus();};
byId('export').onclick=async()=>{try {const value=await api(`/rooms/${room.id}/export`);const url=URL.createObjectURL(new Blob([JSON.stringify(value,null,2)],{type:'application/json'}));const a=document.createElement('a');a.href=url;a.download='project-conversation.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);notice('Complete project record exported.');}catch(e){notice(e.message);}};
byId('reading-export').onclick=async()=>{
  if(!room||joining||readingRequest)return;
  const request={roomId:room.id,person:identity.id,generation:joinGeneration};readingRequest=request;controls();
  const stillHere=()=>room?.id===request.roomId&&identity?.id===request.person&&joinGeneration===request.generation;
  try {
    const response=await fetch(`/api/studio/rooms/${request.roomId}/reading`,{headers:{Authorization:`Bearer ${identity.token}`}});
    if(!response.ok){const error=await response.json();throw new Error(error.error||'Reading copy could not be exported.');}
    const html=await response.text();if(!stillHere())return;
    const url=URL.createObjectURL(new Blob([html],{type:'text/html;charset=utf-8'})),anchor=document.createElement('a');
    anchor.href=url;anchor.download=`project-${request.roomId}-reading.html`;anchor.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
    notice('Reading copy exported with the complete saved record. Review its contents before sharing; later changes will not appear.');
  } catch(error) {if(stillHere())notice(error.message);}
  finally {if(readingRequest===request)readingRequest=null;controls();}
};
byId('link').onclick=async()=>{try {await navigator.clipboard.writeText(location.href);notice('Project link copied. Participants choose their own local identity.');}catch{notice('Copy the current browser address to share this project.');}};
addEventListener('hashchange',()=>{const id=location.hash.slice(1);if(online&&id&&id!==room?.id)openRoom(id).catch(e=>notice(e.message));});
const saved=read('p11-room-identity',null);
if(saved?.token) enter(saved).catch(()=>{identity=null;notice('Your remembered identity is unavailable. Enter a display name to continue.');});
