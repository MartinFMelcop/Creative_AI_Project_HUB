#!/usr/bin/env python3
"""Compare bounded source continuity contracts with an actual original C# consumer."""
from __future__ import annotations
import argparse
import csv
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import xml.etree.ElementTree as ET

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
CSHARP=ROOT/'north-star/csharp'
LEGACY='references/rave-master/snapshots/36af1651271422ae33856e8b5d7b45702215f165/source/'
SOURCE_NAMES={
 'p04_story':'projects/lich-cistern/story.en.md',
 'p04_comparison':'projects/lich-cistern/SOURCE_COMPARISON.md',
 'p10_request':'projects/waystone-dialogue/browser/dist/deferred-request.js',
 'p10_tests':'projects/waystone-dialogue/browser/tests/deferred-request.test.mjs',
 'quest_dev':LEGACY+'RM_ACT1/DATA/DEV/RGSS/RM_UI_QUEST_JOURNAL_RUNTIME.rb',
 'quest_dist':LEGACY+'RM_DIST/RMXP_BASE/ScriptsCustom/RM_UI_QUEST_JOURNAL_RUNTIME.rb',
 'steps_dev':LEGACY+'RM_ACT1/DATA/DEV/QUEST_STEPS.csv',
 'steps_dist':LEGACY+'RM_DIST/RMXP_BASE/Data/RM_CSV/QUEST_STEPS.csv',
}
HEADERS=['RefType','RefID','StepIndex','StepKey','StepText','IsOptional','TriggerTipo','TriggerValor']


