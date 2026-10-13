import test from 'node:test';
import assert from 'node:assert/strict';
import {Campaign,serialize,restore} from '../dist/campaign.js';
const road=['rope','timber','ready','herbs','bargain','causeway','iven','roof','span','convoy'];
const ferry=['timber','oil','ready','leave','ferry','iven','roof'];
const dry=[...ferry,'load','board','row','row','board','row'];
const wet=[...ferry,'board','row','row','load','board','row'];
const sheltered=['rope','oil','ready','leave','retreat'];
const lie=['rope','timber','ready','lie','leave','retreat'];
const lost=['rope','oil','ready','leave','ferry','board','row','row','load','row'];
const play=(actions,g=new Campaign())=>{for(const a of actions)g.act(a);return g;};
const has=(g,name)=>g.choices().some(c=>c.name===name);
const loans=(decision,term,night=wet)=>play([...night,'morning','depot','supply-clinic','grain','grain','seed','handover','hear-iven','settle',decision,term]);
test('handover needs an ended morning; only present witnesses and a ready ferry can be offered',()=>{
  for(const path of [[],road,[...road,'morning']])assert.throws(()=>play([...path,'handover']));
  const g=play([...sheltered,'morning','close','handover']);
  assert.ok(!has(g,'hear-iven'));assert.ok(!has(g,'hear-senn'));g.act('settle');
  assert.ok(!has(g,'lend-ferry'));assert.ok(!has(g,'send-guide'));
  const before=g.handover.snapshot();assert.throws(()=>g.act('send-guide'));assert.deepEqual(g.handover.snapshot(),before);
  assert.match(g.handover.opening(),/cannot ask a stranded man/);
  play(['keep-crossing','decline'],g);assert.match(g.handover.epilogue(),/missing names/);
  const solo=play(['rope','oil','ready','leave','ferry','board','row','finish','morning','ready-ferry','close','handover','settle']);
  assert.equal(solo.morning.state.iven,false);assert.equal(solo.morning.state.ferry,true);
  assert.doesNotMatch(solo.choices().find(c=>c.name==='lend-ferry').detail,/Iven stays/);
  play(['lend-ferry','open-return'],solo);assert.doesNotMatch(solo.handover.epilogue(),/Iven stays at the clinic/);
});
test('same ferry morning yields three concrete local outcomes without changing past work',()=>{
  const keep=loans('keep-crossing','decline'),boat=loans('lend-ferry','return-at-dusk'),guide=loans('send-guide','open-return');
  for(const g of [boat,guide])assert.deepEqual(g.morning.snapshot(),keep.morning.snapshot());
  assert.deepEqual([keep.handover.afternoon().route,keep.handover.afternoon().shifts_per_trip],['ferry',1]);
  assert.deepEqual([boat.handover.afternoon().route,boat.handover.afternoon().grain_per_trip,boat.handover.afternoon().shifts_per_trip],['ridge trail',1,2]);
  assert.deepEqual([guide.handover.afternoon().route,guide.handover.afternoon().shifts_per_trip],['ferry',2]);
  assert.match(boat.handover.epilogue(),/No one has returned yet/);assert.match(guide.handover.epilogue(),/no return time/);
  assert.equal(guide.morning.state.iven,true);assert.equal(guide.handover.afternoon().iven,false);
  for(const g of [keep,boat,guide])assert.deepEqual(g.choices(),[]);
});
test('Iven offers his own help; full road ending can lend its backup without losing the road',()=>{
  const g=play([...road,'morning','grain','seed','plant','ready-ferry','handover','settle']);
  assert.ok(!has(g,'send-guide'));g.act('back-to-table');g.act('hear-iven');g.act('settle');assert.ok(has(g,'send-guide'));
  play(['lend-ferry','open-return'],g);const a=g.handover.afternoon();
  assert.deepEqual([a.road,a.ferry,a.iven,a.route,a.shifts_per_trip],[true,false,true,'causeway',1]);
  assert.match(g.handover.epilogue(),/harvest unknown/);
  const roadOnly=play([...road,'morning','close','handover','hear-iven','settle','send-guide']);
  assert.equal(roadOnly.handover.afternoon().ferry,false);assert.equal(roadOnly.handover.afternoon().road,true);
  assert.doesNotMatch(roadOnly.history.at(-1).text,/Both routes|passes the ferry line/);
});
test('new public correction preserves the night fault and morning list, without inventing a Keeper signature',()=>{
  const g=play([...lie,'morning','close','handover']);const night=g.snapshot(),morning=g.morning.snapshot();
  assert.equal(g.handover.state.order,'disputed');assert.ok(!has(g,'hear-keeper'));
  g.act('correct-order');assert.equal(g.handover.state.order,'clear');assert.ok(!has(g,'hear-keeper'));
  assert.match(g.history.at(-1).text,/no one adds their signature/);
  assert.deepEqual(g.snapshot(),night);assert.deepEqual(g.morning.snapshot(),morning);
  assert.equal(g.workshop.state.apology_due,true);assert.equal(g.morning.state.record_corrected,false);
  assert.throws(()=>g.act('correct-order'));
});
test('schema 1/2 saves continue and schema 3 reconstructs decisions, terms and text at every stage',()=>{
  const g=restore(serialize(play(wet)));assert.equal(serialize(g).schema,1);
  play(['morning','depot','supply-clinic','grain','grain','seed'],g);
  const v2=serialize(g);assert.equal(v2.schema,2);const copy=restore(v2);
  for(const action of ['handover','hear-mara','hear-iven','settle','send-guide','return-at-dusk']) {
    copy.act(action);const saved={...serialize(copy),handover:{ending:'forged',morning:{grain:999}}};
    assert.equal(saved.schema,3);const replay=restore(JSON.parse(JSON.stringify(saved)));
    assert.deepEqual(replay.handover.snapshot(),copy.handover.snapshot());assert.deepEqual(replay.history,copy.history);
  }
  const saved=serialize(copy);
  for(const bad of [{...saved,schema:2,engine_version:'0.4.0'},{...v2,schema:3,engine_version:'0.5.0'},
    {...saved,engine_version:'future'},{...saved,actions:[...saved.actions,'handover']},{...saved,actions:[...saved.actions,'decline']}])assert.throws(()=>restore(bad));
});
test('every reachable handover from six night histories preserves work, consent and bounded local capacity',()=>{
  const morningSeen=new Set(),queue=[road,dry,wet,sheltered,lie,lost].map(a=>serialize(play([...a,'morning']))),endings=[];
  while(queue.length) {
    const save=queue.pop(),g=restore(save),key=JSON.stringify(g.morning.snapshot());if(morningSeen.has(key))continue;morningSeen.add(key);
    if(g.morning.state.ending){endings.push(save);continue;}
    for(const c of g.choices()){const child=restore(save);child.act(c.name);queue.push(serialize(child));}
  }
  const seen=new Set(),pending=endings.map(save=>{const g=restore(save);g.act('handover');return serialize(g);});let transitions=0,completed=0;
  while(pending.length) {
    const save=pending.pop(),g=restore(save),scene=g.handover,before=scene.snapshot(),canonical=structuredClone(before);
    canonical.handover.heard.sort();const key=JSON.stringify(canonical);if(seen.has(key))continue;seen.add(key);
    assert.deepEqual(scene.morning,g.morning.snapshot());assert.equal(scene.state.heard.includes('iven')&& !g.morning.state.iven,false);
    if(scene.state.ending){completed++;assert.deepEqual(g.choices(),[]);scene.epilogue();continue;}
    for(const c of g.choices()) {
      const child=restore(save);child.act(c.name);transitions++;
      assert.deepEqual(child.morning.snapshot(),g.morning.snapshot());assert.deepEqual(child.snapshot(),g.snapshot());
      assert.equal(child.handover.history.at(-1).cost,0);
      const a=child.handover.afternoon();assert.ok(a.grain_per_trip>=1&&a.grain_per_trip<=4);assert.ok([1,2].includes(a.shifts_per_trip));
      if(c.name==='send-guide')assert.ok(scene.state.heard.includes('iven'));
      if(c.name==='lend-ferry')assert.equal(g.morning.state.ferry,true);
      pending.push(serialize(child));
    }
  }
  console.log(`Handover graph: ${endings.length} morning endings, ${seen.size} canonical states, ${transitions} transitions, ${completed} receipts`);
  assert.ok(endings.length>50&&completed>100);
});
