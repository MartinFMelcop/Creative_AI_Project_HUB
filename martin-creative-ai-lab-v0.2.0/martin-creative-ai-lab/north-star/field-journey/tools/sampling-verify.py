#!/usr/bin/env python3
"""Execute actual field sampling and the affected existing owner/UI contracts once."""
import argparse,hashlib,importlib.util,json,shutil,subprocess,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];STUDY=ROOT/'north-star/field-journey'
spec=importlib.util.spec_from_file_location('condition_regressions',ROOT/'north-star/memory-study/tools/conditions-verify.py');prior=importlib.util.module_from_spec(spec);spec.loader.exec_module(prior)
def identities():
    out=prior.identities()
    for name in ['evidence/field-sampling/protocol.json']:
        out[name]=hashlib.sha256((ROOT/name).read_bytes()).hexdigest()
    return out

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--dotnet',required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();out=a.output.resolve()
    if out==ROOT or ROOT in out.parents:p.error('New external output required')
    out.mkdir(parents=True,exist_ok=False);dotnet=shutil.which(a.dotnet) or a.dotnet;before=identities();logs=[];started=time.monotonic()
    commands=[[dotnet,'--version'],[dotnet,'build',str(STUDY/'SamplingChecks/NorthStar.FieldSamplingChecks.csproj'),'-c','Release'],[dotnet,str(STUDY/'SamplingChecks/bin/Release/net10.0/NorthStar.FieldSamplingChecks.dll'),str(out/'native.json')],['python3',str(ROOT/'north-star/memory-study/tools/conditions-verify.py'),'--dotnet',dotnet,'--output',str(out/'conditions-regressions')],['node',str(STUDY/'tools/sampling-browser.mjs'),dotnet,str(out/'browser')]]
    try:
        for command in commands:
            remaining=1200-(time.monotonic()-started)
            if remaining<=0:raise RuntimeError('Whole verification deadline exceeded')
            r=subprocess.run(command,cwd=ROOT,capture_output=True,text=True,timeout=min(600,remaining));logs.append({'command':command,'exit_code':r.returncode,'stdout':r.stdout,'stderr':r.stderr});(out/'commands.json').write_text(json.dumps(logs,indent=2)+'\n')
            if r.returncode:raise RuntimeError('Actual command failed: '+command[1])
            if command[1]=='--version' and r.stdout.strip()!='10.0.401':raise RuntimeError('Pinned SDK required')
        if before!=identities():raise RuntimeError('Sources changed during actual execution')
        native=json.loads((out/'native.json').read_text());browser=json.loads((out/'browser/browser.json').read_text())
        result={'schema_version':1,'source_sha256':before,'source_stable':True,'native':native['checks'],'chromium':browser['checks'],'http':browser.get('http_checks',[]),'affected_regressions':'conditions-regressions/verification.json','elapsed_seconds':time.monotonic()-started,'limits':'Actual overlapping software controls, not participants, independent studies, full item/catalog integration, human balance or Unity/Windows/Steam.'}
        (out/'verification.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS: actual field sampling and affected prior consumers')
    finally:(out/'commands.json').write_text(json.dumps(logs,indent=2)+'\n')
if __name__=='__main__':main()
