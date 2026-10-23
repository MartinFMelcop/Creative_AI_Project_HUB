#!/usr/bin/env python3
"""Actual preserved P08 synthesis, PCM contracts and native source audio lifecycle."""
import argparse
from array import array
import sys
import hashlib
import json
import math
from pathlib import Path
import shutil
import subprocess
import tempfile
import wave
ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
ORIGIN=ROOT/'projects/veil-arena'

def pcm(path):
 with wave.open(str(path),'rb') as w:
  if (w.getnchannels(),w.getsampwidth(),w.getframerate(),w.getcomptype())!=(1,2,44100,'NONE'):raise ValueError('PCM mono16/44100 required')
  n=w.getnframes();samples=array('h',w.readframes(n))
  if sys.byteorder!='little':samples.byteswap()
 if len(samples)!=n or n==0:raise ValueError('PCM length')
 return samples

def signal_checks(samples,frames):
 if len(samples)!=frames:raise ValueError('Frame count')
 peak=max(abs(int(x)) for x in samples)
 if peak<1 or peak>=32767:raise ValueError('Peak clipping/silence')
 if abs(int(samples[0]))>1 or abs(int(samples[-1]))>1:raise ValueError('Endpoint discontinuity')
 return {'frames':len(samples),'peak_integer':peak,'rms_integer':round(math.sqrt(sum(int(x)**2 for x in samples)/len(samples)),6),'first':int(samples[0]),'last':int(samples[-1])}

def invoke(cmd,cwd,timeout=120):
 r=subprocess.run(cmd,cwd=cwd,text=True,capture_output=True,timeout=timeout)
 if r.returncode:raise ValueError('Execution/environment failed: '+(r.stdout+r.stderr)[-2500:])
 return r.stdout

def fingerprints():
 catalog=json.loads((ORIGIN/'media/audio-catalog.json').read_text())
 paths=[ORIGIN/p for p in catalog['files']]+[ORIGIN/p for p in ['media/audio-catalog.json','media/provenance.json','sound.gd','tools/render_audio.py']]+[HERE/'run.py',HERE/'native.gd']
 return {str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(paths)}

def run(output,godot='godot',compare=None,producer=False):
 output=Path(output).resolve()
 if output==ROOT or ROOT in output.parents:raise ValueError('Output must remain outside maintained sources')
 identities=fingerprints();catalog=json.loads((ORIGIN/'media/audio-catalog.json').read_text());observations=[]
 for name,spec in catalog['files'].items():
  p=ORIGIN/name
  if hashlib.sha256(p.read_bytes()).hexdigest()!=spec['sha256']:raise ValueError('Preserved catalog identity mismatch')
  if p.suffix=='.wav':
   samples=pcm(p);expected=spec.get('frames',round(spec['duration_seconds']*44100));observations.append({'path':name,**signal_checks(samples,expected)})
 masters=[pcm(ORIGIN/'media/masters'/f'{n}.wav') for n in ['courtyard','fracture']]
 if any(len(s)!=24*44100 for s in masters) or catalog['music']['bpm']!=80 or catalog['music']['bars']*catalog['music']['beats_per_bar']*60/catalog['music']['bpm']!=24:raise ValueError('Declared transport mismatch')
 negatives=[]
 for name,changed in [('endpoint_step',list(masters[0])),('gain_clipping',[min(32767,max(-32768,int(x)*4)) for x in masters[0]]),('missing_frame',masters[0][:-1])]:
  if name=='endpoint_step':changed[-1]=1000
  try:signal_checks(changed,len(masters[0]))
  except ValueError as e:negatives.append({'policy':name,'detected':True,'reason':str(e),'classification':'controlled in-memory PCM defect'})
  else:raise ValueError('PCM negative escaped')
 with tempfile.TemporaryDirectory(prefix='audio-origin-') as temp:
  stage=Path(temp);(stage/'tools').mkdir();(stage/'media').mkdir()
  shutil.copyfile(ORIGIN/'tools/render_audio.py',stage/'tools/render_audio.py')
  reproduction=[]
  if producer:
   invoke(['python3',str(stage/'tools/render_audio.py')],stage)
   produced=json.loads((stage/'media/audio-catalog.json').read_text());reproduction=[]
   for name in catalog['files']:
    equal=hashlib.sha256((stage/name).read_bytes()).hexdigest()==catalog['files'][name]['sha256']
    reproduction.append({'path':name,'identical':equal,'classification':'exact source-producer reproduction' if equal else 'retained producer/platform encoding difference; not silently repaired'})
    if name.endswith('.wav') and not equal:raise ValueError('Deterministic PCM producer mismatch')
  # Source execution uses preserved runtime bytes, not regenerated substitutions.
  for name in catalog['files']:
   p=stage/name;p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ORIGIN/name,p)
  shutil.copyfile(ORIGIN/'sound.gd',stage/'sound.gd');shutil.copyfile(HERE/'native.gd',stage/'native.gd')
  (stage/'project.godot').write_text('[application]\nconfig/name="Isolated actual audio source"\n[rendering]\nrenderer/rendering_method="gl_compatibility"\n')
  version=invoke([godot,'--version'],stage).strip()
  invoke([godot,'--headless','--path',str(stage),'--editor','--import','--quit'],stage)
  stdout=invoke([godot,'--headless','--path',str(stage),'--script','native.gd'],stage)
  lines=[s for s in stdout.splitlines() if s.startswith('AUDIO_SOURCE_NATIVE ')]
  if len(lines)!=1:raise ValueError('Actual native result missing')
  native=json.loads(lines[0].removeprefix('AUDIO_SOURCE_NATIVE '))
 if fingerprints()!=identities:raise ValueError('Source changed during execution')
 result={'schema_version':1,'kind':'actual_audio_source_study','identities':identities,'runtime':{'godot':version,'python':'standard-library PCM/native method'},'pcm':observations,'producer_contract':'Optional --producer executes NumPy/FFmpeg source regeneration and records sibling .producer.json; canonical source method requires neither NumPy nor regeneration.','negative_pcm_controls':negatives,'native':{'controls':native['controls'],'driver':native['driver'],'measurements_contract':'Actual variable mixer values retained in sibling .measurements.json; exact comparison applies classifications/identities, not nondeterministic scheduling samples.'},'limits':'Actual preserved source and post-limiter digital mixer capture, not physical listening, cue recognition, preference, speaker/headphone quality, latency, Unity, Windows or Steam. Equal PCM transport length is not phase proof; native locked position observations supply bounded alignment controls.'}
 if compare and json.loads(Path(compare).read_text())!=result:raise ValueError('Exact identities/results differ')
 output.parent.mkdir(parents=True,exist_ok=True);output.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');
 if producer:output.with_suffix('.producer.json').write_text(json.dumps(reproduction,indent=2,sort_keys=True)+'\n')
 output.with_suffix('.measurements.json').write_text(json.dumps(native['measurements'],indent=2,sort_keys=True)+'\n');return result
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--output',required=True,type=Path);p.add_argument('--compare',type=Path);p.add_argument('--godot',default='godot');p.add_argument('--producer',action='store_true');a=p.parse_args()
 try:r=run(a.output,a.godot,a.compare,a.producer)
 except (OSError,ValueError,KeyError,subprocess.SubprocessError) as e:p.exit(1,'FAIL: '+str(e)+'\n')
 print('PASS:16 actual PCM files, 3 PCM negatives and '+str(len(r['native']['controls']))+' actual mixer/lifecycle controls')
