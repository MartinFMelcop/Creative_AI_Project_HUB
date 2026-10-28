#!/usr/bin/env python3
"""Execute the actual field presentation and affected existing consumer regressions."""
import argparse,hashlib,importlib.util,json,shutil,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];STUDY=ROOT/'north-star/field-journey'
spec=importlib.util.spec_from_file_location('field_verifier',STUDY/'tools/verify.py');old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
def identities():
    result=old.identities();name='evidence/field-presentation/protocol.json';result[name]=hashlib.sha256((ROOT/name).read_bytes()).hexdigest();return result
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--dotnet',required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();out=a.output.resolve()
    if out==ROOT or ROOT in out.parents:p.error('New external output required')
    out.mkdir(parents=True,exist_ok=False);dotnet=shutil.which(a.dotnet) or a.dotnet;before=identities();logs=[]
    commands=[[dotnet,'--version'],[dotnet,'build',str(STUDY/'PresentationChecks/NorthStar.FieldPresentationChecks.csproj'),'-c','Release'],[dotnet,str(STUDY/'PresentationChecks/bin/Release/net10.0/NorthStar.FieldPresentationChecks.dll'),str(out/'native.json')],['python3',str(STUDY/'tools/verify.py'),'--dotnet',dotnet,'--output',str(out/'regressions')],['node',str(STUDY/'tools/presentation-browser.mjs'),dotnet,str(out/'browser')]]
    try:
        for command in commands:
            r=subprocess.run(command,cwd=ROOT,capture_output=True,text=True,timeout=240);logs.append({'command':command,'exit_code':r.returncode,'stdout':r.stdout,'stderr':r.stderr});(out/'commands.json').write_text(json.dumps(logs,indent=2)+'\n')
            if r.returncode:raise RuntimeError('Actual command failed: '+command[1])
            if command[1]=='--version' and r.stdout.strip()!='10.0.401':raise RuntimeError('Pinned SDK required')
        if identities()!=before:raise RuntimeError('Sources changed during actual verification')
        native=json.loads((out/'native.json').read_text());browser=json.loads((out/'browser/browser.json').read_text())
        (out/'verification.json').write_text(json.dumps({'schema_version':1,'source_sha256':before,'source_stable':True,'native':native['checks'],'chromium':browser['checks'],'affected_regressions':'regressions/verification.json','limits':'Actual software controls overlap outcomes; no people, source integration, Unity, new Windows/Steam or human recognition/balance/experience.'},indent=2)+'\n');print('PASS: actual field presentation and affected prior consumer regressions')
    finally:(out/'commands.json').write_text(json.dumps(logs,indent=2)+'\n')
if __name__=='__main__':main()
