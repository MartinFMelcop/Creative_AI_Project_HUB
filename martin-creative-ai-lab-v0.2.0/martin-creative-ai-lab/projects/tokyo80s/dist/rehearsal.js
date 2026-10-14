// Rehearsal uses performance seconds, so judgment windows and input offset keep
// their real-time meaning at every playback rate. Source score/media stay intact.
export const RATES = Object.freeze([.75, .9, 1]);
export function backingFor(track, session) {
  const rate = session.rate;
  const url = rate === 1 ? track.audio : track.rehearsalAudio?.[String(rate)];
  if (!url) throw new TypeError('The original-pitch backing for this speed is unavailable.');
  return {url, offset: session.cueStart / rate, duration: (session.audioEnd - session.cueStart) / rate,
    bufferDuration: track.duration / rate, playbackRate: 1, tempoRate: rate, pitch: 'original'};
}
export function phrases(track) {
  const bar = 240 / track.bpm;
  const result = [];
  for (let start = track.leadIn, index = 0; start < track.musicEnd - 1e-8; start += bar * 4, index++) {
    const section = [...track.sections].reverse().find(s => s.time <= start + 1e-8);
    result.push({id: String(index), start, end: Math.min(track.musicEnd, start + bar * 4),
      label: `Bars ${index * 4 + 1}–${Math.min(32, index * 4 + 4)} · ${section.name}`});
  }
  return result;
}
export function makeSession(track, chart, phraseId = 'full', rate = 1) {
  if (!track.charts[chart]) throw new TypeError('Unknown chart.');
  if (phraseId === 'full') return {mode: 'full', rate: 1, cueStart: 0, headStart: track.leadIn,
    duration: track.duration, audioEnd: track.duration, notes: track.charts[chart]};
  if (!RATES.includes(rate)) throw new TypeError('Unsupported rehearsal rate.');
  const phrase = phrases(track).find(p => p.id === phraseId);
  if (!phrase) throw new TypeError('Unknown musical phrase.');
  const source = track.charts[chart].filter(n => n.time >= phrase.start - 1e-8 && n.time < phrase.end - 1e-8);
  if (!source.length) throw new TypeError('The phrase has no notes.');
  const cueStart = Math.max(0, phrase.start - 240 / track.bpm);
  // Keep tails that cross the four-bar boundary; never truncate or duplicate a head.
  const audioEnd = Math.min(track.duration, Math.max(phrase.end, ...source.map(n => n.time + (n.duration || 0))) + .3 * rate);
  return {mode: 'rehearsal', phrase, rate, cueStart, audioEnd,
    headStart: (phrase.start - cueStart) / rate, duration: (audioEnd - cueStart) / rate,
    notes: source.map(n => ({...n, sourceTime: n.time, sourceDuration: n.duration || 0,
      time: (n.time - cueStart) / rate, ...(n.duration ? {duration: n.duration / rate} : {})}))};
}
export function phraseResults(track, notes) {
  return phrases(track).map(phrase => {
    const group = notes.filter(n => (n.sourceTime ?? n.time) >= phrase.start - 1e-8 && (n.sourceTime ?? n.time) < phrase.end - 1e-8);
    const counts = {perfect: 0, good: 0, ok: 0, miss: 0};
    for (const n of group) if (n.state in counts) counts[n.state]++;
    const accuracy = group.length ? 100 * (counts.perfect + .7 * counts.good + .4 * counts.ok) / group.length : null;
    return {...phrase, notes: group.length, counts, accuracy: accuracy === null ? null : Math.round(accuracy * 100) / 100,
      lostHolds: group.filter(n => n.duration && n.state === 'miss').length};
  }).filter(p => p.notes);
}
