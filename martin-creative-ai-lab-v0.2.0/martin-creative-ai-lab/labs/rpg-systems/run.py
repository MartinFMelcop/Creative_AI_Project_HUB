#!/usr/bin/env python3
"""Assay preserved progression contracts against the actual North Star C# domain.

No historical RGSS runtime, Unity Editor, Windows player or human study is implied.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

HERE = Path(__file__).resolve().parent
LAB = HERE.parents[1]
SNAPSHOT = LAB / 'references/rave-master/snapshots/36af1651271422ae33856e8b5d7b45702215f165/source'
DOMAIN = LAB / 'north-star/csharp'
SOURCE_NAMES = {
    'thresholds': 'RM_CORE/DATA/CORE/PLAYER_LEVEL_XP_TABLE.csv',
    'budgets': 'RM_CORE/DATA/CORE/PLAYER_LEVEL_STAT_BUDGET.csv',
    'goldens': 'RM_QA/DATA/QA/TEST_PLAYER_LEVEL_RUNTIME.csv',
    'reported_results': 'RM_QA/DATA/QA/RPT_PLAYER_LEVEL_RUNTIME.csv',
    'runtime': 'RM_ACT1/DATA/DEV/RGSS/RM_PLAYER_LEVEL_RUNTIME.rb',
    'shipped_budgets': 'RM_DIST/RMXP_BASE/Data/RM_CSV/PLAYER_LEVEL_STAT_BUDGET.csv',
    'shipped_runtime': 'RM_DIST/RMXP_BASE/ScriptsCustom/RM_PLAYER_LEVEL_RUNTIME.rb',
}
RESULT_FIELDS = {'id','total_xp','level','levels_gained','main_gained','hp_gained','sp_gained'}


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read_rows(text):
    reader = csv.DictReader(io.StringIO(text))
    if not reader.fieldnames or len(set(reader.fieldnames)) != len(reader.fieldnames):
        raise ValueError('Missing or duplicate CSV headers')
    rows = list(reader)
    if not rows or any(None in row or None in row.values() for row in rows):
        raise ValueError('Incomplete CSV rows')
    return reader.fieldnames, rows


def integer(value, label):
    if not isinstance(value, str) or not re.fullmatch(r'0|[1-9][0-9]*', value):
        raise ValueError('Expected nonnegative integer '+label)
    return int(value)


def parse_tables(threshold_text, budget_text):
    threshold_header, thresholds = read_rows(threshold_text)
    budget_header, budgets = read_rows(budget_text)
    if not {'Level','TotalXP','XPToNext'} <= set(threshold_header):
        raise ValueError('Missing threshold contract')
    if not {'Level','MainStatPoints','HP_Gain','SP_Gain'} <= set(budget_header):
        raise ValueError('Missing budget contract (HP_Gain/SP_Gain required)')
    if len(thresholds) != len(budgets) or not 2 <= len(thresholds) <= 4096:
        raise ValueError('Threshold/budget row counts differ or exceed bounds')
    levels = []
    for index, (threshold, budget) in enumerate(zip(thresholds,budgets),1):
        if integer(threshold['Level'],'threshold level') != index or integer(budget['Level'],'budget level') != index:
            raise ValueError('Levels must be complete, ordered and unique')
        row = {'level': index, 'total_xp': integer(threshold['TotalXP'],'total XP'),
               'main': integer(budget['MainStatPoints'],'points'),
               'hp': integer(budget['HP_Gain'],'health'), 'sp': integer(budget['SP_Gain'],'resolve')}
        if row['total_xp'] > 10**12 or index==1 and row['total_xp']!=0:
            raise ValueError('Invalid first threshold or total XP bound')
        if levels and row['total_xp'] <= levels[-1]['total_xp']:
            raise ValueError('Thresholds must increase strictly')
        levels.append(row)
    for index, threshold in enumerate(thresholds):
        expected = levels[index+1]['total_xp']-levels[index]['total_xp'] if index+1<len(levels) else 0
        if integer(threshold['XPToNext'],'XPToNext') != expected:
            raise ValueError('XPToNext does not match adjacent thresholds')
    return levels


def level_at(levels, xp, strict=False):
    # Independent linear reference; destination uses its own lookup/state transitions.
    result = 1
    for row in levels[1:]:
        if row['total_xp'] < xp if strict else row['total_xp'] <= xp:
            result = row['level']
    return result


def reference(levels, case, strict=False):
    start = case['start_xp']; total = start+sum(case['awards'])
    old = level_at(levels,start,strict); new = level_at(levels,total,strict)
    gained = levels[old:new]
    return {'id': case['id'], 'total_xp':total, 'level':new, 'levels_gained':new-old,
            'main_gained':sum(row['main'] for row in gained),
            'hp_gained':sum(row['hp'] for row in gained), 'sp_gained':sum(row['sp'] for row in gained)}


def make_protocol(levels, golden_text):
    header, raw = read_rows(golden_text)
    required = {'TestID','StartTotalXP','StartLevel','AddXP_List','ExpectedLevel','ExpectedTotalXP',
                'ExpectedLevelUps','ExpectedUnspentMainStatPoints','ExpectedBonusHP','ExpectedBonusSP'}
    if not required <= set(header):raise ValueError('Missing historical golden fields')
    cases=[]; expected=[]
    for row in raw:
        case={'id':'golden/'+row['TestID'],'start_xp':integer(row['StartTotalXP'],'start XP'),
              'awards':[integer(value,'award') for value in row['AddXP_List'].split(';')]}
        if level_at(levels,case['start_xp']) != integer(row['StartLevel'],'start level'):
            raise ValueError('Golden initial level disagrees with its threshold')
        observed=reference(levels,case)
        golden={'id':case['id'],'total_xp':integer(row['ExpectedTotalXP'],'expected XP'),
                'level':integer(row['ExpectedLevel'],'expected level'),
                'levels_gained':integer(row['ExpectedLevelUps'],'expected gains'),
                'main_gained':integer(row['ExpectedUnspentMainStatPoints'],'expected points'),
                'hp_gained':integer(row['ExpectedBonusHP'],'expected health'),
                'sp_gained':integer(row['ExpectedBonusSP'],'expected resolve')}
        if observed != golden:raise ValueError('Historical golden contradicts actual source tables: '+case['id'])
        cases.append(case);expected.append(golden)
    golden_count=len(cases)
    for row in levels[1:]:
        for offset in (-1,0,1):
            case={'id':f"boundary/{row['level']}/{offset:+d}",'start_xp':0,'awards':[row['total_xp']+offset]}
            cases.append(case);expected.append(reference(levels,case))
    for original in cases[:golden_count]:
        parts=[]
        for value in original['awards']:
            part=value//3;parts.extend([part,part,value-2*part])
        case={'id':'partition/'+original['id'].split('/',1)[1],'start_xp':original['start_xp'],'awards':parts}
        cases.append(case);expected.append(reference(levels,case))
    if len({case['id'] for case in cases})!=len(cases):raise ValueError('Case IDs must be unique')
    return {'schema_version':1,'levels':levels,'cases':cases}, expected, golden_count


def validate_results(value, expected):
    if not isinstance(value,dict) or set(value)!={'schema_version','rows'} or type(value['schema_version']) is not int or value['schema_version']!=1:
        raise ValueError('Unexpected destination schema')
    rows=value['rows']
    if not isinstance(rows,list) or len(rows)!=len(expected):raise ValueError('Incomplete destination observations')
    for row,golden in zip(rows,expected):
        if not isinstance(row,dict) or set(row)!=RESULT_FIELDS:raise ValueError('Unexpected destination fields')
        if not isinstance(row['id'],str) or any(type(row[key]) is not int for key in RESULT_FIELDS-{'id'}):
            raise ValueError('Wrong destination value types')
        if row!=golden:raise ValueError('Destination differs from controlled expectation: '+str(row['id']))


def source_binding_assay(runtime_text, budget_text, expected, golden_count):
    header,_=read_rows(budget_text)
    keys={}
    for stat in ['hp','sp']:
        match=re.search(r'@@'+stat+r'_by_level\[lvl\]\s*=\s*r\["([^"]+)"\]\.to_i',runtime_text)
        if not match:raise ValueError('Cannot identify actual legacy budget binding')
        keys[stat]=match.group(1)
    missing=sorted(value for value in keys.values() if value not in header)
    mismatches=[]
    for row in expected[:golden_count]:
        projected={stat:0 if keys[stat] not in header else row[stat+'_gained'] for stat in ['hp','sp']}
        if projected['hp']!=row['hp_gained'] or projected['sp']!=row['sp_gained']:
            mismatches.append({'id':row['id'],'projected_hp':projected['hp'],'projected_sp':projected['sp'],
                               'expected_hp':row['hp_gained'],'expected_sp':row['sp_gained']})
    return {'method':'Static source-binding assay with Ruby nil.to_i semantics; not historical RGSS execution',
            'keys':keys,'missing_columns':missing,'golden_mismatches':mismatches,
            'decision':'REJECTED' if missing else 'UNRESOLVED'}


def fingerprint():
    domain_names=sorted(p for p in DOMAIN.rglob('*') if p.is_file() and p.suffix in {'.cs','.csproj','.json','.props','.asmdef'} and not {'bin','obj'} & set(p.parts))
    return {'sources':{name:digest(SNAPSHOT/path) for name,path in SOURCE_NAMES.items()},
            'instrument':{'run.py':digest(HERE/'run.py')},
            'destination':{p.relative_to(LAB).as_posix():digest(p) for p in domain_names}}


def invoke(command, cwd, env, timeout=120):
    result=subprocess.run(command,cwd=cwd,env=env,capture_output=True,text=True,timeout=timeout)
    if result.returncode:raise ValueError(f'Command failed ({result.returncode}): '+(result.stdout+result.stderr)[-5000:])
    return result.stdout


def run(output, dotnet='dotnet', compare=None):
    output=Path(output).resolve()
    if HERE==output or HERE in output.parents or SNAPSHOT==output or SNAPSHOT in output.parents or DOMAIN==output or DOMAIN in output.parents:
        raise ValueError('Keep execution outputs outside source inputs')
    executable=shutil.which(dotnet)
    if not executable:raise ValueError('Pinned .NET SDK executable unavailable; set HUB_DOTNET or --dotnet')
    before=fingerprint()
    text={name:(SNAPSHOT/path).read_text(encoding='utf-8-sig') for name,path in SOURCE_NAMES.items()}
    levels=parse_tables(text['thresholds'],text['budgets'])
    protocol, expected, golden_count=make_protocol(levels,text['goldens'])
    reported_header,reported=read_rows(text['reported_results'])
    if len(reported)!=golden_count or any(row.get('Result')!='PASS' for row in reported):
        raise ValueError('Preserved historical report changed; inspect its claims separately')
    assay=source_binding_assay(text['runtime'],text['budgets'],expected,golden_count)
    shipped_assay=source_binding_assay(text['shipped_runtime'],text['shipped_budgets'],expected,golden_count)
    if assay['keys']!=shipped_assay['keys'] or assay['missing_columns']!=shipped_assay['missing_columns']:
        raise ValueError('DEV and delivered legacy source contracts disagree')
    # Negative calibration changes equality only; it is a reference mutant, not a claim
    # that a modified C# binary or the original RPG Maker game executed.
    mutant=[reference(levels,case,strict=True) for case in protocol['cases']]
    mutant_failures=[row['id'] for row,good in zip(mutant,expected) if row!=good]
    if len(mutant_failures)<len(levels)-1:raise ValueError('Boundary controls do not reject off-by-one reference mutation')
    with tempfile.TemporaryDirectory(prefix='rpg-progression-') as folder:
        scratch=Path(folder);env=os.environ.copy();env['DOTNET_CLI_TELEMETRY_OPTOUT']='1';env['DOTNET_NOLOGO']='1'
        version=invoke([executable,'--version'],DOMAIN,env,15).strip()
        pin=json.loads((DOMAIN/'global.json').read_text())['sdk']['version']
        if version!=pin:raise ValueError('Actual .NET SDK differs from configured pin')
        invoke([executable,'build','Checks/NorthStar.Checks.csproj','-c','Release'],DOMAIN,env)
        source=scratch/'input.json';destination=scratch/'output.json'
        source.write_text(json.dumps(protocol,separators=(',',':'))+'\n')
        assemblies=list((DOMAIN/'Checks/bin/Release').glob('*/NorthStar.Checks.dll'))
        if len(assemblies)!=1:raise ValueError('Expected one built NorthStar.Checks.dll consumer')
        invoke([executable,str(assemblies[0]),'study',str(source),str(destination)],DOMAIN,env,30)
        observed=json.loads(destination.read_text());validate_results(observed,expected)
    if fingerprint()!=before:raise ValueError('Executed source or destination changed during study')
    result={'schema_version':1,'kind':'rpg_progression_contract_study','runtime':{'dotnet_sdk':version,'unity_executed':False,'windows_executed':False},
            'identities':before,'protocol_sha256':hashlib.sha256(json.dumps(protocol,sort_keys=True,separators=(',',':')).encode()).hexdigest(),
            'checks':{'historical_goldens':golden_count,'threshold_neighbors':3*(len(levels)-1),'partition_controls':golden_count,
                      'destination_rows':len(observed['rows']),'failed':0},
            'legacy_binding_assay':assay,'delivered_legacy_binding_assay':shipped_assay,
            'historical_report':{'recorded_passes':len(reported),'reexecuted':False,'scope':'Preserved report claims do not establish the execution path or resolve current helper/table incompatibility'},
            'off_by_one_reference_mutant':{'rejected_rows':len(mutant_failures),'ids':mutant_failures},
            'destination_rows':observed['rows'],
            'decisions':{'legacy_direct_header_adapter':'REJECTED','validated_threshold_and_budget_contract':'INTEGRATED into actual engine-independent North Star C# domain study consumer','legacy_180_level_pacing_and_canon':'UNRESOLVED'},
            'limits':'Preserved helper/table binding assay plus actual engine-independent C# execution. No complete historical RGSS game, Unity Editor, Windows build, networking, balance, final progression canon, independent player or empirical population claim.'}
    if compare and json.loads(Path(compare).read_text())!=result:raise ValueError('Comparison differs in executed inputs or observations')
    output.parent.mkdir(parents=True,exist_ok=True);output.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(f"PASS: {len(observed['rows'])} C# destination cases; {golden_count} legacy header mismatches retained; {len(mutant_failures)} off-by-one reference mutants rejected")
    return result


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--dotnet',default=os.environ.get('HUB_DOTNET','dotnet'))
    parser.add_argument('--output',type=Path,required=True);parser.add_argument('--compare',type=Path)
    args=parser.parse_args(argv)
    try:run(args.output,args.dotnet,args.compare)
    except (OSError,ValueError,KeyError,subprocess.SubprocessError) as error:parser.exit(1,f'FAIL: {error}\n')
    return 0

if __name__=='__main__':raise SystemExit(main())
