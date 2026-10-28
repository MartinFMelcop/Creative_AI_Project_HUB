#!/usr/bin/env python3
"""Execute strict conditions in actual existing services and affected consumers."""
import argparse,hashlib,importlib.util,json,shutil,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];STUDY=ROOT/'north-star/memory-study'
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
memory=load('memory_checks',STUDY/'tools/verify.py');field=load('field_checks',ROOT/'north-star/field-journey/tools/presentation-verify.py');assay=load('dialogue_assay',ROOT/'labs/world-gameplay/dialogue-conditions/assay.py')
def identities():
    out=memory.identities();out.update(field.identities());out.update(assay.identities())
    for n in ['labs/world-gameplay/dialogue-conditions/assay.py','labs/world-gameplay/dialogue-conditions/README.md','evidence/dialogue-conditions/protocol.json']:out[n]=hashlib.sha256((ROOT/n).read_bytes()).hexdigest()
    return out
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--dotnet',required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();out=a.output.resolve()
    if out==ROOT or ROOT in out.parents:p.error('New external output required')
    out.mkdir(parents=True,exist_ok=False);dotnet=shutil.which(a.dotnet) or a.dotnet;before=identities();logs=[]
    commands=[[dotnet,'--version'],['python3',str(ROOT/'labs/world-gameplay/dialogue-conditions/assay.py'),'--output',str(out/'source.json')],[dotnet,'build',str(STUDY/'ConditionsChecks/NorthStar.ConditionsChecks.csproj'),'-c','Release'],[dotnet,str(STUDY/'ConditionsChecks/bin/Release/net10.0/NorthStar.ConditionsChecks.dll'),str(out/'native.json')],[dotnet,'build',str(STUDY/'ServiceChecks/NorthStar.ConditionServiceChecks.csproj'),'-c','Release'],[dotnet,str(STUDY/'ServiceChecks/bin/Release/net10.0/NorthStar.ConditionServiceChecks.dll'),str(out/'consumer.json'),str(out/'source.json')],['python3',str(STUDY/'tools/verify.py'),'--dotnet',dotnet,'--output',str(out/'memory-regressions')],['python3',str(ROOT/'north-star/field-journey/tools/presentation-verify.py'),'--dotnet',dotnet,'--output',str(out/'field-regressions')],['node',str(STUDY/'tools/conditions-browser.mjs'),dotnet,str(out/'browser')]]
    try:
        for command in commands:
            r=subprocess.run(command,cwd=ROOT,capture_output=True,text=True,timeout=300);logs.append({'command':command,'exit_code':r.returncode,'stdout':r.stdout,'stderr':r.stderr});(out/'commands.json').write_text(json.dumps(logs,indent=2)+'\n')
            if r.returncode:raise RuntimeError('Actual command failed: '+command[1])
            if command[1]=='--version' and r.stdout.strip()!='10.0.401':raise RuntimeError('Pinned SDK required')
        if before!=identities():raise RuntimeError('Source closure changed during actual execution')
        result={'schema_version':1,'source_sha256':before,'source_stable':True,'native':json.loads((out/'native.json').read_text())['checks'],'consumer':json.loads((out/'consumer.json').read_text())['checks'],'browser':json.loads((out/'browser/browser.json').read_text())['checks'],'regressions':['memory-regressions/verification.json','field-regressions/verification.json'],'limits':'Overlapping actual software controls; not Ruby/coercion/full dialogue/scoring/functions, human evaluation or Unity/Windows/Steam.'};(out/'verification.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS: strict typed conditions and actual existing service/field consumption')
    finally:(out/'commands.json').write_text(json.dumps(logs,indent=2)+'\n')
if __name__=='__main__':main()
