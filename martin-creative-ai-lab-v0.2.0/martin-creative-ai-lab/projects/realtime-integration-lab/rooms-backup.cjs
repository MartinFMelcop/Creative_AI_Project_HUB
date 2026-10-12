if (Number(process.versions.node.split('.')[0]) < 24) throw new Error('Workspace recovery requires Node 24+.');
const { DatabaseSync, backup } = require('node:sqlite');
const { createHash } = require('node:crypto');
const fs = require('node:fs');
const path = require('node:path');
const { RoomsStore } = require('./rooms-store.cjs');
const VERSION = require('./package.json').version;
const FORMAT = 'p11-workspace-backup';
const IMAGE = 'workspace.sqlite';
const MANIFEST = 'manifest.json';
const hex = /^[a-f0-9]{64}$/;
const uuid = /^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$/;
let expectedSchema;

function schema(db) {
  return db.prepare('SELECT type,name,tbl_name,sql FROM sqlite_schema ORDER BY name').all()
    .map(row => ({ ...row, sql: row.sql?.replace(/\s+/g,' ').trim() ?? null }));
}
function validateDatabase(filename) {
  const db = new DatabaseSync(filename, { readOnly:true, allowExtension:false });
  try {
    db.exec('PRAGMA query_only=ON; PRAGMA trusted_schema=OFF; PRAGMA busy_timeout=5000;');
    if (db.prepare('PRAGMA user_version').get().user_version !== 1) throw new Error('Unsupported workspace schema; use the matching Project Rooms version.');
    if (!expectedSchema) {
      const reference = new RoomsStore(':memory:');
      try { expectedSchema = schema(reference.db); } finally { reference.close(); }
    }
    if (JSON.stringify(schema(db)) !== JSON.stringify(expectedSchema)) throw new Error('Database is not the supported Project Rooms schema.');
    if (db.prepare('PRAGMA integrity_check').all().some(row => row.integrity_check !== 'ok')) throw new Error('SQLite integrity check failed.');
    if (db.prepare('PRAGMA foreign_key_check').all().length) throw new Error('Workspace contains broken authorship or project references.');
    const validText = (value,max) => typeof value === 'string' && !!value.trim() && value === value.trim() && value.length <= max;
    const validTime = value => typeof value === 'string' && Number.isFinite(Date.parse(value)) && new Date(value).toISOString() === value;
    for (const row of db.prepare('SELECT * FROM sessions').iterate()) {
      if (!uuid.test(row.id) || !hex.test(row.token_hash) || !validText(row.name,40)) throw new Error('Invalid saved participant.');
    }
    for (const row of db.prepare('SELECT * FROM rooms').iterate()) {
      if (!uuid.test(row.id) || !validText(row.name,60) || !validTime(row.created_at)) throw new Error('Invalid saved project.');
    }
    for (const row of db.prepare('SELECT * FROM entries').iterate()) {
      if (!Number.isSafeInteger(row.id) || row.id <= 0 || !/^[a-f0-9-]{36}$/.test(row.client_id) ||
          !['note','decision'].includes(row.kind) || !validText(row.body,500) || !validTime(row.created_at)) throw new Error('Invalid saved entry.');
    }
    const totals = db.prepare(`SELECT (SELECT count(*) FROM sessions) AS participants,
      (SELECT count(*) FROM rooms) AS projects, count(*) AS entries,
      coalesce(sum(kind='decision'),0) AS decisions, coalesce(max(id),0) AS latest_id FROM entries`).get();
    const projects = db.prepare(`SELECT r.id,r.name,count(e.id) AS entries,
      coalesce(sum(e.kind='decision'),0) AS decisions, max(e.created_at) AS latest_entry_at
      FROM rooms r LEFT JOIN entries e ON e.room_id=r.id GROUP BY r.id ORDER BY r.id`).all();
    if (totals.participants > 5000 || totals.projects > 100 || projects.some(row => row.entries > 10000)) throw new Error('Workspace exceeds the supported capacity.');
    const sequence = db.prepare('SELECT name,seq FROM sqlite_sequence').all();
    if (sequence.length > 1 || sequence.some(row => row.name !== 'entries' || !Number.isSafeInteger(row.seq) || row.seq < totals.latest_id || row.seq >= Number.MAX_SAFE_INTEGER) ||
        (totals.entries && !sequence.length)) throw new Error('Invalid saved entry sequence.');
    return { ...totals, rooms:projects };
  } finally { db.close(); }
}
function regularFile(filename) {
  const info = fs.lstatSync(filename);
  if (!info.isFile() || info.isSymbolicLink()) throw new Error('Expected a regular, unlinked file.');
  return info;
}
async function fingerprint(filename) {
  const hash = createHash('sha256');
  for await (const chunk of fs.createReadStream(filename)) hash.update(chunk);
  return { bytes:regularFile(filename).size, sha256:hash.digest('hex') };
}
function flush(filename) {
  const fd = fs.openSync(filename,'r');
  try { fs.fsyncSync(fd); } finally { fs.closeSync(fd); }
}
function absent(filename) {
  try { fs.lstatSync(filename); } catch (error) { if (error.code === 'ENOENT') return; throw error; }
  throw new Error(`Destination already exists: ${filename}. Choose a new path; recovery never overwrites data.`);
}

