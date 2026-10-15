import test from 'node:test';
import assert from 'node:assert/strict';
import {Campaign,serialize,restore} from '../dist/campaign.js';
const wet=['timber','oil','ready','leave','ferry','iven','roof','board','row','row','load','board','row'];
const road=['rope','timber','ready','herbs','bargain','causeway','iven','roof','span','convoy'];
const play=(actions,g=new Campaign())=>{for(const a of actions)g.act(a);return g;};
const start=(decision)=>play([...wet,'morning','depot','supply-clinic','close','handover','hear-iven','settle',decision,decision==='keep-crossing'?'decline':'return-at-dusk','afternoon']);
test('identical inherited work makes boat and guide costs playable, without changing noon facts',()=>{
  const keep=start('keep-crossing'),boat=start('lend-ferry'),guide=start('send-guide');
  for(const g of [keep,boat,guide]) {
    const before=g.handover.snapshot();while(g.choices().some(c=>c.name==='grain'))g.act('grain');
    assert.deepEqual(g.handover.snapshot(),before);
  }
  assert.deepEqual([keep,boat,guide].map(g=>g.afternoon.state.grain),[4,2,4]);
  assert.deepEqual([keep,boat,guide].map(g=>g.afternoon.state.time),[2,0,0]);
  play(['seed','close'],keep);assert.equal(keep.afternoon.state.seed,'saved');
  assert.match(boat.afternoon.epilogue(),/No return has been observed/);
  assert.equal(guide.afternoon.state.iven,false);
});
test('late care needs recall; no retroactive timely delivery or automatic harvest',()=>{
  const g=play([...road,'morning','grain','seed','plant','ready-ferry','handover','settle','lend-ferry','open-return','afternoon']);
  assert.equal(g.afternoon.state.timely,true);assert.ok(!g.choices().some(c=>c.name==='recall'));
  g.act('close');assert.match(g.afternoon.epilogue(),/Harvest is unknown/);
  const late=play([...wet,'morning','grain','grain','depot','supply-clinic','seed','handover','settle','keep-crossing','review-later','afternoon']);
  assert.equal(late.afternoon.state.timely,false);late.act('recall');assert.equal(late.afternoon.state.recall,true);
  assert.equal(late.afternoon.state.timely,false);assert.throws(()=>late.act('recall'));late.act('plant');late.act('close');
  assert.match(late.afternoon.epilogue(),/original late supply time remains/);
  assert.match(late.afternoon.epilogue(),/No loan was promised/);
});
test('stranded recovery respects consent and improves only the locally retained ferry',()=>{
  const g=play(['rope','oil','ready','leave','ferry','board','row','finish','morning','ready-ferry','close','handover','settle','keep-crossing','decline','afternoon']);
  assert.equal(g.afternoon.route.shifts_per_trip,2);g.act('recover-crew');
  assert.equal(g.afternoon.state.people,4);assert.equal(g.afternoon.route.shifts_per_trip,1);
  assert.equal(g.morning.state.iven,false);
  const partial=play(['timber','oil','ready','leave','ferry','iven','finish','morning','close','handover','hear-iven','settle','send-guide','open-return','afternoon']);
  assert.ok(partial.choices().some(c=>c.name==='recover-crew'));partial.act('recover-crew');
  assert.equal(partial.afternoon.state.people,4);assert.equal(partial.afternoon.state.iven,false);
  assert.doesNotMatch(partial.history.at(-1).text,/Iven comes/);
});
test('every action replays; schema boundaries reject forged stages and preserve rejected states',()=>{
  const g=start('keep-crossing');
  for(const action of ['grain','grain','seed','close']) {
    g.act(action);const save=serialize(g);assert.equal(save.schema,4);
    const copy=restore({...save,afternoon:{grain:999}});assert.deepEqual(copy.afternoon.snapshot(),g.afternoon.snapshot());assert.deepEqual(copy.history,g.history);
    assert.throws(()=>restore({...save,schema:3,engine_version:'0.5.0'}));
  }
  const before=g.afternoon.snapshot();assert.throws(()=>g.act('grain'));assert.deepEqual(g.afternoon.snapshot(),before);
  for(const actions of [[],road,[...road,'morning','close'],[...road,'morning','close','handover']])assert.throws(()=>play([...actions,'afternoon']));
  assert.throws(()=>restore({format:'waystone-save',schema:4,engine_version:'0.6.0',actions:road}));
});
test('bounded afternoon graph preserves history, resources, time and finite closure',()=>{
  let states=0,edges=0;const seen=new Set(),queue=['keep-crossing','lend-ferry','send-guide'].map(d=>serialize(start(d)));
  queue.push(serialize(play(['rope','oil','ready','leave','retreat','morning','close','handover','settle','keep-crossing','decline','afternoon'])));
  while(queue.length){const save=queue.pop(),g=restore(save),key=JSON.stringify(g.afternoon.snapshot());if(seen.has(key))continue;seen.add(key);states++;
    const s=g.afternoon.state;assert.ok(s.time>=0&&s.time<=4);assert.equal(s.time+s.elapsed,4);assert.ok(s.grain>=0&&s.grain<=4);
    if(s.ending){assert.deepEqual(g.choices(),[]);g.afternoon.epilogue();continue;}
    assert.ok(g.choices().some(c=>c.name==='close'));
    for(const c of g.choices()){const next=restore(save),prior=next.handover.snapshot();next.act(c.name);edges++;assert.deepEqual(next.handover.snapshot(),prior);queue.push(serialize(next));}
  }
  console.log(`Afternoon graph: ${states} states, ${edges} transitions`);assert.ok(states>33&&edges>35);
});
