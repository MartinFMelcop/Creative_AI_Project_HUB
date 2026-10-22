#!/usr/bin/env python3
"""Typed legacy identity assay and executed original C# loadout consumer.

Static helper bindings and explicit behavioral models are not Ruby/RGSS execution.
"""
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
SOURCE = ROOT / 'references/rave-master/snapshots/36af1651271422ae33856e8b5d7b45702215f165/source'
NAMES = {
    'classes': 'RM_ACT1/DATA/CORE/ACT1_CLASSES_CANON.csv',
    'backgrounds': 'RM_ACT1/DATA/CORE/ACT1_ANTECEDENTES_CANON.csv',
    'relations': 'RM_ACT1/DATA/CORE/ACT1_REL_CLASS_ANTECEDENTE_CANON.csv',
    'skills': 'RM_ACT1/DATA/CORE/ACT1_COMBAT_SKILLS_CANON.csv',
    'act1_skills': 'RM_ACT1/DATA/DEV/RGSS/RM_UI_SKILL_EQUIP_RUNTIME.rb',
    'dist_skills': 'RM_DIST/RMXP_BASE/ScriptsCustom/RM_UI_SKILL_EQUIP_RUNTIME.rb',
    'act1_creation': 'RM_ACT1/DATA/DEV/RGSS/RM_CHARACTER_CREATE_RUNTIME.rb',
}


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def table(text, required):
    raw = list(csv.reader(io.StringIO(text)))
    if len(raw) < 2 or len(raw[0]) != len(set(raw[0])) or not set(required) <= set(raw[0]):
        raise ValueError('Missing/duplicate headers or empty source table')
    if len(raw) > 10001 or any(len(row) != len(raw[0]) for row in raw[1:]):
        raise ValueError('Incomplete or overbound source table')
    return [dict(zip(raw[0], row)) for row in raw[1:]]


def identifier(value):
    if not isinstance(value, str) or re.fullmatch(r'[A-Za-z0-9_-]{1,64}', value) is None:
        raise ValueError('Invalid source identity')
    return value


def positive(value):
    if not isinstance(value, str) or re.fullmatch(r'[1-9][0-9]{0,3}', value) is None or int(value) > 4096:
        raise ValueError('Invalid source level/identity integer')
    return int(value)


def catalog(class_text, background_text, relation_text, skill_text):
    classes = table(class_text, ['ClassKey'])
    backgrounds = table(background_text, ['AntecedenteID', 'AntecedenteKey'])
    relations = table(relation_text, ['ClassKey', 'AntecedenteID', 'Allowed'])
    skills = table(skill_text, ['SkillID', 'ClassKey', 'NivelAprendizado', 'ClassVariant'])
    class_ids = [identifier(row['ClassKey']) for row in classes]
    background_ids = [str(positive(row['AntecedenteID'])) for row in backgrounds]
    background_keys = [identifier(row['AntecedenteKey']) for row in backgrounds]
    skill_ids = [identifier(row['SkillID']) for row in skills]
    for values in [class_ids, background_ids, background_keys, skill_ids]:
        if len(set(values)) != len(values): raise ValueError('Duplicate source identity')
    allowed = set()
    seen = set()
    for row in relations:
        pair = (row['ClassKey'], row['AntecedenteID'])
        if pair[0] not in class_ids or pair[1] not in background_ids or pair in seen or row['Allowed'] not in {'0', '1'}:
            raise ValueError('Duplicate/unknown/invalid source class-background relation')
        seen.add(pair)
        if row['Allowed'] == '1': allowed.add(pair)
    parsed_skills = []
    for row in skills:
        if row['ClassKey'] not in class_ids: raise ValueError('Skill references unknown class')
        parsed_skills.append({'id': row['SkillID'], 'class_id': row['ClassKey'], 'level': positive(row['NivelAprendizado'])})
    # Index-based candidate intake versus separately scanned source-row reference.
    # This is source predicate evaluation until the destination study protocol executes it.
    class_background = []
    for class_id in class_ids:
        for background in background_ids:
            candidate = (class_id, background) in allowed
            reference = any(r['ClassKey'] == class_id and r['AntecedenteID'] == background and r['Allowed'] == '1' for r in relations)
            if candidate != reference: raise ValueError('Class/background reference disagreement')
            class_background.append({'class_id': class_id, 'background_id': background, 'allowed': reference})
    owner_index = {row['id']: row['class_id'] for row in parsed_skills}
    class_skill = []
    for class_id in class_ids:
        for skill in parsed_skills:
            candidate = owner_index[skill['id']] == class_id
            reference = any(r['SkillID'] == skill['id'] and r['ClassKey'] == class_id for r in skills)
            if candidate != reference: raise ValueError('Class/skill reference disagreement')
            class_skill.append({'class_id': class_id, 'skill_id': skill['id'], 'allowed': reference})
    return {'classes': class_ids, 'backgrounds': background_ids, 'allowed_pairs': [list(pair) for pair in sorted(allowed)],
            'skills': parsed_skills, 'class_background': class_background, 'class_skill': class_skill,
            'metadata_boundary': 'ClassVariant, fiction, costs, full effects and descriptions are preserved metadata, not adopted restrictions or implemented abilities.'}