async function createBackup(dbPath,out) {
  dbPath = path.resolve(dbPath); out = path.resolve(out);
  regularFile(dbPath);
  // Reserve a new private bundle. A crash leaves an incomplete bundle that inspect refuses.
  absent(out);
  fs.mkdirSync(out,{mode:0o700});
  let source;
  try {
    source = new DatabaseSync(dbPath,{readOnly:true,allowExtension:false});
    source.exec('PRAGMA trusted_schema=OFF; PRAGMA busy_timeout=5000;');
    const image = path.join(out,IMAGE);
    // SQLite's online backup includes committed WAL pages, unlike copying the main file.
    await backup(source,image);
    source.close(); source = null;
    fs.chmodSync(image,0o600);
    const standalone = new DatabaseSync(image,{allowExtension:false});
    try { standalone.exec('PRAGMA journal_mode=DELETE;'); } finally { standalone.close(); }
    const summary = validateDatabase(image);
    const manifest = { format:FORMAT, version:1, created_at:new Date().toISOString(),
      application_version:VERSION, schema:1, database:{file:IMAGE,...await fingerprint(image)}, summary };
    flush(image);
    fs.writeFileSync(path.join(out,MANIFEST),JSON.stringify(manifest,null,2)+'\n',{flag:'wx',mode:0o600});
    flush(path.join(out,MANIFEST)); flush(out);
    return { operation:'backup', bundle:out, ...manifest };
  } catch (error) {
    fs.rmSync(out,{recursive:true,force:true});
    throw error;
  } finally { source?.close(); }
}
async function inspectBackup(from) {
  from = path.resolve(from);
  const directory = fs.lstatSync(from);
  if (!directory.isDirectory() || directory.isSymbolicLink()) throw new Error('Choose an unlinked backup directory.');
  if (fs.readdirSync(from).sort().join('|') !== [MANIFEST,IMAGE].sort().join('|')) throw new Error('Backup is incomplete or contains unexpected files.');
  const manifestFile = path.join(from,MANIFEST);
  if (regularFile(manifestFile).size > 65536) throw new Error('Backup manifest is too large.');
  let manifest;
  try { manifest = JSON.parse(fs.readFileSync(manifestFile,'utf8')); } catch { throw new Error('Invalid backup manifest JSON.'); }
  const fields = ['format','version','created_at','application_version','schema','database','summary'];
  if (!manifest || Array.isArray(manifest) || Object.keys(manifest).sort().join('|') !== fields.sort().join('|') ||
      Object.keys(manifest.database ?? {}).sort().join('|') !== 'bytes|file|sha256' ||
      typeof manifest.application_version !== 'string' || !/^\d+\.\d+\.\d+$/.test(manifest.application_version)) throw new Error('Unsupported backup manifest fields.');
  if (manifest?.format !== FORMAT || manifest.version !== 1 || manifest.schema !== 1 ||
      manifest.database?.file !== IMAGE || !hex.test(manifest.database.sha256) ||
      !Number.isSafeInteger(manifest.database.bytes) || manifest.database.bytes <= 0 ||
      typeof manifest.created_at !== 'string' || !Number.isFinite(Date.parse(manifest.created_at))) throw new Error('Unsupported or invalid backup manifest.');
  const image = path.join(from,IMAGE);
  regularFile(image);
  const actual = await fingerprint(image);
  if (actual.bytes !== manifest.database.bytes || actual.sha256 !== manifest.database.sha256) throw new Error('Backup checksum/size mismatch. No recovery was performed.');
  const summary = validateDatabase(image);
  if (JSON.stringify(summary) !== JSON.stringify(manifest.summary)) throw new Error('Backup inventory does not match the database.');
  return { operation:'inspect', bundle:from, ...manifest };
}
async function restoreBackup(from,dbPath,expectedHash) {
  const inspected = await inspectBackup(from);
  if (expectedHash !== undefined && (!hex.test(expectedHash) || expectedHash !== inspected.database.sha256)) throw new Error('Backup does not match the reviewed SHA-256.');
  dbPath = path.resolve(dbPath);
  const checkDestination = () => [dbPath,dbPath+'-wal',dbPath+'-shm',dbPath+'-journal'].forEach(absent);
  checkDestination();
  const staging = fs.mkdtempSync(path.join(path.dirname(dbPath),'.p11-restore-'));
  fs.chmodSync(staging,0o700);
  try {
    const image = path.join(staging,IMAGE);
    fs.copyFileSync(path.join(inspected.bundle,IMAGE),image,fs.constants.COPYFILE_EXCL);
    fs.chmodSync(image,0o600);
    // Check the actual staged bytes as well: never publish a changed source after inspection.
    const actual = await fingerprint(image);
    if (actual.sha256 !== inspected.database.sha256 || actual.bytes !== inspected.database.bytes) throw new Error('Backup changed during recovery.');
    const summary = validateDatabase(image);
    flush(image); checkDestination();
    // Exclusive hard-link publication is atomic and cannot replace an existing main file.
    fs.linkSync(image,dbPath); flush(path.dirname(dbPath));
    return { operation:'restore', database:dbPath, backup_sha256:actual.sha256, restored_at:new Date().toISOString(), summary };
  } finally { fs.rmSync(staging,{recursive:true,force:true}); }
}

