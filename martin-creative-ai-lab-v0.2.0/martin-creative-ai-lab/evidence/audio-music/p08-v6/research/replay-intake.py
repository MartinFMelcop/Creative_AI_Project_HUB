#!/usr/bin/env python3
"""External intake replay with complete logs and unchanged-source attestation."""
from pathlib import Path
import ast
import hashlib
import importlib.metadata as metadata
import json
import os
import platform
import re
import subprocess
import sys
import time

ROOT = Path('/workspace/work/p08-v6/intake/P08_AUDIO_RESEARCH_V6')
OUT = Path('/workspace/work/p08-v6/science')
ENV = dict(os.environ, PYTHONPATH=str(OUT / 'python-deps'), PYTHONDONTWRITEBYTECODE='1')

def hashes():
    return {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(ROOT.rglob('*')) if p.is_file()}

def invoke(name, args, expected=0):
    cmd = [sys.executable, '-B', *args]
    start = time.monotonic()
    p = subprocess.run(cmd, cwd=ROOT, env=ENV, capture_output=True, text=True, timeout=360)
    (OUT / f'{name}.stdout.log').write_text(p.stdout)
    (OUT / f'{name}.stderr.log').write_text(p.stderr)
    record = {'name': name, 'command': cmd, 'cwd': str(ROOT), 'exit': p.returncode,
              'expected_exit': expected, 'passed': p.returncode == expected,
              'seconds': round(time.monotonic() - start, 3),
              'stdout_sha256': hashlib.sha256(p.stdout.encode()).hexdigest(),
              'stderr_sha256': hashlib.sha256(p.stderr.encode()).hexdigest()}
    counts = re.findall(r'Ran\s+(\d+)\s+tests?', p.stderr)
    if counts:
        record['observed_unit_tests'] = sum(map(int, counts))
    print(name, p.returncode, p.stdout.strip()[-200:], flush=True)
    return record

