import test from 'node:test';
import assert from 'node:assert/strict';
import {Campaign,serialize,restore} from '../dist/campaign.js';
import {REVIEW_ACTIONS} from '../dist/deferred-request.js';
const wet=['timber','oil','ready','leave','ferry','iven','roof','board','row','row','load','board','row'];
const road=['rope','timber','ready','herbs','bargain','causeway','iven','roof','span','convoy'];
const stranded=['rope','oil','ready','leave','ferry','board','row','finish'];
const partial=['timber','oil','ready','leave','ferry','iven','finish'];
const play=(actions,g=new Campaign())=>{for(const a of actions)g.act(a);return g;};
const pending=(night=wet,morning=['depot','supply-clinic','close'],hear=[])=>play([...night,'morning',...morning,'handover',...hear,'settle','keep-crossing','review-later','afternoon']);
const has=(g,a)=>g.choices().some(c=>c.name===a);
const frozenPast=g=>structuredClone({night:g.snapshot(),morning:g.morning.snapshot(),noon:g.handover.snapshot()});
const assertPast=(g,past)=>assert.deepEqual(frozenPast(g),past);

test('deferred request becomes a real choice after work; a later ferry loan changes only future loads',()=>{
  const g=pending(),past=frozenPast(g);g.act('grain');assert.equal(g.afternoon.state.grain,2);
  assert.ok(has(g,'revisit-request'));const before=g.afternoon.snapshot();
  for(const a of ['revisit-request','review-list','review-mara','review-settle','review-boat']){g.act(a);assertPast(g,past);}
  assert.deepEqual(g.afternoon.route,before.route);assert.equal(g.afternoon.state.time,3);
  assert.match(g.history.find(h=>h.action==='review-list').text,/2 of 4 grain crates.*2 remain/);
  g.act('review-dusk');assert.equal(g.afternoon.route.route,'ridge trail');assert.equal(g.afternoon.state.iven,true);
  g.act('grain');assert.equal(g.afternoon.state.grain,3);assert.equal(g.afternoon.state.time,1);
  assert.ok(!has(g,'grain'));g.act('close');assertPast(g,past);
  assert.match(g.afternoon.epilogue(),/left after 1 afternoon shift.*3 shift/);
  assert.match(g.afternoon.epilogue(),/new agreed return is due now.*No return or upstream rescue has been observed/);
});

test('noon consent is insufficient; tentative offers and back spend no time or assets',()=>{
  const g=pending(wet,undefined,['hear-iven']),before=g.afternoon.snapshot();
  play(['revisit-request','review-settle'],g);assert.ok(!has(g,'review-guide'));assert.throws(()=>g.act('review-guide'));
  play(['review-back','review-iven','review-settle','review-guide'],g);
  assert.equal(g.afternoon.review.state.stage,'terms');assert.equal(g.afternoon.state.iven,true);
  assert.deepEqual(g.afternoon.route,before.route);assert.deepEqual(g.afternoon.state,before.afternoon);
  const copy=restore(serialize(g));assert.deepEqual(copy.afternoon.snapshot(),g.afternoon.snapshot());
  copy.act('review-back');assert.equal(copy.afternoon.review.state.decision,null);assert.equal(copy.afternoon.state.iven,true);
  play(['review-settle','review-guide','review-open'],copy);
  assert.equal(copy.afternoon.state.iven,false);assert.equal(copy.afternoon.route.shifts_per_trip,2);
  assert.equal(copy.afternoon.state.time,4);copy.act('grain');assert.equal(copy.afternoon.state.time,2);
});

test('pause returns to real work; a recovered Iven must make a fresh offer at the renewed table',()=>{
  const g=pending(stranded,['ready-ferry','close']),past=frozenPast(g);
  assert.equal(g.afternoon.state.iven,false);assert.match(g.afternoon.opening(),/Iven is still across the channel/);assert.doesNotMatch(g.afternoon.opening(),/Iven has gone upstream/);play(['revisit-request','review-settle'],g);
  assert.ok(!has(g,'review-guide'));assert.throws(()=>g.act('review-iven'));g.act('review-pause');
  assert.ok(has(g,'recover-crew'));g.act('recover-crew');assert.equal(g.afternoon.state.time,2);assert.equal(g.afternoon.state.iven,true);
  g.act('revisit-request');assert.match(g.history.at(-1).text,/gets down from the wall/);
  assert.deepEqual(g.afternoon.review.state.heard,[]);play(['review-iven','review-settle','review-guide','review-dusk'],g);
  assert.equal(g.afternoon.state.iven,false);assert.equal(g.afternoon.review.state.openedAt,2);
  assertPast(g,past);assert.ok(!has(g,'recover-crew'));g.act('close');assert.match(g.afternoon.epilogue(),/guide Iven left after 2/);
});

test('local rescue after a new guide departure never recalls that upstream volunteer',()=>{
  const g=pending(partial,['close']);assert.equal(g.afternoon.state.people,0);
  play(['revisit-request','review-iven','review-settle','review-guide','review-open'],g);
  assert.ok(has(g,'recover-crew'));g.act('recover-crew');assert.equal(g.afternoon.state.people,4);
  assert.equal(g.afternoon.state.iven,false);assert.doesNotMatch(g.history.at(-1).text,/Iven comes/);
  assert.ok(!has(g,'recover-crew'));
});

