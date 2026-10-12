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
