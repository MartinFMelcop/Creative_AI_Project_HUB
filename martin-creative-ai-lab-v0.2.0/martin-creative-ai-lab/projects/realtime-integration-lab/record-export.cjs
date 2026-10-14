const { createHash } = require('node:crypto');
const { readFileSync } = require('node:fs');
const { join } = require('node:path');
const { UUID, STATUSES } = require('./rooms-actions.cjs');

const ACTION_FIELDS = ['id','room_id','source_id','creator_id','title','owner_id','status','note','revision','created_at','updated_at','owner_name','creator_name','decision_body'];
const fail = message => { throw new Error(`Invalid project record: ${message}.`); };
function shape(value, fields, label) {
  if (!value || typeof value !== 'object' || Array.isArray(value) ||
      Object.keys(value).length !== fields.length || fields.some(key => !Object.hasOwn(value,key))) fail(label);
}
function text(value, max, required, label) {
  if (typeof value !== 'string' || value.length > max || (required && !value.trim())) fail(label);
}
const positive = value => Number.isSafeInteger(value) && value > 0;
const uuid = value => typeof value === 'string' && UUID.test(value);
const time = value => typeof value === 'string' && Number.isFinite(Date.parse(value)) && new Date(value).toISOString() === value;

// Validate the existing public JSON export, not a workspace backup or live identity.
// Missing actions means an earlier export, never evidence that no work existed.
function validateRecord(record) {
  shape(record, ['schema','exported_at','project','entries',...(Object.hasOwn(record || {},'actions') ? ['actions'] : [])], 'export fields');
  if (record.schema !== 1 || !time(record.exported_at)) fail('schema or export time');
  shape(record.project, ['id','name','created_at'], 'project fields');
  if (!uuid(record.project.id) || !time(record.project.created_at)) fail('project identity or time');
  text(record.project.name,60,true,'project name');
  if (!Array.isArray(record.entries) || record.entries.length > 10000) fail('entries capacity');
  const entries = new Map(); let previousId = 0;
  for (const entry of record.entries) {
    shape(entry,['id','kind','body','created_at','author'],'entry fields');
    if (!positive(entry.id) || entry.id <= previousId || !['note','decision'].includes(entry.kind) || !time(entry.created_at)) fail('entry identity, kind, order or time');
    text(entry.body,500,true,'entry body'); text(entry.author,40,true,'entry author');
    entries.set(entry.id,entry); previousId=entry.id;
  }
  if (!Object.hasOwn(record,'actions')) return record;
  if (!Array.isArray(record.actions) || record.actions.length > 500) fail('actions capacity');
  const actionIds=new Set(),eventIds=new Set(),labels=new Map(); let eventCount=0;
  function label(id,name) {
    if (labels.has(id) && labels.get(id)!==name) fail('inconsistent participant label');
    labels.set(id,name);
  }
  function action(value,fields) {
    shape(value,fields,'action fields');
    if (!uuid(value.id) || value.room_id!==record.project.id || !uuid(value.creator_id) ||
        !positive(value.revision) || !time(value.created_at) || !time(value.updated_at) || !STATUSES.includes(value.status)) fail('action identity, revision, status or time');
    text(value.title,140,true,'action title'); text(value.note,500,['blocked','done'].includes(value.status),'action note');
    text(value.creator_name,40,true,'creator name'); label(value.creator_id,value.creator_name);
    if (value.owner_id===null) { if (value.owner_name!==null) fail('unassigned owner'); }
    else { if (!uuid(value.owner_id)) fail('owner identity'); text(value.owner_name,40,true,'owner name'); label(value.owner_id,value.owner_name); }
    const source=entries.get(value.source_id);
    if (value.source_id===null) { if (value.decision_body!==null) fail('unlinked decision'); }
    else if (!positive(value.source_id) || source?.kind!=='decision' || source.body!==value.decision_body) fail('decision source');
  }
  for (const current of record.actions) {
    action(current,[...ACTION_FIELDS,'history']);
    if (actionIds.has(current.id)) fail('duplicate action'); actionIds.add(current.id);
    if (!Array.isArray(current.history) || current.history.length!==current.revision || (eventCount+=current.history.length)>10000) fail('complete history or capacity');
    let lastId=0,previous;
    for (const [index,event] of current.history.entries()) {
      shape(event,['id','revision','created_at','author','action'],'event fields');
      action(event.action,ACTION_FIELDS); text(event.author,40,true,'revision author');
      if (!positive(event.id) || event.id<=lastId || eventIds.has(event.id) || event.revision!==index+1 ||
          event.action.revision!==event.revision || event.created_at!==event.action.updated_at) fail('revision identity, order or time');
      if (['id','room_id','source_id','creator_id','created_at'].some(key=>event.action[key]!==current[key])) fail('changed immutable action');
      if (!previous && (event.action.status!=='todo' || event.created_at!==current.created_at)) fail('initial revision');
      if (previous && ['title','owner_id','status','note'].every(key=>previous[key]===event.action[key])) fail('unchanged revision');
      if (previous?.status==='done' && event.action.status!=='done' &&
          (!['todo','doing'].includes(event.action.status) || !event.action.note || previous.note===event.action.note)) fail('reopening reason');
      previous=event.action; lastId=event.id; eventIds.add(event.id);
    }
    if (ACTION_FIELDS.some(key=>current[key]!==previous?.[key])) fail('current action differs from last revision');
  }
  return record;
}

