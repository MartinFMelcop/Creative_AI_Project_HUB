#!/usr/bin/env python3
"""Bounded actual scene rendering, source/PCK parity and optional version control.

Requires Godot 4.6.3, Xorg with the dummy driver and FFmpeg. Local display sockets
need normal OS permission. No remote service, authored pose assignment or participants.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
SELECTED = ('guardian-block', 'guardian-stale', 'counter-00', 'duelist-step',
            'courier-hit', 'guardian-west-block', 'worn-mark', 'sentinel-disabled')


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def invoke(command, env, timeout=35):
    p = subprocess.run(command, env=env, capture_output=True, text=True, timeout=timeout)
    log = p.stdout + p.stderr
    if p.returncode or any(s in log for s in ('SCRIPT ERROR:', 'Parse Error:', 'ERROR:')):
        raise ValueError(f'Execution failed ({p.returncode}): {log[-2200:]}')
    return log


def verify(output, baseline=None, godot='godot'):
    engine = shutil.which(godot)
    if not engine:
        raise ValueError('Godot executable unavailable')
    for name in ('Xorg', 'ffmpeg'):
        if not shutil.which(name):
            raise ValueError(f'{name} unavailable')
    if baseline and not baseline.is_file():
        raise ValueError('Baseline PCK unavailable')
    with tempfile.TemporaryDirectory(prefix='crossing-actors-') as temporary:
        scratch = Path(temporary)
        env = os.environ.copy()
        for key in ('CROSSING_PROFILE', 'CROSSING_CONTROLS', 'CROSSING_CAPTURE'):
            env.pop(key, None)
        env.update({key: str(scratch / key) for key in ('XDG_DATA_HOME', 'XDG_CONFIG_HOME', 'XDG_CACHE_HOME')})
        version = invoke([engine, '--version'], env).strip()
        if not version.startswith('4.6.3.'):
            raise ValueError('Reproduction requires Godot 4.6.3')
        display = next((n for n in range(110, 130) if not Path(f'/tmp/.X11-unix/X{n}').exists()
                        and not Path(f'/tmp/.X{n}-lock').exists()), None)
        if display is None:
            raise ValueError('No unused test display available')
        env['DISPLAY'] = f':{display}'
        records, hashes, logs = {}, {}, {}
        # The child and every engine process have explicit bounds. Finally reaps Xorg
        # on success, test failure, timeout or interruption; never kills other previews.
        with (scratch / 'display.log').open('w') as log:
            server = subprocess.Popen(['Xorg', env['DISPLAY'], '-config', str(ROOT / 'tests/dummy-display.conf'),
                                       '-logfile', str(scratch / 'Xorg.log'), '-noreset', '-nolisten', 'tcp'],
                                      env=env, stdout=log, stderr=log)
            try:
                for _ in range(40):
                    if server.poll() is not None:
                        raise ValueError('Owned Xorg failed: ' + (scratch / 'display.log').read_text()[-1200:])
                    if Path(f'/tmp/.X11-unix/X{display}').exists():
                        break
                    time.sleep(.05)
                else:
                    raise ValueError('Owned display did not become ready')
                for mode in ['source', 'pack'] + (['baseline'] if baseline else []):
                    folder = scratch / mode
                    folder.mkdir()
                    # Profiles are isolated even across delivery forms and baseline.
                    env.update(CROSSING_PROFILE=str(scratch / (mode + '-marks.json')),
                               CROSSING_CONTROLS=str(scratch / (mode + '-keys.json')))
                    command = [engine, '--audio-driver', 'Dummy']
                    command += ['--path', str(ROOT)] if mode == 'source' else [
                        '--main-pack', str(baseline if mode == 'baseline' else ROOT / 'dist/crossing-drill.pck')]
                    command += ['--script', str(ROOT / 'tests/actor_capture.gd'), '--', str(folder)]
                    logs[mode] = invoke(command, env)
                    records[mode] = json.loads((folder / 'presentation.json').read_text())
                    hashes[mode] = {p.stem: digest(p) for p in sorted(folder.glob('*.png'))}
            finally:
                server.terminate()
                try:
                    server.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    server.kill()
                    server.wait()
        if records['source'] != records['pack'] or hashes['source'] != hashes['pack']:
            raise ValueError('Actual source/PCK rendered observations or pixels differ')
        if len(hashes['source']) != 42:
            raise ValueError('Rendered action sequence incomplete')
        samples = records['source']['observations']
        if (samples['sentinel-disabled']['game'].get('enemy_focus') != 0
                or samples['sentinel-disabled']['game']['mode'] != 'play'
                or samples['guardian-block']['actors']['contact'] != 'protected'
                or samples['counter-00']['actors']['contact'] != 'counter'
                or samples['armor-strike']['actors']['contact']
                or samples['courier-hit']['actors']['contact'] != 'courier_hit'
                or samples['guardian-west-block']['actors']['contact'] != 'protected'):
            raise ValueError('Prepared rendering did not execute the intended real contacts')
        if baseline:
            old = records['baseline']['observations']
            if old.keys() != samples.keys() or any(
                    {k: v for k, v in old[n].items() if k != 'actors'} !=
                    {k: v for k, v in samples[n].items() if k != 'actors'} for n in old):
                raise ValueError('Artwork changed baseline combat/contact observations')
            if all(hashes['baseline'][n] == hashes['source'][n] for n in samples):
                raise ValueError('No rendered change from the static baseline')
        output.mkdir(parents=True, exist_ok=True)
        for mode, record in records.items():
            (output / f'{mode}-presentation.json').write_text(json.dumps(record, indent=2, sort_keys=True) + '\n')
            if mode == 'pack':
                continue  # Full pack pixels verified; avoid publishing duplicate images.
            names = SELECTED if mode == 'source' else ('guardian-block', 'counter-00')
            for name in names:
                shutil.copyfile(scratch / mode / (name + '.png'), output / f'{mode}-{name}.png')
            for sequence in ('counter', 'draw'):
                invoke(['ffmpeg', '-v', 'error', '-y', '-framerate', '6', '-i',
                        str(scratch / mode / (sequence + '-%02d.png')), '-c:v', 'libvpx-vp9',
                        '-pix_fmt', 'yuv420p', '-crf', '28', '-b:v', '0', '-an',
                        str(output / f'{mode}-{sequence}.webm')], env)
        result = {'runtime': version, 'rendered_samples': 42, 'source_pack_observations_identical': True,
                  'source_pack_pixels_identical': True, 'baseline_combat_identical': True if baseline else None,
                  'baseline_pack_sha256': digest(baseline) if baseline else None, 'png_sha256': hashes,
                  'motion_scope': '13 real 60Hz model ticks encoded at 6fps for 10x slowed inspection; silent, not real-time performance.',
                  'limits': 'Controlled scene setups and synthetic commands; no human recognition, comfort or accessibility validation.',
                  'driver_logs': logs}
        (output / 'rendering.json').write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
        print('PASS: 42 actual scene samples, source/PCK observations and pixels identical; '
              + ('baseline combat unchanged.' if baseline else 'no version baseline requested.'))
        return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--baseline-pack', type=Path)
    parser.add_argument('--godot', default='godot')
    args = parser.parse_args()
    try:
        verify(args.output, args.baseline_pack, args.godot)
    except (OSError, ValueError, KeyError, subprocess.TimeoutExpired) as error:
        parser.exit(1, f'FAIL: {error}\n')


if __name__ == '__main__':
    main()
