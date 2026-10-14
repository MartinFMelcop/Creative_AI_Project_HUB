const { readFileSync, openSync, writeFileSync, closeSync, unlinkSync, fstatSync } = require('node:fs');
const { resolve } = require('node:path');
const { renderRecord } = require('./record-export.cjs');

// Separate from SQLite recovery: convert a public JSON export to a new file.
function convertRecord(input,output) {
  const source=resolve(input),target=resolve(output);
  const fd=openSync(source,'r'); let data;
  try {
    const stat=fstatSync(fd);
    if (!stat.isFile() || stat.size>64*1024*1024) throw new Error('Use a regular JSON export no larger than 64 MiB.');
    data=JSON.parse(readFileSync(fd,'utf8'));
  } finally { closeSync(fd); }
  const html=renderRecord(data);
  // Exclusive creation also refuses existing symlinks and the input itself.
  const destination=openSync(target,'wx',0o600);
  try { writeFileSync(destination,html,'utf8'); }
  catch(error) { unlinkSync(target); throw error; }
  finally { closeSync(destination); }
  return target;
}
if (require.main===module) {
  const args=process.argv.slice(2);
  if (args.length===1 && ['--help','-h'].includes(args[0])) console.log('Usage: node rooms-record.cjs INPUT.json NEW-OUTPUT.html\nCreates an offline reading copy without modifying the source or any workspace.');
  else if (args.length!==2) { console.error('Usage: node rooms-record.cjs INPUT.json NEW-OUTPUT.html'); process.exitCode=1; }
  else try { console.log(`Reading copy created: ${convertRecord(...args)}`); }
  catch(error) { console.error(error.message); process.exitCode=1; }
}
module.exports={convertRecord};
