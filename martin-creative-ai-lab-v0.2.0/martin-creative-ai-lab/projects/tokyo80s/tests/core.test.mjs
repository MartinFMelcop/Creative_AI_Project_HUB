import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import { RhythmRun, WINDOWS, adjustedTime, calibrationOffset } from '../dist/core.js';
const track=JSON.parse(fs.readFileSync(new URL('../dist/track.json',import.meta.url)));
const note=(id,time,lane=0)=>({id,time,lane});
test('timing boundaries classify both early and late hits with inclusive windows',()=>{
  for(const sign of [-1,1])for(const [delta,expected] of [[0,'perfect'],[.045,'perfect'],[.045001,'good'],[.095,'good'],[.095001,'ok'],[.145,'ok']]){
    const r=new RhythmRun([note(0,1)]);assert.equal(r.hit(0,1+delta*sign).state,expected);
  }
  const early=new RhythmRun([note(0,1)]);assert.equal(early.hit(0,.854).state,'stray');assert.equal(early.notes[0].state,'pending');
  const late=new RhythmRun([note(0,1)]);assert.equal(late.hit(0,1.145001).state,'stray');assert.equal(late.notes[0].state,'miss');
});
test('frame gaps expire each note exactly once instead of changing successful hit windows',()=>{
  const r=new RhythmRun([note(0,1),note(1,2),note(2,3)]);
  r.hit(0,1);assert.equal(r.advance(10).length,2);assert.equal(r.advance(20).length,0);
  assert.deepEqual(r.summary().counts,{perfect:1,good:0,ok:0,miss:2,pending:0});
  assert.equal(r.maxCombo,1);assert.equal(r.combo,0);
});
test('a held or repeated attempt cannot consume the same note twice',()=>{
  const r=new RhythmRun([note(0,1)]);r.hit(0,1);const old=r.score;
  assert.equal(r.hit(0,1).state,'stray');assert.equal(r.notes.filter(n=>n.state==='perfect').length,1);
  assert.equal(r.score,old-50);assert.equal(r.strays,1);assert.equal(r.combo,0);
});
test('simultaneous chord notes remain independently hittable across lanes',()=>{
  const r=new RhythmRun([note(0,1,0),note(1,1,2)]);r.hit(0,1);r.hit(2,1);
  assert.equal(r.combo,2);assert.equal(r.summary().counts.perfect,2);
});
test('Pulse requires earned aura and protects only two misses inside its lifetime',()=>{
  const r=new RhythmRun(Array.from({length:16},(_,i)=>note(i,i)));
  assert.equal(r.pulse(0),false);
  for(let i=0;i<12;i++)r.hit(0,i);
  assert.equal(r.aura,100);assert.equal(r.pulse(11),true);assert.equal(r.aura,0);
  r.advance(13.15);assert.equal(r.notes[12].protected,true);assert.equal(r.notes[13].protected,true);
  assert.equal(r.combo,12);r.advance(14.15);assert.equal(r.notes[14].protected,false);assert.equal(r.combo,0);
  assert.equal(r.summary().counts.miss,3);
});
test('Pulse cannot preserve a miss after its deadline',()=>{
  const r=new RhythmRun([note(0,10)]);r.aura=100;r.combo=5;r.pulse(0);r.advance(11);
  assert.equal(r.notes[0].protected,false);assert.equal(r.combo,0);
});
test('stray input cannot farm points or aura',()=>{
  const r=new RhythmRun([note(0,10)]);
  for(let i=0;i<100;i++)r.hit(i%4,i/100);
  assert.equal(r.score,0);assert.equal(r.aura,0);assert.equal(r.combo,0);assert.equal(r.strays,100);
});
test('positive input offsets compensate late events, and calibration rejects insufficient samples',()=>{
  assert.equal(adjustedTime(1.08,80),1);
  assert.equal(adjustedTime(.92,-80),1);
  assert.equal(calibrationOffset([.08,.075,.085,.08,.08,.24,.08]),80);
  assert.throws(()=>calibrationOffset([0,.01]),RangeError);
  assert.throws(()=>adjustedTime(1,151),TypeError);
});
test('finishing closes residual notes and prevents all later score mutations',()=>{
  const r=new RhythmRun([note(0,1),note(1,2)]);r.hit(0,1);const stats=r.finish(3);
  assert.equal(stats.counts.miss,1);const old=JSON.stringify(r);
  assert.equal(r.hit(0,5),null);assert.equal(r.pulse(5),false);r.advance(8);assert.equal(JSON.stringify(r),old);
});
test('original charts match track sections and can produce complete perfect runs',()=>{
  assert.equal(track.duration,69);assert.equal(track.bpm,120);
  for(const mode of ['practice','arcade']){
    const r=new RhythmRun(track.charts[mode]);
    for(const n of track.charts[mode]){assert.ok(n.time>=track.leadIn&&n.time<track.musicEnd);r.hit(n.lane,n.time);}
    const stats=r.finish(track.duration);
    assert.equal(stats.rank,'S');assert.equal(stats.accuracy,100);assert.equal(stats.counts.perfect,track.charts[mode].length);
    assert.equal(stats.maxCombo,track.charts[mode].length);assert.equal(stats.counts.miss,0);
    const silent=new RhythmRun(track.charts[mode]);assert.equal(silent.finish(track.duration).counts.miss,track.charts[mode].length);
  }
  assert.ok(track.charts.arcade.length>track.charts.practice.length);
  assert.ok(track.charts.arcade.some((n,i)=>i&&n.time===track.charts.arcade[i-1].time));
});
test('invalid data and inputs reject before changing session state',()=>{
  assert.throws(()=>new RhythmRun([]));assert.throws(()=>new RhythmRun([note(0,1,4)]));
  assert.throws(()=>new RhythmRun([note(0,1),note(0,2)]));
  const r=new RhythmRun([note(0,1)]),before=JSON.stringify(r);
  for(const input of [[4,1],[0,NaN]])assert.throws(()=>r.hit(...input),TypeError);
  assert.throws(()=>r.advance(Infinity),TypeError);assert.equal(JSON.stringify(r),before);
});

test('a delayed rendering frame preserves the same Pulse consequences as on-time expiration',()=>{
  const chart=Array.from({length:14},(_,i)=>note(i,i));
  const fine=new RhythmRun(chart),delayed=new RhythmRun(chart);
  for(const r of [fine,delayed]){for(let i=0;i<12;i++)r.hit(0,i);r.pulse(11);}
  fine.advance(12.2);fine.advance(13.2);fine.advance(30);delayed.advance(30);
  assert.deepEqual(delayed.summary(),fine.summary());
  assert.equal(delayed.combo,12);assert.equal(delayed.notes[12].protected,true);
});
