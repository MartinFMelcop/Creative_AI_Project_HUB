#!/usr/bin/env python3
"""Original bell/stone synthesis and phase-aligned score. No imported samples."""
import hashlib
import json
import subprocess
import wave
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
RATE = 44100
SEED = 61012


def bell(freq, duration, strength=1.0):
    t = np.arange(round(duration * RATE)) / RATE
    # Inharmonic bronze partials distinguish the Warden from the courier.
    x = sum(a * np.sin(2*np.pi*freq*r*t) * np.exp(-t*k)
            for r, a, k in [(1, .55, 4), (2.76, .23, 7), (4.07, .12, 11)])
    return x * np.minimum(1, t/.006) * strength


def tone(freq, duration, end=None, noise=0.0, seed=0):
    t = np.arange(round(duration * RATE)) / RATE
    phase = 2*np.pi*(freq*t + ((end or freq)-freq)*t*t/(2*duration))
    x = .6*np.sin(phase) + .18*np.sin(phase*2)
    x += noise*np.random.default_rng(SEED+seed).normal(size=len(t))
    return x*np.sin(np.pi*t/duration)**2


def sequence(notes, spacing, total):
    x = np.zeros(round(total*RATE))
    for i, freq in enumerate(notes):
        add(x, bell(freq, total-i*spacing), i*spacing)
    return x


def add(target, sound, seconds, gain=1):
    start = round(seconds*RATE)
    end = min(len(target), start+len(sound))
    target[start:end] += sound[:end-start]*gain


def write(path, samples, peak):
    samples = samples.copy()
    n = min(round(.008*RATE),len(samples)//2)
    samples[:n] *= np.linspace(0,1,n)
    samples[-n:] *= np.linspace(1,0,n)
    samples = samples * peak / max(1e-9, np.abs(samples).max())
    pcm = np.rint(samples*32767).astype('<i2')
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), 'wb') as f:
        f.setparams((1, 2, RATE, 0, 'NONE', 'not compressed'))
        f.writeframes(pcm.tobytes())
    return {"frames": len(pcm), "duration_seconds": len(pcm)/RATE,
            "peak_dbfs": round(20*np.log10(np.abs(pcm.astype(float)).max()/32768), 2),
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


def score(storm):
    # Eight bars at 80 BPM. Both stems share a 24-second transport and motif.
    total = 24.0
    t = np.arange(round(total*RATE))/RATE
    x = .12*np.sin(2*np.pi*73.416*t) + .07*np.sin(2*np.pi*110*t)
    motif = [293.665, 349.228, 311.127, 220, 293.665, 440, 349.228, 311.127]
    for bar, freq in enumerate(motif):
        add(x, bell(freq, 2.6), bar*3, .30 if storm else .17)
        if bar % 2 == 1: add(x, bell(freq/2, 1.2), bar*3+1.5, .12)
    if storm:
        for beat in range(32):
            add(x, tone(92, .18, 43, noise=.15, seed=beat), beat*.75, .26)
            add(x, tone(310, .09, 200, noise=.8, seed=beat+100), beat*.75+.375, .08)
    # The sustained tones have integer cycles over the transport. A short end
    # ramp also removes tail discontinuities introduced by finite bell envelopes.
    n = round(.025*RATE)
    x[:n] *= np.linspace(0, 1, n)
    x[-n:] *= np.linspace(1, 0, n)
    return x


def main():
    audio = ROOT/'media/audio'
    cues = {
        'sweep': sequence([220, 330], .10, .38),
        'charge': sequence([110, 110], .14, .42),
        'wave': sequence([220, 261.626, 293.665], .11, .55),
        'strike': tone(900, .13, 160, noise=.65, seed=1),
        'seal': tone(330, .23, 990),
        'guard': bell(95, .20),
        'counter': sequence([440, 587.33], .045, .38),
        'break': sequence([587.33, 830.609, 1174.66], .06, .7),
        'hurt': tone(135, .3, 60, noise=.25, seed=2),
        'dodge': tone(600, .16, 1300, noise=.6, seed=3),
        'phase': sequence([73.416, 77.782, 146.832], .16, 1.15),
        'echo': tone(260, .48, 780),
        'victory': sequence([293.665, 349.228, 440, 587.33], .12, 1.2),
        'defeat': sequence([146.832, 123.471, 110], .13, .95),
    }
    assets = {}
    for name, samples in cues.items():
        path = audio/(name+'.wav')
        assets[path.relative_to(ROOT).as_posix()] = write(path, samples, .34)
    for name, storm in [('courtyard', False), ('fracture', True)]:
        master = ROOT/'media/masters'/(name+'.wav')
        assets[master.relative_to(ROOT).as_posix()] = write(master, score(storm), .55)
        runtime = audio/(name+'.ogg')
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', str(master),
                        '-c:a', 'libvorbis', '-q:a', '4', str(runtime)], check=True)
        assets[runtime.relative_to(ROOT).as_posix()] = {
            'duration_seconds': 24, 'loop': True,
            'sha256': hashlib.sha256(runtime.read_bytes()).hexdigest()}
    catalog = {'version': '0.2.0', 'producer': 'Codex original algorithmic score/synthesis',
               'seed': SEED, 'sample_rate': RATE, 'channels': 1,
               'music': {'bpm': 80, 'bars': 8, 'beats_per_bar': 4, 'transport_seconds': 24,
                         'motif_hz': [293.665,349.228,311.127,220,293.665,440,349.228,311.127]},
               'files': assets}
    (ROOT/'media/audio-catalog.json').write_text(json.dumps(catalog, indent=2)+'\n')
    print(json.dumps({'cues': len(cues), 'aligned_music_loops': 2, 'sample_rate': RATE}))


if __name__ == '__main__': main()