def main():
    before = hashes()
    (OUT / 'source-before.json').write_text(json.dumps(before, indent=2, sort_keys=True) + '\n')
    tests = [
        'experiments/test_timing_oracle.py', 'experiments/test_variant_similarity.py',
        'experiments/test_event_policy.py', 'experiments/test_scene_mix_probe.py',
        'governance/test_asset_release_gate.py', 'experiments/test_combat_mix_policy_probe.py',
        'governance/test_whole_package_inventory.py', 'experiments/test_headroom_preservation_probe.py',
        'experiments/test_intersample_peak_probe.py', 'tools/test_claims_v6.py']
    test_inventory = []
    for path in tests:
        tree = ast.parse((ROOT / path).read_text())
        ids = [f'{n.name}.{m.name}' for n in ast.walk(tree) if isinstance(n, ast.ClassDef)
               for m in n.body if isinstance(m, ast.FunctionDef) and m.name.startswith('test_')]
        test_inventory.append({'path': path, 'sha256': before[path], 'case_ids': ids, 'count': len(ids)})
    (OUT / 'test-inventory.json').write_text(json.dumps(test_inventory, indent=2, sort_keys=True) + '\n')
    records = [invoke('validate-before', ['tools/validate_v6.py']),
               invoke('run-v6', ['tools/run_v6_checks.py', '--out', str(OUT / 'V6_RUN_REPLAY.json')]),
               invoke('standalone-intersample', ['experiments/intersample_peak_probe.py', 'demonstrations/sfx', '--out', str(OUT / 'INTERSAMPLE_REPLAY.json')])]
    for i, path in enumerate(tests):
        records.append(invoke(f'test-{i:02d}', [path]))
    generators = [
        ('midi', 'experiments/timing_oracle.py', ['demonstrations/North_Star_R32_Authored_Score.mid'], 'reports/R32_MIDI_INDEPENDENT_AUDIT.json', 0),
        ('sfx', 'experiments/sfx_signal_report.py', ['demonstrations/sfx'], 'reports/R32_SFX_DESCRIPTIVE_SIGNAL.json', 0),
        ('variants', 'experiments/variant_similarity.py', ['demonstrations/sfx'], 'reports/R32_VARIANT_SIMILARITY_TRIAGE.json', 0),
        ('event', 'experiments/event_policy_oracle.py', [], 'reports/R32_SEMANTIC_POLICY_REFERENCE.json', 0),
        ('scene', 'experiments/scene_mix_probe.py', ['demonstrations/sfx'], 'reports/R32_CONTEXTUAL_MIX_DIAGNOSTICS.json', 0),
        ('research-gate', 'governance/asset_release_gate.py', ['demonstrations', 'governance/MEDIA_ASSET_INVENTORY.json', '--mode', 'research'], 'reports/RESEARCH_ASSET_GATE.json', 0),
        ('combat', 'experiments/combat_mix_policy_probe.py', ['demonstrations/sfx'], 'reports/R32_MULTI_EVENT_COMBAT_POLICY_DIAGNOSTICS.json', 0),
        ('factorial', 'experiments/combat_mix_policy_probe.py', ['demonstrations/sfx', '--factorial'], 'reports/R32_FACTORIAL_POLICY_ABLATION.json', 0),
        ('whole-research-gate', 'governance/asset_release_gate.py', ['.', 'governance/WHOLE_PACKAGE_MEDIA_INVENTORY.json', '--mode', 'research'], 'reports/WHOLE_PACKAGE_RESEARCH_ASSET_GATE.json', 0),
        ('public-gate', 'governance/asset_release_gate.py', ['demonstrations', 'governance/MEDIA_ASSET_INVENTORY.json', '--mode', 'public'], 'reports/PUBLIC_ASSET_GATE_BLOCKED.json', 2),
        ('whole-public-gate', 'governance/asset_release_gate.py', ['.', 'governance/WHOLE_PACKAGE_MEDIA_INVENTORY.json', '--mode', 'public'], 'reports/WHOLE_PACKAGE_PUBLIC_ASSET_BLOCKED.json', 2),
        ('headroom', 'experiments/headroom_preservation_probe.py', ['demonstrations/sfx'], 'reports/R32_V5_HEADROOM_PRESERVATION.json', 0)]
    comparisons = []
    for name, producer, args, reference, expected in generators:
        out = OUT / f'{name}.json'
        records.append(invoke(f'produce-{name}', [producer, *args, '--out', str(out)], expected))
        comparisons.append({'producer': producer, 'producer_sha256': before[producer], 'reference': reference,
                            'reference_sha256': before[reference], 'actual_sha256': hashlib.sha256(out.read_bytes()).hexdigest(),
                            'equal_json': json.loads(out.read_text()) == json.loads((ROOT / reference).read_text())})
    comparisons.append({'producer': 'experiments/intersample_peak_probe.py', 'producer_sha256': before['experiments/intersample_peak_probe.py'],
                        'reference': 'reports/R32_V6_INTERSAMPLE_ESTIMATE.json', 'reference_sha256': before['reports/R32_V6_INTERSAMPLE_ESTIMATE.json'],
                        'actual_sha256': hashlib.sha256((OUT / 'INTERSAMPLE_REPLAY.json').read_bytes()).hexdigest(),
                        'equal_json': json.loads((OUT / 'INTERSAMPLE_REPLAY.json').read_text()) == json.loads((ROOT / 'reports/R32_V6_INTERSAMPLE_ESTIMATE.json').read_text())})
    records.append(invoke('validate-after', ['tools/validate_v6.py']))
    after = hashes()
    dependencies = json.loads(subprocess.check_output([sys.executable, '-B', '-c', 'import soundfile, numpy, scipy, json; print(json.dumps({"soundfile":soundfile.__version__,"numpy":numpy.__version__,"scipy":scipy.__version__,"libsndfile":soundfile.__libsndfile_version__}))'], env=ENV, text=True))
    result = {'schema': 'p08.v6.independent-local-intake-replay.v1', 'environment': {'python': sys.version, 'platform': platform.platform(), 'dependencies': dependencies},
              'source_files': len(before), 'source_stable': before == after, 'source_differences': sorted(k for k in set(before) | set(after) if before.get(k) != after.get(k)),
              'tests_by_ast': sum(r['count'] for r in test_inventory), 'tests_observed_individual': sum(r.get('observed_unit_tests', 0) for r in records if r['name'].startswith('test-')),
              'commands': records, 'report_comparisons': comparisons, 'all_commands_passed': all(r['passed'] for r in records),
              'all_reports_equal': all(r['equal_json'] for r in comparisons),
              'limits': ['Offline software/signal observations only; no human listening, Unity, Windows or true-peak certification.',
                         'Archive runner hardcodes dotnet NOT_EXECUTED_SDK_NOT_INSTALLED; that string is historical source behavior and is not a host availability probe.',
                         'validate_v6 checks stored evidence; actual local replay and all ten independently logged suite counts are recorded separately.']}
    (OUT / 'INTAKE_REPLAY.json').write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    (OUT / 'source-after.json').write_text(json.dumps(after, indent=2, sort_keys=True) + '\n')
    print(json.dumps({k: result[k] for k in ('source_files', 'source_stable', 'tests_by_ast', 'tests_observed_individual', 'all_commands_passed', 'all_reports_equal')}, indent=2))
    return 0 if result['source_stable'] and result['all_commands_passed'] and result['all_reports_equal'] and result['tests_observed_individual'] == result['tests_by_ast'] == 112 else 1

if __name__ == '__main__':
    raise SystemExit(main())
