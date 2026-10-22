#!/usr/bin/env python3
"""Actual origin timing contracts and portable C# continuous-work destination."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
ROOT=Path(__file__).resolve().parents[2]
CS=ROOT/'north-star/csharp'
HERE=Path(__file__).resolve().parent
SOURCES=['projects/tokyo80s/dist/'+n for n in ['core.js','rehearsal.js','review.js']]+['north-star/prototype/return_gate.gd','north-star/prototype/controls.gd']

def invoke(command,timeout=120):
 r=subprocess.run(command,cwd=ROOT,text=True,capture_output=True,timeout=timeout)
 if r.returncode:raise ValueError(f'Execution failed ({r.returncode}): '+(r.stdout+r.stderr)[-2500:])
 return r.stdout

def fingerprints():
 paths=[ROOT/p for p in SOURCES]+[HERE/'run.py',HERE/'origin.mjs',CS/'global.json']
 for directory in ['InputTiming','Interaction','InteractionChecks']:
  paths += [p for p in (CS/directory).rglob('*') if p.is_file() and p.suffix in ['.cs','.csproj','.js','.css','.html'] and not {'bin','obj'}&set(p.parts)]
 return {str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(paths)}

def validate(native,demo):
 if type(native.get('schema_version')) is not int or native['schema_version']!=1 or type(native.get('passed')) is not int or native['passed']<1 or type(native.get('failed')) is not int or native['failed']!=0:raise ValueError('Actual native controls required')
 controls=native.get('controls')
 if not isinstance(controls,list) or len(controls)!=native['passed'] or len(set(controls))!=len(controls) or any(not isinstance(x,str) or not x for x in controls):raise ValueError('Native control identities required')
 if demo.get('kind')!='actual_csharp_timed_work' or type(demo.get('schema_version')) is not int or demo['schema_version']!=1:raise ValueError('Real destination schema required')
 names=['grounded_not_goal','completed','release','same_boundary_hit','missing_input','held_resume','optional_grounding']
 for name in names:
  r=demo.get(name)
  if not isinstance(r,dict) or set(r)!={'now_ms','target','required_ms','progress_ms','working','held','paused','need_neutral','health','integrity','catch_a','catch_b','grounded','won','lost','paid','completions','last','last_cause','last_progress_ms','last_cost','events'}:raise ValueError('Complete destination observation required')
  if not isinstance(r['events'],list) or any(not isinstance(x,str) or not x for x in r['events']) or not isinstance(r['last'],str) or not r['last'] or not isinstance(r['last_cause'],str):raise ValueError('Actual event/feedback history required')
  if r['target'] not in ['catch-a','ground','catch-b'] or r['required_ms']!=(1500 if r['target']=='ground' else 1000):raise ValueError('Unknown work contract')
  for key in ['health','integrity','paid','completions','progress_ms','required_ms','now_ms','last_progress_ms','last_cost']:
   if type(r.get(key)) is not int or r[key]<0:raise ValueError('Invalid observed resources/time')
  for key in ['working','held','paused','need_neutral','catch_a','catch_b','grounded','won','lost']:
   if type(r.get(key)) is not bool:raise ValueError('Invalid observed flags')
  if r['health']>3 or r['integrity']>3 or r['paid']>1 or r['progress_ms']>r['required_ms'] or r['grounded']!=(r['paid']==1):raise ValueError('Resource/completion conservation failed')
  if r['won'] and (not r['catch_a'] or not r['catch_b'] or r['health']==0 or r['integrity']==0):raise ValueError('Grounding is not living exit')
 def require(condition):
  if not condition:raise ValueError('Consequential destination/negative outcome changed')
 r=demo['grounded_not_goal'];require(r['grounded'] and r['paid']==1 and not r['won'] and not r['catch_a'] and not r['catch_b'])
 r=demo['completed'];require(r['won'] and r['paid']==1 and r['integrity']==2 and r['completions']==3)
 r=demo['optional_grounding'];require(r['won'] and r['paid']==0 and r['integrity']==3 and r['completions']==2)
 r=demo['release'];require(r['paid']==0 and r['progress_ms']==0 and r['last_cause']=='release' and r['last_progress_ms']==500)
 r=demo['same_boundary_hit'];require(r['paid']==0 and not r['grounded'] and r['health']==2 and r['integrity']==2 and r['last_cause']=='hit')
 r=demo['missing_input'];require(r['paused'] and r['need_neutral'] and r['paid']==0 and r['last_progress_ms']==600)
 r=demo['held_resume'];require(not r['paused'] and r['need_neutral'] and not r['working'] and r['paid']==0)

def run(output,dotnet,compare=None):
 output=Path(output).resolve()
 if output==ROOT or ROOT in output.parents:raise ValueError('Output must remain outside maintained sources')
 before=fingerprints();sdk=invoke([dotnet,'--version']).strip();node=invoke(['node','--version']).strip()
 if sdk!=json.loads((CS/'global.json').read_text())['sdk']['version'] or node!='v24.19.0':raise ValueError('Pinned .NET/Node required')
 origin=json.loads(invoke(['node',str(HERE/'origin.mjs'),str(ROOT/'projects/tokyo80s/dist')]))
 if len(origin.get('checks',[]))!=13:raise ValueError('Missing actual origin observations')
 mutants=[]
 with tempfile.TemporaryDirectory(prefix='input-origin-') as temp:
  dest=Path(temp);(dest/'package.json').write_text('{"type":"module"}')
  for name,filename,old,new in [('paused_engagement','core.js','n.engaged=false;n.regrabUntil=Infinity;','n.regrabUntil=Infinity;'),('wrong_clock','rehearsal.js','time: (n.time - cueStart) / rate','time: (n.time - cueStart)')]:
   for source in ['core.js','rehearsal.js','review.js']:shutil.copyfile(ROOT/'projects/tokyo80s/dist'/source,dest/source)
   p=dest/filename;text=p.read_text()
   if text.count(old)!=1:raise ValueError('Controlled mutation target changed')
   p.write_text(text.replace(old,new))
   try:invoke(['node',str(HERE/'origin.mjs'),str(dest)])
   except ValueError as e:
    if 'AssertionError' not in str(e):raise ValueError('Unexpected mutant environment failure') from e
    mutants.append({'policy':name,'detected':True,'old':old,'new':new,'classification':'actual staged source assertion; no original source changed'})
   else:raise ValueError('Timing mutant escaped')
  invoke([dotnet,'build',str(CS/'InteractionChecks/NorthStar.InteractionChecks.csproj'),'-c','Release'])
  nativepath=dest/'native.json';demopath=dest/'demo.json'
  invoke([dotnet,str(CS/'InteractionChecks/bin/Release/net10.0/NorthStar.InteractionChecks.dll'),str(nativepath)])
  invoke([dotnet,str(CS/'Interaction/bin/Release/net10.0/NorthStar.Interaction.dll'),'--demo',str(demopath)])
  native=json.loads(nativepath.read_text());demo=json.loads(demopath.read_text());validate(native,demo)
 gate=(ROOT/'north-star/prototype/return_gate.gd').read_text();bindings={
 'source_catch_1000_ground_1500':'WORK_TIME:=1.0' in gate and 'GROUND_TIME:=1.5' in gate,
 'source_paid_once_and_goal_separate':'game.cargo-=GROUND_COST;grounded=true' in gate and 'return raised[0] and raised[1]' in gate,
 'source_harm_precedes_progress':gate.index('elif game.hp<previous_hp:')<gate.index('progress+=clampf(delta,0,0.05)'),
 'source_quarantine':'func quarantine()' in (ROOT/'north-star/prototype/controls.gd').read_text()}
 if not all(bindings.values()) or fingerprints()!=before:raise ValueError('Inspected source/input binding changed')
 result={'schema_version':1,'kind':'input_timing_destination_study','identities':before,'runtime':{'dotnet':sdk,'node':node},'origin':origin,'origin_mutants':mutants,'source_bindings':bindings,'native':native,'destination':demo,'limits':'Actual P03 modules and controlled mutants; selected static Godot contracts; independently executed C# integer-clock subset, not full combat parity. Rhythm regrab remains distinct from dangerous-world work cancellation. No physical latency, listening, human accessibility/readability, Unity/Windows/Steam or production network claims.'}
 if compare and json.loads(Path(compare).read_text())!=result:raise ValueError('Exact executed identities/results differ')
 output.parent.mkdir(parents=True,exist_ok=True);output.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');return result
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--dotnet',default=os.environ.get('HUB_DOTNET','dotnet'));p.add_argument('--output',type=Path,required=True);p.add_argument('--compare',type=Path);a=p.parse_args()
 try:r=run(a.output,a.dotnet,a.compare)
 except (OSError,ValueError,KeyError,subprocess.SubprocessError) as e:p.exit(1,'FAIL: '+str(e)+'\n')
 print('PASS: actual origin timing, two detected mutants and '+str(r['native']['passed'])+' C# work controls')
