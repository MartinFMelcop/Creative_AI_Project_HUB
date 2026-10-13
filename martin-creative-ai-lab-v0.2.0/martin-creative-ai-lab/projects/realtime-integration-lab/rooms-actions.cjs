const {randomUUID}=require('node:crypto');
const UUID=/^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$/;
const STATUSES=['todo','doing','blocked','done'];
function value(text,max,required=false) {
  if(typeof text!=='string'||text.length>max||(required&&!text.trim()))throw new Error(`Use ${required?'1':'0'}–${max} characters.`);
  return text.trim();
}
function normalize(p) {
  if(!p||!UUID.test(p.roomId)||!UUID.test(p.clientId)||!['create','update'].includes(p.op))throw new Error('Invalid action attempt.');
  const command={op:p.op,roomId:p.roomId,title:value(p.title,140,true),ownerId:p.ownerId??null,status:p.status??'todo',note:value(p.note??'',500)};
  if(command.ownerId!==null&&!UUID.test(command.ownerId))throw new Error('Choose an owner from this project.');
  if(!STATUSES.includes(command.status))throw new Error('Choose a supported action status.');
  if(['blocked','done'].includes(command.status)&&!command.note)throw new Error('Describe the blocker or completed outcome.');
  if(p.op==='create') {
    command.sourceId=p.sourceId??null;
    if(command.status!=='todo'||(command.sourceId!==null&&(!Number.isSafeInteger(command.sourceId)||command.sourceId<=0)))throw new Error('New actions start in To do with an optional decision source.');
  } else {
    if(!UUID.test(p.actionId)||!Number.isSafeInteger(p.expectedRevision)||p.expectedRevision<=0)throw new Error('Invalid action revision.');
    command.actionId=p.actionId;command.expectedRevision=p.expectedRevision;
  }
  return command;
}
class Actions {
  constructor(store) {this.store=store;this.db=store.db;}
  join(roomId,session) {
    this.store.room(roomId);
    this.db.prepare('INSERT OR IGNORE INTO room_members VALUES (?,?,?)').run(roomId,session.id,new Date().toISOString());
  }
  members(roomId) {
    return this.db.prepare(`SELECT s.id,s.name FROM room_members m JOIN sessions s ON s.id=m.session_id
      WHERE room_id=? ORDER BY s.name COLLATE NOCASE,s.id`).all(roomId);
  }
  get(id,roomId) {
    const action=this.db.prepare(`SELECT a.*,s.name AS owner_name,c.name AS creator_name,e.body AS decision_body
      FROM actions a LEFT JOIN sessions s ON s.id=a.owner_id JOIN sessions c ON c.id=a.creator_id
      LEFT JOIN entries e ON e.id=a.source_id WHERE a.id=? AND a.room_id=?`).get(id,roomId);
    if(!action)throw new Error('Action not found in this project.');
    return action;
  }
  snapshot(roomId) {
    this.store.room(roomId);
    const ids=this.db.prepare('SELECT id FROM actions WHERE room_id=? ORDER BY updated_at DESC,id').all(roomId);
    return {actions:ids.map(a=>this.get(a.id,roomId)),members:this.members(roomId)};
  }
  history(id,roomId,limit=50) {
    this.get(id,roomId);
    const rows=this.db.prepare(`SELECT e.id,e.revision,e.created_at,s.name AS author,e.snapshot FROM action_events e
      JOIN sessions s ON s.id=e.session_id WHERE action_id=? ORDER BY e.id DESC LIMIT ?`).all(id,limit+1);
    return {hasMore:rows.length>limit,events:rows.slice(0,limit).reverse().map(({snapshot,...row})=>({...row,action:JSON.parse(snapshot)}))};
  }
  receipt(session,roomId,clientId) {
    this.store.room(roomId);
    if(!UUID.test(clientId))throw new Error('Invalid attempt ID.');
    const e=this.db.prepare('SELECT * FROM action_events WHERE session_id=? AND room_id=? AND client_id=?').get(session.id,roomId,clientId);
    return e?{accepted:true,action:JSON.parse(e.snapshot),clientId,sessionId:session.id,eventId:e.id,duplicate:true}:{accepted:false};
  }
  apply(session,payload) {
    const command=normalize(payload),encoded=JSON.stringify(command);
    this.db.exec('BEGIN IMMEDIATE');
    try {
      const old=this.db.prepare('SELECT * FROM action_events WHERE session_id=? AND client_id=?').get(session.id,payload.clientId);
      if(old) {
        if(old.command!==encoded)throw new Error('Attempt ID already belongs to different action content.');
        this.db.exec('COMMIT');return {action:JSON.parse(old.snapshot),eventId:old.id,clientId:payload.clientId,sessionId:session.id,duplicate:true};
      }
      this.store.room(command.roomId);
      if(!this.db.prepare('SELECT 1 FROM room_members WHERE room_id=? AND session_id=?').get(command.roomId,session.id))throw new Error('Join this project before changing actions.');
      if(command.ownerId&&!this.db.prepare('SELECT 1 FROM room_members WHERE room_id=? AND session_id=?').get(command.roomId,command.ownerId))throw new Error('Choose an owner who has joined this project.');
      if(this.db.prepare('SELECT count(*) AS n FROM action_events WHERE room_id=?').get(command.roomId).n>=10000)throw new Error('Action history limit reached. Export this project.');
      const time=new Date().toISOString();let id=command.actionId,revision;
      if(command.op==='create') {
        if(this.db.prepare('SELECT count(*) AS n FROM actions WHERE room_id=?').get(command.roomId).n>=500)throw new Error('Project action limit reached.');
        if(command.sourceId!==null&&!this.db.prepare("SELECT 1 FROM entries WHERE id=? AND room_id=? AND kind='decision'").get(command.sourceId,command.roomId))throw new Error('Link a recorded decision from this project.');
        id=randomUUID();revision=1;
        this.db.prepare('INSERT INTO actions VALUES (?,?,?,?,?,?,?,?,?,?,?)').run(id,command.roomId,command.sourceId,session.id,command.title,command.ownerId,command.status,command.note,revision,time,time);
      } else {
        const current=this.get(id,command.roomId);
        if(current.revision!==command.expectedRevision) {
          const error=new Error('This action changed. Compare the latest version before saving.');
          error.code='conflict';error.action=current;throw error;
        }
        if(current.status==='done'&&command.status!==current.status) {
          if(!['todo','doing'].includes(command.status)||!command.note||command.note===current.note)throw new Error('Reopen completed work in To do or In progress with a new reason.');
        }
        if(['title','status','note'].every(k=>current[k]===command[k])&&current.owner_id===command.ownerId)throw new Error('Make a change before saving.');
        revision=current.revision+1;
        this.db.prepare('UPDATE actions SET title=?,owner_id=?,status=?,note=?,revision=?,updated_at=? WHERE id=?').run(command.title,command.ownerId,command.status,command.note,revision,time,id);
      }
      const action=this.get(id,command.roomId);
      const event=this.db.prepare('INSERT INTO action_events(action_id,room_id,session_id,client_id,revision,created_at,command,snapshot) VALUES (?,?,?,?,?,?,?,?) RETURNING id')
        .get(id,command.roomId,session.id,payload.clientId,revision,time,encoded,JSON.stringify(action));
      this.db.exec('COMMIT');return {action,eventId:event.id,clientId:payload.clientId,sessionId:session.id,duplicate:false};
    } catch(error) {this.db.exec('ROLLBACK');throw error;}
  }
  export(roomId) {
    return this.snapshot(roomId).actions.map(action=>({...action,history:this.history(action.id,roomId,10000).events}));
  }
}
function validateActionData(db) {
  const fail=()=>{throw new Error('Invalid saved action or action history.');};
  const time=x=>typeof x==='string'&&Number.isFinite(Date.parse(x))&&new Date(x).toISOString()===x;
  const people=new Map(db.prepare('SELECT id,name FROM sessions').all().map(s=>[s.id,s.name]));
  const members=new Set();
  for(const m of db.prepare('SELECT * FROM room_members').all()) {
    if(!time(m.joined_at))fail();members.add(m.room_id+'|'+m.session_id);
  }
  const decisions=new Map(db.prepare('SELECT * FROM entries').all().map(e=>[e.id,e]));
  const actions=db.prepare('SELECT * FROM actions').all(),events=db.prepare('SELECT * FROM action_events ORDER BY id').all();
  const grouped=new Map();
  for(const e of events) {
    if(!Number.isSafeInteger(e.id)||e.id<=0||!UUID.test(e.client_id)||!time(e.created_at))fail();
    const list=grouped.get(e.action_id)||[];list.push(e);grouped.set(e.action_id,list);
  }
  for(const a of actions) {
    if(!UUID.test(a.id)||!Number.isSafeInteger(a.revision)||a.revision<1||!time(a.created_at)||!time(a.updated_at))fail();
    const linked=decisions.get(a.source_id);
    if(a.source_id!==null&&(!linked||linked.room_id!==a.room_id||linked.kind!=='decision'))fail();
    const history=grouped.get(a.id)||[];if(history.length!==a.revision)fail();
    let previous;
    for(let i=0;i<history.length;i++) {
      const e=history[i];let snapshot,command;
      try {snapshot=JSON.parse(e.snapshot);command=JSON.parse(e.command);}catch{fail();}
      if(!snapshot||!command)fail();
      try {if(JSON.stringify(normalize({...command,clientId:e.client_id}))!==e.command)fail();}catch{fail();}
      if(e.room_id!==a.room_id||e.revision!==i+1||snapshot.revision!==e.revision||snapshot.updated_at!==e.created_at||
        !members.has(a.room_id+'|'+e.session_id)||snapshot.creator_name!==people.get(a.creator_id)||
        snapshot.owner_name!==(snapshot.owner_id===null?null:people.get(snapshot.owner_id))||
        (snapshot.owner_id!==null&&!members.has(a.room_id+'|'+snapshot.owner_id))||snapshot.decision_body!==(linked?.body??null))fail();
      if(['id','room_id','source_id','creator_id','created_at'].some(k=>snapshot[k]!==a[k])||
        ['title','status','note'].some(k=>snapshot[k]!==command[k])||snapshot.owner_id!==command.ownerId||command.roomId!==a.room_id)fail();
      if(i===0) {if(command.op!=='create'||command.sourceId!==a.source_id||e.session_id!==a.creator_id||snapshot.created_at!==e.created_at)fail();}
      else {
        if(command.op!=='update'||command.actionId!==a.id||command.expectedRevision!==i)fail();
        if(previous.status==='done'&&snapshot.status!=='done'&&(!['todo','doing'].includes(snapshot.status)||!snapshot.note||snapshot.note===previous.note))fail();
        if(['title','status','note','owner_id'].every(k=>previous[k]===snapshot[k]))fail();
      }
      const fields=[...Object.keys(a),'creator_name','owner_name','decision_body'].sort();
      if(Object.keys(snapshot).sort().join('|')!==fields.join('|'))fail();
      previous=snapshot;
    }
    if(Object.keys(a).some(k=>previous[k]!==a[k]))fail();
  }
  return {actions:actions.length,action_updates:events.length,latest_action_event_id:events.at(-1)?.id??0};
}
module.exports={Actions,normalize,UUID,STATUSES,validateActionData};
