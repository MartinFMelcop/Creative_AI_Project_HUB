import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import { RhythmRun, WINDOWS } from '../dist/core.js';
import { makeSession } from '../dist/rehearsal.js';
import { reviewNotes } from '../dist/review.js';

const hold = (id, time, lane = id % 4) => ({id, time, lane, duration: 1});

test('same-score opposing lane bias and alternating errors produce different lane reviews', () => {
  const chart = [0, 1, 2, 3].map(id => ({id, time: id + 4, lane: id % 2 ? 3 : 0}));
  function perform(errors) {
    const run = new RhythmRun(chart);
    chart.forEach((note, index) => run.hit(note.lane, note.time + errors[index]));
    return {stats: run.finish(9), review: reviewNotes(run.notes)};
  }
  const biased = perform([-.08, .08, -.08, .08]);
  const mixed = perform([-.08, .08, .08, -.08]);
  assert.deepEqual(biased.stats, mixed.stats);
  assert.equal(biased.stats.meanErrorMs, 0);
  assert.equal(biased.review.meanHeadErrorMs, 0);
  assert.equal(biased.review.meanAbsoluteHeadErrorMs, 80);
  assert.equal(biased.review.early, 2);
  assert.equal(biased.review.late, 2);
  assert.equal(biased.review.lanes[0].meanHeadErrorMs, -80);
  assert.equal(biased.review.lanes[3].meanHeadErrorMs, 80);
  assert.equal(mixed.review.lanes[0].meanHeadErrorMs, 0);
  assert.equal(mixed.review.lanes[3].meanHeadErrorMs, 0);
  assert.notDeepEqual(biased.review.lanes, mixed.review.lanes);
});

test('actual hold paths distinguish missed heads, early release, regrab loss and unheld finish', () => {
  const run = new RhythmRun([hold(0, 1), hold(1, 3), hold(2, 5), hold(3, 7), hold(4, 9)]);
  run.advance(2.5); // Never received the first head.
  run.hit(1, 3); run.advance(4); // Carried the second tail.
  run.hit(2, 5); run.release(2, 5.3);
  run.hit(3, 7); run.pause(7.1); run.resume(7.1); run.advance(7.31);
  run.hit(0, 9); run.pause(9.1); run.finish(10.5);
  const before = structuredClone(run.notes);
  const review = reviewNotes(run.notes);
  assert.deepEqual(review.holds, {total: 5, carried: 1, missedHead: 1, earlyRelease: 1,
    regrabTimeout: 1, unheldAtFinish: 1, unknown: 0});
  assert.equal(review.noteCount, 5);
  assert.equal(review.receivedHeads, 4);
  assert.equal(review.missedHeads, 1);
  assert.equal(review.withinPerfect, 4);
  assert.equal(review.meanAbsoluteHeadErrorMs, 0);
  assert.deepEqual(run.notes, before);
});

test('a failed hold retains its received head timing while score summary remains unchanged', () => {
  const run = new RhythmRun([hold(0, 1)]);
  run.hit(0, 1.08); run.release(0, 1.4);
  const stats = run.finish(3);
  assert.equal(stats.meanErrorMs, null);
  assert.equal(stats.counts.miss, 1);
  const review = reviewNotes(run.notes);
  assert.equal(review.receivedHeads, 1);
  assert.equal(review.missedHeads, 0);
  assert.equal(review.meanHeadErrorMs, 80);
  assert.equal(review.meanAbsoluteHeadErrorMs, 80);
  assert.equal(review.late, 1);
  assert.equal(review.holds.earlyRelease, 1);
  assert.deepEqual(run.summary(), stats);
});

test('historical and unfamiliar failed holds remain unknown without fabricated causes', () => {
  const notes = [
    {...hold(0, 1), state: 'miss', error: null},
    {...hold(1, 3), state: 'miss', error: 0},
    {...hold(2, 5), state: 'miss', error: .08, failureReason: 'constructor'},
    {...hold(3, 7), state: 'miss', error: -.08, failureReason: 'future-reason'}
  ];
  const review = reviewNotes(notes);
  assert.deepEqual(review.holds, {total: 4, carried: 0, missedHead: 0, earlyRelease: 0,
    regrabTimeout: 0, unheldAtFinish: 0, unknown: 4});
  assert.equal(review.receivedHeads, 3);
  assert.equal(review.missedHeads, 1);
  assert.equal(review.meanHeadErrorMs, 0);
});

