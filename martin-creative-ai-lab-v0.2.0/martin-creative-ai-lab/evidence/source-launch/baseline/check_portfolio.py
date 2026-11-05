#!/usr/bin/env python3
"""Bind public navigation to existing artifacts and recorded execution, without rerunning games."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import zipfile

ROOT = Path(__file__).resolve().parents[1]
RECIPIENTS = {
    'windows-x64': ('windows', 'AuthoredSceneWindows/', 'win-x64', 'run-demo.ps1',
                    'evidence/windows-recipient/RUN.json'),
    'linux-x64': ('linux', 'AuthoredSceneDemo/', 'linux-x64', 'run-demo.sh',
                  'evidence/request-continuity/RUN.json'),
}
EXPERIMENTS = {
    'field-journey': 'north-star/field-journey/Host/',
    'selected-passives': 'north-star/combat-study/',
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def exact_keys(value, keys, label):
    require(isinstance(value, dict) and set(value) == set(keys), label + ': unsupported or missing fields')


def local(root, name):
    require(isinstance(name, str) and bool(name) and '\\' not in name and ':' not in name,
            'Noncanonical local navigation path')
    p = PurePosixPath(name)
    require(not p.is_absolute() and '..' not in p.parts and str(p) == name,
            'Noncanonical local navigation path')
    path = root / name
    require(path.is_file() and not path.is_symlink() and path.resolve().is_relative_to(root.resolve()),
            'Missing or escaping navigation path: ' + name)
    return path


def digest(path):
    with path.open('rb') as handle:
        return hashlib.file_digest(handle, 'sha256').hexdigest()


def parse(data):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            require(key not in result, 'Duplicate JSON key')
            result[key] = value
        return result
    return json.loads(data, object_pairs_hook=unique)


def load(path):
    return parse(path.read_bytes())


def proof(root, row):
    path = local(root, row['evidence_path'])
    data = path.read_bytes()
    require(re.fullmatch('[0-9a-f]{64}', row['evidence_sha256'] or '') is not None
            and hashlib.sha256(data).hexdigest() == row['evidence_sha256'], 'Recorded evidence identity mismatch')
    record = parse(data)
    require(record.get('kind') == 'destination_execution', 'Recorded evidence is not destination execution')
    checks = record.get('checks', {})
    require(type(checks.get('passed')) is int and checks['passed'] > 0
            and checks.get('failed') == 0, 'Recorded execution has no successful checks')
    return record


def inspect_navigation(archive, prefix, target, launcher):
    # Artifact SHA is already bound to an existing executed record. This is a
    # navigation/closure projection, not a replacement for the delivery inspectors.
    with zipfile.ZipFile(archive) as source:
        entries = source.infolist()
        names = [item.filename for item in entries]
        require(len(names) <= 3000 and len(names) == len(set(names))
                and sum(item.file_size for item in entries) <= 300_000_000,
                'Invalid recipient ZIP inventory')
        require(all(name.startswith(prefix) and '..' not in PurePosixPath(name).parts
                    and '\\' not in name for name in names), 'Unexpected recipient ZIP root')
        relative = {name[len(prefix):] for name in names}
        required = {'BUILDINFO.json', launcher, 'README.txt', 'payload.sha256',
                    'runtime/LICENSE.txt', 'runtime/ThirdPartyNotices.txt',
                    'app/NorthStar.AuthoredScene.dll', 'web/index.html'}
        require(required <= relative, 'Missing recipient launcher, notices or authored-scene payload')
        info = parse(source.read(prefix + 'BUILDINFO.json'))
        require(info.get('schema_version') == 1 and info.get('target') == target,
                'Recipient BUILDINFO platform mismatch')
        managed = {name: hashlib.sha256(source.read(prefix + name)).hexdigest()
                   for name in sorted(relative) if name.startswith(('app/', 'web/', 'source/'))}
        require(any(name.startswith('source/') for name in managed), 'Missing recipient source closure')
        if target == 'win-x64':
            require(info.get('kind') == 'authored_scene_windows_recipient'
                    and info.get('managed_closure_sha256') == managed,
                    'Recipient managed closure mismatch')
        else:
            require(info.get('kind') == 'authored_scene_local_demo'
                    and info.get('source_sha256') == {
                        name.removeprefix('source/'): value for name, value in managed.items()
                        if name.startswith('source/')}, 'Recipient source closure mismatch')
        return info, managed


def validate(root, catalog):
    root = Path(root).resolve()
    exact_keys(catalog, ('schema_version', 'laboratory_catalog', 'recipients', 'source_experiments'), 'Portfolio')
    require(catalog['schema_version'] == 1, 'Unsupported portfolio schema')
    require(catalog['laboratory_catalog'] == 'labs/origins.json', 'Laboratory authority differs')
    recipients = catalog['recipients']
    require(isinstance(recipients, list) and len(recipients) == len(RECIPIENTS), 'Recipient identities required')
    reports, closures, buildinfo = {}, {}, {}
    for row in recipients:
        exact_keys(row, ('id', 'archive_path', 'evidence_path', 'evidence_sha256', 'guide_path',
                         'launcher_path', 'platform'), 'Recipient')
        rid = row['id']
        require(rid in RECIPIENTS and rid not in reports, 'Duplicate or unknown recipient identity')
        platform, prefix, target, launcher, evidence_path = RECIPIENTS[rid]
        require(row['platform'] == platform, 'Recipient platform differs from identity')
        require(row['evidence_path'] == evidence_path, 'Recipient evidence authority differs')
        record = proof(root, row)
        archive = local(root, row['archive_path'])
        observed = digest(archive)
        expected = ({'path': record.get('archive_path'), 'sha256': record.get('artifact_sha256'),
                     'bytes': record.get('artifact_bytes')} if platform == 'windows' else record.get('archive', {}))
        require(expected.get('path') == row['archive_path'] and expected.get('sha256') == observed
                and expected.get('bytes') == archive.stat().st_size, 'Recipient identity mismatch')
        if platform == 'windows':
            require(record.get('executed') is True and record.get('platform') == 'Windows',
                    'Windows execution platform is not recorded')
        else:
            require('Linux' in record.get('runtime', ''), 'Linux execution platform is not recorded')
        require(row['launcher_path'] == prefix + launcher, 'Recipient launcher path differs')
        local(root, row['guide_path'])
        info, managed = inspect_navigation(archive, prefix, target, launcher)
        require(digest(archive) == observed, 'Recipient identity changed during inspection')
        closures[rid], buildinfo[rid] = managed, info
        reports[rid] = {'archive_path': row['archive_path'], 'bytes': archive.stat().st_size,
                        'sha256': observed, 'target': target, 'launcher_path': row['launcher_path'],
                        'recorded_execution': row['evidence_path'], 'guide_path': row['guide_path'],
                        'runtime_version': info.get('runtime_version'),
                        'source_files': sum(n.startswith('source/') for n in managed)}
    require(closures['windows-x64'] == closures['linux-x64'], 'Recipient managed applications differ')
    require(buildinfo['windows-x64'].get('linux_archive_sha256') == reports['linux-x64']['sha256'],
            'Windows adaptation does not bind the declared Linux recipient')
    experiments = catalog['source_experiments']
    require(isinstance(experiments, list) and len(experiments) == len(EXPERIMENTS), 'Source experiment identities required')
    sources = {}
    for row in experiments:
        exact_keys(row, ('id', 'guide_path', 'evidence_path', 'evidence_sha256', 'consumer_paths'), 'Source experiment')
        eid = row['id']
        require(eid in EXPERIMENTS and eid not in sources, 'Duplicate or unknown source experiment identity')
        record = proof(root, row)
        paths = row['consumer_paths']
        require(isinstance(paths, list) and paths and len(paths) == len(set(paths))
                and all(isinstance(n, str) and n.startswith(EXPERIMENTS[eid]) for n in paths),
                'Source experiment consumer identity differs')
        require(set(paths) <= set(record.get('consumer_paths', [])), 'Source experiment consumer not in recorded execution')
        artifacts = {item.get('local_path'): item for item in record.get('source_artifacts', [])}
        for name in paths:
            path = local(root, name)
            require(name in artifacts and artifacts[name].get('sha256') == digest(path)
                    and artifacts[name].get('size_bytes') == path.stat().st_size,
                    'Source experiment consumer identity mismatch')
            require(all('source/' + name not in closure for closure in closures.values()),
                    'Source experiment consumer is included in recipient')
        local(root, row['guide_path'])
        sources[eid] = {'guide_path': row['guide_path'], 'recorded_execution': row['evidence_path'],
                        'consumer_paths': paths, 'included_in_recipient': False}
    labs = load(local(root, catalog['laboratory_catalog']))['labs']
    require(len(labs) == 11 and len({row['id'] for row in labs}) == 11, 'Eleven laboratory destinations required')
    maturity = {row['id']: row['status'] for row in labs}
    require(set(maturity.values()) <= {'operational', 'incomplete'}, 'Invalid laboratory maturity')
    return {'schema_version': 1, 'recipients': reports, 'source_experiments': sources,
            'laboratories': maturity, 'limits': 'Artifact/navigation identity and recorded execution only. No fresh gameplay, participant, ordinary-user Windows, licensed Unity/Steam, rights clearance or production readiness assessment.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--catalog', type=Path, default=ROOT / 'showcase/portfolio.json')
    args = parser.parse_args()
    try:
        print(json.dumps(validate(ROOT, load(args.catalog)), indent=2, sort_keys=True))
    except (OSError, ValueError, KeyError, TypeError, zipfile.BadZipFile) as error:
        parser.exit(1, str(error) + '\n')


if __name__ == '__main__':
    main()
