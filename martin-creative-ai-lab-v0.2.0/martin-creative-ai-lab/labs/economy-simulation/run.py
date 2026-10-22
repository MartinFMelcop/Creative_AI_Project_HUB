#!/usr/bin/env python3
"""Preserved crafting-schema assay and actual C# transactional destination execution."""
from __future__ import annotations
import argparse
import csv
import hashlib
import io
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
CSHARP = ROOT / 'north-star/csharp'
SOURCE = ROOT / 'references/rave-master/snapshots/36af1651271422ae33856e8b5d7b45702215f165/source/RM_CORE/DATA/CORE'
STATUS = {'Implementar', 'Em análise', 'Parcial', 'Futuro'}
ACCESS = {'Inner', 'Chunk', 'Quest', 'MiniDungeon', 'Item'}
UNLOCK = {'Sidequest', 'Quest', 'Drop', 'Discovery'}


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def table(text, required):
    raw = list(csv.reader(io.StringIO(text)))
    if len(raw) < 2 or len(set(raw[0])) != len(raw[0]) or not set(required) <= set(raw[0]):
        raise ValueError('Missing/duplicate headers or empty table')
    if any(len(row) != len(raw[0]) for row in raw[1:]):
        raise ValueError('CSV width mismatch')
    return [dict(zip(raw[0], row)) for row in raw[1:]]


def positive(value):
    return isinstance(value, str) and re.fullmatch(r'[1-9][0-9]{0,8}', value) is not None and int(value) <= 1000000


def ingredients(value):
    """Parse explicit bounded quantities; reject duplicate IDs instead of overwriting."""
    result = {}
    for token in value.split('|'):
        match = re.fullmatch(r'([A-Z][A-Z0-9_]*)\*([1-9][0-9]{0,8})', token)
        if not match or match[1] in result or not positive(match[2]):
            raise ValueError('Malformed or duplicate ingredient')
        result[match[1]] = int(match[2])
    return result


def assay(station_text, recipe_text):
    stations = table(station_text, ['WorkstationID', 'Tipo', 'Acesso_Tipo', 'DC_Padrao', 'StatusImplementacao'])
    recipes = table(recipe_text, ['RecipeID', 'Output_Qtd', 'Ingredientes', 'WorkstationID_Referencia', 'Workstation_Tipo', 'Unlock_Tipo', 'StatusImplementacao'])
    errors = []
    by_id = {}
    for index, row in enumerate(stations, 2):
        sid = row['WorkstationID']
        if not sid or sid in by_id:
            errors.append({'table': 'stations', 'line': index, 'id': sid, 'field': 'WorkstationID', 'value': sid, 'reason': 'missing_or_duplicate_id'})
        else:
            by_id[sid] = row
        for field, valid in [('Acesso_Tipo', row['Acesso_Tipo'] in ACCESS),
                             ('DC_Padrao', positive(row['DC_Padrao'])),
                             ('StatusImplementacao', row['StatusImplementacao'] in STATUS)]:
            if not valid:
                errors.append({'table': 'stations', 'line': index, 'id': sid, 'field': field, 'value': row[field], 'reason': 'invalid_typed_field'})
    seen = set()
    for index, row in enumerate(recipes, 2):
        rid = row['RecipeID']
        problems = []
        if not rid or rid in seen: problems.append(('RecipeID', 'missing_or_duplicate_id'))
        seen.add(rid)
        if not positive(row['Output_Qtd']): problems.append(('Output_Qtd', 'invalid_quantity'))
        try: ingredients(row['Ingredientes'])
        except ValueError: problems.append(('Ingredientes', 'invalid_ingredients'))
        if row['Unlock_Tipo'] not in UNLOCK: problems.append(('Unlock_Tipo', 'invalid_enum'))
        if row['StatusImplementacao'] not in STATUS: problems.append(('StatusImplementacao', 'invalid_enum'))
        station = by_id.get(row['WorkstationID_Referencia'])
        if station is None: problems.append(('WorkstationID_Referencia', 'missing_station'))
        elif row['Workstation_Tipo'] != station['Tipo']: problems.append(('Workstation_Tipo', 'station_type_mismatch'))
        for field, reason in problems:
            errors.append({'table': 'recipes', 'line': index, 'id': rid, 'field': field, 'value': row[field], 'reason': reason})
    invalid_stations = sorted({error['id'] for error in errors if error['table'] == 'stations'})
    return {'station_rows': len(stations), 'recipe_rows': len(recipes),
            'width_only_rival': {'accepted': True, 'limitation': 'Equal field counts do not establish semantic alignment'},
            'typed_direct_adapter': {'accepted': not errors, 'errors': errors},
            'recipes_referencing_invalid_stations': sorted(row['RecipeID'] for row in recipes if row['WorkstationID_Referencia'] in invalid_stations),
            'scope': 'Static preserved CSV assay, not execution of historical crafting or RGSS'}


