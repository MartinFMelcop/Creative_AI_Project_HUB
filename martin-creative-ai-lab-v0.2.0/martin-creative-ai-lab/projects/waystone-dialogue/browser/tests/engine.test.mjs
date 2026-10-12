import test from 'node:test';
import assert from 'node:assert/strict';
import {spawnSync} from 'node:child_process';
import {fileURLToPath} from 'node:url';
import {Adventure,serialize,restore} from '../dist/engine.js';

const play=actions=>{const g=new Adventure();for(const a of actions)g.act(a);return g;};
test('browser matches real Python choices, traces, state and endings across the river graph',()=>{
  const r=spawnSync('python3',[fileURLToPath(new URL('../tools/oracle.py',import.meta.url))],{encoding:'utf8',maxBuffer:128*1024*1024});
  assert.equal(r.status,0,r.stderr);
  let compared=0,summary;
  for(const line of r.stdout.trim().split('\n')) {
    const row=JSON.parse(line);
    if(row.river_states) {summary=row;continue;}
    const make=()=>{const g=new Adventure();g.state=structuredClone(row.snapshot.expedition);g.workshop.state=structuredClone(row.snapshot.workshop);return g;};
    assert.deepEqual(make().choices(),row.choices);
    if(row.epilogue!==null)assert.equal(make().epilogue(),row.epilogue);
    for(const expected of row.transitions) {
      assert.deepEqual(make().act(expected.action),expected,JSON.stringify({state:row.snapshot,action:expected.action}));
      compared++;
    }
  }
  assert.ok(summary.river_states>=8000);
  console.log(`Python oracle: ${summary.river_states} river states, ${compared} transitions compared`);
});
test('replayed save retains cargo, memory and both complete rescue routes',()=>{
  for(const actions of [
    ['rope','timber','ready','herbs','bargain','causeway','iven','roof','span','convoy'],
    ['timber','oil','ready','leave','ferry','iven','roof','load','board','row','row','board','row'],
    ['rope','timber','ready','lie','apologize','herbs','bargain','causeway','roof','span','lead']
  ]) {
    const g=play(actions),copy=restore(JSON.parse(JSON.stringify(serialize(g))));
    assert.deepEqual(copy.snapshot(),g.snapshot());assert.deepEqual(copy.history,g.history);
    assert.equal(copy.epilogue(),g.epilogue());
  }
});
test('invalid saves and unavailable input cannot alter an active session',()=>{
  const game=play(['rope','oil','ready','leave','ferry']),before=game.snapshot();
  assert.throws(()=>game.act('convoy'));assert.deepEqual(game.snapshot(),before);
  for(const data of [null,{}, {...serialize(game),schema:2}, {...serialize(game),engine_version:'0.1.0'},
    {...serialize(game),actions:['<script>']}, {...serialize(game),actions:[{}]},
    {...serialize(game),actions:['ready']}, {...serialize(game),actions:Array(1025).fill('rope')}])assert.throws(()=>restore(data));
  assert.deepEqual(game.snapshot(),before);
  const long=new Adventure();for(let i=0;i<1025;i++)long.act('rope');
  assert.throws(()=>serialize(long),/save limit/);assert.equal(long.state.phase,'pack');
});
test('same ferry equipment saves the same people with a different medicine consequence',()=>{
  const start=['timber','oil','ready','leave','ferry','iven','roof'];
  const first=play([...start,'load','board','row','row','board','row']);
  const last=play([...start,'board','row','row','load','board','row']);
  assert.equal(first.state.saved,4);assert.equal(last.state.saved,4);
  assert.equal(first.state.medicine,'delivered');assert.equal(last.state.medicine,'spoiled');
  assert.equal(first.state.ending,'FULL_RESCUE');assert.equal(last.state.ending,'PEOPLE_SAFE');
});
