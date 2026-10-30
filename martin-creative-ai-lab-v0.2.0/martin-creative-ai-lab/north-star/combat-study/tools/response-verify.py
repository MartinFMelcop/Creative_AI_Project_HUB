#!/usr/bin/env python3
"""Execute paid reaction windows in the existing C# owner and actual browser."""
import argparse,hashlib,json,shutil,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];STUDY=ROOT/'north-star/combat-study'
def identities():
    files=[p for base in [STUDY,ROOT/'labs/combat-response/responses'] for p in base.rglob('*') if p.is_file() and not {'bin','obj','__pycache__'}.intersection(p.parts)]
    files += [ROOT/'north-star/csharp/global.json',ROOT/'projects/realtime-integration-lab/package.json',ROOT/'projects/realtime-integration-lab/package-lock.json',ROOT/'references/rave-master/snapshots/36af1651271422ae33856e8b5d7b45702215f165/source/RM_CORE/DATA/CORE/REGRAS_DE_COMBATE.csv']
    return {str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(files)}
def main():
    p=argparse.ArgumentParser();p.add_argument('--dotnet',required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();out=a.output.resolve()
    if out.is_relative_to(ROOT) or out.exists():p.error('New external output directory required')
    out.mkdir(parents=True);dotnet=shutil.which(a.dotnet) or a.dotnet;before=identities();records=[]
    commands=[[dotnet,'--version'],[dotnet,'build',str(STUDY/'ResponseChecks/NorthStar.ResponseChecks.csproj'),'-c','Release','-m:1','--disable-build-servers'],[dotnet,str(STUDY/'ResponseChecks/bin/Release/net10.0/NorthStar.ResponseChecks.dll'),str(out/'native.json')],['python3',str(ROOT/'labs/combat-response/responses/assay.py'),'--native',str(out/'native.json'),'--output',str(out/'source.json')],['node',str(STUDY/'tools/response-browser.mjs'),dotnet,str(out/'browser')]]
    try:
        for cmd in commands:
            r=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True,timeout=240);records.append({'command':cmd,'exit_code':r.returncode,'stdout':r.stdout,'stderr':r.stderr});(out/'commands.json').write_text(json.dumps(records,indent=2)+'\n')
            if r.returncode:raise RuntimeError('Actual command failed: '+cmd[1])
            if cmd[1]=='--version' and r.stdout.strip()!='10.0.401':raise RuntimeError('Pinned SDK required')
        if before!=identities():raise RuntimeError('Source changed during execution')
        (out/'verification.json').write_text(json.dumps({'schema_version':1,'source_stable':True,'source_sha256':before,'native':json.loads((out/'native.json').read_text())['checks'],'browser':json.loads((out/'browser/browser.json').read_text())['checks'],'http':json.loads((out/'browser/browser.json').read_text())['http_checks'],'limits':'Bounded overlapping software controls; source requirements not historical runtime, human balance, Unity/Windows/Steam or full stack.'},indent=2)+'\n');print('PASS: actual paid response chain and browser; stable inputs '+str(len(before)))
    finally:(out/'commands.json').write_text(json.dumps(records,indent=2)+'\n')
if __name__=='__main__':main()
