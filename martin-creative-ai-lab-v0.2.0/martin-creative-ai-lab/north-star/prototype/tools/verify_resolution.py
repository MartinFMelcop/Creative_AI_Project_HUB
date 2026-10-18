#!/usr/bin/env python3
"""Execute matched protective/offensive consumer routes in source, PCK and prior PCK."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def verify(godot, baseline, output):
    engine = shutil.which(godot)
    if not engine:
        raise ValueError('Godot executable unavailable')
    if not baseline.is_file():
        raise ValueError('Baseline PCK unavailable')
    with tempfile.TemporaryDirectory(prefix='crossing-resolution-') as directory:
        scratch = Path(directory)
        env = os.environ.copy()
        for name in ('CROSSING_PROFILE', 'CROSSING_CONTROLS', 'CROSSING_CAPTURE'):
            env.pop(name, None)
        env.update({k: str(scratch / k) for k in ('XDG_DATA_HOME', 'XDG_CONFIG_HOME', 'XDG_CACHE_HOME')})
        version = subprocess.run([engine, '--version'], env=env, capture_output=True, text=True, timeout=10)
        if version.returncode or not version.stdout.strip().startswith('4.6.3.'):
            raise ValueError('Reproduction requires Godot 4.6.3')
        reports = {}
        for mode in ('source', 'pack', 'baseline'):
            result = scratch / (mode + '.json')
            command = [engine, '--headless']
            command += ['--path', str(ROOT)] if mode == 'source' else [
                '--main-pack', str(baseline if mode == 'baseline' else ROOT / 'dist/crossing-drill.pck')]
            command += ['--script', str(ROOT / 'tests/resolution_routes.gd'), '--', str(result)]
            process = subprocess.run(command, env=env, capture_output=True, text=True, timeout=45)
            log = process.stdout + process.stderr
            if process.returncode or any(e in log for e in ('SCRIPT ERROR:', 'Parse Error:', 'ERROR:')):
                raise ValueError(f'{mode} route execution failed: {log[-2500:]}')
            reports[mode] = json.loads(result.read_text())
        if reports['source'] != reports['pack']:
            raise ValueError('Source/PCK route observations differ')
        for name, policies in reports['source'].items():
            for policy, current in policies.items():
                prior = reports['baseline'][name][policy]
                if (current['prefix_ticks'] != prior['prefix_ticks']
                        or current['common_prefix_sha256'] != prior['common_prefix_sha256']):
                    raise ValueError('Version control changed before shutdown: ' + name + '/' + policy)
                if current['combat']['mode'] != 'won' or prior['combat']['mode'] != 'won':
                    raise ValueError('Protective/offensive completion is missing')
            protect, counter = policies['protect']['combat'], policies['counter']['combat']
            if (protect['enemy_focus'] != 3 or protect['counters']['counters'] != 0
                    or counter['enemy_focus'] != 0 or counter['counters']['counters'] != 3
                    or counter['tick'] >= protect['tick']
                    or counter['tick'] >= reports['baseline'][name]['counter']['combat']['tick']):
                raise ValueError('Shutdown or its bounded consequence is missing: ' + name)
        record = {'scope': 'Same fixed policies, not optimal strategies or participants. Exact common state prefix before the third valid counter; protective routes compare the entire crossing.',
                  'source_pack_identical': True, 'common_prefix_identical_to_baseline': True,
                  'reports': reports}
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(record, indent=2, sort_keys=True) + '\n')
        print('PASS: six matched consumer routes per version; source/PCK identical; '
              'protective crossings and pre-shutdown state prefixes match the prior PCK.')
        return record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--godot', default='godot')
    parser.add_argument('--baseline-pack', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    try:
        verify(args.godot, args.baseline_pack, args.output)
    except (OSError, ValueError, KeyError, subprocess.TimeoutExpired) as error:
        parser.exit(1, f'FAIL: {error}\n')


if __name__ == '__main__':
    main()