def digest(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def source_assay(texts):
    story=texts['p04_story']; dev=texts['quest_dev']; dist=texts['quest_dist']
    # This selected passage binding is documentary, not an automated literary score.
    passage=['“No.”','“Eno, get the men off the stairs,”','Sava untied the rope around Nera’s waist.',
             '“With Lesto, would you have to stay down there?”','“When I tell you to stop, you stop,”']
    offsets=[story.find(term) for term in passage]
    if min(offsets)<0 or offsets!=sorted(offsets): raise ValueError('Selected P04 causal passage binding changed')
    if 'And he comes up before any box.' not in story: raise ValueError('P04 limited permission binding missing')
    rows=[]
    for key in ['steps_dev','steps_dist']:
        reader=csv.DictReader(io.StringIO(texts[key])); values=list(reader)
        if reader.fieldnames!=HEADERS: raise ValueError('Quest step schema changed')
        seen=set()
        for row in values:
            if None in row or any(v is None for v in row.values()): raise ValueError('Quest row width mismatch')
            step=row['StepIndex']
            if not step.isdecimal() or int(step)<1 or row['IsOptional'] not in {'0','1'} or row['TriggerTipo'] not in {'EnterArea','Talk','Var'}: raise ValueError('Invalid typed quest row')
            identity=(row['RefType'],row['RefID'],int(step))
            if identity in seen or row['RefType'] not in {'QUEST','SIDEQUEST'} or not row['TriggerValor']: raise ValueError('Invalid quest identity/trigger')
            seen.add(identity)
        rows.append(values)
    if rows[0]!=rows[1] or len(rows[0])!=73: raise ValueError('Preserved quest table observations changed')
    bindings={
      'manual_completion_both_variants':all('RM_QuestState.complete!(qid)' in t and 'elsif Input.trigger?(Input::A)' in t for t in [dev,dist]),
      'dev_has_trigger_progress':all(x in dev for x in ['module RM_QuestProgress','def self.record_trigger','return if current_idx >= target_idx',':step_index => 1']),
      'dist_lacks_trigger_progress':'module RM_QuestProgress' not in dist,
      'p10_fresh_offer':"s.heard.includes('iven')" in texts['p10_request'] and 'His noon answer does not supply consent' in texts['p10_request'],
      'p10_promise_is_not_observation':'A signature has set the deadline; no return has been observed.' in texts['p10_request'],
    }
    if not all(bindings.values()): raise ValueError('Inspected continuity binding changed')
    return {'scope':'Selected P04 passage/schema/helper source assay; no RMXP execution or automated literary/consent validation.',
            'p04_causal_passage_offsets':offsets,'quest_rows_per_copy':len(rows[0]),
            'quest_trigger_types':sorted({r['TriggerTipo'] for r in rows[0]}),'bindings':bindings,
            'retained_negative':'Both helpers permit manual completion. DEV additionally has event progress but fresh step_index1 causes target step1 to be ignored by its >= guard; DIST has no progress module. Neither proves actual objective completion.'}


def fingerprint():
    paths={ROOT/name for name in SOURCE_NAMES.values()}|{HERE/'run.py',CSHARP/'global.json'}
    pending=[CSHARP/'NarrativeChecks/NorthStar.NarrativeChecks.csproj']; visited=set()
    while pending:
        project=pending.pop().resolve()
        if project in visited: continue
        visited.add(project); paths.add(project)
        paths.update(p for p in project.parent.rglob('*.cs') if not {'bin','obj'}&set(p.parts))
        tree=ET.parse(project)
        for item in tree.iter():
            if item.tag.split('}')[-1]=='ProjectReference': pending.append((project.parent/item.attrib['Include']).resolve())
            if item.tag.split('}')[-1]=='Compile' and 'Include' in item.attrib:
                path=(project.parent/item.attrib['Include']).resolve()
                if '*' in str(path): raise ValueError('Unbounded compile include requires explicit inventory')
                paths.add(path)
    scene=CSHARP/'Narrative/SCENE.md'
    if scene.exists(): paths.add(scene)
    if any(ROOT not in p.parents for p in paths): raise ValueError('Consumer input outside maintained scope')
    return {p.relative_to(ROOT).as_posix():digest(p) for p in sorted(paths)}


def invoke(command,cwd=CSHARP,timeout=120):
    env=os.environ.copy();env.update(DOTNET_CLI_TELEMETRY_OPTOUT='1',DOTNET_NOLOGO='1')
    result=subprocess.run(command,cwd=cwd,env=env,text=True,capture_output=True,timeout=timeout)
    if result.returncode: raise ValueError(f'Command failed ({result.returncode}): '+(result.stdout+result.stderr)[-4000:])
    return result.stdout


def origin_execution(node='node',module_path=None):
    module=(Path(module_path) if module_path else ROOT/SOURCE_NAMES['p10_request']).as_uri()
    script="""
import assert from 'node:assert/strict';
const {DeferredRequest}=await import(MODULE);
const receipt={handover:{ending:'keep-crossing',decision:'keep-crossing',term:'review-later'}};
const afternoon={ending:null,time:4,elapsed:0,people:4,iven:true,medicine:'supplied',timely:true,recall:false,grain:0,seed:'saved',reserve_used:false};
const route={road:false,ferry:true,iven:true,route:'ferry',grain_per_trip:2,shifts_per_trip:1};
const before=JSON.stringify({receipt,afternoon,route});
const g=new DeferredRequest(receipt,{afternoon,route});g.act('review-settle');
assert.throws(()=>g.act('review-guide'));g.act('review-back');g.act('review-iven');g.act('review-settle');g.act('review-guide');
assert.deepEqual(g.route,route);assert.deepEqual(g.afternoon,afternoon);const committed=g.act('review-dusk');assert.match(committed.text,/no return has been observed/);
assert.equal(g.routeAfter().iven,false);assert.match(g.facts().join(' '),/4 shifts of light/);
assert.equal(JSON.stringify({receipt,afternoon,route}),before);
const paused=new DeferredRequest(receipt,{afternoon,route});paused.act('review-iven');paused.act('review-pause');
const fresh=new DeferredRequest(receipt,{afternoon:{...afternoon,time:2,elapsed:2,grain:2},route});fresh.act('review-settle');
assert.throws(()=>fresh.act('review-guide'));assert.match(fresh.facts().join(' '),/2 shifts of light.*2 of 4 grain/s);
const refusal=new DeferredRequest(receipt,{afternoon,route});refusal.act('review-settle');refusal.act('review-keep');assert.deepEqual(refusal.routeAfter(),route);
console.log(JSON.stringify({schema_version:1,kind:'p10_actual_deferred_request',checks:['prior consent refused','tentative preserves assets','commit changes future route','historical inputs immutable','revisit requires fresh offer and facts','refusal preserves local capacity'],term:g.snapshot().term,return_observed:false,committed_route:g.routeAfter()}));
""".replace('MODULE',json.dumps(module))
    result=json.loads(invoke([node,'--input-type=module','-e',script],cwd=ROOT,timeout=30))
    if result.get('kind')!='p10_actual_deferred_request' or result.get('return_observed') is not False or len(result.get('checks',[]))!=6: raise ValueError('Missing actual P10 controls')
    return result


def origin_mutation_controls(node='node'):
    text=(ROOT/SOURCE_NAMES['p10_request']).read_text()
    mutants=[('stale_consent',"if(a.iven&&r.iven&&s.heard.includes('iven'))",'if(a.iven&&r.iven)'),
             ('promise_as_observation','A signature has set the deadline; no return has been observed.','The signature proves the guide returned safely.')]
    outcomes=[]
    with tempfile.TemporaryDirectory(prefix='narrative-origin-mutants-') as folder:
        for policy,old,new in mutants:
            if text.count(old)!=1: raise ValueError('Controlled origin mutation target changed')
            path=Path(folder)/(policy+'.mjs');path.write_text(text.replace(old,new))
            try: origin_execution(node,path)
            except ValueError as error:
                if 'AssertionError' not in str(error): raise ValueError('Origin mutant failed for an unexpected environment/code reason') from error
                outcomes.append({'policy':policy,'replacement':{'old':old,'new':new},'detected':True,'failure_class':'actual Node assertion; instrument/source fixtures unchanged'})
            else: raise ValueError('Controlled origin continuity defect escaped: '+policy)
    return outcomes


def validate_native(native):
    if not isinstance(native,dict) or type(native.get('schema_version')) is not int or native['schema_version']!=1: raise ValueError('Invalid native schema')
    checks=native.get('checks');controls=native.get('controls')
    if not isinstance(checks,dict) or type(checks.get('passed')) is not int or checks['passed']<1 or type(checks.get('failed')) is not int or checks['failed']!=0: raise ValueError('Missing actual native controls')
    if not isinstance(controls,list) or len(controls)!=checks['passed'] or any(not isinstance(c,str) or not c for c in controls) or len(set(controls))!=len(controls): raise ValueError('Native control identities missing or duplicated')


STATE_FIELDS={'revision','shift','remaining','crates','crates_required','capacity','guide_available','guide_location','surveyed','delivered','returned','status','conversation','term','due_elapsed','delivery_started','receipts','encounter','scope'}
ENCOUNTER_FIELDS={'kind','active','stage','beat','position','health','resolve','required_position','maximum_beats','threat','xp'}

def validate_state(row):
    if not isinstance(row,dict) or set(row)!=STATE_FIELDS: raise ValueError('Complete destination state required')
    for key in ['revision','shift','remaining','crates','crates_required','capacity']:
        if type(row[key]) is not int or row[key]<0: raise ValueError('Invalid state count')
    if row['shift']+row['remaining']!=4 or row['crates']>5 or row['crates_required']!=5 or row['capacity'] not in [1,2]: raise ValueError('Broken daylight/cargo conservation')
    for key in ['guide_available','surveyed','delivered','returned','due_elapsed','delivery_started']:
        if type(row[key]) is not bool: raise ValueError('Invalid destination flag')
    if row['capacity']!=(2 if row['guide_available'] else 1): raise ValueError('Capacity disagrees with guide ownership')
    if row['guide_location'] not in ['local','local-preparing','travelling','unaccounted'] or row['status'] not in ['open','deferred','declined','committed','delivered','failed'] or row['conversation'] not in ['closed','table','terms','ready'] or row['term'] not in [None,'dusk','open','solo']: raise ValueError('Unknown narrative state')
    expected_location='local' if row['guide_available'] else 'local-preparing' if not row['delivery_started'] else 'unaccounted' if row['status']=='failed' else 'travelling'
    if row['guide_location']!=expected_location: raise ValueError('Availability is not physical location')
    if row['due_elapsed']!=(row['status'] in ['committed','failed'] and row['term']=='dusk' and row['remaining']==0 and not row['returned']): raise ValueError('Deadline/result conflated')
    if row['delivered']!=row['returned'] or row['delivered']!=(row['status']=='delivered'): raise ValueError('Completion has no actual delivery/return')
    e=row['encounter']
    if not isinstance(e,dict) or set(e)!=ENCOUNTER_FIELDS or type(e['active']) is not bool or e['kind'] not in ['none','survey','guided','solo']: raise ValueError('Complete real encounter required')
    for key in ['stage','beat','position','health','resolve','required_position','maximum_beats','xp']:
        if type(e[key]) is not int or e[key]<0: raise ValueError('Invalid real encounter observation')
    if not isinstance(e['threat'],str) or not e['threat'] or e['xp'] not in [0,10,25] or e['stage'] not in [0,1]: raise ValueError('Invalid actual encounter state')
    if row['delivered'] and (e['active'] or e['health']==0 or e['xp']!=25 or e['kind'] not in ['guided','solo']): raise ValueError('Narrative completion manufactured without encounter result')
    receipts=row['receipts']
    if not isinstance(receipts,list): raise ValueError('Missing immutable receipts')
    for r in receipts:
        if not isinstance(r,dict) or set(r)!={'kind','revision','shift','crates','term','guide','delivered','returned'}: raise ValueError('Incomplete receipt')
        if r['kind'] not in ['commitment','withdrawal','solo_departure','observed_return','failed_crossing'] or r['term'] not in ['dusk','open','solo'] or r['guide'] not in ['Rill','none']: raise ValueError('Invalid receipt provenance')
        for key in ['revision','shift','crates']:
            if type(r[key]) is not int or r[key]<0 or r[key]>row[key]: raise ValueError('Receipt rewrites future facts')
        if type(r['delivered']) is not bool or type(r['returned']) is not bool or r['delivered']!=r['returned'] or r['delivered']!=(r['kind']=='observed_return'): raise ValueError('Promise receipt claims unobserved result')
    if not isinstance(row['scope'],str) or 'In-session original experiment' not in row['scope']: raise ValueError('Missing production scope limit')


def validate_demo(demo):
    if not isinstance(demo,dict) or type(demo.get('schema_version')) is not int or demo['schema_version']!=1: raise ValueError('Invalid destination schema')
    rows=demo.get('journeys')
    expected={
      'local_refusal':('declined',5,3,False,False,True,None,0,[],['hear']),
      'guided_dusk':('delivered',2,4,True,True,True,'dusk',25,['commitment','observed_return'],[]),
      'solo_delivery':('delivered',0,4,True,True,True,'solo',25,['solo_departure','observed_return'],[]),
      'defer_fresh':('delivered',2,4,True,True,True,'open',25,['commitment','observed_return'],['confirm']),
      'withdraw_before_departure':('deferred',2,2,False,False,True,None,10,['commitment','withdrawal'],[]),
      'failed_delivery':('failed',0,3,False,False,False,'dusk',10,['commitment','failed_crossing'],[]),
      'deadline_not_return':('committed',3,4,False,False,False,'dusk',10,['commitment'],['depart guided']),
      'stale_proposal':('open',2,2,False,False,True,None,10,[],['confirm','offer'])}
    if not isinstance(rows,list) or len(rows)!=len(expected) or any(not isinstance(j,dict) for j in rows): raise ValueError('Missing actual eight journeys')
    names=[j.get('name') for j in rows]
    if any(not isinstance(name,str) for name in names) or set(names)!=set(expected) or len(set(names))!=len(names): raise ValueError('Journey identities missing or repeated')
    for j in rows:
        observations=j.get('observations')
        if not isinstance(observations,list) or not observations: raise ValueError('Missing real command trace')
        previous=None;rejections=[]
        for observation in observations:
            if not isinstance(observation,dict) or set(observation)!={'command','accepted','text','after'} or type(observation['accepted']) is not bool or not isinstance(observation['command'],str) or not observation['command'] or not isinstance(observation['text'],str) or not observation['text']: raise ValueError('Invalid command observation')
            state=observation['after'];validate_state(state)
            if previous is not None:
                if not observation['accepted'] and state!=previous: raise ValueError('Rejected action changed whole gameplay state')
                if state['receipts'][:len(previous['receipts'])]!=previous['receipts']: raise ValueError('Historical receipt rewritten')
                if state['revision']<previous['revision'] or state['shift']<previous['shift'] or state['crates']<previous['crates']: raise ValueError('Historical work/time refunded')
                if observation['accepted'] and observation['command'] in ['offer','terms dusk','terms open']:
                    for key in ['guide_available','crates','shift','term','receipts','delivered','returned']:
                        if state[key]!=previous[key]: raise ValueError('Tentative conversation spent ownership or claimed result')
            if not observation['accepted']: rejections.append(observation['command'])
            previous=state
        validate_state(j.get('final'))
        if previous!=j['final']: raise ValueError('Final state differs from actual last observation')
        state=j['final'];status,crates,shift,delivered,returned,guide,term,xp,kinds,refused=expected[j['name']]
        actual=(state['status'],state['crates'],state['shift'],state['delivered'],state['returned'],state['guide_available'],state['term'],state['encounter']['xp'],[r['kind'] for r in state['receipts']],rejections)
        if actual!=(status,crates,shift,delivered,returned,guide,term,xp,kinds,refused): raise ValueError('Consequential journey/negative outcome changed: '+j['name'])
        if j['name']=='failed_delivery' and (state['guide_location']!='unaccounted' or state['encounter']['health']!=0): raise ValueError('Failed crossing inferred a return or death')
        if j['name']=='deadline_not_return' and (not state['due_elapsed'] or state['delivery_started'] or state['guide_location']!='local-preparing'): raise ValueError('Elapsed deadline manufactured a trip/result')


def run(output,dotnet='dotnet',node='node',compare=None):
    output=Path(output).resolve()
    if output==ROOT or ROOT in output.parents: raise ValueError('Keep outputs outside maintained workspace')
    executable=shutil.which(dotnet); js=shutil.which(node)
    if not executable or not js: raise ValueError('Actual pinned SDK and Node required')
    before=fingerprint();assay=source_assay({k:(ROOT/v).read_text() for k,v in SOURCE_NAMES.items()})
    version=invoke([executable,'--version'],timeout=15).strip()
    node_version=invoke([js,'--version'],timeout=15).strip()
    if node_version!='v24.19.0': raise ValueError('Node differs from exercised CI pin24.19.0')
    if version!=json.loads((CSHARP/'global.json').read_text())['sdk']['version']: raise ValueError('SDK differs from configured pin')
    origin=origin_execution(js)
    origin_mutants=origin_mutation_controls(js)
    invoke([executable,'build','NarrativeChecks/NorthStar.NarrativeChecks.csproj','-c','Release'])
    with tempfile.TemporaryDirectory(prefix='narrative-continuity-') as folder:
        native_path=Path(folder)/'native.json';demo_path=Path(folder)/'demo.json'
        invoke([executable,str(CSHARP/'NarrativeChecks/bin/Release/net10.0/NorthStar.NarrativeChecks.dll'),str(native_path)],timeout=60)
        invoke([executable,str(CSHARP/'Narrative/bin/Release/net10.0/NorthStar.Narrative.dll'),'--demo',str(demo_path)],timeout=60)
        native=json.loads(native_path.read_text());demo=json.loads(demo_path.read_text());validate_native(native);validate_demo(demo)
    if fingerprint()!=before: raise ValueError('Study inputs changed during execution')
    result={'schema_version':1,'kind':'narrative_continuity_contract_study','identities':before,'runtime':{'dotnet_sdk':version,'node':node_version,'unity_executed':False,'windows_executed':False},'source_assay':assay,'origin_execution':origin,'origin_mutation_controls':origin_mutants,'native':native,'destination':demo,'limits':'Selected static P04/legacy assay, actual P10 module controls and original local C# journeys. Synthetic transitions are not participants or literary quality, human agency/enjoyment, final canon, RGSS runtime, production persistence, Unity/Windows/Steam proof.'}
    if compare and json.loads(Path(compare).read_text())!=result: raise ValueError('Executed identities/results differ from comparison')
    output.parent.mkdir(parents=True,exist_ok=True);output.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print('PASS: bounded narrative continuity sources and real destination journeys');return result


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);p.add_argument('--dotnet',default=os.environ.get('HUB_DOTNET','dotnet'));p.add_argument('--node',default='node');p.add_argument('--compare',type=Path);a=p.parse_args()
    try:run(a.output,a.dotnet,a.node,a.compare)
    except (OSError,ValueError,KeyError,subprocess.SubprocessError,ET.ParseError) as e:p.exit(1,f'FAIL: {e}\n')
if __name__=='__main__':main()