const HELP = `Project Rooms workspace recovery (Node 24+)
  node rooms-backup.cjs backup --db /path/rooms.sqlite --out /path/new-backup
  node rooms-backup.cjs inspect --from /path/new-backup
  node rooms-backup.cjs restore --from /path/new-backup --db /path/new-rooms.sqlite [--expect-sha SHA256]

Backup may run while Project Rooms is live. Keep the entire private bundle.
Inspect its date/inventory/hash, then stop the server and restore to a NEW file.
Restart with ROOMS_DB pointing to that file. Later writes are not in the snapshot.
Browser identities/drafts require the original browser storage; it is not backed up.
No overwrite, force option, network endpoint or scheduled/off-site backup is provided.
`;
async function main(args) {
  if (!args.length || (args.length === 1 && ['--help','help'].includes(args[0]))) { console.log(HELP); return; }
  const [command,...rest] = args;
  const allowed = {backup:['--db','--out'],inspect:['--from'],restore:['--from','--db','--expect-sha']}[command];
  if (!allowed) throw new Error('Choose backup, inspect or restore. Use --help for the workflow.');
  const options = {};
  for (let i=0;i<rest.length;i+=2) {
    const key=rest[i],value=rest[i+1];
    if (!allowed.includes(key) || key in options || !value || value.startsWith('--')) throw new Error('Invalid or duplicate option. Use --help.');
    options[key]=value;
  }
  for (const key of allowed.filter(key=>key!=='--expect-sha')) if (!options[key]) throw new Error(`Missing ${key}. Use --help.`);
  const result = command === 'backup' ? await createBackup(options['--db'],options['--out']) :
    command === 'inspect' ? await inspectBackup(options['--from']) : await restoreBackup(options['--from'],options['--db'],options['--expect-sha']);
  console.log(JSON.stringify(result,null,2));
}
if (require.main === module) main(process.argv.slice(2)).catch(error=>{console.error(`Recovery failed: ${error.message}`);process.exitCode=1;});
module.exports = {createBackup,inspectBackup,restoreBackup};