def helper_assay(act1, distributed, creation, data):
    bindings = {
        'act1': {'four_slots': 'SLOTS = 4' in act1,
                 'class_filter': 'next if allowed_class && class_key && class_key != allowed_class' in act1,
                 'global_unkeyed_cache': 'def self.skill_ids; @cache ||= _load; @cache[0]; end' in act1,
                 'silent_erasure': 'eq_hash[i] = nil unless allowed.include?(sid)' in act1},
        'distributed': {'four_slots': 'SLOTS = 4' in distributed,
                        'class_filter': 'next if allowed_class && class_key && class_key != allowed_class' in distributed,
                        'global_unkeyed_cache': 'def self.skill_ids; @cache ||= _load; @cache[0]; end' in distributed,
                        'silent_erasure': 'eq_hash[i] = nil unless allowed.include?(sid)' in distributed},
        'creation': {'stray_regex_fragment': '\n/)\n' in creation,
                     'missing_relation_all_background_fallback': 'return ANTECEDENTES if @allowed_by_class.nil? || @allowed_by_class[class_key].nil?' in creation,
                     'missing_kit_generic_supplies': "Fallback: dinheiro +200 (B)." in creation},
    }
    expected = {'four_slots': True, 'class_filter': True, 'global_unkeyed_cache': True, 'silent_erasure': True}
    if bindings['act1'] != expected or bindings['distributed'] != dict(expected, class_filter=False, silent_erasure=False):
        raise ValueError('Preserved skill helper variant bindings changed; review before claiming model relevance')
    first, second = data['classes'][:2]
    old = [s['id'] for s in data['skills'] if s['class_id'] == first]
    new = [s['id'] for s in data['skills'] if s['class_id'] == second]
    if not old or not new: raise ValueError('Counterexamples require two populated classes')
    original = [old[0], None, None, None]
    cleaned = [sid if sid in new else None for sid in original]
    return {'scope': 'Static code bindings plus explicit Python models; no historical helper or Ruby/RGSS game executed.',
            'bindings': bindings,
            'stale_cache_model': {'first_class': first, 'second_class': second, 'cached_ids': old, 'required_second_ids': new,
                                 'incompatible_retained': sorted(set(old) - set(new)), 'missing_second': sorted(set(new) - set(old))},
            'silent_erasure_model': {'prior_equipped': original, 'after_legacy_cleanup_model': cleaned,
                                    'after_transactional_rejection': original, 'prior_choice_erased': cleaned != original},
            'missing_relation_model': {'unknown_class': 'UNKNOWN_CLASS', 'permissive_background_count': len(data['backgrounds']), 'strict_result': 'REJECTED without state change'}}


