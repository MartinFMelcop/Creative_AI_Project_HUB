import { WINDOWS } from './core.js';

const FINAL_STATES = new Set(['perfect', 'good', 'ok', 'miss']);
const HOLD_FAILURES = Object.freeze({
  'missed-head': 'missedHead',
  'early-release': 'earlyRelease',
  'regrab-timeout': 'regrabTimeout',
  'unheld-at-finish': 'unheldAtFinish'
});
const EPS = 1e-9;

function milliseconds(seconds) {
  return Math.round(seconds * 10000) / 10 || 0;
}

function summarize(notes) {
  // A received head remains a timing observation even if its hold later fails.
  const heads = notes.filter(note => Number.isFinite(note.error));
  const holds = {total: 0, carried: 0, missedHead: 0, earlyRelease: 0,
    regrabTimeout: 0, unheldAtFinish: 0, unknown: 0};
  for (const note of notes) {
    if (!(Number.isFinite(note.duration) && note.duration > 0)) continue;
    holds.total++;
    if (note.state !== 'miss') holds.carried++;
    else {
      const kind = Object.hasOwn(HOLD_FAILURES, note.failureReason) ? HOLD_FAILURES[note.failureReason] : 'unknown';
      holds[kind]++;
    }
  }
  const perfectLimit = WINDOWS.perfect + EPS;
  return {
    noteCount: notes.length,
    receivedHeads: heads.length,
    missedHeads: notes.filter(note => note.state === 'miss' && !Number.isFinite(note.error)).length,
    meanHeadErrorMs: heads.length ? milliseconds(heads.reduce((sum, note) => sum + note.error, 0) / heads.length) : null,
    meanAbsoluteHeadErrorMs: heads.length ? milliseconds(heads.reduce((sum, note) => sum + Math.abs(note.error), 0) / heads.length) : null,
    early: heads.filter(note => note.error < -perfectLimit).length,
    withinPerfect: heads.filter(note => Math.abs(note.error) <= perfectLimit).length,
    late: heads.filter(note => note.error > perfectLimit).length,
    holds
  };
}

// Errors are already performance seconds, at every rehearsal tempo. Source times
// locate musical phrases; they must not scale these real-time observations.
export function reviewNotes(notes) {
  if (!Array.isArray(notes)) throw new TypeError('Review needs a finished note array.');
  for (const note of notes) {
    if (!note || !Number.isInteger(note.lane) || note.lane < 0 || note.lane > 3 || !FINAL_STATES.has(note.state)) {
      throw new TypeError('Review needs finished notes with valid lanes.');
    }
  }
  return {...summarize(notes), lanes: Array.from({length: 4}, (_, lane) =>
    ({lane, ...summarize(notes.filter(note => note.lane === lane))}))};
}
