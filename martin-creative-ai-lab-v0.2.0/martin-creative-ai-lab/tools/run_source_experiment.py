#!/usr/bin/env python3
"""Build and supervise one declared trusted-local source experiment, never a recipient."""
import argparse
from collections import deque
import json
from pathlib import Path
import shutil
import signal
import socket
import subprocess
import sys
import threading
import time
from urllib.error import URLError
from urllib.request import urlopen
import check_portfolio as portfolio

ROOT = Path(__file__).resolve().parents[1]
SDK = '10.0.401'


def resolve_executable(name):
    found = shutil.which(name)
    if not found:
        raise ValueError('An executable dotnet path is required; install the pinned SDK separately.')
    return str(Path(found).resolve())


def validate_http(eid, data):
    if not isinstance(data, dict) or type(data.get('sequence')) is not int or type(data.get('accepted')) is not bool:
        raise ValueError('Unexpected live observation schema')
    if eid == 'field-journey':
        if not isinstance(data.get('intake'), dict) or not isinstance(data.get('memory'), dict):
            raise ValueError('Expected Field observation')
    elif eid == 'selected-passives':
        if data.get('phase') not in ('preparation', 'active', 'ended') or not isinstance(data.get('preparation'), dict):
            raise ValueError('Expected Treatment Line observation')
    else:
        raise ValueError('Unknown source experiment')
    return data


def wait_ready(process, url, eid, lines, deadline, state_path=None):
    expected = 'READY ' + url
    state_path = state_path or portfolio.LAUNCHES[eid]['state_path']
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise ValueError('Source host exited before verified readiness')
        if expected in lines:
            try:
                with urlopen(url.rstrip('/') + state_path, timeout=.5) as response:
                    if response.status != 200 or response.headers.get_content_type() != 'application/json':
                        raise ValueError('Unexpected observation HTTP response')
                    body = response.read(131073)
                    if len(body) > 131072:
                        raise ValueError('Observation exceeds bounded response')
                    validate_http(eid, json.loads(body))
                if process.poll() is not None:
                    raise ValueError('Source host exited during readiness verification')
                return
            except (URLError, TimeoutError, ConnectionError):
                pass
        time.sleep(.025)
    raise ValueError('Source host did not provide verified HTTP readiness before deadline')


def linked(path, root):
    current = path
    while current != root.parent:
        if current.is_symlink():
            return True
        current = current.parent
    return False