def fingerprint():
    paths = [SOURCE / name for name in ['CRAFTING_STATION.csv', 'CRAFTING_RECIPE.csv']]
    paths += [ROOT / 'projects/eclipse-fair/Core/Game.cs', ROOT / 'projects/eclipse-fair/Cli/Journal.cs', HERE / 'run.py']
    paths += [p for p in CSHARP.rglob('*') if p.is_file() and p.suffix in {'.cs', '.csproj', '.json', '.props', '.asmdef'} and not {'bin', 'obj'} & set(p.parts)]
    return {p.relative_to(ROOT).as_posix(): digest(p) for p in sorted(paths)}


def invoke(command, timeout=120):
    env = os.environ.copy()
    env.update(DOTNET_CLI_TELEMETRY_OPTOUT='1', DOTNET_NOLOGO='1')
    result = subprocess.run(command, cwd=CSHARP, env=env, text=True, capture_output=True, timeout=timeout)
    if result.returncode:
        raise ValueError(f'Command failed ({result.returncode}): ' + (result.stdout + result.stderr)[-4000:])
    return result.stdout


def validate_destination(native, demo):
    if not isinstance(native, dict) or native.get('schema_version') != 1 or type(native.get('schema_version')) is not int:
        raise ValueError('Invalid native schema')
    if type(native.get('passed')) is not int or native['passed'] <= 0 or type(native.get('failed')) is not int or native['failed'] != 0:
        raise ValueError('Missing or failed actual native controls')
    if native.get('kind') != 'north_star_crafting_native' or not isinstance(native.get('controls'), list) or len(native['controls']) != native['passed'] or any(not isinstance(label, str) or not label.strip() for label in native['controls']):
        raise ValueError('Missing typed native control identities')
    if not isinstance(demo, dict) or type(demo.get('schema_version')) is not int or demo['schema_version'] != 1 or demo.get('kind') != 'north_star_crafting_journeys':
        raise ValueError('Invalid journey schema/kind')
    for key in ['trail_complete', 'plate_complete', 'mixed_complete', 'unprepared_survey_success', 'unprepared_walking_failure', 'failed_trail_no_refund', 'unprepared_retry']:
        row = demo.get(key)
        if not isinstance(row, dict) or any(type(row.get(field)) is not bool for field in ['active', 'complete', 'won']):
            raise ValueError('Invalid journey flags')
        if any(type(row.get(field)) is not int or row[field] < 0 for field in ['attempts', 'consumed_rigs', 'transactions', 'health', 'xp']):
            raise ValueError('Invalid journey resource observations')
        if not isinstance(row.get('inventory'), dict) or any(not isinstance(k, str) or type(v) is not int or v < 0 for k, v in row['inventory'].items()):
            raise ValueError('Invalid journey inventory')
    for key in ['trail_complete', 'plate_complete']:
        row = demo[key]
        if not row['complete'] or not row['won'] or row['active'] or row['consumed_rigs'] != 2 or row['attempts'] != 2:
            raise ValueError('Crafted connected journey did not complete')
    failure = demo['unprepared_walking_failure']
    mixed = demo['mixed_complete']
    survey = demo['unprepared_survey_success']
    failed_rig = demo['failed_trail_no_refund']
    retry = demo['unprepared_retry']
    if failure['won'] or failure['complete'] or failure['active'] or failure['health'] != 0:
        raise ValueError('Unprepared negative missing')
    if not survey['won'] or survey['complete'] or survey['active'] or survey['consumed_rigs'] != 0 or survey['health'] <= 0:
        raise ValueError('Unprepared survey counterexample missing')
    if not mixed['complete'] or not mixed['won'] or mixed['active'] or mixed['consumed_rigs'] != 1 or mixed['attempts'] != 2 or mixed['inventory'].get('fiber') != 2 or mixed['inventory'].get('binder') != 1:
        raise ValueError('Mixed conservative journey missing')
    if failed_rig['won'] or failed_rig['active'] or failed_rig['consumed_rigs'] != 1 or failed_rig['inventory'].get('trail_rig', 0) != 0:
        raise ValueError('Failed rig was refunded or negative missing')
    if demo.get('missing_rig_rejected') is not True or not retry['active'] or retry['attempts'] != 2 or retry['consumed_rigs'] != 1:
        raise ValueError('No-refund retry control missing')


