#!/usr/bin/env python3
"""Verify focused access to the same authoritative paid FieldJourney."""
import argparse,hashlib,importlib.util,json,shutil,subprocess,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
STUDY=ROOT/'north-star/field-journey'
spec=importlib.util.spec_from_file_location('existing_field_closure',STUDY/'tools/preparation-verify.py')
prior=importlib.util.module_from_spec(spec);spec.loader.exec_module(prior)
def identities():
    result=prior.identities()
    for name in ['north-star/field-journey/tools/journey-view-protocol.json']:
        result[name]=hashlib.sha256((ROOT/name).read_bytes()).hexdigest()
    return result

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--dotnet',required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();out=a.output.resolve()
    if out==ROOT or ROOT in out.parents:p.error('New external output required')
    out.mkdir(parents=True,exist_ok=False);dotnet=shutil.which(a.dotnet) or a.dotnet;before=identities();logs=[];start=time.monotonic()
    commands=[[dotnet,'--version'],[dotnet,'build',str(STUDY/'Host/NorthStar.FieldJourney.csproj'),'-c','Release'],['node',str(STUDY/'tools/journey-view-browser.mjs'),dotnet,str(out/'browser')]]
    try:
        for command in commands:
            remaining=600-(time.monotonic()-start)
            if remaining<=0:raise RuntimeError('Whole verification deadline exceeded')
            r=subprocess.run(command,cwd=ROOT,capture_output=True,text=True,timeout=min(300,remaining));logs.append({'command':command,'exit_code':r.returncode,'stdout':r.stdout,'stderr':r.stderr});(out/'commands.json').write_text(json.dumps(logs,indent=2)+'\n')
            if r.returncode:raise RuntimeError('Actual command failed: '+command[1])
            if command[1]=='--version' and r.stdout.strip()!='10.0.401':raise RuntimeError('Pinned SDK required')
        if before!=identities():raise RuntimeError('Source/protocol closure changed during actual execution')
        browser=json.loads((out/'browser/journey-view-browser.json').read_text())
        result={'schema_version':1,'kind':'destination_execution','source_sha256':before,'source_stable':True,'chromium':browser['checks'],'negative_controls':browser['negatives'],'elapsed_seconds':time.monotonic()-start,'limits':'Actual presentation and command routing in the same FieldJourney only. Full/focused routes are matched software controls, not independent people, human comprehension/accessibility or Unity/Windows/Steam acceptance. Existing maximal Field, keyboard and withdrawal regressions are separate executions.'}
        (out/'verification.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS: same-owner focused journey, exact route parity and source stability')
    finally:(out/'commands.json').write_text(json.dumps(logs,indent=2)+'\n')
if __name__=='__main__':main()
