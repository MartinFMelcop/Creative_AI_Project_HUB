#!/usr/bin/env python3
"""Run the frozen four-participant Eclipse Fair policy experiment and replay it."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
PROJECT = ROOT / 'projects/eclipse-fair'
DEFAULT_CONFIG = ROOT / 'evidence/commander-policy/config.json'


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def identities(config: Path) -> dict[str, str]:
    """Only source/configuration inputs; generated output never enters its own hash."""
    paths = {Path(__file__).resolve(), PROJECT / 'Directory.Build.props', PROJECT / 'global.json',
             ROOT / 'evidence/commander-policy/protocol.json', config}
    for folder in ('Core', 'Cli', 'Checks', 'PolicyEvaluation'):
        for path in (PROJECT / folder).rglob('*'):
            if path.is_file() and not {'bin', 'obj'}.intersection(path.relative_to(PROJECT).parts):
                if path.suffix in ('.cs', '.csproj'):
                    paths.add(path)
    result = {}
    for path in sorted(paths):
        if not path.is_file():
            raise ValueError('Missing declared input: ' + str(path))
        try:
            key = path.relative_to(ROOT).as_posix()
        except ValueError:
            key = 'external-configuration/' + path.name
        if key in result:
            raise ValueError('Ambiguous input identity: ' + key)
        result[key] = digest(path)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dotnet', required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--config', type=Path, default=DEFAULT_CONFIG)
    args = parser.parse_args()
    output = args.output.resolve()
    config = args.config.resolve()
    if output == ROOT or ROOT in output.parents:
        parser.error('Output must be a new directory outside the maintained workspace.')
    if output.exists():
        parser.error('Refusing an existing output directory.')
    before = identities(config)
    closure = hashlib.sha256(json.dumps(before, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    output.mkdir(parents=True, exist_ok=False)
    dotnet = shutil.which(args.dotnet) or str(Path(args.dotnet).resolve())
    logs: list[dict] = []
    status = 'failed'
    started_at = time.monotonic()
    deadline = started_at + 1800

    def save() -> None:
        (output / 'commands.json').write_text(json.dumps(logs, indent=2) + '\n')

    def run(label: str, command: list[str], timeout: int = 600) -> str:
        started = time.monotonic()
        remaining = deadline - started
        if remaining <= 0:
            raise RuntimeError('Total 1800-second execution budget exhausted before ' + label)
        timeout = min(timeout, remaining)
        try:
            process = subprocess.run(command, cwd=PROJECT, capture_output=True, text=True, timeout=timeout)
        except subprocess.TimeoutExpired as error:
            def text(value):
                return value.decode(errors='replace') if isinstance(value, bytes) else value or ''
            stdout, stderr = text(error.stdout), text(error.stderr)
            (output / (label + '.stdout')).write_text(stdout)
            (output / (label + '.stderr')).write_text(stderr)
            logs.append({'label': label, 'command': command, 'exit_code': None,
                         'status': 'timeout', 'timeout_seconds': timeout, 'elapsed_seconds': time.monotonic() - started})
            save()
            raise RuntimeError('Actual command timed out: ' + label) from error
        stdout_path, stderr_path = output / (label + '.stdout'), output / (label + '.stderr')
        stdout_path.write_text(process.stdout)
        stderr_path.write_text(process.stderr)
        logs.append({'label': label, 'command': command, 'exit_code': process.returncode,
                     'stdout_sha256': digest(stdout_path), 'stderr_sha256': digest(stderr_path),
                     'elapsed_seconds': time.monotonic() - started})
        save()
        if process.returncode:
            raise RuntimeError('Actual command failed: ' + label)
        return process.stdout

    try:
        version = run('sdk', [dotnet, '--version'], 30).strip()
        if version != '10.0.401':
            raise RuntimeError('Pinned SDK10.0.401 required; observed ' + version)
        evaluator = PROJECT / 'PolicyEvaluation/Eclipse.PolicyEvaluation.csproj'
        checks = PROJECT / 'PolicyEvaluation/Checks/Eclipse.PolicyEvaluation.Checks.csproj'
        run('build-evaluator', [dotnet, 'build', str(evaluator), '-c', 'Release'])
        run('build-controls', [dotnet, 'build', str(checks), '-c', 'Release'])
        controls = run('controls', [dotnet, str(PROJECT / 'PolicyEvaluation/Checks/bin/Release/net10.0/Eclipse.PolicyEvaluation.Checks.dll')])
        run('build-regressions', [dotnet, 'build', str(PROJECT / 'Checks/Eclipse.Checks.csproj'), '-c', 'Release'])
        regressions = run('regressions', [dotnet, str(PROJECT / 'Checks/bin/Release/net10.0/Eclipse.Checks.dll')])
        instrument = str(PROJECT / 'PolicyEvaluation/bin/Release/net10.0/Eclipse.PolicyEvaluation.dll')
        run('experiment', [dotnet, instrument, 'run', str(config), str(output / 'report.json'), closure])
        run('replay', [dotnet, instrument, 'verify', str(output / 'report.json')])
        run('repeat', [dotnet, instrument, 'run', str(config), str(output / 'repeated-report.json'), closure])
        run('repeat-replay', [dotnet, instrument, 'verify', str(output / 'repeated-report.json')])
        if (output / 'report.json').read_bytes() != (output / 'repeated-report.json').read_bytes():
            raise RuntimeError('Separate executions did not reproduce exact report bytes.')
        report = json.loads((output / 'report.json').read_text())
        if report.get('configuration') != json.loads(config.read_text()):
            raise RuntimeError('Report configuration differs from the frozen input.')
        if any(game.get('status') != 'complete' for game in report.get('games', [])):
            raise RuntimeError('Interrupted primary game; retain report without claiming successful study.')
        if time.monotonic() > deadline:
            raise RuntimeError('Total 1800-second execution budget exhausted.')
        if report.get('source_hash') != closure:
            raise RuntimeError('Report does not bind the actual source closure.')
        if before != identities(config):
            raise RuntimeError('Source/configuration closure changed during actual execution.')
        result = {'schema_version': 1, 'status': 'passed', 'sdk': version, 'python': sys.version,
                  'source_sha256': before, 'source_closure_sha256': closure, 'source_stable': True,
                  'execution_limit_seconds': 1800, 'elapsed_seconds': time.monotonic() - started_at,
                  'complete_games': len(report['games']), 'interrupted_games': 0,
                  'controls': json.loads(controls.strip().splitlines()[-1]),
                  'affected_regressions': json.loads(regressions.strip().splitlines()[-1]),
                  'report_sha256': digest(output / 'report.json'), 'repeated_report_byte_identical': True,
                  'limits': 'Complete Eclipse Fair games only; software controls are not participants, CommanderSIM surrogate episodes, Magic games, human findings or Unity/Windows/Steam execution.'}
        (output / 'verification.json').write_text(json.dumps(result, indent=2) + '\n')
        status = 'passed'
        print('PASS: frozen policy experiment, actual replay and exact repeated execution')
        return 0
    finally:
        save()
        after = identities(config)
        (output / 'source-guard.json').write_text(json.dumps({'status': status, 'before': before, 'after': after,
                                                            'stable': before == after, 'source_closure_sha256': closure}, indent=2) + '\n')


if __name__ == '__main__':
    raise SystemExit(main())
