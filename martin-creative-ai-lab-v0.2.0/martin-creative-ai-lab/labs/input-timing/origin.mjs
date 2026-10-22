import assert from 'node:assert/strict';
import {pathToFileURL} from 'node:url';
const base=process.argv[2];const {RhythmRun,WINDOWS}=await import(pathToFileURL(base+'/core.js'));
const {makeSession}=await import(pathToFileURL(base+'/rehearsal.js'));
const checks=[];function check(id,condition){assert.ok(condition,id);checks.push(id);}
for(const [seconds,expected] of [[.045,'perfect'],[.045001,'good'],[.095,'good'],[.095001,'ok'],[.145,'ok']]){const r=new RhythmRun([{id:1,lane:0,time:1}]);check('head '+seconds,r.hit(0,1+seconds).state===expected);}
for(const [time,state] of [[.904,'miss'],[.905,'perfect']]){const r=new RhythmRun([{id:1,lane:0,time:0,duration:1}]);r.hit(0,0);r.release(0,time);check('tail '+time,r.notes[0].state===state);}
for(const [time,state] of [[.599,'perfect'],[.601,'miss']]){const r=new RhythmRun([{id:1,lane:0,time:0,duration:1}]);r.hit(0,0);r.pause(.4);r.resume(.4,[]);r.hit(0,time);r.advance(2);check('regrab '+time,r.notes[0].state===state);}
const paused=new RhythmRun([{id:1,lane:0,time:0,duration:1}]);paused.hit(0,0);paused.pause(.4);paused.advance(2);check('paused held cannot award',paused.score===0&&paused.notes[0].state==='holding');
function frames(step){const r=new RhythmRun([{id:1,lane:0,time:0,duration:1},{id:2,lane:1,time:1.2}]);r.hit(0,0);for(let t=step;t<2;t+=step)r.advance(t);r.advance(2);return {score:r.score,combo:r.combo,notes:r.notes};}
check('deadline order independent of polling',JSON.stringify(frames(.01))===JSON.stringify(frames(2)));
const track={bpm:120,leadIn:1,musicEnd:9,duration:10,sections:[{time:0,name:'a'}],charts:{a:[{id:1,lane:0,time:1,duration:1}]}};
const s=makeSession(track,'a','0',.75);check('performance clock scales head',Math.abs(s.notes[0].time-1/.75)<1e-9);check('performance clock scales tail',Math.abs(s.notes[0].duration-1/.75)<1e-9);
console.log(JSON.stringify({schema_version:1,checks,windows:WINDOWS,scope:'Actual P03 modules, synthetic timestamped events; not audio playback, browser/hardware latency or player validation.'}));
