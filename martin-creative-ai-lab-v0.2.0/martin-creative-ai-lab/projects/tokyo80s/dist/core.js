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
      if(n.duration!==undefined && (!Number.isFinite(n.duration)||n.duration<.2||n.duration>4)) throw new TypeError('Invalid sustain duration.');
      return { ...n, state: 'pending', error: null, protected: false, engaged:false,
        failureReason:null, failureTime:null };
    }).sort((a,b) => a.time-b.time || a.lane-b.lane);
    for(let lane=0;lane<4;lane++) {
      const notes=this.notes.filter(n=>n.lane===lane);
      for(let i=1;i<notes.length;i++)if(notes[i-1].duration && notes[i].time<notes[i-1].time+notes[i-1].duration-EPS) throw new TypeError('Overlapping sustain lane.');
    }
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
    // Resolve due events in song order, including tails, independently of frame gaps.
    const due=this.notes.flatMap(n=>{
      if(n.state==='pending' && this.lastTime>n.time+WINDOWS.ok+EPS) return [{n,deadline:n.time+WINDOWS.ok,success:false,reason:'missed-head'}];
      if(n.state==='holding' && n.engaged && this.lastTime>=n.time+n.duration-EPS) return [{n,deadline:n.time+n.duration,success:true}];
      if(n.state==='holding' && !n.engaged && this.lastTime>n.regrabUntil+EPS) return [{n,deadline:n.regrabUntil,success:false,
        reason:n.unheldAtFinish?'unheld-at-finish':'regrab-timeout'}];
      return [];
    }).sort((a,b)=>a.deadline-b.deadline||a.n.id-b.n.id);
    for(const event of due) {
      if(event.success) this.award(event.n,event.n.startJudgment);
      else {this.fail(event.n,event.deadline,event.reason);misses.push(event.n);}
    }
    return misses;
  }
  fail(n,deadline,reason) {
    n.failureReason=reason;n.failureTime=deadline;
    n.state='miss';n.engaged=false;
    if(this.shields>0&&deadline<=this.shieldUntil+EPS){n.protected=true;this.shields--;}else this.combo=0;
    this.aura=Math.max(0,this.aura-16);
  }
  award(n,judgment) {
    n.state=judgment;n.engaged=false;
    this.combo++;this.maxCombo=Math.max(this.maxCombo,this.combo);
    this.aura=Math.min(100,this.aura+{perfect:9,good:6,ok:3}[judgment]);
    this.score+={perfect:1000,good:700,ok:400}[judgment]*Math.min(4,1+Math.floor(this.combo/20));
  }
  hit(lane,time) {
    if (!Number.isInteger(lane) || lane<0 || lane>3 || !Number.isFinite(time)) throw new TypeError('Invalid input.');
    if (this.finished) return null;
    this.advance(time);
    const regrab=this.notes.find(n=>n.state==='holding'&&!n.engaged&&n.lane===lane&&time<=n.regrabUntil+EPS);
    if(regrab){regrab.engaged=true;this.advance(time);return regrab;}
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
    const judgment=d<=WINDOWS.perfect+EPS?'perfect':d<=WINDOWS.good+EPS?'good':'ok';
    if(n.duration){n.state='holding';n.startJudgment=judgment;n.engaged=true;}
    else this.award(n,judgment);
    return n;
  }
  release(lane,time) {
    if(!Number.isInteger(lane)||lane<0||lane>3||!Number.isFinite(time))throw new TypeError('Invalid release.');
    if(this.finished)return null;
    this.advance(time);
    const n=this.notes.find(n=>n.state==='holding'&&n.engaged&&n.lane===lane);
    if(!n)return null;
    if(time>=n.time+n.duration-WINDOWS.good-EPS)this.award(n,n.startJudgment);
    else this.fail(n,time,'early-release');
    return n;
  }
  pause(time) {
    this.advance(time);
    for(const n of this.notes)if(n.state==='holding'){n.engaged=false;n.regrabUntil=Infinity;}
  }
  resume(time,lanes=[]) {
    if(!Number.isFinite(time))throw new TypeError('Time must be finite.');
    if(this.finished)return;
    for(const n of this.notes)if(n.state==='holding'&&!n.engaged){n.engaged=lanes.includes(n.lane);n.regrabUntil=time+.2;}
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
    if(this.finished)return this.summary();
    for(const n of this.notes)if(n.state==='holding'&&!n.engaged) {
      // Preserve the existing resolution order/deadline; identify an abandoned
      // finish separately from a re-hold window that already elapsed.
      n.unheldAtFinish=n.regrabUntil>=time-EPS;
      n.regrabUntil=Math.min(n.regrabUntil,time);
    }
    this.advance(Math.max(time+1,...this.notes.map(n=>n.time+(n.duration||0)+WINDOWS.ok+1)));
    this.finished=true;
    return this.summary();
  }
  summary() {
    const counts={perfect:0,good:0,ok:0,miss:0,pending:0};
    const hits=[];
    for(const n of this.notes) { counts[n.state==='holding'?'pending':n.state]++; if(n.error!==null&&n.state!=='miss'&&n.state!=='holding') hits.push(n.error); }
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
