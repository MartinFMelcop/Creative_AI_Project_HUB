#!/usr/bin/env python3
"""Run selected initiative source, native owner and actual existing browser once.

Existing passive/control/response regressions run separately through their unchanged
wrappers in CI and final acceptance; this wrapper does not duplicate those suites.
"""
import argparse
import hashlib
import json
import shutil
import subprocess
import time
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
STUDY = ROOT / 'north-star/combat-study'
ASSAY = ROOT / 'labs/combat-response/initiative/source_assay.py'
SOURCE = ROOT / 'references/rave-master/snapshots/36af1651271422ae33856e8b5d7b45702215f165/source'


def identities():
    files = [p for base in [STUDY, ASSAY.parent] for p in base.rglob('*')
             if p.is_file() and not {'bin', 'obj', '__pycache__', 'node_modules'}.intersection(p.parts)]
    files += [ROOT / name for name in ['north-star/csharp/global.json', 'projects/realtime-integration-lab/package.json', 'projects/realtime-integration-lab/package-lock.json']]
    files += [SOURCE / name for name in ['RM_CORE/DATA/CORE/REGRAS_DE_COMBATE.csv', 'RM_ACT1/DATA/DEV/RGSS/RM_COMBAT_RUNTIME.rb', 'RM_DIST/RMXP_BASE/ScriptsCustom/RM_COMBAT_RUNTIME.rb']]
    return {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(set(files))}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dotnet', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    out = args.output.resolve()
    if out.is_relative_to(ROOT) or out.exists():
        parser.error('New external output directory required')
    out.mkdir(parents=True)
    dotnet = shutil.which(args.dotnet) or args.dotnet
    before = identities()
    records = []
    started = time.monotonic()
    dll = STUDY / 'InitiativeChecks/bin/Release/net10.0/NorthStar.InitiativeChecks.dll'
    commands = [
        [dotnet, '--version'],
        [dotnet, 'build', str(STUDY / 'InitiativeChecks/NorthStar.InitiativeChecks.csproj'), '-c', 'Release', '-m:1', '--disable-build-servers'],
        ['python3', '-B', str(ASSAY), '--output', str(out / 'source-initial.json'), '--export-cases', str(out / 'cases.json')],
        [dotnet, str(dll), str(out / 'native.json'), '--vectors', str(out / 'cases.json')],
        ['python3', '-B', str(ASSAY), '--output', str(out / 'source.json'), '--native', str(out / 'native.json')],
        ['node', str(STUDY / 'tools/initiative-browser.mjs'), dotnet, str(out / 'browser')],
    ]
    try:
        for command in commands:
            remaining = 900 - (time.monotonic() - started)
            if remaining <= 0:
                raise RuntimeError('Whole initiative verification deadline exceeded')
            result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, timeout=min(300, remaining))
            records.append(dict(command=command, exit_code=result.returncode, stdout=result.stdout, stderr=result.stderr))
            (out / 'commands.json').write_text(json.dumps(records, indent=2) + '\n')
            if result.returncode:
                raise RuntimeError('Actual command failed: ' + command[1])
            if command[1] == '--version' and result.stdout.strip() != '10.0.401':
                raise RuntimeError('Pinned SDK required')
        if before != identities():
            raise RuntimeError('Source closure changed during initiative execution')
        native = json.loads((out / 'native.json').read_text())
        browser = json.loads((out / 'browser/browser.json').read_text())
        report = dict(schema_version=1, kind='selected_initiative_destination_execution',
                      source_stable=True, source_sha256=before, native=native['checks'],
                      browser=browser['checks'], http=browser['http_checks'],
                      source='source.json', affected_regressions='Separate unchanged passive/control/response wrappers required; results are bound in acceptance evidence.',
                      elapsed_seconds=time.monotonic() - started,
                      limits='Selected source requirements plus original numeric round policy in existing consumer. Overlapping deterministic controls, not historical runtime, people, complete initiative, balance or Unity/Windows/Steam.')
        (out / 'verification.json').write_text(json.dumps(report, indent=2) + '\n')
        print('PASS: selected initiative, same-case comparison and actual browser; stable inputs ' + str(len(before)))
    finally:
        (out / 'commands.json').write_text(json.dumps(records, indent=2) + '\n')


if __name__ == '__main__':
    main()
