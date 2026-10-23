#!/usr/bin/env python3
"""Pinned source assay; reviewed historical Python surrogate, never Ruby/RMXP execution."""
import argparse
import csv
import hashlib
import importlib.util
import json
import math
import re
from pathlib import Path
import shutil
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SOURCE = ROOT / 'references/rave-master/snapshots/36af1651271422ae33856e8b5d7b45702215f165/source'
COMPONENTS = ('HIT', 'CRIT', 'RAW', 'MIT', 'APPLY', 'DUR', 'DOT', 'REAPPLY', 'FINAL_DAMAGE')
RUNNER = 'RM_QA/DATA/QA/TOOLS/run_combat_vector_runner.py'


def verify(source=SOURCE):
    lock = json.loads((HERE / 'source-lock.json').read_text())
    for rel, expected in lock.items():
        path = source / rel
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError('Missing or changed pinned source: ' + rel)
    return lock


def stage(output, source=SOURCE):
    lock = verify(source)
    staged = output / 'staged'
    staged.mkdir(parents=True, exist_ok=True)
    vectors = []
    for comp in COMPONENTS:
        rel = 'DATA/QA/TEST_COMBAT_' + comp + '.csv'
        target = staged / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source / ('RM_QA/' + rel), target)
        with target.open(encoding='utf-8') as handle:
            rows = list(csv.DictReader(handle))
        if not rows:
            raise ValueError('Empty vectors: ' + comp)
        vectors.extend({'component': comp, 'row': row} for row in rows)
    shutil.copyfile(source / RUNNER, staged / 'runner.py')
    (output / 'vectors.json').write_text(json.dumps({'vectors': vectors}, indent=2) + '\n')
    return staged, vectors, lock


def verify_staged(staged, lock):
    for component in COMPONENTS:
        rel = 'RM_QA/DATA/QA/TEST_COMBAT_' + component + '.csv'
        actual = hashlib.sha256((staged / rel.removeprefix('RM_QA/')).read_bytes()).hexdigest()
        if actual != lock[rel]:
            raise ValueError('Changed staged vector: ' + component)
    if hashlib.sha256((staged / 'runner.py').read_bytes()).hexdigest() != lock[RUNNER]:
        raise ValueError('Changed staged runner')


def verify_results(vectors, records, historical=False):
    if len(records) != len(vectors):
        raise AssertionError('Result count differs from source')
    for vector, record in zip(vectors, records):
        component, row = vector['component'], vector['row']
        actual_id = (record['Component'], record['TestID']) if historical else (record['component'], record['id'])
        if actual_id != (component, row['TestID']):
            raise AssertionError('Result identity differs from ordered source vectors')
        fields = [key for key in row if key.startswith('Expected_')]
        if len(fields) != 1:
            raise AssertionError('Ambiguous expected source field')
        expected = float(row[fields[0]])
        declared = float(record['Expected'] if historical else record['expected'])
        actual = float(record['Got'] if historical else record['actual'])
        tolerance = 0.00001 if component == 'RAW' else 0.000001 if component in ('HIT', 'CRIT', 'APPLY') else 0
        if not all(math.isfinite(value) for value in (expected, declared, actual)):
            raise AssertionError('Nonfinite source or reported numeric result')
        if tolerance == 0 and (not expected.is_integer() or not actual.is_integer()):
            raise AssertionError('Integer component contains fractional result')
        passed = record['PASS'] == 'TRUE' if historical else record['passed'] is True
        if not passed or abs(declared - expected) > 0.000001 or abs(actual - expected) > tolerance:
            raise AssertionError('Failed or altered source expectation')


def ruby_bindings(source=SOURCE):
    dev = (source / 'RM_ACT1/DATA/DEV/RGSS/RM_COMBAT_RUNTIME.rb').read_bytes()
    dist = (source / 'RM_DIST/RMXP_BASE/ScriptsCustom/RM_COMBAT_RUNTIME.rb').read_bytes()
    text = dev.decode('utf-8')
    defaults = {key: float(value) for key, value in re.findall(r':(\w+)\s*=>\s*([0-9.]+)', text)}
    if dev != dist or len(defaults) != 13 or 'dd = 0.000001 if dd <= 0.0' not in text:
        raise AssertionError('Reviewed Ruby static bindings changed')
    return {'variants_byte_identical': True, 'embedded_defaults': defaults,
            'runtime_kind': 'helper without status container or battle loop',
            'csv_loaded': False, 'inspection': 'Static reviewed source; no Ruby execution'}