def study_protocol(data):
    cases = []; expected = []
    def add(class_id, background, level, slots, accepted, prefix):
        key = prefix + '_' + str(len(cases))
        cases.append(dict(id=key, class_id=class_id, background_id=background, level=level, slots=slots))
        expected.append(dict(id=key, accepted=accepted))
    for row in data['class_background']:
        add(row['class_id'], row['background_id'], 4096, [None] * 4, row['allowed'], 'pair')
    first_background = {c: next(pair[1] for pair in data['allowed_pairs'] if pair[0] == c) for c in data['classes']}
    for row in data['class_skill']:
        add(row['class_id'], first_background[row['class_id']], 4096, [row['skill_id'], None, None, None], row['allowed'], 'skill')
    for skill in data['skills']:
        if skill['level'] > 1:
            add(skill['class_id'], first_background[skill['class_id']], skill['level'] - 1, [skill['id'], None, None, None], False, 'level_below')
        add(skill['class_id'], first_background[skill['class_id']], skill['level'], [skill['id'], None, None, None], True, 'level_exact')
    protocol = dict(schema_version=1, classes=data['classes'], backgrounds=data['backgrounds'],
                    relations=[dict(class_id=c, background_id=b) for c, b in data['allowed_pairs']],
                    skills=[dict(id=row['id'], class_id=row['class_id'], min_level=row['level'], action='skill') for row in data['skills']], cases=cases)
    return protocol, expected


def validate_study(result, expected):
    if not isinstance(result, dict) or type(result.get('schema_version')) is not int or result['schema_version'] != 1 or result.get('kind') != 'loadout_compatibility_results':
        raise ValueError('Invalid compatibility result schema/kind')
    rows = result.get('rows')
    if not isinstance(rows, list) or len(rows) != len(expected): raise ValueError('Incomplete compatibility execution')
    for row, reference in zip(rows, expected):
        if not isinstance(row, dict) or set(row) != {'id', 'accepted'} or not isinstance(row.get('id'), str) or type(row.get('accepted')) is not bool or row != reference:
            raise ValueError('Actual C# compatibility disagrees with independent source reference')


def protocol_rejections(executable, protocol, folder):
    """Exercise the actual compiled host; expected failures must not emit success data."""
    base = json.dumps(protocol)
    variants = {
        'schema_boolean': base.replace('"schema_version": 1', '"schema_version": true', 1),
        'duplicate_field': base.replace('"schema_version": 1', '"schema_version": 1, "schema_version": 1', 1),
        'unknown_field': base[:-1] + ', "unknown": 0}',
        'missing_field': base.replace('"schema_version": 1, ', '', 1),
    }
    fractional = json.loads(base); fractional['cases'][0]['level'] = 1.5
    variants['fractional_level'] = json.dumps(fractional)
    duplicate = json.loads(base); duplicate['cases'].append(duplicate['cases'][0])
    variants['duplicate_case'] = json.dumps(duplicate)
    observations = []
    for label, text in variants.items():
        source = Path(folder) / (label + '.json'); target = Path(folder) / (label + '-result.json')
        source.write_text(text)
        command = [executable, str(CSHARP / 'LoadoutChecks/bin/Release/net10.0/NorthStar.LoadoutChecks.dll'), 'study', str(source), str(target)]
        result = subprocess.run(command, cwd=CSHARP, text=True, capture_output=True, timeout=15)
        if result.returncode == 0 or target.exists():
            raise ValueError('Malformed protocol accepted or emitted success: ' + label)
        observations.append({'control': label, 'expected_failure_observed': True, 'success_output_created': False})
    return observations


def fingerprint():
    paths = [SOURCE / name for name in NAMES.values()] + [HERE / 'run.py']
    paths += [p for p in CSHARP.rglob('*') if p.is_file() and p.suffix in {'.cs', '.csproj', '.json', '.props', '.asmdef'} and not {'bin', 'obj'} & set(p.parts)]
    return {p.relative_to(ROOT).as_posix(): digest(p) for p in sorted(paths)}


