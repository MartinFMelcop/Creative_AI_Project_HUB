#!/usr/bin/env python3
"""Render an original score and matching beat charts; no external samples."""
from pathlib import Path
import hashlib
import json
import math
import subprocess
import wave

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SR = 44100
BPM = 120
BEAT = 60 / BPM
LEAD = 3.0
DURATION = 69.0
rng = np.random.default_rng(803120)
mix = np.zeros((int(SR * DURATION), 2), dtype=np.float64)


def add(t, signal, level=1, pan=0):
    start = round(t * SR)
    end = min(len(mix), start + len(signal))
    if end <= start:
        return
    gains = np.array([math.sqrt((1-pan)/2), math.sqrt((1+pan)/2)])
    mix[start:end] += signal[:end-start, None] * gains * level


def tone(midi, duration, kind='lead'):
    x = np.arange(round(duration * SR)) / SR
    f = 440 * 2 ** ((midi - 69) / 12)
    if kind == 'pad':
        signal = (np.sin(2*np.pi*f*x) + .23*np.sin(2*np.pi*f*1.003*x) + .12*np.sin(4*np.pi*f*x))
        env = np.minimum(x/.1, 1) * np.minimum((duration-x)/.22, 1)
    elif kind == 'bass':
        signal = np.sin(2*np.pi*f*x) + .3*np.sin(4*np.pi*f*x)
        env = np.minimum(x/.012, 1) * np.exp(-x*3) * np.minimum((duration-x)/.05, 1)
    else:
        signal = sum(np.sin(2*np.pi*f*h*x)/(h*h) for h in (1, 2, 3, 4))
        env = np.minimum(x/.009, 1) * np.exp(-x*2) * np.minimum((duration-x)/.06, 1)
    return signal * np.maximum(env, 0)


def drum(kind):
    duration = {'kick': .29, 'snare': .17, 'hat': .055, 'click': .055}[kind]
    x = np.arange(round(duration * SR)) / SR
    if kind == 'kick':
        phase = 2*np.pi*(49*x + 7*(1-np.exp(-x*32)))
        return np.sin(phase)*np.exp(-x*15)
    if kind == 'click':
        return np.sin(2*np.pi*1200*x)*np.exp(-x*80)
    noise = rng.normal(0, .35, len(x))
    if kind == 'hat':
        return np.diff(noise, prepend=0) * np.exp(-x*75)
    return (noise*.75 + np.sin(2*np.pi*185*x)*.22)*np.exp(-x*22)


# Original eight-bar call/response; no quoted recordings, MIDI or existing melody.
chords = [(45, 48, 52, 55), (41, 45, 48, 52), (48, 52, 55, 59), (43, 47, 50, 57)]
phrases = [
 [(0, 69), (.75, 72), (1.5, 71), (2.5, 67), (3.25, 64)],
 [(0, 69), (1, 65), (1.75, 67), (2.5, 72), (3.5, 69)],
 [(.5, 67), (1.25, 71), (2, 76), (2.75, 74), (3.5, 72)],
 [(0, 71), (.75, 74), (1.5, 72), (2.5, 67), (3.25, 69)],
 [(0, 76), (1, 72), (1.5, 71), (2.25, 69), (3.5, 67)],
 [(.25, 69), (1, 72), (1.75, 77), (2.75, 76), (3.5, 72)],
 [(0, 76), (.75, 79), (1.5, 76), (2.5, 74), (3.25, 71)],
 [(0, 74), (.75, 71), (1.5, 67), (2.5, 64), (3.5, 69)],
]
for i in range(6):
    add(i * BEAT, drum('click'), .18 if i < 5 else .3)
