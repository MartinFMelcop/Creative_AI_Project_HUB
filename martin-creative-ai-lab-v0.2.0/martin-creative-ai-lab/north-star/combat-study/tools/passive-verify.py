#!/usr/bin/env python3
"""Execute actual passive behavior and affected existing combat regressions."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[3]
STUDY=ROOT/'north-star/combat-study'
sys.path.insert(0,str(ROOT/'labs/combat-response/passives'))
import assay

def inputs():
    files=[p for p in STUDY.rglob('*') if p.is_file() and not {'bin','obj','__pycache__'}&set(p.parts)]
    files+=[ROOT/n for n in assay.identities()]
    files+=list((ROOT/'labs/combat-response/passives').glob('*.py'))
    files+=[ROOT/'evidence/passive-response/protocol.json',ROOT/'north-star/csharp/global.json',ROOT/'projects/realtime-integration-lab/package.json',ROOT/'projects/realtime-integration-lab/package-lock.json']
    return {str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(set(files))}

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--dotnet',required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();output=a.output.resolve()
    if output==ROOT or ROOT in output.parents:p.error('New output outside maintained sources required')
    output.mkdir(parents=True,exist_ok=False);dotnet=shutil.which(a.dotnet) or a.dotnet;before=inputs();records=[]
    commands=[[dotnet,'--version'],[dotnet,'build',str(STUDY/'PassiveChecks/NorthStar.PassiveChecks.csproj'),'-c','Release'],[dotnet,str(STUDY/'PassiveChecks/bin/Release/net10.0/NorthStar.PassiveChecks.dll'),str(output/'native.json')],['python3',str(ROOT/'labs/combat-response/passives/assay.py'),'--output',str(output/'source-assay.json')],['python3',str(STUDY/'tools/verify.py'),'--dotnet',dotnet,'--output',str(output/'regressions')],['node',str(STUDY/'tools/passive-browser.mjs'),dotnet,str(output/'browser')]]
    try:
        for cmd in commands:
            r=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True,timeout=240);records.append({'command':cmd,'exit_code':r.returncode,'stdout':r.stdout,'stderr':r.stderr});(output/'commands.json').write_text(json.dumps(records,indent=2)+'\n')
            if r.returncode:raise RuntimeError('Actual command failed: '+cmd[1])
            if cmd[1]=='--version' and r.stdout.strip()!='10.0.401':raise RuntimeError('Pinned SDK required')
        if before!=inputs():raise RuntimeError('Source closure changed during verification')
        native=json.loads((output/'native.json').read_text());browser=json.loads((output/'browser/browser.json').read_text())
        (output/'verification.json').write_text(json.dumps({'schema_version':1,'source_stable':True,'input_hashes':before,'native':native['checks'],'browser_result':'browser/browser.json','regressions':'regressions/results.json','limits':'Overlapping software controls, not people/independent studies, source Ruby execution, Unity, Windows/Steam or human experience.'},indent=2)+'\n');print('PASS: actual passives and affected prior consumer/source/browser regressions')
    finally:(output/'commands.json').write_text(json.dumps(records,indent=2)+'\n')
if __name__=='__main__':main()
