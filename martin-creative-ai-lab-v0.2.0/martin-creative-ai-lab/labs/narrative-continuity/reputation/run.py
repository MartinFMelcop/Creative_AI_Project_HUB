#!/usr/bin/env python3
"""Assay preserved reputation contracts and execute the SAME cases in portable C# rules.

Historical Ruby is read as source data, never executed. The Python model is a declared
interpretation of the inspected helpers, not proof of a historical RGSS game.
"""
from __future__ import annotations
import argparse
import csv
from decimal import Decimal, InvalidOperation
import hashlib
import io
import json
import os
from pathlib import Path
import re
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
SOURCE = 'references/rave-master/snapshots/36af1651271422ae33856e8b5d7b45702215f165/source/'
DEV = SOURCE + 'RM_ACT1/DATA/DEV/RGSS/RM_REPUTATION_RUNTIME.rb'
DIST = SOURCE + 'RM_DIST/RMXP_BASE/ScriptsCustom/RM_REPUTATION_RUNTIME.rb'
CORE_TABLE = SOURCE + 'RM_CORE/DATA/CORE/REPUTATION_RULES.csv'
DIST_TABLE = SOURCE + 'RM_DIST/RMXP_BASE/Data/RM_CSV/REPUTATION_RULES.csv'
REGIONS = SOURCE + 'RM_CORE/DATA/CORE/DIC_REPUTACAO_REGIOES.csv'
LEVEL_TABLE = SOURCE + 'RM_CORE/DATA/CORE/DIC_REPUTACAO_NIVEIS.csv'
RULES_DOC = SOURCE + 'RM_CORE/DATA/CORE/REPUTATION_RULES.md'
QA = SOURCE + 'RM_QA/DATA/QA/RPT_REPUTATION_CONSISTENCY.csv'
SOURCES = (DEV, DIST, CORE_TABLE, DIST_TABLE, REGIONS, LEVEL_TABLE, RULES_DOC, QA)
LEVELS = (-3, -2, -1, 1, 2, 3)
DELTAS = (-2147483648, -100, -7, -6, -5, -4, -3, -2, -1, 0, 1, 2, 3, 4, 5, 6, 7, 100, 2147483647)
SETS = (-2147483648, -100, -4, -3, -2, -1, 0, 1, 2, 3, 4, 100, 2147483647)
ZONES = {'VILA_ROSE', 'FADAS', 'GOBLINS', 'BREJO', 'REINO_ELFO'}
EFFECTS = {
    'shop_buy_mult': ('SHOP', 'float', 'override'),
    'shop_sell_mult': ('SHOP', 'float', 'override'),
    'shop_inventory_tier': ('SHOP', 'enum', 'override'),
    'spawn_enemy_density_mult': ('SPAWN', 'float', 'multiply'),
    'spawn_rare_bonus': ('SPAWN', 'float', 'add'),
    'aggro_on_sight': ('AGGRO', 'bool', 'override'),
    'aggro_range_mult': ('AGGRO', 'float', 'multiply'),
    'ambush_chance_bonus': ('AGGRO', 'float', 'add'),
    'dialogue_tone': ('DIALOGUE', 'enum', 'override'),
    'dialogue_persuasion_dc_delta': ('DIALOGUE', 'int', 'add'),
    'dialogue_options_tier': ('DIALOGUE', 'int', 'max'),
    'access_services_tier': ('ACCESS', 'int', 'max'),
    'quest_tier_max': ('ACCESS', 'int', 'max'),
    'fast_travel': ('ACCESS', 'bool', 'override'),
}
ENUMS = {
    'shop_inventory_tier': {'NONE', 'POOR', 'BASIC', 'STANDARD', 'GOOD', 'VIP'},
    'dialogue_tone': {'HOSTILE', 'THREATENING', 'GUARDED', 'NEUTRAL', 'FRIENDLY', 'ADMIRING'},
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def table(text, headers=None):
    rows = list(csv.reader(io.StringIO(text)))
    require(bool(rows), 'Missing table header')
    require(len(rows[0]) == len(set(rows[0])), 'Duplicate table columns')
    if headers is not None:
        require(rows[0] == headers, 'Unexpected table header')
    require(all(len(row) == len(rows[0]) for row in rows), 'Ragged source table')
    return [dict(zip(rows[0], row)) for row in rows[1:]]


def source_assay(root=ROOT):
    texts = {name: (root / name).read_text(encoding='utf-8-sig') for name in SOURCES}
    require(texts[DEV] == texts[DIST], 'DEV/DIST reputation helper disagreement')
    code = texts[DEV]
    config = {}
    for name in ('clamp_min', 'clamp_max', 'crossing_threshold_abs'):
        found = re.findall(r'def self\.' + name + r';\s*(-?\d+);\s*end', code)
        require(len(found) == 1, 'Missing or repeated source configuration ' + name)
        config[name] = int(found[0])
    require(config == {'clamp_min': -3, 'clamp_max': 3, 'crossing_threshold_abs': 2},
            'Selected source configuration changed; inspect before changing the declared contract')
    # Explicit source-review anchors are guards, not Ruby parsing/execution.
    for anchor in ('v = value.to_i', 'v = normalize_no_zero(v, 0)', 'tentative = cur + d',
                   'if cur == clamp_min && d < 0', 'if cur == clamp_max && d > 0',
                   '(cur < 0 && tentative > 0) || (cur > 0 && tentative < 0)',
                   'if d.abs < crossing_threshold_abs', 'if tentative == 0',
                   'if d.abs >= crossing_threshold_abs', 'tentative = (d > 0) ? 1 : -1',
                   'return (sign_hint >= 0) ? 1 : -1'):
        require(anchor in code, 'Inspected helper contract anchor changed: ' + anchor)
    hook = re.search(r'def self\.effects_for\(zone\)(.*?)\n  end', code, re.S)
    require(hook is not None, 'Missing source effects hook')
    uncommented = '\n'.join(line.split('#', 1)[0].strip() for line in hook.group(1).splitlines()).strip()
    require(uncommented == '[]', 'Source effects hook no longer empty; inspect before claiming its behavior')
    default = re.search(r'def self\.default_for\(zone\)(.*?)\n  end', code, re.S)
    require(default is not None, 'Missing source defaults')
    require(re.search(r'\n\s*1\s*$', default.group(1)) is not None, 'Unknown-zone source fallback changed')
    defaults = table(texts[REGIONS], ['RepZona', 'NomeRegiao', 'VariavelRMXP', 'Start_Default', 'Start_Obs'])
    require({row['RepZona'] for row in defaults} == ZONES and len(defaults) == 5, 'Region table coverage changed')
    village = next(row for row in defaults if row['RepZona'] == 'VILA_ROSE')
    require(Decimal(village['Start_Default']) == -1, 'Retained village table/default conflict changed')
    levels = table(texts[LEVEL_TABLE])
    require(tuple(int(row['RepValor']) for row in levels) == LEVELS, 'Source six-level/no-zero domain changed')
    require(texts[CORE_TABLE] == texts[DIST_TABLE], 'CORE/DIST effect table disagreement')
    effects = table(texts[CORE_TABLE], ['RepZona', 'RepValor', 'EffectType', 'EffectKey', 'EffectValue', 'ValueType', 'StackRule', 'Notes', 'CanonStatus'])
    seen = set()
    for row in effects:
        zone, level, key = row['RepZona'], int(row['RepValor']), row['EffectKey']
        require(zone in ZONES and level in LEVELS and key in EFFECTS, 'Unknown source effect identity/domain')
        require((row['EffectType'], row['ValueType'], row['StackRule']) == EFFECTS[key], 'Source effect type/composition mismatch')
        identity = (zone, level, key)
        require(identity not in seen, 'Duplicate source effect identity')
        seen.add(identity)
        value = row['EffectValue']
        if row['ValueType'] == 'enum':
            require(value in ENUMS[key], 'Invalid source enum')
        elif row['ValueType'] == 'bool':
            require(value in ('0', '1'), 'Invalid source bool')
        elif row['ValueType'] == 'int':
            require(re.fullmatch(r'-?\d+', value) is not None, 'Invalid source integer')
        else:
            require(Decimal(value).is_finite(), 'Invalid source decimal')
    require(len(effects) == 420 and len(seen) == len(ZONES) * len(LEVELS) * len(EFFECTS), 'Incomplete source effect grid')
    qa = table(texts[QA], ['IssueID', 'Severity', 'CheckName', 'RefType', 'RefID', 'Details', 'Suggestion'])
    require(not qa, 'Historical report now has observations; inspect rather than retaining header-only claim')
    return {
        'config': config, 'legal_levels': list(LEVELS), 'typed_source_effect_rows': len(effects),
        'source_only_effect_keys': sorted(EFFECTS), 'dev_dist_helpers_identical': True,
        'core_dist_effect_tables_identical': True,
        'retained_negatives': [
            {'kind': 'default-conflict', 'region': 'VILA_ROSE', 'table': -1, 'helper_fallback': 1, 'resolution': 'UNRESOLVED; neither imported as destination policy'},
            {'kind': 'empty-effects-hook', 'actual_source_return': [], 'resolution': 'No historical effects execution or destination table import claimed'},
            {'kind': 'unknown-zone-fallback', 'helper_result': 1, 'resolution': 'Source permissiveness is not destination authority'},
            {'kind': 'header-only-qa', 'data_rows': 0, 'resolution': 'Not an executed historical consistency result'},
            {'kind': 'ruby-coercion', 'source': 'value.to_i and delta.to_i', 'resolution': 'Only explicit int32 input contract is adapted; Ruby coercion is not ported'},
        ],
        'scope': 'Static source-bound interpretation and complete typed table audit; no historical Ruby/RGSS/RMXP execution, effects application, source fiction/default import or human evidence.',
    }


def model_set(value, config):
    value = 1 if value == 0 else value
    return min(config['clamp_max'], max(config['clamp_min'], value))


def model_add(current, delta, config):
    require(current in LEVELS, 'Python model requires explicit legal standing')
    if current == config['clamp_min'] and delta < 0 or current == config['clamp_max'] and delta > 0:
        return current
    tentative = current + delta
    threshold = config['crossing_threshold_abs']
    if current < 0 < tentative or current > 0 > tentative:
        if abs(delta) < threshold:
            return current
    if tentative == 0:
        if abs(delta) < threshold:
            return current
        tentative = 1 if delta > 0 else -1
    return min(config['clamp_max'], max(config['clamp_min'], tentative))


def vectors(config):
    cases = []
    for index, value in enumerate(SETS):
        cases.append({'id': 'set-' + str(index), 'operation': 'set', 'value': value, 'expected': model_set(value, config)})
    for current in LEVELS:
        for index, delta in enumerate(DELTAS):
            cases.append({'id': 'add-' + str(current) + '-' + str(index), 'operation': 'add', 'current': current, 'delta': delta, 'expected': model_add(current, delta, config)})
    return {'schema_version': 1, 'cases': cases}


def compare_results(vector, result):
    require(result.get('schema_version') == 1, 'Unexpected C# vector result schema')
    rows = result.get('cases')
    require(isinstance(rows, list) and len(rows) == len(vector['cases']), 'C# result count mismatch')
    for expected, actual in zip(vector['cases'], rows):
        require(actual == {'id': expected['id'], 'actual': expected['expected'], 'expected': expected['expected'], 'passed': True}, 'False, reordered or misbound C# result')
    require(result.get('passed') == len(rows) and result.get('failed') == 0, 'C# vector result totals disagree')


def input_hashes(root=ROOT):
    names = set(SOURCES)
    names.update(str(p.relative_to(root)) for folder in (root/'north-star/reputation-study/Rules', root/'north-star/reputation-study/Checks', root/'labs/narrative-continuity/reputation')
                 for p in folder.rglob('*') if p.suffix in ('.cs', '.csproj', '.py', '.json') and not {'bin', 'obj', '__pycache__'} & set(p.parts))
    return {name: sha(root/name) for name in sorted(names)}


def run(output, dotnet):
    output = output.resolve()
    require(not output.is_relative_to(ROOT), 'Keep outputs outside maintained workspace')
    output.mkdir(parents=True, exist_ok=False)
    sdk = shutil.which(str(dotnet))
    require(sdk is not None, 'Actual pinned SDK executable unavailable')
    before = input_hashes()
    commands = []
    def save(name, value):
        (output/name).write_text(json.dumps(value, indent=2) + '\n')
    def execute(command, cwd=ROOT/'north-star/csharp', timeout=180):
        result = subprocess.run([str(x) for x in command], cwd=cwd, capture_output=True, text=True,
                                env=dict(os.environ, DOTNET_PROCESSOR_COUNT='2', DOTNET_CLI_TELEMETRY_OPTOUT='1', DOTNET_NOLOGO='1'), timeout=timeout)
        commands.append({'command': [str(x) for x in command], 'cwd': str(cwd), 'exit_code': result.returncode, 'stdout': result.stdout, 'stderr': result.stderr})
        save('commands.json', commands)
        require(result.returncode == 0, (result.stdout + result.stderr)[-4000:])
        return result.stdout
    require(execute([sdk, '--version']).strip() == '10.0.401', 'Actual SDK differs from existing pin')
    assay = source_assay()
    vector = vectors(assay['config'])
    save('source-assay.json', assay)
    save('source-vectors.json', vector)
    execute(['python3', HERE/'test_instrument.py'], cwd=ROOT)
    project = ROOT/'north-star/reputation-study/Checks/NorthStar.ReputationChecks.csproj'
    execute([sdk, 'build', project, '-c', 'Release', '-m:1', '--disable-build-servers'])
    dll = project.parent/'bin/Release/net10.0/NorthStar.ReputationChecks.dll'
    execute([sdk, dll, '--vectors', output/'source-vectors.json', output/'csharp-vectors.json'])
    native_path = output/'native.json'
    execute([sdk, dll, '--native', native_path])
    result = json.loads((output/'csharp-vectors.json').read_text())
    compare_results(vector, result)
    require(input_hashes() == before, 'Source or instrument changed during actual execution')
    save('results.json', {'schema_version': 1, 'checks': {'passed': len(vector['cases']), 'failed': 0},
                          'same_python_csharp_cases': len(vector['cases']), 'source_assay': assay,
                          'source_hashes': before, 'source_stable': True,
                          'native': json.loads(native_path.read_text()),
                          'scope': 'Selected source arithmetic interpretation and actual C# rules; table effects remain source-only. No Ruby/RMXP, historical game, Unity/Windows, human trust or balance claim.'})
    print('PASS: SAME ' + str(len(vector['cases'])) + ' Python/C# source cases;420 typed source-only effects; native controls and retained negative decisions')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dotnet', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    try:
        run(args.output, args.dotnet)
    except (OSError, ValueError, InvalidOperation, subprocess.SubprocessError) as error:
        parser.exit(1, 'FAIL: ' + str(error) + '\n')
