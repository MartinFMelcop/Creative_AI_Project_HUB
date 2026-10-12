#!/usr/bin/env python3
"""Verify actual audio bytes and their musical/chart contract, without claiming taste."""
from pathlib import Path
import hashlib
import json
import math
import struct
import wave
root=Path(__file__).resolve().parents[1]
provenance=json.loads((root/'media/provenance.json').read_text())
for path,digest in provenance['files'].items():
 assert hashlib.sha256((root/path).read_bytes()).hexdigest()==digest,path
with wave.open(str(root/'media/midnight-signal.wav'),'rb') as w:
 assert (w.getnchannels(),w.getsampwidth(),w.getframerate())==(2,2,44100)
 assert w.getnframes()==69*44100
 samples=memoryview(w.readframes(w.getnframes())).cast('h')
 peak=max(abs(n) for n in samples)
 assert 0<peak<32767
 assert any(samples[-88200:]),'The ending has actual audio.'
 rms=math.sqrt(sum(float(n*n) for n in samples)/len(samples))/32768
 assert -30<20*math.log10(rms)<-10
track=json.loads((root/'dist/track.json').read_text())
assert track['duration']==69 and track['bpm']==120
for name,notes in track['charts'].items():
 assert len(notes)==provenance['notes'][name]
 assert len({(n['time'],n['lane']) for n in notes})==len(notes)
 assert all(3<=n['time']<67 and 0<=n['lane']<4 for n in notes)
 assert notes==sorted(notes,key=lambda n:(n['time'],n['lane']))
 for n in notes:
  beat=(n['time']-3)/.5
  bar=math.floor((beat+1e-7)/4)
  within=beat-4*bar
  lane=n['lane']
  if lane==0: assert abs(within*2-round(within*2))<1e-6
  elif lane==1: assert abs(within)<1e-6
  elif lane==2:
   assert bar>=4
   phrase=track['sourceScore']['leadPhrases'][(bar-4)%8]
   assert any(abs(within-onset)<1e-6 for onset,_ in phrase)
  else: assert min(abs(within-1),abs(within-3))<1e-6
print(f'PASS: real 69s stereo PCM master, matching OGG/chart hashes, no clipped PCM samples; {provenance["notes"]}.')

rain=json.loads((root/'media/rain-provenance.json').read_text())
for path,digest in rain['files'].items():
 assert hashlib.sha256((root/path).read_bytes()).hexdigest()==digest,path
with wave.open(str(root/'media/rain-circuit.wav'),'rb') as w:
 assert (w.getnchannels(),w.getsampwidth(),w.getframerate())==(2,2,44100)
 assert w.getnframes()==round(84.5*44100)
 samples=memoryview(w.readframes(w.getnframes())).cast('h')
 assert 0<max(abs(n) for n in samples)<32767
 assert max(abs(n) for n in samples[-200:])<100,'Ending must approach silence.'
score=json.loads((root/'dist/rain-circuit.json').read_text())
assert score['duration']==84.5 and score['bpm']==96
for mode,notes in score['charts'].items():
 assert len(notes)==rain['notes'][mode]
 assert sum('duration' in n for n in notes)==rain['holds'][mode]>0
 assert notes==sorted(notes,key=lambda n:(n['time'],n['lane']))
 assert len({(n['time'],n['lane']) for n in notes})==len(notes)
 for n in notes:
  assert 2.5<=n['time']<82.5 and 0<=n['lane']<4
  assert any(e['time']==n['time'] and e['lane']==n['lane'] and n.get('duration',0)<=e['duration'] for e in score['sourceScore']['played']),n
  if 'duration' in n: assert n['time']+n['duration']<=score['musicEnd']
setlist=json.loads((root/'dist/setlist.json').read_text())
assert {item['id'] for item in setlist}=={'midnight-signal','rain-circuit'}
for item in setlist:
 assert json.loads((root/'dist'/item['score']).read_text())['id']==item['id']
print(f'PASS: Rain Circuit 84.5s PCM/hash/ending/actual attack and sustain score contracts; {rain["notes"]}, holds {rain["holds"]}.')