def launch(eid, dotnet, port, seconds, report):
    if type(port) is not int or not 1024 <= port <= 65535 or type(seconds) is not int or not 1 <= seconds <= 600:
        raise ValueError('Bound port1024..65535 and lifetime1..600 required')
    report.update(stage='preflight', commands=[])
    catalog = portfolio.load(ROOT / 'showcase/portfolio.json')
    portfolio.validate(ROOT, catalog)
    row = next(row for row in catalog['source_experiments'] if row['id'] == eid)
    config = portfolio.validate_launch(ROOT, eid, row['launch'])
    exe = resolve_executable(dotnet)
    version = subprocess.run([exe, '--version'], cwd=ROOT/'north-star/csharp', capture_output=True, text=True, timeout=15)
    report['commands'].append({'command':[exe,'--version'],'exit_code':version.returncode,'stdout':version.stdout[-4096:],'stderr':version.stderr[-4096:]})
    if version.returncode != 0 or version.stdout.strip() != SDK:
        raise ValueError('Exact SDK10.0.401 required; no automatic installation or substitution')
    with socket.socket() as check:
        check.bind(('127.0.0.1', port))
    commands = report['commands']
    report['stage'] = 'build'
    build = [exe, 'build', str(ROOT/config['project']), '-c', 'Release', '-m:1', '--disable-build-servers']
    built = subprocess.run(build, cwd=ROOT/'north-star/csharp', capture_output=True, text=True, timeout=120)
    commands.append({'command': build, 'exit_code': built.returncode,
                     'stdout': built.stdout[-65536:], 'stderr': built.stderr[-65536:]})
    if built.returncode:
        raise ValueError('Source build failed: ' + built.stderr[-1024:] + built.stdout[-1024:])
    assembly = ROOT/config['assembly']
    if not assembly.is_file() or linked(assembly, ROOT):
        raise ValueError('Missing or linked built source assembly')
    args = [exe, str(assembly), '--serve', str(port), str(ROOT/config['web']), '--seconds', str(seconds)]
    report['stage'] = 'start'
    host_command = {'command':args,'exit_code':None}
    commands.append(host_command)
    lines = deque(maxlen=256)
    process = subprocess.Popen(args, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    def collect():
        for line in process.stdout:
            lines.append(line.rstrip('\r\n')[:4096])
    reader = threading.Thread(target=collect, daemon=True)
    reader.start()
    report.update(id=eid, pid=process.pid, sdk=SDK, commands=commands, url=f'http://127.0.0.1:{port}/')
    try:
        wait_ready(process, report['url'], eid, lines, time.monotonic()+min(15, seconds+1), config['state_path'])
        report['stage'] = 'running'
        event = {'event':'ready', 'id':eid, 'url':report['url'], 'pid':process.pid}
        report['events'].append(event)
        print(json.dumps(event), flush=True)
        code = process.wait(timeout=seconds+5)
        host_command['exit_code'] = code
        if code:
            raise ValueError('Source host terminated unsuccessfully')
        report['status'] = 'success'
        report['stage'] = 'expired'
        report['events'].append({'event':'expired','exit_code':code})
    finally:
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                process.kill(); process.wait(timeout=3)
        reader.join(timeout=1)
        host_command['exit_code'] = process.returncode
        report['host_exit_code'] = process.returncode
        report['host_lines'] = list(lines)
        report['owned_process_exited'] = process.poll() is not None
        process.stdout.close()


def interrupted(signum, frame):
    raise KeyboardInterrupt


def main():
    signal.signal(signal.SIGTERM, interrupted)
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='mode', required=True)
    commands.add_parser('list')
    run = commands.add_parser('run')
    run.add_argument('id', choices=sorted(portfolio.LAUNCHES))
    run.add_argument('--dotnet', default='dotnet')
    run.add_argument('--port', type=int, default=8099)
    run.add_argument('--seconds', type=int, default=300)
    run.add_argument('--report', '--output', type=Path)
    args = parser.parse_args()
    report = {'schema':'hub.source-launch.v1', 'status':'failed', 'events':[],
              'boundary':'Trusted-local source experiment, ephemeral and SDK-required. No Unity/Windows/Steam, recipient inclusion, sandbox or human validation.'}
    destination = None
    try:
        if args.mode == 'list':
            catalog = portfolio.load(ROOT/'showcase/portfolio.json');portfolio.validate(ROOT,catalog)
            print(json.dumps({'source_experiments':[{'id':row['id'],'guide':row['guide_path']} for row in catalog['source_experiments']], 'sdk':SDK,'boundary':report['boundary']}))
            return 0
        if args.report:
            candidate = args.report.absolute()
            if candidate.resolve().is_relative_to(ROOT) or candidate.exists() or not candidate.parent.is_dir() or any(p.is_symlink() for p in [candidate,*candidate.parents]):
                raise ValueError('Report must be a new file in an existing external unlinked directory')
            destination = candidate
        print(json.dumps({'event':'preflight','id':args.id,'boundary':report['boundary']}),flush=True)
        launch(args.id,args.dotnet,args.port,args.seconds,report)
        return 0
    except KeyboardInterrupt:
        report['events'].append({'event':'interrupted'})
        report['status']='interrupted';report['error']='Explicit interrupt; owned host stopped.'
        return 130
    except (OSError, ValueError, KeyError, StopIteration, subprocess.SubprocessError) as error:
        report['error']=str(error)
        print(json.dumps({'event':'failed','error':str(error)}),file=sys.stderr,flush=True)
        return 1
    finally:
        if destination is not None and not destination.exists():
            with destination.open('x') as output:
                output.write(json.dumps(report,indent=2)+'\n')


if __name__ == '__main__':
    raise SystemExit(main())
