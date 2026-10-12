#!/usr/bin/env python3
"""Compose Rain Circuit and its playable score from new synthesized performances."""
import hashlib
import json
import math
import subprocess
import wave
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SR, BPM = 44100, 96
BEAT, LEAD, DURATION = 60 / BPM, 2.5, 84.5
rng = np.random.default_rng(803096)
mix = np.zeros((round(SR * DURATION), 2))
events = []


def voice(note, duration, kind):
    t = np.arange(round(SR * duration)) / SR
    f = 440 * 2 ** ((note - 69) / 12)
    if kind == 'keys':
        sound = np.sin(2*np.pi*f*t + 1.3*np.sin(2*np.pi*f*2*t)*np.exp(-t*4))
        env = np.minimum(t/.008, 1) * np.exp(-t*.7) * np.minimum((duration-t)/.12, 1)
    elif kind == 'bass':
        sound = np.sin(2*np.pi*f*t) + .14*np.sin(4*np.pi*f*t)
        env = np.minimum(t/.02, 1) * np.exp(-t*1.8) * np.minimum((duration-t)/.07, 1)
    elif kind == 'lead':
        sound = np.sin(2*np.pi*f*t + .015*np.sin(2*np.pi*5*t)) + .15*np.sin(4*np.pi*f*t)
        env = np.minimum(t/.045, 1) * np.minimum((duration-t)/.12, 1)
    else:
        sound = np.sin(2*np.pi*f*t) + .18*np.sin(2*np.pi*f*.998*t)
        env = np.minimum(t/.3, 1) * np.minimum((duration-t)/.3, 1)
    return sound * np.maximum(env, 0)


def add(time, sound, gain, pan=0):
    start = round(time*SR); count = min(len(sound), len(mix)-start)
    mix[start:start+count] += sound[:count,None] * gain * np.array([math.sqrt((1-pan)/2),math.sqrt((1+pan)/2)])


def drum(kind):
    d = {'kick':.3, 'snare':.2, 'hat':.07, 'click':.065}[kind]
    t = np.arange(round(d*SR))/SR
    if kind == 'kick': return np.sin(2*np.pi*(43*t+5*(1-np.exp(-t*28))))*np.exp(-t*16)
    if kind == 'click': return np.sin(2*np.pi*1300*t)*np.exp(-t*75)
    noise = rng.normal(0,.4,len(t))
    return (np.diff(noise,prepend=0) if kind == 'hat' else noise+.2*np.sin(2*np.pi*170*t))*np.exp(-t*(65 if kind == 'hat' else 20))


# D major/B minor colour, with a dominant turn: distinct from Midnight Signal.
chords = [(50,54,57,61),(47,50,54,57),(43,47,50,54),(45,49,52,55)]
call = [[(0,73,1), (1.5,69,.7), (2.5,66,1)],[(.5,71,1),(2,69,1.5)],
        [(0,66,1.5),(2,64,.7),(3,66,.7)],[(0,68,1),(1.5,69,1),(3,73,.7)],
        [(0,66,.7),(1.25,69,.7),(2.5,73,1)],[(0,74,1.5),(2.5,71,1)],
        [(0,71,1),(1.5,69,.7),(3,66,.7)],[(.5,64,1),(2,68,.7),(3,69,.7)]]
answer = [[(0,78,1.5),(2,76,.7),(3,73,.7)],[(.5,74,1),(2,73,1.5)],
          [(0,71,1),(1.5,69,1),(3,66,.7)],[(0,68,1),(1.5,71,.7),(2.5,69,1)],
          [(0,73,1),(1.25,76,.7),(2.5,78,1)],[(0,78,1.5),(2.5,74,1)],
          [(0,76,1),(1.5,74,.7),(3,71,.7)],[(.5,73,1),(2,71,.7),(3,69,.7)]]
charts = {'practice': [], 'arcade': []}


def played(lane, time, duration, practice=False, sustain=False):
    event = {'lane':lane,'time':round(time,6),'duration':round(duration,6)}
    events.append(event)
    for mode in ('practice','arcade'):
        if mode == 'practice' and not practice: continue
        n = {'time':event['time'],'lane':lane}
        if sustain: n['duration'] = event['duration']
        charts[mode].append(n)


