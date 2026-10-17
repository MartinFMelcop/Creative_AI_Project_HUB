#!/usr/bin/env python3
"""Capture actual source/PCK AudioServer output; no physical listening claim."""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import struct
import tempfile
import wave

from verify import ROOT, invoke


def signal(path):
    with wave.open(str(path)) as wav:
        if wav.getsampwidth() != 2 or wav.getnchannels() not in (1, 2):
            raise ValueError(f"Unsupported PCM: {path.name}")
        frames, rate, channels = wav.getnframes(), wav.getframerate(), wav.getnchannels()
        data = wav.readframes(frames)
    values = struct.unpack('<' + 'h' * (len(data) // 2), data)
    if not values or rate not in (22050, 44100, 48000):
        raise ValueError(f"Missing/unsupported samples: {path.name}")
    return {"frames": frames, "rate": rate, "channels": channels,
            "peak": max(map(abs, values)),
            "rms": round(math.sqrt(sum(v*v for v in values) / len(values)), 3),
            "pcm_sha256": hashlib.sha256(data).hexdigest()}


def inspect(folder, baseline=False):
    record = json.loads((folder / 'capture.json').read_text())
    metrics = {p.stem: signal(p) for p in sorted(folder.glob('*.wav'))}
    expected = ('title-silence', 'guardian-block', 'duelist-draw', 'pulse-avoided')
    if not all(name in metrics for name in expected):
        raise ValueError('Missing actual mixer capture')
    if baseline:
        if any(metrics[name]['peak'] for name in expected):
            raise ValueError('Historical silent consumer produced unexpected audio')
    else:
        for name in ('title-silence', 'muted-block', 'paused-silence'):
            if name not in metrics or metrics[name]['peak'] != 0:
                raise ValueError(f'Silence control failed: {name}')
        for name in ('guardian-block', 'duelist-draw', 'pulse-avoided', 'counter-contact', 'pulse-damage', 'crossing-won', 'crossing-lost'):
            if not 100 < metrics[name]['peak'] < 16384 or metrics[name]['rms'] < 20:
                raise ValueError(f'Expected bounded audible mixer signal: {name}')
        rows = {row['name']: row for row in record['records']}
        for name, cues in [('guardian-block', ['bolt', 'block']),
                           ('duelist-draw', ['bolt', 'draw']),
                           ('pulse-avoided', ['pulse'])]:
            if [e['cue'] for e in rows[name]['sound']['events']] != cues:
                raise ValueError(f'Wrong model-to-cue ownership: {name}')
            if rows[name]['combat']['hp'] != 5 or rows[name]['combat']['cargo'] != 3:
                raise ValueError('Prepared successful exercise changed its actual outcome')
        for name, cues in [('counter-contact', ['counter']), ('pulse-damage', ['hurt']),
                           ('crossing-won', ['won']), ('crossing-lost', ['hurt', 'lost'])]:
            if [e['cue'] for e in rows[name]['sound']['events']] != cues:
                raise ValueError(f'Wrong actual consequence sound: {name}')
        native = json.loads((ROOT.parents[1] / 'evidence/north-star-sound/results.json').read_text())
        for name, cue in native['sound']['cues'].items():
            observed = metrics['cue-' + name]
            if observed['pcm_sha256'] != cue['pcm_sha256'] or observed['frames'] != cue['frames']:
                raise ValueError(f'Exported synthesis differs from the native consumer: {name}')
    return {"driver": record['driver'], "mix_rate": record['mix_rate'],
            "metrics": metrics, "records": record['records']}


def verify(godot, output, baseline_pack=None):
    executable = shutil.which(godot)
    if executable is None:
        raise ValueError('Godot executable unavailable')
    with tempfile.TemporaryDirectory(prefix='crossing-sound-') as temporary:
        scratch = Path(temporary)
        env = os.environ.copy()
        for key in ('CROSSING_PROFILE', 'CROSSING_CONTROLS', 'CROSSING_CAPTURE'):
            env.pop(key, None)
        env.update({key: str(scratch / key) for key in ('XDG_DATA_HOME', 'XDG_CACHE_HOME', 'XDG_CONFIG_HOME')})
        reports = {}
        modes = ['source', 'pack'] + (['baseline'] if baseline_pack else [])
        for mode in modes:
            folder = scratch / mode
            command = [executable, '--headless', '--audio-driver', 'Dummy']
            if mode == 'source':
                command += ['--path', str(ROOT)]
            else:
                command += ['--main-pack', str(baseline_pack if mode == 'baseline' else ROOT / 'dist/crossing-drill.pck')]
            script = str(ROOT / 'tests/sound_capture.gd') if mode == 'baseline' else 'res://tests/sound_capture.gd'
            invoke(command + ['--script', script, '--', str(folder)], env, timeout=30)
            reports[mode] = inspect(folder, baseline=mode == 'baseline')
        if reports['source']['records'] != reports['pack']['records']:
            # Mixer sample counts vary; compare only deterministic behavior, not buffers.
            for left, right in zip(reports['source']['records'], reports['pack']['records'], strict=True):
                for key in ('name', 'combat', 'sound'):
                    if left[key] != right[key]:
                        raise ValueError('Source/PCK audio workflow behavior differs')
        Path(output).write_text(json.dumps({"schema_version": 1, "captures": reports,
            "limit": "Actual software AudioServer output, not hardware latency, listening quality, recognition or accessibility validation."}, indent=2, sort_keys=True)+'\n')
    print('PASS: source/PCK actual mixer, cue ownership, PCM identity, mute/pause and baseline controls')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--godot', default='godot')
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--baseline-pack', type=Path)
    args = parser.parse_args()
    try:
        verify(args.godot, args.output, args.baseline_pack)
    except (ValueError, OSError, KeyError) as exc:
        parser.exit(1, f'FAIL: {exc}\n')
