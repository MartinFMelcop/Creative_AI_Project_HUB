#!/usr/bin/env python3
"""Bind inspected recovery invariants to actual persistent C# consumer execution.

Source bindings are static observations, not execution of the historical origins.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
CSHARP = ROOT / 'north-star/csharp'
SOURCE_NAMES = {
    'cinder_journal': 'projects/cinderwatch/Core/Journal.cs',
    'eclipse_journal': 'projects/eclipse-fair/Cli/Journal.cs',
    'rooms_store': 'projects/realtime-integration-lab/rooms-store.cjs',
    'rooms_actions': 'projects/realtime-integration-lab/rooms-actions.cjs',
    'rooms_backup': 'projects/realtime-integration-lab/rooms-backup.cjs',
}


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def source_assay(texts):
    """Require the exact inspected invariant bindings before transferring their scope."""
    cinder = texts['cinder_journal']; actions = texts['rooms_actions']
    bindings = {
        'cinder_bounded_versioned_replay': all(x in cinder for x in ['save.Schema!=1', 'save.Version!="0.1.0"', 'save.Actions.Length>512', 'foreach(var e in save.Actions)', 'if(!accepted)throw new InvalidDataException']),
        'cinder_unknown_json_fields_refused': 'UnmappedMemberHandling=JsonUnmappedMemberHandling.Disallow' in cinder,
        'cinder_temporary_replace_cleanup': all(x in cinder for x in ['File.WriteAllText(temp,Encode(game)); File.Move(temp,full,true);', 'finally { if(File.Exists(temp))File.Delete(temp); }']),
        'eclipse_temporary_replace_cleanup': all(x in texts['eclipse_journal'] for x in ['File.Move(temporary,path,true)', 'finally {if(File.Exists(temporary))File.Delete(temporary);}']),
        'rooms_content_bound_retry': 'if(old.command!==encoded)throw new Error' in actions and 'duplicate:true' in actions,
        'rooms_transaction_rollback': "this.db.exec('BEGIN IMMEDIATE')" in actions and "this.db.exec('ROLLBACK')" in actions,
        'rooms_commit_before_receipt': "this.db.exec('COMMIT');return {action,eventId:event.id" in actions,
        'rooms_entry_content_bound_retry': 'old.room_id !== roomId || old.body !== body || old.kind !== kind' in texts['rooms_store'],
        'rooms_backup_flush': 'fs.fsyncSync(fd)' in texts['rooms_backup'],
        'rooms_backup_refuses_overwrite': 'recovery never overwrites data' in texts['rooms_backup'],
    }
    if not all(bindings.values()):
        raise ValueError('Inspected origin recovery binding changed: ' + ', '.join(k for k, v in bindings.items() if not v))
    return {'scope': 'Static binding assay of inspected source invariants; origins were not executed by this instrument.',
            'bindings': bindings,
            'material_limits': {
                'cinder_store_explicit_file_flush_present': 'Flush(true)' in cinder or 'fsync' in cinder,
                'sqlite_transfer_scope': 'P11 transaction invariants inform the consumer; no provider compatibility follows from source inspection.',
                'execution_limit': 'These bindings do not establish power-loss durability, network authority or origin execution.',
            }}


def fingerprint():
    paths = [ROOT / name for name in SOURCE_NAMES.values()] + [HERE / 'run.py']
    paths += [p for p in CSHARP.rglob('*') if p.is_file() and p.suffix in {'.cs', '.csproj', '.json', '.props', '.asmdef'} and not {'bin', 'obj'} & set(p.parts)]
    return {p.relative_to(ROOT).as_posix(): digest(p) for p in sorted(paths)}


def invoke(command, timeout=120):
    env = os.environ.copy(); env.update(DOTNET_CLI_TELEMETRY_OPTOUT='1', DOTNET_NOLOGO='1')
    result = subprocess.run(command, cwd=CSHARP, env=env, text=True, capture_output=True, timeout=timeout)
    if result.returncode:
        raise ValueError(f'Command failed ({result.returncode}): ' + (result.stdout + result.stderr)[-4000:])
    return result.stdout


def validate_native(native):
    if not isinstance(native, dict) or type(native.get('schema_version')) is not int or native['schema_version'] != 1 or native.get('kind') != 'north_star_recovery_native':
        raise ValueError('Invalid native recovery schema/kind')
    if type(native.get('passed')) is not int or native['passed'] < 1 or type(native.get('failed')) is not int or native['failed'] != 0:
        raise ValueError('Missing or failed native recovery controls')
    if not isinstance(native.get('controls'), list) or len(native['controls']) != native['passed'] or any(not isinstance(x, str) or not x.strip() for x in native['controls']):
        raise ValueError('Native controls require actual identities')


def validate_state(row):
    if not isinstance(row, dict): raise ValueError('Expected complete gameplay observations')
    if any(type(row.get(field)) is not bool for field in ['active', 'complete', 'won']):
        raise ValueError('Invalid gameplay flags')
    numeric = ['stage', 'beat', 'position', 'health', 'resolve', 'attempts', 'consumed_rigs', 'transactions', 'level', 'xp', 'unspent', 'vitality', 'focus']
    if any(type(row.get(field)) is not int or row[field] < 0 for field in numeric) or not 1 <= row['level'] <= 4096:
        raise ValueError('Invalid gameplay resource observations')
    if row.get('class_id') not in {'anchor', 'lure'} or row.get('background_id') not in {'workshop', 'trailborn'} or row.get('rig') not in {'Plate', 'Trail', 'Unprepared'}:
        raise ValueError('Invalid original consumer identity')
    slots = row.get('slots')
    if not isinstance(slots, list) or len(slots) != 4 or any(x is not None and (not isinstance(x, str) or not x) for x in slots):
        raise ValueError('Invalid four-slot observations')
    stock = row.get('inventory')
    if not isinstance(stock, dict) or any(not isinstance(k, str) or not k or type(v) is not int or not 0 <= v <= 1000000 for k, v in stock.items()):
        raise ValueError('Invalid inventory observations')


def validate_demo(demo):
    if not isinstance(demo, dict) or type(demo.get('schema_version')) is not int or demo['schema_version'] != 1 or demo.get('kind') != 'north_star_recovery_journeys':
        raise ValueError('Invalid persistent destination schema/kind')
    for key in ['mid_encounter_before_restart', 'mid_encounter_after_restart', 'completed', 'no_refund']:
        validate_state(demo.get(key))
    before = demo['mid_encounter_before_restart']; after = demo['mid_encounter_after_restart']
    if before != after or not before['active'] or before['complete'] or before['beat'] != 1 or before['xp'] != 0 or before['consumed_rigs'] != 1:
        raise ValueError('Actual mid-encounter process restart did not preserve whole state')
    complete = demo['completed']
    if complete['active'] or not complete['complete'] or not complete['won'] or complete['xp'] != 25 or complete['level'] != 3 or complete['consumed_rigs'] != 2 or complete['attempts'] != 2 or complete['slots'] != ['brace', 'dash', None, None]:
        raise ValueError('Recovered connected earned-action journey missing')
    if type(demo.get('completed_revision')) is not int or demo['completed_revision'] != 16:
        raise ValueError('Completed command revision is missing or inconsistent')
    replay = demo.get('replay_after_restart')
    if not isinstance(replay, dict) or replay.get('duplicate') is not True or replay.get('unchanged') is not True or replay.get('request_id') != 'craft_1' or replay.get('command') != {'op': 'craft', 'recipe': 'trail_rig'}:
        raise ValueError('Durable request replay must preserve ownership and gameplay')
    for flag in ['conflict_rejected', 'invalid_file_rejected', 'existing_new_rejected', 'second_writer_rejected', 'owner_death_recovered', 'no_refund_retry_rejected']:
        if demo.get(flag) is not True: raise ValueError('Missing retained recovery refusal: ' + flag)
    rows = demo.get('failure_boundaries')
    if not isinstance(rows, list) or len(rows) != 3 or any(not isinstance(row, dict) for row in rows):
        raise ValueError('Missing actual child-process failure boundaries')
    if {row.get('point') for row in rows} != {'before_write', 'before_replace', 'after_replace'}:
        raise ValueError('Failure boundaries must be distinct and complete')
    for row in rows:
        validate_state(row.get('expected')); validate_state(row.get('recovered'))
        committed = row['point'] == 'after_replace'
        revision = 1 if committed else 0
        if type(row.get('child_exit')) is not int or row['child_exit'] != 79:
            raise ValueError('Declared process termination boundary was not reached')
        if any(type(row.get(field)) is not int or row[field] != revision for field in ['expected_revision', 'recovered_revision']):
            raise ValueError('Recovered journal revision does not match commit boundary')
        if row['expected'] != row['recovered'] or row.get('state_preserved') is not True:
            raise ValueError('Failure recovered mixed or partial gameplay state')
        if row.get('retry_request_id') != 'attempt' or row.get('retry_command') != {'op': 'craft', 'recipe': 'trail_rig'} or type(row.get('retry_duplicate')) is not bool or row['retry_duplicate'] != committed or row.get('retry_accepted') is not True:
            raise ValueError('Retry receipt disagrees with durable commit ownership')
        stock = row['recovered']['inventory']
        if stock.get('fiber') != (2 if committed else 4) or stock.get('binder') != (1 if committed else 2) or stock.get('trail_rig', 0) != (1 if committed else 0) or row['recovered']['transactions'] != revision:
            raise ValueError('Crash prefix did not conserve input/output ownership')
    lost = demo['no_refund']
    if lost['active'] or lost['won'] or lost['health'] != 0 or lost['xp'] != 0 or lost['consumed_rigs'] != 1 or lost['inventory'].get('trail_rig', 0) != 0 or lost['inventory'].get('fiber') != 2 or lost['inventory'].get('binder') != 1:
        raise ValueError('Failed encounter recovery refunded supplies or awarded XP')


def run(output, dotnet='dotnet', compare=None):
    output = Path(output).resolve()
    if output == ROOT or ROOT in output.parents:
        raise ValueError('Keep outputs outside the entire maintained workspace')
    executable = shutil.which(dotnet)
    if not executable: raise ValueError('Pinned .NET SDK unavailable')
    before = fingerprint()
    assay = source_assay({key: (ROOT / name).read_text() for key, name in SOURCE_NAMES.items()})
    version = invoke([executable, '--version'], 15).strip()
    if version != json.loads((CSHARP / 'global.json').read_text())['sdk']['version']:
        raise ValueError('SDK differs from actual configured pin')
    invoke([executable, 'build', 'RecoveryChecks/NorthStar.RecoveryChecks.csproj', '-c', 'Release'])
    with tempfile.TemporaryDirectory(prefix='networking-persistence-') as folder:
        native_path = Path(folder) / 'native.json'; demo_path = Path(folder) / 'demo.json'
        invoke([executable, str(CSHARP / 'RecoveryChecks/bin/Release/net10.0/NorthStar.RecoveryChecks.dll'), 'native', str(native_path)], 60)
        invoke([executable, str(CSHARP / 'Recovery/bin/Release/net10.0/NorthStar.Recovery.dll'), '--demo', str(demo_path)], 90)
        native = json.loads(native_path.read_text()); demo = json.loads(demo_path.read_text())
        validate_native(native); validate_demo(demo)
    if fingerprint() != before: raise ValueError('Executed inputs changed during study')
    result = {'schema_version': 1, 'kind': 'persistent_expedition_contract_study', 'identities': before,
              'runtime': {'dotnet_sdk': version, 'unity_executed': False, 'windows_executed': False},
              'origin_assay': assay, 'native': native, 'destination': demo,
              'limits': 'Static origin binding assay and actual local single-owner C# process/file consumer. No full origin runtime, power-loss durability, hostile save authentication, concurrent distributed ownership, Unity, Windows, Steam, human experience or final canon proof.'}
    if compare and json.loads(Path(compare).read_text()) != result:
        raise ValueError('Executed identities or observations differ from comparison')
    output.parent.mkdir(parents=True, exist_ok=True); output.write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    print('PASS: persistent C# consumer and retained recovery failure controls')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--dotnet', default=os.environ.get('HUB_DOTNET', 'dotnet')); parser.add_argument('--compare', type=Path)
    args = parser.parse_args()
    try: run(args.output, args.dotnet, args.compare)
    except (OSError, ValueError, KeyError, subprocess.SubprocessError) as error: parser.exit(1, f'FAIL: {error}\n')


if __name__ == '__main__': main()
