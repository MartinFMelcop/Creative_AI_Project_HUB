if (Number(process.versions.node.split('.')[0]) < 24) throw new Error('Project Rooms and its full test suite require Node 24+. The legacy exercise supports Node 22+.');
const { DatabaseSync } = require('node:sqlite');
const { randomUUID, randomBytes, createHash } = require('node:crypto');
const { mkdirSync } = require('node:fs');
const { dirname } = require('node:path');
const {initialize}=require('./rooms-schema.cjs');
const {Actions}=require('./rooms-actions.cjs');

const digest = (token) => createHash('sha256').update(token).digest('hex');
function text(value, max, label) {
  if (typeof value !== 'string' || !value.trim() || value.length > max) {
    throw new Error(`${label} must contain 1–${max} characters.`);
  }
  return value.trim();
}

class RoomsStore {
  constructor(filename) {
    if (filename !== ':memory:') mkdirSync(dirname(filename), { recursive: true });
    this.db = new DatabaseSync(filename);
    try {
      if(this.db.prepare('PRAGMA user_version').get().user_version>2)throw new Error('This database requires a newer Project Rooms version.');
      this.db.exec('PRAGMA foreign_keys=ON; PRAGMA journal_mode=WAL; PRAGMA busy_timeout=3000;');
      initialize(this.db);this.work=new Actions(this);
    } catch(error) {this.db.close();throw error;}
  }
  session(name) {
    name = text(name, 40, 'Display name');
    if (this.db.prepare('SELECT count(*) AS n FROM sessions').get().n >= 5000) throw new Error('Participant limit reached.');
    const token = randomBytes(32).toString('hex');
    const id = randomUUID();
    this.db.prepare('INSERT INTO sessions VALUES (?,?,?)').run(id, name, digest(token));
    return { id, name, token };
  }
  authenticate(token) {
    if (typeof token !== 'string' || !/^[a-f0-9]{64}$/.test(token)) return null;
    return this.db.prepare('SELECT id,name FROM sessions WHERE token_hash=?').get(digest(token)) || null;
  }
  rooms() {
    return this.db.prepare(`SELECT r.id,r.name,r.created_at,
      count(e.id) AS entries, coalesce(max(e.id),0) AS latest_id
      FROM rooms r LEFT JOIN entries e ON e.room_id=r.id
      GROUP BY r.id ORDER BY r.created_at,r.id`).all();
  }
  createRoom(name) {
    name = text(name, 60, 'Project name');
    if (this.db.prepare('SELECT count(*) AS n FROM rooms').get().n >= 100) throw new Error('Project limit reached.');
    if (this.db.prepare('SELECT id FROM rooms WHERE name=? COLLATE NOCASE').get(name)) throw new Error('That project already exists.');
    const room = { id: randomUUID(), name, created_at: new Date().toISOString() };
    this.db.prepare('INSERT INTO rooms VALUES (?,?,?)').run(room.id,room.name,room.created_at);
    return room;
  }
  room(id) {
    if (typeof id !== 'string') throw new Error('Choose a project.');
    const row = this.db.prepare('SELECT * FROM rooms WHERE id=?').get(id);
    if (!row) throw new Error('Project not found.');
    return row;
  }
  history(roomId, before) {
    this.room(roomId);
    if (before !== undefined && (!Number.isSafeInteger(before) || before <= 0)) throw new Error('Invalid history cursor.');
    const rows = this.db.prepare(`SELECT e.*,s.name AS author FROM entries e
      JOIN sessions s ON s.id=e.session_id WHERE room_id=? AND e.id<? ORDER BY e.id DESC LIMIT 51`)
      .all(roomId,before ?? Number.MAX_SAFE_INTEGER);
    const hasMore = rows.length > 50;
    const messages = rows.slice(0,50).reverse();
    return { messages, hasMore, before: messages[0]?.id ?? null };
  }
  decisions(roomId) {
    this.room(roomId);
    return this.db.prepare(`SELECT e.*,s.name AS author FROM entries e
      JOIN sessions s ON s.id=e.session_id WHERE room_id=? AND kind='decision'
      ORDER BY e.id DESC LIMIT 100`).all(roomId);
  }
  append(session, payload) {
    if (!payload || typeof payload !== 'object') throw new Error('Invalid entry.');
    const { roomId, clientId, kind } = payload;
    this.room(roomId);
    if (typeof clientId !== 'string' || !/^[a-f0-9-]{36}$/.test(clientId)) throw new Error('Invalid attempt ID.');
    if (!['note','decision'].includes(kind)) throw new Error('Choose note or decision.');
    const body = text(payload.body,500,'Entry');
    const old = this.db.prepare('SELECT * FROM entries WHERE session_id=? AND client_id=?').get(session.id,clientId);
    if (old) {
      if (old.room_id !== roomId || old.body !== body || old.kind !== kind) throw new Error('Attempt ID already belongs to different content.');
      return { message: { ...old, author: session.name }, inserted: false };
    }
    if (this.db.prepare('SELECT count(*) AS n FROM entries WHERE room_id=?').get(roomId).n >= 10000) throw new Error('Project entry limit reached. Export this project before continuing elsewhere.');
    // A single SQLite INSERT commits before any broadcast or acknowledgement.
    const row = this.db.prepare('INSERT INTO entries(room_id,session_id,client_id,kind,body,created_at) VALUES (?,?,?,?,?,?) RETURNING *')
      .get(roomId,session.id,clientId,kind,body,new Date().toISOString());
    return { message: { ...row, author: session.name }, inserted: true };
  }
  export(roomId) {
    const room = this.room(roomId);
    const entries = this.db.prepare(`SELECT e.id,e.kind,e.body,e.created_at,s.name AS author
      FROM entries e JOIN sessions s ON s.id=e.session_id WHERE room_id=? ORDER BY e.id`).all(roomId);
    return { schema:1, exported_at:new Date().toISOString(), project:room, entries, actions:this.work.export(roomId) };
  }
  close() { this.db.close(); }
}
module.exports = { RoomsStore };
