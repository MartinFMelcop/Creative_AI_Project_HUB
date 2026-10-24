#!/usr/bin/env python3
"""Literal source phase-mask assay; never interprets locations as observed presence."""
from __future__ import annotations
import argparse,csv,hashlib,json,re,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
BASE='references/rave-master/snapshots/36af1651271422ae33856e8b5d7b45702215f165/source/'
PATHS={
 'schedules':BASE+'RM_ACT1/DATA/DEV/NPC_SCHEDULE_RULES.csv',
 'phases':BASE+'RM_CORE/DATA/CORE/TIME_PHASES_MASTER.csv',
 'bundled_phases':BASE+'RM_DIST/RMXP_BASE/Data/RM_CSV/TIME_PHASES_MASTER.csv',
 'state':BASE+'RM_ACT1/DATA/DEV/NPC_STATE.csv',
 'bundled_state':BASE+'RM_DIST/RMXP_BASE/Data/RM_CSV/NPC_STATE.csv',
 'dialogue':BASE+'RM_ACT1/DATA/DEV/RGSS/RM_DIALOGUE_SCORING_RUNTIME.rb',
}
SCHEDULE_HEADER=['IdNPC','Nome','TagRotina','PhaseMask','LocalPreferido','ChaveMapa_Base','Observacao']
PHASE_HEADER=['PhaseID','Ordem','DuracaoSeg','SwitchDia','SwitchNoite','LuzCasasEstado','ToneR','ToneG','ToneB','ToneGray','NPC_Rua_Densidade','WorkersEstado']
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def table(path,header):
 with path.open(encoding='utf-8-sig',newline='') as stream:rows=list(csv.reader(stream,strict=True))
 if not rows or rows[0]!=header:raise ValueError('Unexpected ordered CSV header')
 if any(len(row)!=len(header) for row in rows[1:]):raise ValueError('CSV row width mismatch')
 return [dict(zip(header,row)) for row in rows[1:]]
def cases(root=ROOT):
 phases=table(root/PATHS['phases'],PHASE_HEADER)
 if len(phases)!=5 or [r['Ordem'] for r in phases]!=list('01234') or [r['PhaseID'] for r in phases]!=['PH_DAY','PH_AFTERNOON_START','PH_NIGHT_START','PH_NIGHT_PEAK','PH_DAWN']:raise ValueError('Expected exact five ordered unique phases')
 rows=table(root/PATHS['schedules'],SCHEDULE_HEADER)
 if len(rows)!=27:raise ValueError('Expected27 actual schedule rows')
 seen=set();result=[]
 for row in rows:
  identity=row['IdNPC']
  if not re.fullmatch(r'NPC-\d{4}',identity) or identity in seen:raise ValueError('Invalid/duplicate NPC identity')
  seen.add(identity);tokens=row['PhaseMask'].split('|')
  if not tokens or any(t not in list('01234') for t in tokens) or len(set(tokens))!=len(tokens):raise ValueError('Invalid/duplicate/unknown phase mask')
  mask=[int(t) for t in tokens]
  for phase in range(5):result.append({'id':identity+':p'+str(phase),'phase':phase,'mask':mask,'expected':str(phase) in tokens})
 return {'schema':1,'cases':result},rows,phases
def verify(actual,expected):
 if not isinstance(actual,dict) or set(actual)!={'schema','case_count','passed','failed','results'} or type(actual['schema'])is not int or actual['schema']!=1:raise ValueError('Unexpected result schema')
 results=actual['results']
 if type(actual['case_count'])is not int or actual['case_count']!=len(expected['cases']) or type(actual['passed'])is not int or actual['passed']!=len(expected['cases']) or type(actual['failed'])is not int or actual['failed']!=0:raise ValueError('False source result totals')
 if not isinstance(results,list) or len(results)!=len(expected['cases']):raise ValueError('Missing/excess source results')
 for row,case in zip(results,expected['cases']):
  if not isinstance(row,dict) or set(row)!={'id','allowed','expected','passed'} or row['id']!=case['id'] or type(row['allowed'])is not bool or row['allowed']!=case['expected'] or type(row['expected'])is not bool or row['expected']!=case['expected'] or row['passed']is not True:raise ValueError('False/reordered source eligibility result')
 return len(results)
