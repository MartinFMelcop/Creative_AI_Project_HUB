import test from 'node:test';
import assert from 'node:assert/strict';
import {Campaign,serialize,restore} from '../dist/campaign.js';
const road=['rope','timber','ready','herbs','bargain','causeway','iven','roof','span','convoy'];
const ferry=['timber','oil','ready','leave','ferry','iven','roof'];
const dry=[...ferry,'load','board','row','row','board','row'];
const wet=[...ferry,'board','row','row','load','board','row'];
const play=(actions,g=new Campaign())=>{for(const a of actions)g.act(a);return g;};
test('night outcomes really change morning supply, transport, labor and repair options',()=>{
  const a=play([...road,'morning']),b=play([...wet,'morning']);
  assert.equal(a.morning.state.medicine,'supplied');assert.equal(b.morning.state.medicine,'missing');
  assert.match(a.morning.choices().find(c=>c.name==='grain').label,/4 grain/);
  assert.match(b.morning.choices().find(c=>c.name==='grain').label,/2 grain/);
  assert.equal(a.morning.choices().find(c=>c.name==='grain').cost,1);
  assert.equal(a.morning.state.time,6);assert.equal(a.state.time,0);
  assert.ok(b.morning.choices().some(c=>c.name==='depot'));assert.ok(!b.morning.choices().some(c=>c.name==='retrieve-chest'));
  const dryLeft=play(['rope','oil','ready','leave','retreat','morning']);
  assert.ok(dryLeft.choices().some(c=>c.name==='retrieve-chest'));assert.ok(!dryLeft.choices().some(c=>c.name==='depot'));
});
test('complete road campaign plants seed, delivers grain and preserves the exact night state',()=>{
  const g=play(road),night=g.snapshot();
  play(['morning','grain','seed','plant','ready-ferry'],g);
  assert.deepEqual(g.snapshot(),night);assert.equal(g.morning.state.ending,'READY_FOR_NOON');
  assert.equal(g.morning.state.seed,'sown');assert.equal(g.morning.state.grain,4);
  assert.equal(g.morning.state.elapsed,6);assert.match(g.morning.epilogue(),/no.*harvest|check the rows/);
  assert.match(g.morning.epilogue(),/second supply route/);
  assert.deepEqual(g.choices(),[]);
});
test('same spoiled-cargo night yields timely or delayed care through actual work order',()=>{
  const timely=play([...wet,'morning','depot','supply-clinic','grain','grain','seed']);
  const late=play([...wet,'morning','grain','grain','depot','supply-clinic','seed']);
  assert.equal(timely.morning.state.timely,true);assert.equal(late.morning.state.timely,false);
  for(const g of [timely,late])assert.deepEqual([g.morning.state.people,g.morning.state.grain,g.morning.state.seed],[4,4,'saved']);
  assert.match(timely.morning.epilogue(),/in time/);assert.match(late.morning.epilogue(),/afternoon crew/);
  assert.equal(timely.morning.state.reserve_used,true);assert.match(timely.morning.epilogue(),/reserve box is empty/);
});
test('recovery changes ferry labor; missing crew cannot appear in planting scenes',()=>{
  const g=play(['rope','oil','ready','leave','ferry','board','row','finish','morning']);
  assert.equal(g.morning.state.people,2);assert.equal(g.morning.state.iven,false);
  g.act('ready-ferry');assert.equal(g.morning.choices().find(c=>c.name==='grain').cost,2);
  g.act('recover-crew');assert.equal(g.morning.choices().find(c=>c.name==='grain').cost,1);
  play(['grain','grain'],g);assert.equal(g.morning.state.people,4);assert.equal(g.morning.state.grain,4);
  const missing=play(['rope','oil','ready','leave','retreat','morning','seed']);
  assert.ok(!missing.choices().some(c=>c.name==='plant'));assert.equal(missing.morning.state.seed,'saved');
});
test('public correction opens road work without rewriting the recorded night lie',()=>{
  const g=play(['rope','timber','ready','lie','leave','retreat','morning']);
  const night=g.snapshot();assert.ok(!g.choices().some(c=>c.name==='repair-road'));
  g.act('correct-record');assert.ok(g.choices().some(c=>c.name==='repair-road'));
  assert.deepEqual(g.snapshot(),night);assert.equal(g.workshop.state.apology_due,true);
  assert.match(g.history.at(-1).text,/keeps the old line legible/);
});
test('old crossing saves and new campaign saves replay without trusted snapshot fields',()=>{
  const night=play(dry),old=serialize(night);assert.equal(old.schema,1);
  const imported=restore(old);play(['morning','grain','seed'],imported);
  const saved={...serialize(imported),morning:{people:999,seed:'sown'}};
  assert.equal(saved.schema,2);const copy=restore(JSON.parse(JSON.stringify(saved)));
  assert.deepEqual(copy.morning.snapshot(),imported.morning.snapshot());assert.deepEqual(copy.history,imported.history);
  for(const data of [{...saved,actions:['morning']},{...saved,actions:[...saved.actions,'morning']},{...saved,engine_version:'old'}])assert.throws(()=>restore(data));
  const before=copy.morning.snapshot();assert.throws(()=>copy.act('not-real'));assert.deepEqual(copy.morning.snapshot(),before);
});
test('every reachable morning successor preserves time, deliveries and inherited night facts',()=>{
  const starts=[road,dry,wet,['rope','oil','ready','leave','retreat'],
    ['rope','oil','ready','leave','ferry','board','row','row','load','row'],
    ['rope','timber','ready','lie','leave','retreat']];
  const seen=new Set(),pending=starts.map(a=>serialize(play([...a,'morning'])));let transitions=0;
  while(pending.length) {
    const save=pending.pop(),g=restore(save),s=g.morning.state,key=JSON.stringify(g.morning.snapshot());
    if(seen.has(key))continue;seen.add(key);
    assert.equal(s.time+s.elapsed,6);assert.ok(s.people>=g.state.saved&&s.people<=4);
    assert.ok(s.grain>=0&&s.grain<=4);assert.ok(s.timber>=0);
    if(s.ending){assert.deepEqual(g.choices(),[]);g.morning.epilogue();continue;}
    for(const c of g.choices()) {
      const child=restore(save);child.act(c.name);transitions++;
      assert.equal(child.morning.state.time,s.time-c.cost);
      assert.deepEqual(child.snapshot(),g.snapshot());pending.push(serialize(child));
    }
  }
  console.log(`Morning graph: ${seen.size} states, ${transitions} transitions from six specified night endings`);
  assert.ok(seen.size>100);
});
