#!/usr/bin/env python3
"""Run selected breakbar source, portable rules and actual existing consumer."""
import argparse
import hashlib
import json
import shutil
import subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
STUDY=ROOT/'north-star/combat-study'
def identities():
    files=[p for base in [STUDY,ROOT/'labs/combat-response/breakbar'] for p in base.rglob('*') if p.is_file() and not {'bin','obj','__pycache__'}.intersection(p.parts)]
    files += [ROOT/'tools/verify_breakbar_source.py',ROOT/'north-star/csharp/global.json',ROOT/'projects/realtime-integration-lab/package.json',ROOT/'projects/realtime-integration-lab/package-lock.json',ROOT/'references/rave-master/snapshots/36af1651271422ae33856e8b5d7b45702215f165/source/RM_CORE/DATA/CORE/REGRAS_DE_COMBATE.csv']
    return {str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(files)}
def main():
    p=argparse.ArgumentParser();p.add_argument('--dotnet',required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();out=a.output.resolve()
    if out.is_relative_to(ROOT) or out.exists():p.error('New external output directory required')
    out.mkdir(parents=True);dotnet=shutil.which(a.dotnet) or a.dotnet;before=identities();records=[]
    dll=STUDY/'ControlChecks/bin/Release/net10.0/NorthStar.ControlChecks.dll'
    commands=[[dotnet,'--version'],[dotnet,'build',str(STUDY/'ControlChecks/NorthStar.ControlChecks.csproj'),'-c','Release','-m:1','--disable-build-servers'],[dotnet,str(dll),str(out/'native.json')],['python3','-B',str(ROOT/'tools/verify_breakbar_source.py'),'--output',str(out/'source-initial.json'),'--export-cases',str(out/'cases.json')],[dotnet,str(dll),'--source-vectors',str(out/'cases.json'),str(out/'csharp-cases.json')],['python3','-B',str(ROOT/'tools/verify_breakbar_source.py'),'--output',str(out/'source.json'),'--csharp-results',str(out/'csharp-cases.json')],['node',str(STUDY/'tools/control-browser.mjs'),dotnet,str(out/'browser')]]
    try:
        for cmd in commands:
            r=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True,timeout=240);records.append({'command':cmd,'exit_code':r.returncode,'stdout':r.stdout,'stderr':r.stderr});(out/'commands.json').write_text(json.dumps(records,indent=2)+'\n')
            if r.returncode:raise RuntimeError('Actual command failed: '+cmd[1])
            if cmd[1]=='--version' and r.stdout.strip()!='10.0.401':raise RuntimeError('Pinned SDK required')
        if before!=identities():raise RuntimeError('Source changed during execution')
        report={'schema_version':1,'kind':'destination_execution','source_stable':True,'source_sha256':before,'native':json.loads((out/'native.json').read_text())['checks'],'browser':json.loads((out/'browser/browser.json').read_text())['checks'],'source':json.loads((out/'source.json').read_text()),'limits':'Overlapping deterministic software controls, not human balance, full source engine, Unity/Windows/Steam or complete combat.'}
        (out/'verification.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS: selected breakbar and actual consumer; stable inputs '+str(len(before)))
    finally:(out/'commands.json').write_text(json.dumps(records,indent=2)+'\n')
if __name__=='__main__':main()
