#!/usr/bin/env python3
"""Execute the actual memory-study consumer and browser outside maintained sources."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

ROOT=Path(__file__).resolve().parents[3]
STUDY=ROOT/'north-star/memory-study'

def identities():
    names=[]
    for part in ['memory-study']:
        for path in (ROOT/'north-star'/part).rglob('*'):
            if path.is_file() and not {'bin','obj','__pycache__'}.intersection(path.parts):
                names.append(path)
    names += list((ROOT/'labs/narrative-continuity/memory').glob('*.py'))
    names += [ROOT/'evidence/memory-study/protocol.json', ROOT/'north-star/csharp/global.json', ROOT/'projects/realtime-integration-lab/package.json', ROOT/'projects/realtime-integration-lab/package-lock.json']
    return {str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(names)}

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dotnet',required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    output=args.output.resolve()
    if output==ROOT or ROOT in output.parents:
        parser.error('Output must be a new directory outside the maintained tree')
    output.mkdir(parents=True,exist_ok=False)
    dotnet=shutil.which(args.dotnet) or args.dotnet
    before=identities();logs=[]
    commands=[[dotnet,'--version'],[dotnet,'build',str(STUDY/'Checks/NorthStar.MemoryChecks.csproj'),'-c','Release'],[dotnet,str(STUDY/'Checks/bin/Release/net10.0/NorthStar.MemoryChecks.dll'),'--native',str(output/'native.json')],['python3',str(ROOT/'labs/narrative-continuity/memory/run.py'),'--dotnet',dotnet,'--output',str(output/'source')],['node',str(STUDY/'tools/browser.mjs'),dotnet,str(output/'browser')]]
    try:
        for command in commands:
            r=subprocess.run(command,cwd=STUDY,capture_output=True,text=True,timeout=180)
            logs.append({'command':command,'returncode':r.returncode,'stdout':r.stdout,'stderr':r.stderr})
            if r.returncode:raise RuntimeError('Actual command failed: '+command[1])
            if command[1]=='--version' and r.stdout.strip()!='10.0.401':raise RuntimeError('Pinned SDK required')
        if identities()!=before:raise RuntimeError('Source changed during execution')
        native=json.loads((output/'native.json').read_text());browser=json.loads((output/'browser/browser.json').read_text())
        (output/'verification.json').write_text(json.dumps({'schema_version':1,'kind':'memory-study_consumer_verification','source_sha256':before,'source_stable':True,'checks':{'native':native['checks'],'chromium':browser['checks'],'http':browser['http_checks'],'source_cases':json.loads((output/'source/results.json').read_text())['same_cases']},'limits':'Software controls overlap outcomes, not people, independent studies, Unity, Windows or Steam.'},indent=2)+'\n')
        print('PASS: scoped memory and actual witness service')
    finally:
        (output/'execution.json').write_text(json.dumps(logs,indent=2)+'\n')

if __name__=='__main__':main()