for i in range(4): add(i*BEAT,drum('click'),.22)
for bar in range(32):
    start = LEAD + bar*4*BEAT; chord = chords[bar%4]; bridge = 12<=bar<16
    for i,note in enumerate(chord): add(start,voice(note+12,4*BEAT,'pad'),.045,-.6+i*.4)
    for beat in ([0,2] if bridge else [0,1.5,2,3.5]):
        add(start+beat*BEAT,voice(chord[0],.46,'bass'),.35)
        played(0,start+beat*BEAT,.46,practice=beat==0)
    # Sustain keys at each downbeat; the chart tail follows the actual envelope.
    key_duration = 2*BEAT
    for note in chord: add(start,voice(note+12,key_duration,'keys'),.09,-.25)
    played(1,start,key_duration,practice=(bar%2==0 or bridge),sustain=True)
    for beat in ([2] if bridge else [1,3]):
        add(start+beat*BEAT,drum('snare'),.36,.1)
        played(3,start+beat*BEAT,.2,practice=not bridge and beat==3)
    for beat in ([0,2] if bridge else [0,2,2.75]): add(start+beat*BEAT,drum('kick'),.55)
    if not bridge:
        for step in range(8): add(start+(step//2+(0 if step%2==0 else .58))*BEAT,drum('hat'),.12 if step%2==0 else .07,.6)
    if bar>=4:
        phrase = [(0,69+bar%2*2,2),(2.5,66+bar%2*2,1)] if bridge else (answer if bar>=16 else call)[bar%8]
        for index,(beat,note,length) in enumerate(phrase):
            duration=length*BEAT; time=start+beat*BEAT
            add(time,voice(note,duration,'lead'),.16,-.35)
            # A quiet ping-pong answer remains audio only, not an invisible chart attack.
            add(time+.22,voice(note,.35,'keys'),.035,.5)
            played(2,time,duration,practice=index==0,sustain=length>=1.5)
    if bar>=24:
        for step in [1,3]:
            time=start+step*BEAT/2;note=chord[step]+24
            add(time,voice(note,.28,'keys'),.035,.55)
    if bar in (11,15,23,31):
        for beat in [3.25,3.5,3.75]: add(start+beat*BEAT,drum('snare'),.1)
for i,note in enumerate(chords[0]): add(82.5,voice(note+12,1.9,'keys'),.12,-.45+i*.3)
mix = np.tanh(mix*1.3)
mix *= .7/np.max(np.abs(mix))
mix[-round(SR*.7):] *= np.linspace(1,0,round(SR*.7))[:,None]
master=ROOT/'media/rain-circuit.wav'
with wave.open(str(master),'wb') as w:
    w.setnchannels(2);w.setsampwidth(2);w.setframerate(SR)
    w.writeframes(np.round(mix*32767).astype('<i2').tobytes())
asset=ROOT/'dist/assets/rain-circuit.ogg'
subprocess.run(['ffmpeg','-y','-loglevel','error','-i',str(master),'-c:a','libvorbis','-q:a','5',str(asset)],check=True)
for mode,rows in charts.items():
    rows.sort(key=lambda n:(n['time'],n['lane']))
    charts[mode]=[{**row,'id':i} for i,row in enumerate(rows)]
score={'id':'rain-circuit','title':'Rain Circuit','bpm':BPM,'duration':DURATION,'leadIn':LEAD,'musicEnd':82.5,
       'audio':'assets/rain-circuit.ogg','sections':[{'time':LEAD+bar*4*BEAT,'name':name} for bar,name in
         [(0,'Signal on glass'),(4,'Wet avenue'),(12,'Under the canopy'),(16,'Return current'),(24,'Window lights')]],
       'charts':charts,'sourceScore':{'chords':chords,'call':call,'answer':answer,'laneVoices':['bass','keys','lead','snare'],'played':events}}
metadata=ROOT/'dist/rain-circuit.json';metadata.write_text(json.dumps(score,indent=2)+'\n')
record={'title':'Rain Circuit','seed':803096,'bpm':BPM,'duration_seconds':DURATION,'sample_rate':SR,'channels':2,
 'origin':'New Codex algorithmic composition under Martin direction; original synthesis/score, no external samples/MIDI/melody. Not historical audio recovery or independent listening approval.',
 'arrangement':'96 BPM swung hats, FM-like keys, rounded bass, sustained lead call/answer; stripped canopy bridge and higher-key finale. Chart tails use actual played envelopes.',
 'notes':{m:len(ns) for m,ns in charts.items()},'holds':{m:sum('duration' in n for n in ns) for m,ns in charts.items()},
 'peak_dbfs':float(20*np.log10(np.max(np.abs(mix)))),'rms_dbfs':float(20*np.log10(np.sqrt(np.mean(mix**2)))),
 'files':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [master,asset,metadata]}}
(ROOT/'media/rain-provenance.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps({k:v for k,v in record.items() if k!='files'},indent=2))
