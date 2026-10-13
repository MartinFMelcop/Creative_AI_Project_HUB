#!/usr/bin/env python3
"""Original short synthesized action cues; no samples, MIDI or music import."""
from pathlib import Path
import hashlib,json,wave
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
RATE=44100
rng=np.random.default_rng(505020)

def tone(freq,t):return np.sin(2*np.pi*freq*t)
def write(name,seconds,signal):
    t=np.arange(round(seconds*RATE))/RATE
    y=signal(t)
    envelope=np.minimum(1,t/.008)*np.minimum(1,(seconds-t)/.05)
    y=y*envelope
    y=.6*y/max(1,np.max(np.abs(y)))
    data=np.round(y*32767).astype('<i2').tobytes()
    path=ROOT/'Native/media/audio'/f'{name}.wav'
    with wave.open(str(path),'wb') as f:f.setparams((1,2,RATE,0,'NONE','not compressed'));f.writeframes(data)
    return {'name':name,'seconds':seconds,'sample_rate':RATE,'channels':1,'peak_dbfs':float(20*np.log10(np.max(np.abs(y)))),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}

cues=[
 write('strike',.24,lambda t:(rng.normal(0,.28,len(t))+tone(160,t)*.5)*np.exp(-t*18)),
 write('brace',.38,lambda t:(tone(220,t)+.3*tone(440,t)+.15*tone(910,t))*np.exp(-t*11)),
 write('pin',.3,lambda t:(tone(760-900*t,t)+.25*tone(180,t))*np.exp(-t*12)),
 write('mend',.58,lambda t:(tone(392,t)+.6*tone(523.25,t)+.3*tone(659.25,t))*np.exp(-t*5)),
 write('shift',.18,lambda t:(rng.normal(0,.2,len(t))+tone(90,t)*.4)*np.exp(-t*25)),
 write('steam',.65,lambda t:(rng.normal(0,.35,len(t))+tone(65,t)*.5)*np.exp(-t*5)),
 write('stage',.72,lambda t:(tone(261.63,t)*np.exp(-t*5)+np.where(t>=.16,tone(392,t-.16)*np.exp(-np.maximum(0,t-.16)*5),0))*.7)
]
path=ROOT/'Native/media/audio/catalog.json';path.write_text(json.dumps({'origin':'New Codex algorithmic synthesis under Martin direction; no samples/MIDI/external recording. Action cues, not a soundtrack or physical listening approval.','seed':505020,'cues':cues},indent=2)+'\n')
print('Rendered seven mono PCM16 action cues, fixed seed and actual hashes.')