function renderRecord(record) {
  validateRecord(record);
  const serialized=JSON.stringify(record);
  const fingerprint=createHash('sha256').update(serialized).digest('hex');
  const css=readFileSync(join(__dirname,'record-view.css'),'utf8');
  const script=readFileSync(join(__dirname,'record-view.js'),'utf8');
  const hash=value=>createHash('sha256').update(value).digest('base64');
  const policy=`default-src 'none'; script-src 'sha256-${hash(script)}'; style-src 'sha256-${hash(css)}'; base-uri 'none'; form-action 'none'`;
  // Escaping '<' prevents data containing </script> from leaving the inert block.
  const payload=serialized.replace(/</g,'\\u003c');
  return `<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="${policy}">
<title>Project Rooms · Reading copy</title><style>${css}</style></head><body>
<header><p class="eyebrow">Creative AI Lab / Project Rooms</p><h1 id="project-name">Project record</h1>
<p id="snapshot-time"></p><p class="scope">Immutable reading copy. Names are chosen display labels. “Done” records a participant's outcome; it does not independently verify delivery.</p>
<p id="summary"></p><button id="download-json" type="button">Save embedded JSON record</button></header>
<noscript><p>This interactive reading copy requires JavaScript. Ask the sender for the companion JSON export if scripts are unavailable.</p></noscript>
<main>
<section aria-labelledby="work-heading"><h2 id="work-heading">Work at export</h2><p id="work-help">Filter current actions, then open their decision source and complete revision history.</p>
<div class="filters"><label>Status<select id="work-status"><option value="all">All statuses</option><option value="todo">To do</option><option value="doing">In progress</option><option value="blocked">Blocked</option><option value="done">Done</option></select></label>
<label>Owner label<select id="work-owner"><option value="all">All labels</option><option value="null">Unassigned</option></select></label></div>
<p id="work-count" role="status"></p><ol id="work-list" aria-label="Work at export"></ol>
<nav aria-label="Work pages"><button id="work-prev" type="button">Previous actions</button><button id="work-next" type="button">Next actions</button></nav></section>
<section aria-labelledby="record-heading"><h2 id="record-heading">Complete saved record</h2>
<p id="search-help">Search discussion, decisions and every action revision. All words must match; case and accents are ignored. Punctuation is literal. Leave empty to browse.</p>
<form id="search-form"><label for="query">Words to find</label><input id="query" type="search" maxlength="160" aria-describedby="search-help" placeholder="e.g. valve replacement">
<div class="filters"><label>Record type<select id="record-kind"><option value="all">All records</option><option value="note">Discussion notes</option><option value="decision">Decisions</option><option value="action">Action revisions</option></select></label><button type="submit">Find records</button></div></form>
<p id="result-count" role="status"></p><ol id="results" aria-label="Saved records"></ol>
<nav aria-label="Record pages"><button id="result-prev" type="button">Previous records</button><button id="result-next" type="button">Next records</button></nav></section>
<section id="detail" hidden aria-labelledby="detail-heading"><h2 id="detail-heading" tabindex="-1">Saved context</h2><button id="back" type="button">Back to opened record</button><div id="detail-body"></div></section>
</main><footer><p>This file contains the entire exported project, including earlier text and chosen names. Review its contents before sharing. It cannot update or restore a workspace.</p>
<details><summary>Source integrity identifier</summary><p>SHA-256 of the embedded compact JSON; this identifies the source bytes, not their author or authenticity.</p><code>${fingerprint}</code></details></footer>
<script id="record-data" type="application/json">${payload}</script><script>${script}</script></body></html>\n`;
}
module.exports={validateRecord,renderRecord};