def run(output, dotnet='dotnet', compare=None):
    output = Path(output).resolve()
    if output == ROOT or ROOT in output.parents:
        raise ValueError('Keep outputs outside the entire maintained workspace')
    executable = shutil.which(dotnet)
    if not executable: raise ValueError('Pinned .NET SDK unavailable')
    before = fingerprint()
    source_assay = assay(*( (SOURCE / name).read_text(encoding='utf-8-sig') for name in ['CRAFTING_STATION.csv', 'CRAFTING_RECIPE.csv']))
    version = invoke([executable, '--version'], 15).strip()
    if version != json.loads((CSHARP / 'global.json').read_text())['sdk']['version']:
        raise ValueError('SDK differs from actual configured pin')
    invoke([executable, 'build', 'ForgeChecks/NorthStar.ForgeChecks.csproj', '-c', 'Release'])
    with tempfile.TemporaryDirectory(prefix='economy-simulation-') as folder:
        native_path = Path(folder) / 'native.json'
        demo_path = Path(folder) / 'demo.json'
        invoke([executable, str(CSHARP / 'ForgeChecks/bin/Release/net10.0/NorthStar.ForgeChecks.dll'), 'native', str(native_path)], 30)
        invoke([executable, str(CSHARP / 'Forge/bin/Release/net10.0/NorthStar.Forge.dll'), '--demo', str(demo_path)], 30)
        native = json.loads(native_path.read_text())
        demo = json.loads(demo_path.read_text())
        validate_destination(native, demo)
    if fingerprint() != before: raise ValueError('Inputs changed during execution')
    result = {'schema_version': 1, 'kind': 'crafting_transaction_contract_study', 'identities': before,
              'runtime': {'dotnet_sdk': version, 'unity_executed': False, 'windows_executed': False},
              'legacy_assay': source_assay, 'native': native, 'destination': demo,
              'limits': 'Static legacy-data assay and actual engine-independent C# consumers. No historical full-game, Unity, Windows, Steam, persistence, multiplayer, final canon, human enjoyment or population claims.'}
    if compare and json.loads(Path(compare).read_text()) != result:
        raise ValueError('Executed identities or observations differ from comparison')
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    print('PASS: actual C# forge execution; retained', len(source_assay['typed_direct_adapter']['errors']), 'legacy semantic field failures')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--dotnet', default=os.environ.get('HUB_DOTNET', 'dotnet'))
    parser.add_argument('--compare', type=Path)
    args = parser.parse_args()
    try: run(args.output, args.dotnet, args.compare)
    except (OSError, ValueError, KeyError, subprocess.SubprocessError) as error: parser.exit(1, f'FAIL: {error}\n')


if __name__ == '__main__': main()
