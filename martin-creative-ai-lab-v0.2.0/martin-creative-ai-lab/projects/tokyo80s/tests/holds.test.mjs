import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {RhythmRun} from '../dist/core.js';
const hold=(time=1,duration=1)=>({id:0,time,lane:1,duration});
test('holds earn their start judgment only after a carried tail, once',()=>{
  const r=new RhythmRun([hold()]);assert.equal(r.hit(1,1).state,'holding');
  assert.equal(r.score,0);assert.equal(r.aura,0);assert.equal(r.summary().counts.pending,1);
  r.advance(2);assert.equal(r.score,1000);assert.equal(r.combo,1);
  r.release(1,2.1);r.advance(4);assert.equal(r.score,1000);
});
test('release tolerance is inclusive, and early release cannot farm aura or score',()=>{
  for(const [time,expected] of [[1.905,'perfect'],[1.90499,'miss'],[1.2,'miss']]){
    const r=new RhythmRun([hold()]);r.hit(1,1);assert.equal(r.release(1,time).state,expected);
    if(expected==='miss'){assert.equal(r.score,0);assert.equal(r.aura,0);assert.equal(r.combo,0);}
  }
});
test('pause freezes ownership; re-hold before resume or inside grace, but not indefinitely',()=>{
  for(const preheld of [true,false]){
    const r=new RhythmRun([hold()]);r.hit(1,1);r.pause(1.3);r.resume(1.3,preheld?[1]:[]);
    if(!preheld)r.hit(1,1.49);r.advance(2);assert.equal(r.summary().counts.perfect,1);
  }
  const missed=new RhythmRun([hold()]);missed.hit(1,1);missed.pause(1.3);missed.resume(1.3);missed.advance(1.501);
  assert.equal(missed.summary().counts.miss,1);assert.equal(missed.score,0);
  const frozen=new RhythmRun([hold()]);frozen.hit(1,1);frozen.pause(1.3);assert.equal(frozen.finish(3).counts.pending,0);
});
test('simultaneous holds and taps retain lane identity and Pulse uses real failure time',()=>{
  const r=new RhythmRun([hold(),{id:1,time:1,lane:0}]);r.hit(1,1);r.hit(0,1);
  r.aura=100;assert.equal(r.pulse(1.1),true);r.release(1,1.2);
  assert.equal(r.notes.find(n=>n.id===0).protected,true);assert.equal(r.combo,1);assert.equal(r.summary().counts.miss,1);
});
test('late frames resolve mixed tail completions and misses in event order',()=>{
  const chart=[hold(),{id:1,time:1.5,lane:0},{id:2,time:2.5,lane:2}];
  const a=new RhythmRun(chart),b=new RhythmRun(chart);for(const r of [a,b])r.hit(1,1);
  a.advance(1.7);a.advance(2);a.advance(3);b.advance(3);
  assert.deepEqual(a.summary(),b.summary());assert.equal(a.combo,b.combo);
});
test('sustain duration and lane overlaps reject ambiguous charts',()=>{
  for(const duration of [NaN,Infinity,-1,0,.1,5])assert.throws(()=>new RhythmRun([hold(1,duration)]));
  assert.throws(()=>new RhythmRun([hold(),{id:1,time:1.7,lane:1}]));
  const r=new RhythmRun([hold()]);assert.throws(()=>r.release(4,1));assert.throws(()=>r.resume(NaN));
});
test('both Rain Circuit charts can be carried to perfect completion or missed honestly',()=>{
  const track=JSON.parse(fs.readFileSync(new URL('../dist/rain-circuit.json',import.meta.url)));
  for(const chart of Object.values(track.charts)){
    const r=new RhythmRun(chart);
    const events=chart.flatMap(n=>[{time:n.time,lane:n.lane,head:true},...(n.duration?[{time:n.time+n.duration,lane:n.lane,head:false}]:[])]).sort((a,b)=>a.time-b.time||Number(a.head)-Number(b.head));
    for(const e of events)e.head?r.hit(e.lane,e.time):r.release(e.lane,e.time);
    const s=r.finish(track.duration);assert.equal(s.accuracy,100);assert.equal(s.counts.perfect,chart.length);assert.equal(s.counts.pending,0);
    const silent=new RhythmRun(chart);assert.equal(silent.finish(track.duration).counts.miss,chart.length);
  }
});
