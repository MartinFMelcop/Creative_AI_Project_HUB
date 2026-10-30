#!/usr/bin/env python3
"""Execute the actual field-journey consumer and browser outside maintained sources."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

ROOT=Path(__file__).resolve().parents[3]
STUDY=ROOT/'north-star/field-journey'

def identities():
    names=[]
    for part in ['field-journey','intake','memory-study','csharp/Domain','csharp/Portable','csharp/Crossing','csharp/Forge','csharp/Loadout']:
        for path in (ROOT/'north-star'/part).rglob('*'):
            if path.is_file() and not {'bin','obj','__pycache__'}.intersection(path.parts):
                names.append(path)
    names += [ROOT/'evidence/field-journey/protocol.json', ROOT/'north-star/csharp/global.json', ROOT/'projects/realtime-integration-lab/package.json', ROOT/'projects/realtime-integration-lab/package-lock.json']
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
    commands=[[dotnet,'--version'],[dotnet,'build',str(STUDY/'Checks/NorthStar.FieldChecks.csproj'),'-c','Release'],[dotnet,str(STUDY/'Checks/bin/Release/net10.0/NorthStar.FieldChecks.dll'),str(output/'native.json')],['node',str(STUDY/'tools/browser.mjs'),dotnet,str(output/'browser')]]
    try:
        for command in commands:
            r=subprocess.run(command,cwd=STUDY,capture_output=True,text=True,timeout=180)
            logs.append({'command':command,'returncode':r.returncode,'stdout':r.stdout,'stderr':r.stderr})
            if r.returncode:raise RuntimeError('Actual command failed: '+command[1])
            if command[1]=='--version' and r.stdout.strip()!='10.0.401':raise RuntimeError('Pinned SDK required')
        if identities()!=before:raise RuntimeError('Source changed during execution')
        native=json.loads((output/'native.json').read_text());browser=json.loads((output/'browser/browser.json').read_text())
        (output/'verification.json').write_text(json.dumps({'schema_version':1,'kind':'field-journey_consumer_verification','source_sha256':before,'source_stable':True,'checks':{'native':native['checks'],'chromium':browser['checks'],'http':browser['http_checks']},'limits':'Software controls overlap outcomes, not people, independent studies, Unity, Windows or Steam.'},indent=2)+'\n')
        print('PASS: confirmed field journey with actual finite component use')
    finally:
        (output/'execution.json').write_text(json.dumps(logs,indent=2)+'\n')

if __name__=='__main__':main()