def ratio_distinction(runner):
    # These are a reviewed formula transcription, not a Ruby interpreter.
    ruby_denominator = 0.000001
    ruby_hit = min(.95, max(.05, .9 * (10 / ruby_denominator)))
    python_hit = runner.hit_chance(10, -10, 1, 1, None)
    if python_hit != .05 or ruby_hit != .95:
        raise AssertionError('Invalid-domain discrepancy was hidden')
    return {'input': {'ACC': 10, 'EVA': -10}, 'python_surrogate_hit': python_hit,
            'ruby_static_transcription_hit': ruby_hit, 'equivalent': False,
            'scope': 'Zero denominator only; destination rejects negative EVA. No Ruby execution.'}


def validate_output(output):
    output = output.resolve()
    if output == ROOT or ROOT in output.parents:
        raise ValueError('Evidence must be strictly outside the maintained workspace')
    return output


def resolve_dotnet(value):
    found = shutil.which(value)
    if found:
        return Path(found).resolve()
    path = Path(value).expanduser().resolve()
    if not path.is_file():
        raise ValueError('dotnet executable not found: ' + value)
    return path


def consumer_path(configuration):
    if configuration not in ('Debug', 'Release'):
        raise ValueError('Unsupported configuration')
    return ROOT / ('north-star/combat-study/Checks/bin/' + configuration + '/net10.0/NorthStar.CombatChecks.dll')


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--output', required=True, type=Path)
    ap.add_argument('--dotnet', required=True)
    ap.add_argument('--configuration', choices=('Debug', 'Release'), default='Release')
    ap.add_argument('--consumer', type=Path, help='Explicit prebuilt consumer DLL override')
    args = ap.parse_args()
    output = validate_output(args.output)
    dotnet = resolve_dotnet(args.dotnet)
    dll = args.consumer.resolve() if args.consumer else consumer_path(args.configuration)
    if not dll.is_file():
        raise ValueError('Build the selected consumer first: ' + str(dll))
    output.mkdir(parents=True, exist_ok=True)
    staged, vectors, lock = stage(output)
    verify_staged(staged, lock)  # Copied payloads are checked before executing them.
    result = subprocess.run([sys.executable, str(staged / 'runner.py'), str(staged)], capture_output=True, text=True, timeout=60)
    (output / 'surrogate.log').write_text(result.stdout + result.stderr)
    if result.returncode:
        raise RuntimeError('Historical Python surrogate failed; retain log')
    with (staged / 'DATA/QA/RPT_COMBAT_VECTOR_RUNNER.csv').open() as handle:
        report = list(csv.DictReader(handle))
    verify_results(vectors, report, historical=True)
    spec = importlib.util.spec_from_file_location('reviewed_combat_surrogate', staged / 'runner.py')
    runner = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = runner
    spec.loader.exec_module(runner)
    distinction = ratio_distinction(runner)
    (output / 'csharp-vectors.json').unlink(missing_ok=True)
    run = subprocess.run([str(dotnet), str(dll), '--vectors', str(output / 'vectors.json'), str(output / 'csharp-vectors.json')], capture_output=True, text=True, timeout=60)
    (output / 'csharp.log').write_text(run.stdout + run.stderr)
    if run.returncode:
        raise RuntimeError('C# consumer failed; retain log')
    actual = json.loads((output / 'csharp-vectors.json').read_text())['vectors']
    verify_results(vectors, actual)
    verify_staged(staged, lock)
    verify()  # Source stability gate after executions.
    summary = {'source_sha256': lock, 'components': len(COMPONENTS), 'source_vectors': len(vectors),
               'python_surrogate_passed': len(report), 'csharp_passed': len(actual),
               'invalid_ratio_difference': distinction, 'ruby_static_bindings': ruby_bindings(), 'ruby_executed': False, 'rmxp_executed': False,
               'scope': 'Preserved QA formula vectors; not battle integration, human experience, or complete runtime equivalence.'}
    (output / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps({k: summary[k] for k in ('components', 'source_vectors', 'python_surrogate_passed', 'csharp_passed', 'ruby_executed', 'rmxp_executed')}))


if __name__ == '__main__':
    main()
