#!/usr/bin/env python3
"""Execute original authoring data through existing preparation and affected consumers."""
import argparse,hashlib,importlib.util,json,shutil,subprocess,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];STUDY=ROOT/'north-star/field-journey'
spec=importlib.util.spec_from_file_location('sampling_regressions',STUDY/'tools/sampling-verify.py');prior=importlib.util.module_from_spec(spec);spec.loader.exec_module(prior)
def identities():
    out=prior.identities();name='evidence/preparation-authoring/protocol.json';out[name]=hashlib.sha256((ROOT/name).read_bytes()).hexdigest();return out

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--dotnet',required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();out=a.output.resolve()
    if out==ROOT or ROOT in out.parents:p.error('New external output required')
    out.mkdir(parents=True,exist_ok=False);dotnet=shutil.which(a.dotnet) or a.dotnet;before=identities();logs=[];started=time.monotonic()
    commands=[[dotnet,'--version'],[dotnet,'build',str(STUDY/'PreparationChecks/NorthStar.PreparationChecks.csproj'),'-c','Release'],[dotnet,str(STUDY/'PreparationChecks/bin/Release/net10.0/NorthStar.PreparationChecks.dll'),str(out/'native.json')],['python3',str(STUDY/'tools/sampling-verify.py'),'--dotnet',dotnet,'--output',str(out/'regressions')],['node',str(STUDY/'tools/preparation-browser.mjs'),dotnet,str(out/'browser')]]
    try:
        for command in commands:
            remaining=1500-(time.monotonic()-started)
            if remaining<=0:raise RuntimeError('Whole verification deadline exceeded')
            r=subprocess.run(command,cwd=ROOT,capture_output=True,text=True,timeout=min(900,remaining));logs.append({'command':command,'exit_code':r.returncode,'stdout':r.stdout,'stderr':r.stderr});(out/'commands.json').write_text(json.dumps(logs,indent=2)+'\n')
            if r.returncode:raise RuntimeError('Actual command failed: '+command[1])
            if command[1]=='--version' and r.stdout.strip()!='10.0.401':raise RuntimeError('Pinned SDK required')
        if before!=identities():raise RuntimeError('Source/book/protocol closure changed during execution')
        native=json.loads((out/'native.json').read_text());browser=json.loads((out/'browser/browser.json').read_text())
        if native['source_book_sha256']!=before['north-star/field-journey/preparations.json']:raise RuntimeError('Copied runtime book differs from guarded authored source')
        result={'schema_version':1,'source_sha256':before,'source_stable':True,'native':native['checks'],'chromium':browser['checks'],'http':browser.get('http_checks',[]),'affected_regressions':'regressions/verification.json','elapsed_seconds':time.monotonic()-started,'limits':'Original authoring-to-owner software controls; not people, independent studies, full legacy creation/catalog execution, human authoring utility, balance or Unity/Windows/Steam.'}
        (out/'verification.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS: authored preparations and affected existing consumers')
    finally:(out/'commands.json').write_text(json.dumps(logs,indent=2)+'\n')
if __name__=='__main__':main()