for bar in range(32):
    t = LEAD + bar * 4 * BEAT
    chord = chords[bar % 4]
    bridge = 12 <= bar < 16
    for j, note in enumerate(chord):
        add(t, tone(note+12, 2.35, 'pad'), .075, -.55 + j*.35)
    for step in range(8):
        onset = t + step * BEAT / 2
        root = chord[0] + (12 if step in (3, 7) else 0)
        add(onset, tone(root, .32, 'bass'), .24 if not bridge else .14)
        add(onset, drum('hat'), .16 if step % 2 == 0 else .1, .45)
    for b in range(4):
        if not bridge or b % 2 == 0:
            add(t+b*BEAT, drum('kick'), .58)
        if b % 2:
            add(t+b*BEAT, drum('snare'), .35, -.12)
    if bar >= 4:
        phrase = phrases[(bar-4) % 8]
        for onset, note in phrase:
            add(t+onset*BEAT, tone(note, .48 if not bridge else .68), .12 if bridge else .18, -.3)
            add(t+onset*BEAT+.19, tone(note, .38), .035, .4)
    if bar >= 24:
        # A quieter high arpeggio gives the final section a second musical layer.
        for step in range(8):
            add(t+step*BEAT/2, tone(chord[step % 4]+24, .22), .055, .35)
    if bar in (3, 11, 15, 23, 31):
        for step in range(4):
            add(t+1.5+step*.125, drum('snare'), .11 + step*.035)
for j,note in enumerate(chords[0]):
    add(67, tone(note+12, 1.95, 'pad'), .13, -.4+j*.25)
mix *= .88 / np.max(np.abs(mix))
mix[-round(SR*.6):] *= np.linspace(1,0,round(SR*.6))[:,None]
master = ROOT/'media'/'midnight-signal.wav'
master.parent.mkdir(exist_ok=True)
with wave.open(str(master), 'wb') as w:
    w.setnchannels(2);w.setsampwidth(2);w.setframerate(SR)
    w.writeframes(np.round(mix * 32767).astype('<i2').tobytes())
asset = ROOT/'dist/assets/midnight-signal.ogg'
subprocess.run(['ffmpeg','-y','-loglevel','error','-i',str(master),'-c:a','libvorbis','-q:a','5',str(asset)],check=True)


def chart(mode):
    notes = []
    for bar in range(32):
        start = LEAD + bar * 4 * BEAT
        phrase = phrases[(bar-4) % 8]
        if bar < 4:
            pattern = [(0,0), (2,0)]  # Bass onsets during the instrumental count-in.
        elif 12 <= bar < 16:
            pattern = [(0,1), (phrase[2][0],2)]  # Held harmony and one lead answer.
        else:
            pattern = [(0,0 if bar % 2 == 0 else 1), (1,3), (phrase[2][0],2), (3,3)]
        if mode == 'arcade' and bar >= 4 and not 12 <= bar < 16:
            # Each lane names an actual instrument attack from the rendered score.
            pattern += [(onset,2) for onset,_ in phrase]
            pattern += [(0,1)]
            if bar >= 24:
                pattern += [(.5,0), (2.5,0)]
        for beat,lane in sorted(set(pattern)):
            notes.append({'time':round(start+beat*BEAT,6),'lane':lane})
    notes.sort(key=lambda n:(n['time'],n['lane']))
    return [{**n,'id':i} for i,n in enumerate(notes)]

metadata = {'id':'midnight-signal','title':'Midnight Signal','bpm':BPM,'duration':DURATION,
            'leadIn':LEAD,'musicEnd':67,'audio':'assets/midnight-signal.ogg',
            'sections':[{'time':3,'name':'Platform lights'},{'time':11,'name':'Night train'},
                        {'time':27,'name':'Underpass'},{'time':35,'name':'Neon ascent'},
                        {'time':51,'name':'Last train'}],
            'charts':{mode:chart(mode) for mode in ('practice','arcade')},
            'sourceScore':{'chords':chords,'leadPhrases':phrases,'laneVoices':['bass','chord','lead','snare']}}
(ROOT/'dist/track.json').write_text(json.dumps(metadata,indent=2)+'\n')
summary = {'title':metadata['title'],'provenance':'New algorithmic composition and synthesized instruments by Codex under Martin\'s direction. No external samples or third-party melody. Not a recovered historical recording.',
           'seed':803120,'bpm':BPM,'duration_seconds':DURATION,'sample_rate':SR,'channels':2,
           'peak_dbfs':float(20*np.log10(np.max(np.abs(mix)))),
           'rms_dbfs':float(20*np.log10(np.sqrt(np.mean(mix**2)))),
           'notes':{mode:len(rows) for mode,rows in metadata['charts'].items()},
           'files':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [master,asset,ROOT/'dist/track.json']}}
(ROOT/'media/provenance.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps(summary,indent=2))
