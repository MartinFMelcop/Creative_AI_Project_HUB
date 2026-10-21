#!/usr/bin/env python3
"""Execute mapped event receipt and complete journeys in source/PCK/release consumers."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import tempfile
import zipfile
from verify import ROOT, invoke

EXPECTED = 56


def validate(row):
    if (row['checks'] != {'passed': EXPECTED, 'failed': 0}
            or len(row['labels']) != EXPECTED or len(set(row['labels'])) != EXPECTED
            or row['physical_controller'] is not False):
        raise ValueError('Mapped event controls incomplete or misrepresented')
    if [j['role'] for j in row['journeys']] != ['Guardian', 'Duelist'] or any(
            j['game']['mode'] != 'won' or not all(j['return_gate']['raised'])
            for j in row['journeys']):
        raise ValueError('Actual mapped two-goal journeys incomplete')
    for name, sha in row['consumer_hashes'].items():
        if hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != sha:
            raise ValueError('Executed consumer identity mismatch: ' + name)
    if set(row['consumer_hashes']) != {'arena.gd', 'gamepad.gd', 'tests/gamepad_checks.gd', 'tests/gamepad_driver.gd'}:
        raise ValueError('Incomplete executed identity inventory')


def verify(output, godot='godot', archive=None, compare=None):
    engine = shutil.which(godot)
    if not engine:
        raise ValueError('Godot unavailable')
    with tempfile.TemporaryDirectory(prefix='mapped-pad-') as folder:
        work = Path(folder)
        env = os.environ.copy()
        for key in ('CROSSING_PROFILE', 'CROSSING_CONTROLS', 'CROSSING_CAPTURE'):
            env.pop(key, None)
        env.update({key: str(work / key) for key in ('XDG_DATA_HOME', 'XDG_CONFIG_HOME', 'XDG_CACHE_HOME')})
        if not invoke([engine, '--version'], env).startswith('4.6.3.'):
            raise ValueError('Godot 4.6.3 required')
        deliveries = [('source', [engine, '--headless', '--path', str(ROOT), '--script', 'res://tests/gamepad_checks.gd']),
                      ('pack', [engine, '--headless', '--main-pack', str(ROOT / 'dist/crossing-drill.pck'), '--script', 'res://tests/gamepad_checks.gd'])]
        if archive:
            from check_linux import check
            check(archive)
            with zipfile.ZipFile(archive) as package:
                package.extractall(work / 'release')
            player = work / 'release/CrossingDrill/crossing-drill.x86_64'
            player.chmod(0o755)
            deliveries.append(('release', [str(player), '--headless', '--', '--verify-pad']))
        rows = []
        for label, command in deliveries:
            env['CROSSING_PROFILE'] = str(work / (label + '-profile.json'))
            env['CROSSING_CONTROLS'] = str(work / (label + '-controls.json'))
            target = work / (label + '.json')
            invoke([*command, *([] if label == 'release' else ['--']), str(target)], env)
            row = json.loads(target.read_text())
            validate(row)
            rows.append(row)
        if any(row != rows[0] for row in rows[1:]):
            raise ValueError('Delivery observations differ')
        result = {'schema_version': 1, 'deliveries': [label for label, _ in deliveries], **rows[0]}
        if compare and result != json.loads(Path(compare).read_text()):
            raise ValueError('Recorded mapped observations differ')
        Path(output).write_text(json.dumps(result, sort_keys=True, indent=2) + '\n')
        print(f'PASS: {EXPECTED} mapped-event controls and both two-goal journeys; {len(rows)} identical deliveries; no physical controller claim')
        return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--godot', default='godot')
    parser.add_argument('--archive', type=Path)
    parser.add_argument('--compare', type=Path)
    args = parser.parse_args()
    try:
        verify(args.output, args.godot, args.archive, args.compare)
    except (OSError, ValueError, KeyError) as exc:
        parser.exit(1, f'FAIL: {exc}\n')