def invoke(command, timeout=120):
    env = os.environ.copy(); env.update(DOTNET_CLI_TELEMETRY_OPTOUT='1', DOTNET_NOLOGO='1')
    result = subprocess.run(command, cwd=CSHARP, env=env, text=True, capture_output=True, timeout=timeout)
    if result.returncode: raise ValueError(f'Command failed ({result.returncode}): ' + (result.stdout + result.stderr)[-4000:])
    return result.stdout


def validate_native(native):
    if not isinstance(native, dict) or type(native.get('schema_version')) is not int or native['schema_version'] != 1 or native.get('kind') != 'north_star_loadout_native':
        raise ValueError('Invalid actual native schema/kind')
    if type(native.get('passed')) is not int or native['passed'] < 1 or type(native.get('failed')) is not int or native['failed'] != 0:
        raise ValueError('Missing/failed actual native controls')
    if not isinstance(native.get('controls'), list) or len(native['controls']) != native['passed'] or any(not isinstance(x, str) or not x.strip() for x in native['controls']):
        raise ValueError('Native controls must have actual identities')


def validate_demo(demo):
    if not isinstance(demo, dict) or type(demo.get('schema_version')) is not int or demo['schema_version'] != 1 or demo.get('kind') != 'north_star_loadout_journeys':
        raise ValueError('Invalid destination journey schema/kind')
    for key in ['earned_level2', 'anchor_trail_complete', 'lure_plate_complete', 'empty_survey_success', 'empty_crossing_failure']:
        row = demo.get(key)
        if not isinstance(row, dict) or any(type(row.get(field)) is not bool for field in ['active', 'complete', 'won']):
            raise ValueError('Invalid actual journey flags')
        if any(type(row.get(field)) is not int or row[field] < 0 for field in ['stage', 'beat', 'position', 'health', 'resolve', 'attempts', 'consumed_rigs', 'transactions', 'xp', 'level', 'unspent', 'vitality', 'focus']):
            raise ValueError('Invalid actual journey resource observations')
        if not isinstance(row.get('class_id'), str) or not isinstance(row.get('background_id'), str) or row.get('rig') not in {'Plate', 'Trail', 'Unprepared'}:
            raise ValueError('Invalid actual journey identity')
        slots = row.get('slots')
        if not isinstance(slots, list) or len(slots) != 4 or any(x is not None and (not isinstance(x, str) or not x) for x in slots):
            raise ValueError('Invalid actual four-slot preparation')
        if not isinstance(row.get('inventory'), dict) or any(not isinstance(k, str) or type(v) is not int or v < 0 for k, v in row['inventory'].items()):
            raise ValueError('Invalid actual journey inventory')
    for key, class_id, rig in [('anchor_trail_complete', 'anchor', 'Trail'), ('lure_plate_complete', 'lure', 'Plate')]:
        row = demo[key]
        if not row['complete'] or not row['won'] or row['active'] or row['class_id'] != class_id or row['rig'] != rig or row['attempts'] != 2 or row['consumed_rigs'] != 2 or row['xp'] != 25 or row['health'] <= 0:
            raise ValueError('Independent discipline/outfit connected journey missing')
    earned = demo['earned_level2']
    if earned['xp'] != 10 or earned['level'] != 2 or earned['active'] or earned['complete'] or not earned['won']:
        raise ValueError('Actual earned preparation boundary missing')
    anchor = demo['anchor_trail_complete']
    if anchor['slots'] != ['brace', 'dash', None, None]: raise ValueError('Earned shared action was not equipped')
    empty = demo['empty_survey_success']; failed = demo['empty_crossing_failure']
    if empty['slots'] != [None] * 4 or not empty['won'] or empty['complete'] or empty['active'] or empty['xp'] != 10 or empty['consumed_rigs'] != 0:
        raise ValueError('Empty-loadout survey counterexample missing')
    if failed['slots'] != [None] * 4 or failed['won'] or failed['complete'] or failed['active'] or failed['health'] != 0 or failed['xp'] != 10:
        raise ValueError('Empty-loadout walking failure missing')
    if demo.get('invalid_proposal_rejected') is not True or demo.get('invalid_proposal_unchanged') is not True:
        raise ValueError('Transactional preparation rejection missing')


