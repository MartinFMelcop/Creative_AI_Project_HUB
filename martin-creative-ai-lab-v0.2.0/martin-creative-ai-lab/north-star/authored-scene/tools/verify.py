#!/usr/bin/env python3
"""Execute the authored scene's real C# owner and browser observation contract."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[3]
SCENE = ROOT / 'north-star/authored-scene'
CSHARP = ROOT / 'north-star/csharp'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inputs():
    # Forward project references are actual inputs; unrelated reverse consumers are not.
    pending = [SCENE / 'Checks/NorthStar.AuthoredSceneChecks.csproj']
    projects, files = set(), {CSHARP / 'global.json', CSHARP / 'Narrative/SCENE.md'}
    while pending:
        project = pending.pop().resolve()
        if project in projects:
            continue
        if not project.is_relative_to(ROOT):
            raise ValueError('Project dependency escapes maintained workspace')
        projects.add(project)
        files.add(project)
        files.update(p for p in project.parent.rglob('*.cs') if not {'bin', 'obj'} & set(p.parts))
        for item in ET.parse(project).iter():
            tag = item.tag.split('}')[-1]
            if tag == 'ProjectReference':
                pending.append((project.parent / item.attrib['Include']).resolve())
            elif tag == 'Compile' and 'Include' in item.attrib:
                value = item.attrib['Include']
                if '*' in value:
                    raise ValueError('Explicit wildcard needs a bounded input inventory')
                files.add((project.parent / value).resolve())
    for folder in ('web', 'tools'):
        files.update(p for p in (SCENE / folder).rglob('*') if p.suffix in {'.html', '.css', '.js', '.mjs', '.py'})
    if any(not p.resolve().is_relative_to(ROOT) or p.is_symlink() or not p.is_file() for p in files):
        raise ValueError('Missing, linked or external consumer input')
    return {p.relative_to(ROOT).as_posix(): sha(p) for p in sorted(files)}


def verify(output, dotnet='dotnet', node='node'):
    output = output.absolute()
    if output.resolve().is_relative_to(ROOT):
        raise ValueError('Keep outputs outside maintained workspace')
    output.mkdir(parents=True, exist_ok=False)
    before = inputs()
    records = []
    environment = dict(os.environ, DOTNET_CLI_TELEMETRY_OPTOUT='1', DOTNET_NOLOGO='1', DOTNET_PROCESSOR_COUNT='2')

    def execute(command, cwd=CSHARP, timeout=300):
        result = subprocess.run(command, cwd=cwd, env=environment, capture_output=True, text=True, timeout=timeout)
        record = {'command': [str(x) for x in command], 'exit_code': result.returncode,
                  'stdout': result.stdout, 'stderr': result.stderr}
        records.append(record)
        (output / 'commands.json').write_text(json.dumps(records, indent=2) + '\n')
        if result.returncode:
            raise ValueError('Execution failed: ' + ' '.join(record['command']) + '\n' + (result.stdout + result.stderr)[-3000:])
        return result.stdout.strip()

    sdk, js = shutil.which(dotnet), shutil.which(node)
    if not sdk or not js:
        raise ValueError('Actual pinned SDK and Node are required')
    version = execute([sdk, '--version'], timeout=15)
    if version != json.loads((CSHARP / 'global.json').read_text())['sdk']['version']:
        raise ValueError('SDK differs from existing pin')
    node_version = execute([js, '--version'], timeout=15)
    if node_version != 'v24.19.0':
        raise ValueError('Node differs from existing exercised pin')
    execute([sdk, 'build', str(SCENE / 'Checks/NorthStar.AuthoredSceneChecks.csproj'), '-c', 'Release', '-m:1', '--disable-build-servers'])
    execute([sdk, str(SCENE / 'Checks/bin/Release/net10.0/NorthStar.AuthoredSceneChecks.dll'), str(output / 'native.json')], timeout=60)
    execute([js, str(SCENE / 'tools/browser.mjs'), sdk, str(output / 'browser')], cwd=ROOT, timeout=300)
    if inputs() != before:
        raise ValueError('Consumer or instrument sources changed during execution')
    native = json.loads((output / 'native.json').read_text())
    browser = json.loads((output / 'browser/browser.json').read_text())
    if native['checks']['failed'] != 0 or native['checks']['passed'] != len(native['controls']) or not native['controls']:
        raise ValueError('Incomplete native acceptance')
    if browser['checks']['failed'] != 0 or browser['checks']['passed'] != len(browser['controls']) or not browser['controls']:
        raise ValueError('Incomplete actual browser controls')
    if not browser.get('negatives') or not any(m.get('detected') is True for m in browser['negatives']):
        raise ValueError('Missing detected renderer negative')
    consumers = sorted(name for name in before if name.startswith('north-star/authored-scene/Host/') and name.endswith('.cs'))
    result = {'schema_version': 1, 'kind': 'destination_execution', 'consumer_paths': consumers,
              'source_artifacts': [{'local_path': name, 'sha256': digest, 'size_bytes': (ROOT / name).stat().st_size} for name, digest in before.items()],
              'checks': {'passed': native['checks']['passed'] + browser['checks']['passed'], 'failed': 0},
              'commands': records, 'runtime': {'sdk': version, 'node': node_version, 'unity_executed': False, 'windows_executed': False, 'steam_executed': False},
              'native': 'native.json', 'browser': 'browser/browser.json',
              'limits': 'Actual local C# and synthetic Chromium journeys; no Unity Editor, Windows player, Steam, participants, device experience, production network, durable narrative or final creative canon.'}
    (output / 'RUN.json').write_text(json.dumps(result, indent=2) + '\n')
    print('PASS: actual authored C# scene, browser consequences and source-stable input closure')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dotnet', default='dotnet')
    parser.add_argument('--node', default='node')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    try:
        verify(args.output, args.dotnet, args.node)
    except (OSError, ValueError, KeyError, subprocess.SubprocessError, ET.ParseError) as error:
        parser.exit(1, f'FAIL: {error}\n')


if __name__ == '__main__':
    main()