test('refusal, pauses and unchanged prior loans stay distinct; dusk cannot reopen a consultation',()=>{
  const g=pending();g.act('revisit-request');assert.doesNotMatch(g.history.at(-1).text,/We've worked/);
  play(['review-iven','review-settle','review-guide','review-pause','revisit-request','review-settle'],g);
  assert.ok(!has(g,'review-guide'));g.act('review-keep');assert.ok(!has(g,'revisit-request'));
  assert.equal(g.afternoon.route.route,'ferry');g.act('close');assert.match(g.afternoon.epilogue(),/refused the deferred request/);
  const before=g.afternoon.snapshot();assert.throws(()=>g.act('revisit-request'));assert.deepEqual(g.afternoon.snapshot(),before);
  for(const [decision,term] of [['keep-crossing','decline'],['lend-ferry','return-at-dusk'],['send-guide','open-return']]) {
    const other=play([...wet,'morning','close','handover','hear-iven','settle',decision,term,'afternoon']);
    assert.ok(!has(other,'revisit-request'));
  }
});

test('a causeway stays usable when a backup ferry leaves; no ferry can be lent from a ridge-only crew',()=>{
  const g=pending(road,['grain','seed','plant','ready-ferry']);
  play(['revisit-request','review-settle','review-boat','review-open'],g);
  assert.deepEqual([g.afternoon.route.road,g.afternoon.route.ferry,g.afternoon.route.grain_per_trip,g.afternoon.route.shifts_per_trip],[true,false,4,1]);
  const ridge=pending(['rope','oil','ready','leave','retreat'],['close']);play(['revisit-request','review-settle'],ridge);
  assert.ok(!has(ridge,'review-boat'));assert.ok(!has(ridge,'review-guide'));assert.throws(()=>ridge.act('review-boat'));
});

test('schema 5 replays every consultation stage; downgrade, forged facts and impossible continuations are rejected safely',()=>{
  const g=pending();assert.equal(serialize(g).schema,4);
  for(const a of ['grain','revisit-request','review-iven','review-settle','review-guide','review-dusk','grain','close']) {
    g.act(a);const saved=serialize(g);assert.equal(saved.schema,g.afternoon.review?5:4);
    const copy=restore({...saved,review:{heard:['iven'],decision:'lend-ferry'},afternoon:{grain:999}});
    assert.deepEqual(copy.afternoon.snapshot(),g.afternoon.snapshot());assert.deepEqual(copy.history,g.history);
    if(g.afternoon.review)assert.throws(()=>restore({...saved,schema:4,engine_version:'0.6.0'}));
  }
  const saved=serialize(g),before=g.afternoon.snapshot();
  for(const bad of [{...saved,engine_version:'future'},{...saved,actions:[...saved.actions,'review-boat']},
    {...saved,actions:pending().history.map(h=>h.action)}, {...saved,actions:Array(1025).fill('review-pause')}])assert.throws(()=>restore(bad));
  assert.deepEqual(g.afternoon.snapshot(),before);
});

test('bounded consultation graph conserves old records, light and assets until commitment',()=>{
  let states=0,edges=0;const seen=new Set(),queue=[pending(),play(['grain'],pending()),pending(stranded,['ready-ferry','close'])].map(serialize);
  while(queue.length){
    const save=queue.pop(),g=restore(save),canonical=g.afternoon.snapshot();if(canonical.review)canonical.review.heard.sort();
    const key=JSON.stringify(canonical);if(seen.has(key))continue;seen.add(key);states++;
    const old=frozenPast(g),s=g.afternoon.state;assert.equal(s.time+s.elapsed,4);
    for(const c of g.choices().filter(c=>REVIEW_ACTIONS.has(c.name)||c.name==='close')){
      const next=restore(save),before=next.afternoon.snapshot();next.act(c.name);edges++;assertPast(next,old);
      if(REVIEW_ACTIONS.has(c.name)){
        assert.equal(next.afternoon.state.time,before.afternoon.time);assert.equal(next.afternoon.state.grain,before.afternoon.grain);
        if(!next.afternoon.review.state.ending)assert.deepEqual(next.afternoon.route,before.route);
      }
      assert.deepEqual(restore(serialize(next)).afternoon.snapshot(),next.afternoon.snapshot());queue.push(serialize(next));
    }
  }
  console.log(`Deferred-request graph: ${states} canonical states, ${edges} transitions from three declared local states`);
  assert.ok(states>50&&edges>100);
});


test('current clinic facts distinguish afternoon supply from the missed morning deadline',()=>{
  const g=pending(wet,['depot','close']);
  assert.equal(g.afternoon.state.medicine,'ready');g.act('supply-clinic');
  play(['revisit-request','review-list','review-iven'],g);
  const facts=g.history.findLast(h=>h.action==='review-list').text;
  assert.match(facts,/clinic is supplied.*morning callers still need contacting.*morning deadline was missed/s);
  assert.doesNotMatch(facts,/morning delivery was late/);
  assert.match(g.history.at(-1).text,/choose what this crew leaves unfinished/);
  g.act('review-pause');g.act('recall');play(['revisit-request','review-list'],g);
  assert.match(g.history.at(-1).text,/morning callers have been contacted.*morning deadline was missed/s);
});