def identities(root):return {name:{'local_path':path,'sha256':digest(root/path),'size_bytes':(root/path).stat().st_size} for name,path in PATHS.items()}
def inspect(root=ROOT):
 initial=identities(root)
 fixture,rows,phases=cases(root)
 if initial!=identities(root):raise ValueError('Source changed while interpreting source rows')
 workers=[r['IdNPC'] for r in rows if r['TagRotina']=='Worker' and '1' in r['PhaseMask'].split('|')]
 return {'source_artifacts':initial,'schedule_rows':len(rows),'phase_rows':len(phases),'literal_mask_cases':len(fixture['cases']),'allowed_cases':sum(c['expected'] for c in fixture['cases']),'cases':fixture,'observed_position':'UNKNOWN: masks and descriptive locations do not observe a body or prove completed work.','retained_ambiguities':[
 {'id':'NPC-0006-phase1','observation':"PhaseMask contains1 while LocalPreferido places phase1 at home; this is not resolved as work availability or physical presence."},
 {'id':'worker-phase1-global-rest','npcs':workers,'observation':'Worker masks include1 while TIME_PHASES_MASTER phase1 WorkersEstado is DESCANSANDO. Neither file establishes override precedence.'},
 {'id':'worker-phase4-heuristic','observation':'Worker masks and dawn work allow4 while repeated notes say outside street during phases2–4; retain the wording conflict.'},
 {'id':'quest-cutscene-ownership','observation':'Unique rows and initial-scene notes explicitly allow cutscene/quest control. PhaseMask does not override an actual authoritative activity.'}],
 'scope':'Static literal source data and explicit counterexample models, not historical Ruby/RMXP or complete NPC scheduling.'}
def counterexamples():
 # Controlled original model: advertised hours never replace explicit activity or events.
 traces=[{'scheduled':True,'authority':'away','accepted_work_events':0,'expected_available':False,'expected_completed':0},
         {'scheduled':True,'authority':'present','accepted_work_events':0,'expected_available':True,'expected_completed':0}]
 observations=[]
 for trace in traces:
  actual_available=trace['scheduled'] and trace['authority']=='present'
  actual_completed=trace['accepted_work_events']
  if actual_available!=trace['expected_available'] or actual_completed!=trace['expected_completed']:raise ValueError('Authority model contradicts declared observations')
  observations.append({**trace,'authority_policy_available':actual_available,'authority_policy_completed':actual_completed,
   'mask_presence_policy_available':trace['scheduled'],'mask_completion_policy_completed':int(trace['scheduled'])})
 presence_errors=sum(r['mask_presence_policy_available']!=r['expected_available'] for r in observations)
 completion_errors=sum(r['mask_completion_policy_completed']!=r['expected_completed'] for r in observations)
 if presence_errors!=1 or completion_errors!=2:raise ValueError('Negative policies were not discriminated')
 return {'kind':'controlled original counterexample models, not historical runtime execution',
  'observations':observations,'mask_presence_policy_errors':presence_errors,'mask_completion_policy_errors':completion_errors}
def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True);parser.add_argument('--responses',type=Path);args=parser.parse_args()
 output=args.output.resolve()
 if output.is_relative_to(ROOT):parser.error('Outputs must remain outside maintained sources')
 result=inspect();fixture=result.pop('cases');result['schema']=1;result['cases']=fixture['cases'];recorded=json.loads((Path(__file__).with_name('source-cases.json')).read_text())
 if fixture!=recorded:raise ValueError('Canonical source cases differ from current source data')
 if args.responses:result['actual_csharp_cases']=verify(json.loads(args.responses.read_text()),fixture)
 result['negative_policies']=counterexamples()
 if result['source_artifacts']!=inspect()['source_artifacts']:raise ValueError('Source changed during assay')
 output.parent.mkdir(parents=True,exist_ok=True);output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'source_cases':len(fixture['cases']),'actual_csharp_cases':result.get('actual_csharp_cases'),'source_stable':True}))
if __name__=='__main__':
 try:main()
 except (ValueError,OSError,KeyError,json.JSONDecodeError) as error:raise SystemExit('FAIL: '+str(error))
