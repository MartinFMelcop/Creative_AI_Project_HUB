// Timing and scoring use song seconds. Rendering and browser event clocks stay outside.
export const WINDOWS = Object.freeze({ perfect: .045, good: .095, ok: .145 });
const EPS = 1e-9;
export class RhythmRun {
  constructor(chart) {
    if (!Array.isArray(chart) || !chart.length) throw new TypeError('A chart needs notes.');
    const ids = new Set();
    this.notes = chart.map(n => {
      if (!Number.isFinite(n.time) || n.time < 0 || !Number.isInteger(n.lane) || n.lane < 0 || n.lane > 3 || ids.has(n.id)) throw new TypeError('Invalid chart note.');
      ids.add(n.id);
      return { ...n, state: 'pending', error: null, protected: false };
    }).sort((a,b) => a.time-b.time || a.lane-b.lane);
    this.score = 0;
    this.combo = 0;
    this.maxCombo = 0;
    this.aura = 0;
    this.shieldUntil = -1;
    this.shields = 0;
    this.pulses = 0;
    this.strays = 0;
    this.lastTime = -Infinity;
    this.finished = false;
  }
  advance(time) {
    if (!Number.isFinite(time)) throw new TypeError('Time must be finite.');
    if (this.finished) return [];
    this.lastTime = Math.max(this.lastTime, time);
    const misses = [];
    for (const n of this.notes) {
      if (n.state !== 'pending' || this.lastTime-n.time <= WINDOWS.ok+EPS) continue;
      n.state = 'miss';
      if (this.shields > 0 && n.time+WINDOWS.ok <= this.shieldUntil+EPS) {
        n.protected = true;
        this.shields--;
      } else this.combo = 0;
      this.aura = Math.max(0, this.aura-16);
      misses.push(n);
    }
    return misses;
  }
  hit(lane,time) {
    if (!Number.isInteger(lane) || lane<0 || lane>3 || !Number.isFinite(time)) throw new TypeError('Invalid input.');
    if (this.finished) return null;
    this.advance(time);
    const n = this.notes.find(n => n.state==='pending' && n.lane===lane && Math.abs(time-n.time)<=WINDOWS.ok+EPS);
    if (!n) {
      this.strays++;
      this.combo=0;
      this.aura=Math.max(0,this.aura-8);
      this.score=Math.max(0,this.score-50);
      return { state:'stray', error:null, lane };
    }
    n.error = time-n.time;
    const d=Math.abs(n.error);
    n.state=d<=WINDOWS.perfect+EPS?'perfect':d<=WINDOWS.good+EPS?'good':'ok';
    this.combo++;
    this.maxCombo=Math.max(this.maxCombo,this.combo);
    this.aura=Math.min(100,this.aura+{perfect:9,good:6,ok:3}[n.state]);
    this.score+={perfect:1000,good:700,ok:400}[n.state]*Math.min(4,1+Math.floor(this.combo/20));
    return n;
  }
  pulse(time) {
    if (!Number.isFinite(time)) throw new TypeError('Time must be finite.');
    if (this.finished) return false;
    this.advance(time);
    if (this.aura<100) return false;
    this.aura=0;
    this.shields=2;
    this.shieldUntil=time+8;
    this.pulses++;
    return true;
  }
  finish(time) {
    if (!Number.isFinite(time)) throw new TypeError('Time must be finite.');
    this.advance(Math.max(time, this.notes.at(-1).time+WINDOWS.ok+1));
    this.finished=true;
    return this.summary();
  }
  summary() {
    const counts={perfect:0,good:0,ok:0,miss:0,pending:0};
    const hits=[];
    for(const n of this.notes) { counts[n.state]++; if(n.error!==null) hits.push(n.error); }
    const judged=this.notes.length-counts.pending;
    const accuracy=judged?100*(counts.perfect+counts.good*.7+counts.ok*.4)/(judged+this.strays*.1):0;
    return { score:this.score, maxCombo:this.maxCombo, counts, strays:this.strays, pulses:this.pulses,
      accuracy:Math.round(accuracy*100)/100,
      meanErrorMs:hits.length?Math.round(10000*hits.reduce((a,b)=>a+b,0)/hits.length)/10:null,
      rank:!judged?'—':accuracy>=95?'S':accuracy>=85?'A':accuracy>=70?'B':accuracy>=50?'C':'D' };
  }
}
export function adjustedTime(songTime, offsetMs) {
  if(!Number.isFinite(songTime)||!Number.isFinite(offsetMs)||Math.abs(offsetMs)>150) throw new TypeError('Invalid timing offset.');
  return songTime-offsetMs/1000;
}
export function calibrationOffset(samples) {
  const sorted=samples.filter(Number.isFinite).sort((a,b)=>a-b);
  if(sorted.length<6) throw new RangeError('At least six taps are required.');
  const center=sorted.length%2?sorted[(sorted.length-1)/2]:(sorted[sorted.length/2-1]+sorted[sorted.length/2])/2;
  return Math.max(-150,Math.min(150,Math.round(center*1000/5)*5));
}
