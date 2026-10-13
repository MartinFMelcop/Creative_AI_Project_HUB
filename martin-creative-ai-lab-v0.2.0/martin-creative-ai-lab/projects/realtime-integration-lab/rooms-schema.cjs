// Shared by live migrations and read-only backup schema verification.
const BASE_SQL = `
  CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY, name TEXT NOT NULL, token_hash TEXT NOT NULL UNIQUE
  );
  CREATE TABLE IF NOT EXISTS rooms (
    id TEXT PRIMARY KEY, name TEXT NOT NULL COLLATE NOCASE UNIQUE,
    created_at TEXT NOT NULL
  );
  CREATE TABLE IF NOT EXISTS entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    room_id TEXT NOT NULL REFERENCES rooms(id),
    session_id TEXT NOT NULL REFERENCES sessions(id),
    client_id TEXT NOT NULL, kind TEXT NOT NULL CHECK(kind IN ('note','decision')),
    body TEXT NOT NULL, created_at TEXT NOT NULL,
    UNIQUE(session_id,client_id)
  );
  CREATE INDEX IF NOT EXISTS entries_room ON entries(room_id,id);`;
const ACTION_SQL = `
  CREATE TABLE room_members (
    room_id TEXT NOT NULL REFERENCES rooms(id), session_id TEXT NOT NULL REFERENCES sessions(id),
    joined_at TEXT NOT NULL, PRIMARY KEY(room_id,session_id)
  );
  INSERT INTO room_members SELECT room_id,session_id,min(created_at) FROM entries GROUP BY room_id,session_id;
  CREATE TABLE actions (
    id TEXT PRIMARY KEY, room_id TEXT NOT NULL REFERENCES rooms(id),
    source_id INTEGER REFERENCES entries(id), creator_id TEXT NOT NULL REFERENCES sessions(id),
    title TEXT NOT NULL, owner_id TEXT, status TEXT NOT NULL CHECK(status IN ('todo','doing','blocked','done')),
    note TEXT NOT NULL, revision INTEGER NOT NULL CHECK(revision>0), created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
    FOREIGN KEY(room_id,owner_id) REFERENCES room_members(room_id,session_id)
  );
  CREATE INDEX actions_room ON actions(room_id,updated_at);
  CREATE TABLE action_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT, action_id TEXT NOT NULL REFERENCES actions(id),
    room_id TEXT NOT NULL REFERENCES rooms(id), session_id TEXT NOT NULL REFERENCES sessions(id),
    client_id TEXT NOT NULL, revision INTEGER NOT NULL, created_at TEXT NOT NULL,
    command TEXT NOT NULL, snapshot TEXT NOT NULL,
    UNIQUE(session_id,client_id), UNIQUE(action_id,revision)
  );
  CREATE INDEX action_events_room ON action_events(room_id,id);`;

function initialize(db,target=2) {
  const current=db.prepare('PRAGMA user_version').get().user_version;
  if(current>target)throw new Error('This database requires a newer Project Rooms version.');
  if(current===target)return;
  db.exec('BEGIN IMMEDIATE');
  try {
    if(current===0)db.exec(BASE_SQL+' PRAGMA user_version=1;');
    if(target===2)db.exec(ACTION_SQL+' PRAGMA user_version=2;');
    db.exec('COMMIT');
  } catch(error) {db.exec('ROLLBACK');throw error;}
}
module.exports={initialize};
