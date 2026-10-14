// Search immutable records directly; no derived index or backup schema migration.
const PAGE_SIZE = 20;
const KINDS = ['all', 'note', 'decision', 'action'];
const fold = text => text.normalize('NFKD').replace(/\p{M}/gu, '').toLowerCase();
const entryColumns = 'e.id,e.kind,e.body,e.created_at,s.name AS author';

class RecordSearch {
  constructor(store) {
    this.store = store;
    this.db = store.db;
    this.db.function('record_contains', { deterministic: true }, (body, query) => {
      const haystack = fold(body);
      return Number(query.split(' ').every(term => haystack.includes(term)));
    });
  }

  search(roomId, { q, kind = 'all', cursor } = {}) {
    this.store.room(roomId);
    if (typeof q !== 'string' || q.length > 160 || !KINDS.includes(kind)) throw new Error('Use 1–160 characters and a supported record type.');
    const query = fold(q.trim()).split(/\s+/u).filter(Boolean).join(' ');
    if (!query || query.split(' ').length > 8) throw new Error('Search for 1–8 literal words.');
    const ceilings = this.db.prepare(`SELECT
      (SELECT coalesce(max(id),0) FROM entries WHERE room_id=?) AS entryMax,
      (SELECT coalesce(max(id),0) FROM action_events WHERE room_id=?) AS eventMax`).get(roomId, roomId);
    let page = { roomId, query, kind, ...ceilings, offset: 0 };
    if (cursor !== undefined) {
      try {
        if (typeof cursor !== 'string' || cursor.length > 8192) throw new Error();
        const decoded = JSON.parse(Buffer.from(cursor, 'base64url').toString());
        if (Object.keys(decoded).sort().join() !== Object.keys(page).sort().join() ||
          decoded.roomId !== roomId || decoded.query !== query || decoded.kind !== kind ||
          !['entryMax', 'eventMax', 'offset'].every(k => Number.isSafeInteger(decoded[k]) && decoded[k] >= 0) ||
          decoded.entryMax > ceilings.entryMax || decoded.eventMax > ceilings.eventMax ||
          decoded.offset > 20000 || decoded.offset % PAGE_SIZE !== 0) throw new Error();
        page = decoded;
      } catch { throw new Error('Invalid search cursor. Start a new search.'); }
    }
    // Bound both indexed room streams before literal Unicode matching. User text
    // never becomes SQL, a regular expression or SQLite MATCH syntax.
    const selection = `WITH records AS (
      SELECT e.id, e.kind, e.body, '' AS title, e.created_at, s.name AS author,
        NULL AS action_id, NULL AS revision, NULL AS status, NULL AS owner_name,
        0 AS stream FROM entries e JOIN sessions s ON s.id=e.session_id
        WHERE e.room_id=? AND e.id<=? AND (?='all' OR e.kind=?)
      UNION ALL
      SELECT e.id, 'action', json_extract(e.snapshot,'$.note'),
        json_extract(e.snapshot,'$.title'), e.created_at, s.name,
        e.action_id, e.revision, json_extract(e.snapshot,'$.status'),
        json_extract(e.snapshot,'$.owner_name'), 1
        FROM action_events e JOIN sessions s ON s.id=e.session_id
        WHERE e.room_id=? AND e.id<=? AND ? IN ('all','action')
    ) SELECT * FROM records WHERE record_contains(title || ' ' || body, ?)`;
    const params = [roomId, page.entryMax, kind, kind, roomId, page.eventMax, kind, query];
    const total = this.db.prepare(`SELECT count(*) AS n FROM (${selection})`).get(...params).n;
    const rows = this.db.prepare(`${selection} ORDER BY created_at DESC,stream DESC,id DESC LIMIT ? OFFSET ?`)
      .all(...params, PAGE_SIZE + 1, page.offset);
    return {
      results: rows.slice(0, PAGE_SIZE).map(({ stream, ...row }) => row), total,
      offset: page.offset, pageSize: PAGE_SIZE,
      cursor: Buffer.from(JSON.stringify(page)).toString('base64url'),
      next: rows.length > PAGE_SIZE ? Buffer.from(JSON.stringify({ ...page, offset: page.offset + PAGE_SIZE })).toString('base64url') : null,
      snapshot: { entryMax: page.entryMax, eventMax: page.eventMax },
      stale: page.entryMax < ceilings.entryMax || page.eventMax < ceilings.eventMax
    };
  }

  context(roomId, kind, id) {
    this.store.room(roomId);
    if (!['entry', 'action'].includes(kind) || !Number.isSafeInteger(id) || id <= 0) throw new Error('Choose a saved record.');
    if (kind === 'entry') {
      const entry = this.db.prepare(`SELECT ${entryColumns} FROM entries e JOIN sessions s ON s.id=e.session_id
        WHERE e.room_id=? AND e.id=?`).get(roomId, id);
      if (!entry) throw new Error('Entry not found in this project.');
      const neighbors = direction => this.db.prepare(`SELECT ${entryColumns} FROM entries e JOIN sessions s ON s.id=e.session_id
        WHERE e.room_id=? AND e.id${direction === 'before' ? '<' : '>'}? ORDER BY e.id ${direction === 'before' ? 'DESC' : 'ASC'} LIMIT 2`).all(roomId, id);
      const actions = this.db.prepare('SELECT id FROM actions WHERE room_id=? AND source_id=? ORDER BY created_at,id')
        .all(roomId, id).map(a => this.store.work.get(a.id, roomId));
      return { kind, selectedId: id, entries: [...neighbors('before').reverse(), entry, ...neighbors('after')], actions };
    }
    const event = this.db.prepare('SELECT * FROM action_events WHERE room_id=? AND id=?').get(roomId, id);
    if (!event) throw new Error('Action revision not found in this project.');
    const action = this.store.work.get(event.action_id, roomId);
    const events = this.db.prepare(`SELECT e.id,e.revision,e.created_at,s.name AS author,e.snapshot
      FROM action_events e JOIN sessions s ON s.id=e.session_id
      WHERE e.room_id=? AND e.action_id=? AND e.revision BETWEEN ? AND ? ORDER BY e.revision`)
      .all(roomId, action.id, event.revision - 2, event.revision + 2)
      .map(({ snapshot, ...row }) => ({ ...row, action: JSON.parse(snapshot) }));
    const decision = action.source_id === null ? null : this.db.prepare(`SELECT ${entryColumns}
      FROM entries e JOIN sessions s ON s.id=e.session_id WHERE e.room_id=? AND e.id=?`).get(roomId, action.source_id);
    return { kind, selectedId: id, events, decision, actions: [action] };
  }
}
module.exports = { RecordSearch };
