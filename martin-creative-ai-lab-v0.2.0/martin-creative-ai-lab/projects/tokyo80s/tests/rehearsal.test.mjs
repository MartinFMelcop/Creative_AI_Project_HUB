import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {phrases, makeSession, phraseResults, RATES, backingFor} from '../dist/rehearsal.js';
import {RhythmRun, adjustedTime} from '../dist/core.js';
const tracks=['track','rain-circuit'].map(name=>JSON.parse(fs.readFileSync(new URL(`../dist/${name}.json`,import.meta.url))));
test('stretched backing covers the same phrase/tails with one-to-one performance playback; missing variants cannot detune',()=>{
  const catalogue=JSON.parse(fs.readFileSync(new URL('../dist/setlist.json',import.meta.url)));
  for(const score of tracks)for(const rate of RATES) {
    const track={...score,...catalogue.find(t=>t.id===score.id)};
    const session=makeSession(track,'arcade','3',rate),backing=backingFor(track,session);
    assert.equal(backing.playbackRate,1);
    assert.ok(Math.abs(backing.offset*rate-session.cueStart)<1e-8);
    assert.ok(Math.abs(backing.duration-session.duration)<1e-8);
    assert.ok(backing.offset+backing.duration<=backing.bufferDuration);
    const full=backingFor(track,makeSession(track,'arcade','full',rate));
    assert.equal(full.url,score.audio);assert.equal(full.offset,0);assert.equal(full.duration,score.duration);
  }
  assert.throws(()=>backingFor(tracks[0],makeSession(tracks[0],'practice','0',.75)),/unavailable/);
});
test('every source head belongs to exactly one four-bar rehearsal, across both charts and all rates',()=>{
  for(const track of tracks)for(const chart of ['practice','arcade'])for(const rate of RATES) {
    const all=phrases(track).flatMap(p=>{
      const session=makeSession(track,chart,p.id,rate);
      const run=new RhythmRun(session.notes);
      for(const note of run.notes){
        const source=track.charts[chart].find(n=>n.id===note.id);
        assert.ok(Math.abs(session.cueStart+note.time*rate-source.time)<1e-8);
        assert.ok(Math.abs((note.duration||0)*rate-(source.duration||0))<1e-8);
        assert.ok(note.time+(note.duration||0)<session.duration);
      }
      return run.notes.map(n=>n.id);
    });
    assert.deepEqual(all.sort((a,b)=>a-b),track.charts[chart].map(n=>n.id).sort((a,b)=>a-b));
    assert.equal(new Set(all).size,all.length);
    assert.equal(phrases(track).length,8);
  }
});
test('source sustain crossing a phrase boundary is carried in its original phrase',()=>{
  const track={bpm:120,leadIn:2,musicEnd:18,duration:20,sections:[{time:2,name:'Test'}],charts:{practice:[{id:0,time:9.5,lane:1,duration:1},{id:1,time:10,lane:0}]}};
  const first=makeSession(track,'practice','0',.75),next=makeSession(track,'practice','1',.75);
  assert.deepEqual(first.notes.map(n=>n.id),[0]);assert.deepEqual(next.notes.map(n=>n.id),[1]);
  assert.ok(first.audioEnd>10.5);assert.equal(first.notes[0].sourceDuration,1);
  const run=new RhythmRun(first.notes);run.hit(1,first.notes[0].time);run.advance(first.notes[0].time+1/.75);
  assert.equal(run.finish(first.duration).counts.perfect,1);
});
test('slowing a phrase preserves real judgment/offset, release grace and pause regrab windows',()=>{
  const track=tracks[1];
  for(const rate of RATES) {
    const session=makeSession(track,'arcade','0',rate);
    const tap=session.notes.find(n=>!n.duration),hold=session.notes.find(n=>n.duration);
    const run=new RhythmRun(session.notes);
    run.hit(tap.lane,adjustedTime(tap.time+.115,20));assert.equal(run.notes.find(n=>n.id===tap.id).state,'good');
    const held=new RhythmRun(session.notes);held.hit(hold.lane,hold.time);held.pause(hold.time+.2);
    held.resume(hold.time+.2);held.hit(hold.lane,hold.time+.39);
    held.release(hold.lane,hold.time+hold.duration-.095);
    assert.equal(held.notes.find(n=>n.id===hold.id).state,'perfect');
    const dropped=new RhythmRun(session.notes);dropped.hit(hold.lane,hold.time);
    dropped.release(hold.lane,hold.time+hold.duration-.096);
    assert.equal(dropped.notes.find(n=>n.id===hold.id).state,'miss');
  }
});
test('full chart identity/rate stay original; review reflects actual misses and lost holds',()=>{
  const track=tracks[1],full=makeSession(track,'arcade','full',.75);
  assert.strictEqual(full.notes,track.charts.arcade);assert.equal(full.rate,1);assert.equal(full.duration,84.5);
  const run=new RhythmRun(full.notes);run.hit(0,2.5);run.finish(84.5);
  const review=phraseResults(track,run.notes);
  assert.equal(review.length,8);assert.equal(review[0].counts.perfect,1);
  assert.equal(review.reduce((n,p)=>n+p.counts.miss,0),full.notes.length-1);
  assert.equal(review.reduce((n,p)=>n+p.lostHolds,0),full.notes.filter(n=>n.duration).length);
  assert.throws(()=>makeSession(track,'arcade','8',1));assert.throws(()=>makeSession(track,'arcade','0',.5));
});
