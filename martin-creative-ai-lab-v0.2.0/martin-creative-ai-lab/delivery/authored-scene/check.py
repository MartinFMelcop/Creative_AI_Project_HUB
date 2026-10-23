#!/usr/bin/env python3
"""Independently inspect one local-demo ZIP before extracting any payload."""
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import tarfile
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parents[2]
PREFIX = 'AuthoredSceneDemo/'
SDK_SHA512 = '51c8b999af9e8dd9998c9edc5944e19a90788862068acd38694e098889054ce8c23d4f0c5cccfa16bf187d044562359e5ee69a9f8ad0bbe913ba90311fbce25b'
SDK_VERSION = '10.0.401'
RUNTIME_VERSION = '10.0.12'


def digest(data):
    return hashlib.sha256(data).hexdigest()


def safe_name(name):
    if not name or '\\' in name or ':' in name or '\x00' in name or name.startswith('/'):
        raise ValueError('Unsafe archive path')
    parts = name.split('/')
    if any(part in ('', '.', '..') for part in parts) or str(PurePosixPath(name)) != name:
        raise ValueError('Unsafe archive path')
    return name


def json_object(data):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError('Duplicate JSON key')
            result[key] = value
        return result
    return json.loads(data, object_pairs_hook=unique)


def source_minimum(root):
    pending = [root / 'north-star/authored-scene/Host/NorthStar.AuthoredScene.csproj']
    found, files = set(), {'north-star/csharp/global.json'}
    while pending:
        project = pending.pop().resolve()
        if project in found:
            continue
        if not project.is_relative_to(root) or project.is_symlink():
            raise ValueError('Source dependency escapes workspace')
        found.add(project)
        files.add(project.relative_to(root).as_posix())
        files.update(p.relative_to(root).as_posix() for p in project.parent.rglob('*.cs') if not {'bin','obj'} & set(p.parts))
        for name in ('README.md','SCENE.md'):
            if (project.parent/name).is_file():files.add((project.parent/name).relative_to(root).as_posix())
        for item in ET.parse(project).iter():
            tag = item.tag.split('}')[-1]
            if tag == 'ProjectReference':
                pending.append((project.parent / item.attrib['Include']).resolve())
            elif tag in ('Compile', 'Import', 'PackageReference'):
                raise ValueError('Unreviewed source build dependency')
    files.add('north-star/authored-scene/README.md')
    files.update('north-star/authored-scene/web/' + x for x in ('index.html', 'style.css', 'app.js'))
    return files


def runtime_name(name):
    return name in ('runtime/dotnet', 'runtime/LICENSE.txt', 'runtime/ThirdPartyNotices.txt') or name.startswith(
        ('runtime/host/fxr/' + RUNTIME_VERSION + '/', 'runtime/shared/Microsoft.NETCore.App/' + RUNTIME_VERSION + '/'))


def sdk_runtime(archive):
    with archive.open('rb') as handle:
        if hashlib.file_digest(handle, 'sha512').hexdigest() != SDK_SHA512:
            raise ValueError('Official SDK archive SHA512 mismatch')
    result = {}
    with tarfile.open(archive, 'r:gz') as source:
        for item in source:
            name = item.name.removeprefix('./')
            candidate = 'runtime/' + name
            if not runtime_name(candidate):
                continue
            if not item.isfile():
                if item.isdir():
                    continue
                raise ValueError('Unsupported SDK runtime member')
            if candidate in result:
                raise ValueError('Duplicate SDK runtime member')
            result[candidate] = digest(source.extractfile(item).read())
    return result