def run(output, dotnet='dotnet', compare=None):
    output = Path(output).resolve()
    if output == ROOT or ROOT in output.parents: raise ValueError('Keep outputs outside entire maintained workspace')
    executable = shutil.which(dotnet)
    if not executable: raise ValueError('Pinned .NET SDK unavailable')
    before = fingerprint()
    texts = {key: (SOURCE / name).read_text(encoding='utf-8-sig') for key, name in NAMES.items()}
    data = catalog(*(texts[key] for key in ['classes', 'backgrounds', 'relations', 'skills']))
    helper = helper_assay(texts['act1_skills'], texts['dist_skills'], texts['act1_creation'], data)
    version = invoke([executable, '--version'], 15).strip()
    if version != json.loads((CSHARP / 'global.json').read_text())['sdk']['version']: raise ValueError('SDK differs from configured pin')
    invoke([executable, 'build', 'LoadoutChecks/NorthStar.LoadoutChecks.csproj', '-c', 'Release'])
    with tempfile.TemporaryDirectory(prefix='world-gameplay-') as folder:
        native_path = Path(folder) / 'native.json'; demo_path = Path(folder) / 'demo.json'
        invoke([executable, str(CSHARP / 'LoadoutChecks/bin/Release/net10.0/NorthStar.LoadoutChecks.dll'), 'native', str(native_path)], 30)
        invoke([executable, str(CSHARP / 'Loadout/bin/Release/net10.0/NorthStar.Loadout.dll'), '--demo', str(demo_path)], 30)
        native = json.loads(native_path.read_text()); demo = json.loads(demo_path.read_text())
        validate_native(native); validate_demo(demo)
        protocol, expected = study_protocol(data)
        study_input = Path(folder) / 'input.json'; study_output = Path(folder) / 'study.json'
        study_input.write_text(json.dumps(protocol))
        invoke([executable, str(CSHARP / 'LoadoutChecks/bin/Release/net10.0/NorthStar.LoadoutChecks.dll'), 'study', str(study_input), str(study_output)], 30)
        study = json.loads(study_output.read_text()); validate_study(study, expected)
        malformed_protocol_controls = protocol_rejections(executable, protocol, folder)
    if fingerprint() != before: raise ValueError('Inputs changed during execution')
    result = {'schema_version': 1, 'kind': 'world_loadout_contract_study', 'identities': before,
              'runtime': {'dotnet_sdk': version, 'unity_executed': False, 'windows_executed': False},
              'legacy_catalog': data, 'helper_assay': helper, 'native': native, 'destination': demo,
              'compatibility_execution': study, 'compatibility_cases': len(expected),
              'malformed_protocol_controls': malformed_protocol_controls,
              'protocol_sha256': hashlib.sha256(json.dumps(protocol, sort_keys=True, separators=(',', ':')).encode()).hexdigest(),
              'limits': 'Typed preserved-data/static-binding assay, labeled behavioral models and actual original C# consumers. No historical Ruby/RGSS game, Unity, Windows, Steam, final class canon, implemented legacy skill catalog, human preference or balance proof.'}
    if compare and json.loads(Path(compare).read_text()) != result: raise ValueError('Executed identities or observations differ from comparison')
    output.parent.mkdir(parents=True, exist_ok=True); output.write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    print('PASS: World loadout assay and actual C# destination; retained helper variant/counterexample limits')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--dotnet', default=os.environ.get('HUB_DOTNET', 'dotnet')); parser.add_argument('--compare', type=Path)
    args = parser.parse_args()
    try: run(args.output, args.dotnet, args.compare)
    except (OSError, ValueError, KeyError, subprocess.SubprocessError) as error: parser.exit(1, f'FAIL: {error}\n')


if __name__ == '__main__': main()