test('timing bins retain the actual inclusive Perfect boundary on both sides', () => {
  const chart = [0, 1, 2, 3].map(id => ({id, time: 2 + id, lane: id}));
  const errors = [-WINDOWS.perfect, WINDOWS.perfect, -WINDOWS.perfect - .000001, WINDOWS.perfect + .000001];
  const run = new RhythmRun(chart);
  chart.forEach((note, index) => run.hit(note.lane, note.time + errors[index]));
  const stats = run.finish(8);
  const review = reviewNotes(run.notes);
  assert.equal(stats.counts.perfect, 2);
  assert.equal(review.withinPerfect, 2);
  assert.equal(review.early, 1);
  assert.equal(review.late, 1);
  assert.equal(review.early + review.withinPerfect + review.late, review.receivedHeads);
});

test('empty and unplayed finished lanes have null timing rather than zero error', () => {
  const empty = reviewNotes([]);
  assert.equal(empty.noteCount, 0);
  assert.equal(empty.receivedHeads, 0);
  assert.equal(empty.meanHeadErrorMs, null);
  assert.equal(empty.meanAbsoluteHeadErrorMs, null);
  assert.deepEqual(empty.lanes.map(lane => lane.lane), [0, 1, 2, 3]);
  for (const lane of empty.lanes) {
    assert.equal(lane.receivedHeads, 0);
    assert.equal(lane.meanHeadErrorMs, null);
    assert.equal(lane.meanAbsoluteHeadErrorMs, null);
  }
  const run = new RhythmRun([{id: 0, time: 1, lane: 2}]); run.finish(3);
  const silent = reviewNotes(run.notes);
  assert.equal(silent.missedHeads, 1);
  assert.equal(silent.lanes[2].missedHeads, 1);
  assert.equal(silent.meanHeadErrorMs, null);
});

test('unfinished notes and invalid lanes reject a finished-only review', () => {
  for (const state of ['pending', 'holding', 'stray', undefined]) {
    assert.throws(() => reviewNotes([{lane: 0, state, error: 0}]), TypeError);
  }
  for (const lane of [-1, 4, 1.5, '0']) {
    assert.throws(() => reviewNotes([{lane, state: 'perfect', error: 0}]), TypeError);
  }
  assert.throws(() => reviewNotes(null), TypeError);
  assert.throws(() => reviewNotes([null]), TypeError);
});

test('head observations stay in performance milliseconds at every delivered rehearsal speed', () => {
  const track = JSON.parse(fs.readFileSync(new URL('../dist/rain-circuit.json', import.meta.url)));
  const reviews = [.75, .9, 1].map(rate => {
    const session = makeSession(track, 'practice', '0', rate);
    const run = new RhythmRun(session.notes);
    session.notes.forEach((note, index) => run.hit(note.lane, note.time + [-.08, .08, 0][index % 3]));
    run.finish(session.duration);
    return reviewNotes(run.notes);
  });
  assert.deepEqual(reviews[0], reviews[1]);
  assert.deepEqual(reviews[1], reviews[2]);
});

test('Pulse-protected failure keeps its actual hold cause and received head timing', () => {
  const chart = Array.from({length: 12}, (_, id) => ({id, time: 1 + id * .5, lane: 0}));
  chart.push(hold(12, 8, 1));
  const run = new RhythmRun(chart);
  for (const note of chart.slice(0, 12)) run.hit(note.lane, note.time);
  assert.equal(run.pulse(7), true);
  run.hit(1, 8); run.release(1, 8.3); run.finish(11);
  assert.equal(run.notes.at(-1).protected, true);
  const review = reviewNotes(run.notes);
  assert.equal(review.holds.earlyRelease, 1);
  assert.equal(review.holds.carried, 0);
  assert.equal(review.receivedHeads, 13);
  assert.equal(review.missedHeads, 0);
});
