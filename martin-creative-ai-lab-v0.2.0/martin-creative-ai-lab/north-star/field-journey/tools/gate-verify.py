#!/usr/bin/env python3
"""Execute the portable post-Crossing objective through the existing actual consumer."""
import argparse,hashlib,importlib.util,json,shutil,subprocess,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]; STUDY=ROOT/'north-star/field-journey'
spec=importlib.util.spec_from_file_location('existing_field_closure',STUDY/'tools/preparation-verify.py')
prior=importlib.util.module_from_spec(spec);spec.loader.exec_module(prior)
def identities():
    result=prior.identities()
    for name in ['north-star/prototype/return_gate.gd','north-star/prototype/tests/gate_checks.gd','north-star/prototype/tests/gate_policy.gd','north-star/prototype/analysis/return_envelope.gd']:
        result[name]=hashlib.sha256((ROOT/name).read_bytes()).hexdigest()
    return result

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--dotnet',required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();out=a.output.resolve()
    if out==ROOT or ROOT in out.parents:p.error('New external output required')
    out.mkdir(parents=True,exist_ok=False);dotnet=shutil.which(a.dotnet) or a.dotnet;before=identities();logs=[];started=time.monotonic()
    commands=[[dotnet,'--version'],[dotnet,'build',str(STUDY/'GateChecks/NorthStar.GateChecks.csproj'),'-c','Release'],[dotnet,str(STUDY/'GateChecks/bin/Release/net10.0/NorthStar.GateChecks.dll'),str(out/'native.json')],['node',str(STUDY/'tools/gate-browser.mjs'),dotnet,str(out/'browser')]]
    try:
        for command in commands:
            remaining=900-(time.monotonic()-started)
            if remaining<=0:raise RuntimeError('Whole verification deadline exceeded')
            r=subprocess.run(command,cwd=ROOT,capture_output=True,text=True,timeout=min(600,remaining));logs.append({'command':command,'exit_code':r.returncode,'stdout':r.stdout,'stderr':r.stderr});(out/'commands.json').write_text(json.dumps(logs,indent=2)+'\n')
            if r.returncode:raise RuntimeError('Actual command failed: '+command[1])
            if command[1]=='--version' and r.stdout.strip()!='10.0.401':raise RuntimeError('Pinned SDK required')
        if before!=identities():raise RuntimeError('Actual gate source/protocol closure changed during execution')
        native=json.loads((out/'native.json').read_text());browser=json.loads((out/'browser/gate-browser.json').read_text())
        result={'schema_version':1,'kind':'destination_execution','source_sha256':before,'source_stable':True,'native':native['checks'],'chromium':browser['checks'],'http':browser['http_checks'],'negative_controls':browser['negatives'],'elapsed_seconds':time.monotonic()-started,'limits':'Actual original discrete portable gate after unchanged completed Crossing. Source Godot read/identity is not fresh source execution or timing equivalence. Software controls/policies overlap outcomes, not independent people or balance/Unity/Windows/Steam acceptance. Affected prior regressions are separately executed.'}
        (out/'verification.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS: portable actual gate, real completed Field entry, paid policies and source stability')
    finally:(out/'commands.json').write_text(json.dumps(logs,indent=2)+'\n')
if __name__=='__main__':main()