def inspect(archive, root=ROOT, sdk_archive=None):
    root = root.resolve()
    payload = {}
    with zipfile.ZipFile(archive) as source:
        entries = source.infolist()
        names = [x.filename for x in entries]
        if len(entries) > 3000 or len(names) != len(set(names)) or names != sorted(names):
            raise ValueError('Duplicate, unordered or excessive ZIP entries')
        if sum(x.file_size for x in entries) > 300_000_000:
            raise ValueError('Excessive uncompressed payload')
        for item in entries:
            safe_name(item.filename)
            if not item.filename.startswith(PREFIX):
                raise ValueError('Unexpected bundle root')
            name = item.filename[len(PREFIX):]
            safe_name(name)
            mode = item.external_attr >> 16
            expected = 0o755 if name in ('run-demo.sh', 'runtime/dotnet') else 0o644
            if item.create_system != 3 or not stat.S_ISREG(mode) or stat.S_IMODE(mode) != expected:
                raise ValueError('Unexpected member type or permissions')
            if item.flag_bits & 1 or item.compress_type != zipfile.ZIP_DEFLATED:
                raise ValueError('Unsupported archive encoding')
            payload[name] = source.read(item)
    manifest = payload.get('payload.sha256', b'').decode('utf-8')
    declared = {}
    for line in manifest.splitlines():
        if not re.fullmatch(r'[0-9a-f]{64}  .+', line):
            raise ValueError('Malformed payload manifest')
        value, name = line.split('  ', 1)
        safe_name(name)
        if name in declared or name == 'payload.sha256':
            raise ValueError('Duplicate or recursive payload manifest')
        declared[name] = value
    observed = {name: digest(data) for name, data in payload.items() if name != 'payload.sha256'}
    if declared != observed or list(declared) != sorted(declared):
        raise ValueError('Payload manifest differs from exact archive inventory')
    required = {'BUILDINFO.json', 'run-demo.sh', 'README.txt', 'runtime/dotnet', 'runtime/LICENSE.txt',
                'runtime/ThirdPartyNotices.txt', 'runtime/host/fxr/' + RUNTIME_VERSION + '/libhostfxr.so',
                'runtime/shared/Microsoft.NETCore.App/' + RUNTIME_VERSION + '/libcoreclr.so',
                'runtime/shared/Microsoft.NETCore.App/' + RUNTIME_VERSION + '/System.Private.CoreLib.dll'}
    required.update('web/' + x for x in ('index.html', 'style.css', 'app.js'))
    required.update('app/' + x for x in ('NorthStar.AuthoredScene.dll', 'NorthStar.Narrative.dll', 'NorthStar.Crossing.dll', 'NorthStar.Domain.dll',
                                       'NorthStar.AuthoredScene.deps.json', 'NorthStar.AuthoredScene.runtimeconfig.json','NorthStar.Narrative.deps.json','NorthStar.Narrative.runtimeconfig.json','NorthStar.Crossing.deps.json','NorthStar.Crossing.runtimeconfig.json'))
    if not required.issubset(payload) or any(not payload[name] for name in required):
        raise ValueError('Missing required application/runtime/web/notices payload')
    info = json_object(payload['BUILDINFO.json'])
    if info.get('schema_version') != 1 or info.get('kind') != 'authored_scene_local_demo' or info.get('sdk_version') != SDK_VERSION or info.get('runtime_version') != RUNTIME_VERSION or info.get('sdk_archive_sha512') != SDK_SHA512:
        raise ValueError('Unexpected build identity')
    sources, runtime = info.get('source_sha256'), info.get('runtime_sha256')
    if not isinstance(sources, dict) or not isinstance(runtime, dict) or source_minimum(root)!=set(sources):
        raise ValueError('Incomplete source/runtime build inventory')
    source_prefixes = ('north-star/authored-scene/', 'north-star/csharp/Narrative/', 'north-star/csharp/Crossing/', 'north-star/csharp/Domain/', 'delivery/authored-scene/')
    for name, expected in sources.items():
        safe_name(name)
        local = root / name
        if not (name.startswith(source_prefixes) or name == 'north-star/csharp/global.json') or not local.is_file() or local.is_symlink() or not local.resolve().is_relative_to(root):
            raise ValueError('Unexpected source input')
        if name.startswith('north-star/authored-scene/') and not name.startswith(('north-star/authored-scene/Host/', 'north-star/authored-scene/web/')) and not name.endswith('.md'):
            raise ValueError('Unexpected authored-scene source input')
        if payload.get('source/' + name) != local.read_bytes() or expected != digest(local.read_bytes()):
            raise ValueError('Source binding mismatch')
    observed_runtime = {name: digest(data) for name, data in payload.items() if name.startswith('runtime/')}
    if runtime != observed_runtime or any(not runtime_name(name) for name in runtime):
        raise ValueError('Runtime inventory mismatch')
    anchor=json_object((root/'delivery/authored-scene/runtime-lock.json').read_bytes())
    if anchor.get('sdk_archive_sha512')!=SDK_SHA512 or anchor.get('files')!=runtime:
        raise ValueError('Bundled runtime differs from trusted official runtime lock')
    build_inputs=info.get('build_inputs_sha256',{})
    expected_inputs={'delivery/authored-scene/'+n for n in ('package.py','runtime-lock.json','bundle/run-demo.sh','bundle/README.txt')}
    if set(build_inputs)!=expected_inputs or any(build_inputs[n]!=digest((root/n).read_bytes()) for n in expected_inputs):
        raise ValueError('Packaging input identity mismatch')
    if payload['run-demo.sh']!=(root/'delivery/authored-scene/bundle/run-demo.sh').read_bytes() or payload['README.txt']!=(root/'delivery/authored-scene/bundle/README.txt').read_bytes():
        raise ValueError('Recipient support content mismatch')
    if sdk_archive and sdk_runtime(Path(sdk_archive)) != runtime:
        raise ValueError('Bundled runtime differs from verified official archive')
    allowed = required | {'payload.sha256'} | {'source/' + name for name in sources} | set(runtime)
    if set(payload) != allowed:
        raise ValueError('Unexpected package payload')
    config = json_object(payload['app/NorthStar.AuthoredScene.runtimeconfig.json'])['runtimeOptions']
    framework = config.get('framework', {})
    if framework.get('name') != 'Microsoft.NETCore.App' or framework.get('version') != RUNTIME_VERSION:
        raise ValueError('Runtime configuration differs from bundled runtime')
    return payload, {'files': len(payload), 'source_files': len(sources), 'runtime_files': len(runtime),
                     'sdk_archive_verified': sdk_archive is not None, 'windows_executed': False, 'unity_executed': False,
                     'scope': 'Structural identity and current-source binding; actual execution is separate.'}


def extract(payload, output, root=ROOT):
    output = output.resolve()
    if output == root or output.is_relative_to(root):
        raise ValueError('Extraction must be outside maintained workspace')
    output.mkdir(parents=True, exist_ok=False)
    for name, data in payload.items():
        target = output / 'AuthoredSceneDemo' / name
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open('xb') as handle:
            handle.write(data)
        target.chmod(0o755 if name in ('run-demo.sh', 'runtime/dotnet') else 0o644)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('archive', type=Path)
    parser.add_argument('--extract', type=Path)
    parser.add_argument('--sdk-archive', type=Path, help='Independently anchor every runtime byte to the pinned official archive')
    args = parser.parse_args()
    try:
        payload, report = inspect(args.archive, sdk_archive=args.sdk_archive)
        if args.extract:
            extract(payload, args.extract)
        print(json.dumps(report, sort_keys=True))
    except (OSError, ValueError, KeyError, ET.ParseError, zipfile.BadZipFile, tarfile.TarError) as error:
        parser.exit(1, str(error) + '\n')


if __name__ == '__main__':
    main()
