#!/usr/bin/env python3
"""Execute one declared leaf plan using the unchanged actual workflow command.

This is a local bounded scenario execution, not the GitHub Actions service or a
claim that this cycle's routing/workflow edits themselves have narrow scope.
"""
import argparse, hashlib, importlib.util, json, os, shutil, subprocess, time, sys
from pathlib import Path

def module(path,name):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def main():
    p=argparse.ArgumentParser();p.add_argument('--workspace',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--dotnet',type=Path,required=True);a=p.parse_args()
    root=a.workspace.resolve();out=a.output.resolve();assert root not in out.parents
    out.mkdir(parents=True,exist_ok=False)
    sys.path.insert(0,str(root/'tools'));scope=module(root/'tools/csharp_scope.py','scope');workflow=module(root/'tools/test_csharp_workflow.py','workflow')
    scenario=scope.WORKSPACE+'north-star/field-journey/preparations.json'
    selected=scope.classify([scenario]);assert {k for k,v in selected.items() if v}=={'field'},selected
    text=workflow.WORKFLOW.read_text();workflow.validate_workflow(text);workflow.validate_wrappers();_,steps=workflow.steps(text)
    guard=module(root/'north-star/field-journey/tools/preparation-verify.py','guard')
    def identities():
        d=guard.identities()
        for name in ['tools/csharp_scope.py','tools/test_csharp_scope.py','tools/test_csharp_workflow.py','tools/ci_scope.py','tools/test_ci_scope.py','evidence/verification-routing/protocol.json']:
            d[name]=hashlib.sha256((root/name).read_bytes()).hexdigest()
        d['../../.github/workflows/lab-checks.yml']=hashlib.sha256(workflow.WORKFLOW.read_bytes()).hexdigest()
        return d
    before=identities();env=os.environ.copy();env['PATH']=str(a.dotnet.resolve().parent)+os.pathsep+env['PATH'];env['RUNNER_TEMP']=str(out/'runtime');env['CHROMIUM_PATH']=env.get('CHROMIUM_PATH','/usr/bin/chromium');Path(env['RUNNER_TEMP']).mkdir()
    records=[];start=time.monotonic()
    def run(command):
        r=subprocess.run(command,cwd=root,env=env,text=True,capture_output=True,timeout=max(1,480-(time.monotonic()-start)))
        records.append({'command':command,'exit_code':r.returncode,'stdout':r.stdout,'stderr':r.stderr});(out/'commands.json').write_text(json.dumps(records,indent=2)+'\n')
        if r.returncode:raise RuntimeError('Required command failed; inspect commands.json')
        return r.stdout
    run(['python3','tools/csharp_scope.py','--path',scenario,'--report',str(out/'plan.json')])
    versions={k:run(c).strip() for k,c in {'dotnet':['dotnet','--version'],'node':['node','--version'],'python':['python3','--version'],'chromium':[env['CHROMIUM_PATH'],'--version']}.items()}
    assert versions['dotnet']=='10.0.401' and versions['node']=='v24.19.0'
    executed=[]
    for name,key in workflow.EXPECTED.items():
        if selected[key]:
            body=workflow.run_body(steps[name]);run(['bash','--noprofile','--norc','-e','-o','pipefail','-c',body]);executed.append({'step':name,'suite':key,'body':body})
    assert before==identities(),'Source closure changed during execution'
    actual=json.loads((out/'runtime/preparation-authoring/verification.json').read_text())
    result={'schema_version':1,'scenario':'Declared actual leaf path; input file was not modified for this trial','path':scenario,'selected':[k for k,v in selected.items() if v],'executed_workflow_steps':executed,'unexecuted_suite_keys':[k for k,v in selected.items() if not v],'versions':versions,'source_sha256':before,'source_stable':True,'actual_consumer':actual,'elapsed_seconds':time.monotonic()-start,'limits':'One real local selected command. Routing/workflow changes in the actual cycle require full scope. Not GitHub Actions execution, speedup, human productivity, production Unity/Windows/Steam or a timeout diagnosis. Existing locked browser dependency was already installed; no dependency installation was simulated.'}
    (out/'execution.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS: actual selected workflow command and unchanged composed consumer')
if __name__=='__main__':main()
