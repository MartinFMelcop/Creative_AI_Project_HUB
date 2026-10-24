#!/usr/bin/env python3
"""Execute selected source interpretation, actual native consumer and Chromium with a stable input closure."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess

ROOT=Path(__file__).resolve().parents[3]
STUDY=ROOT/'north-star/reputation-study'
METHOD=ROOT/'labs/narrative-continuity/reputation/run.py'

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def inputs():
    spec=importlib.util.spec_from_file_location('standing_method',METHOD)
    method=importlib.util.module_from_spec(spec);spec.loader.exec_module(method)
    names=set(method.SOURCES)|{'north-star/csharp/global.json','projects/realtime-integration-lab/package.json','projects/realtime-integration-lab/package-lock.json'}
    for folder in (STUDY,METHOD.parent):
        for p in folder.rglob('*'):
            if {'bin','obj','__pycache__','node_modules'}&set(p.parts):continue
            if p.suffix in {'.cs','.csproj','.html','.css','.js','.mjs','.py','.json'}:names.add(str(p.relative_to(ROOT)))
    for n in names:
        p=ROOT/n
        if not p.is_file() or p.is_symlink() or not p.resolve().is_relative_to(ROOT):raise ValueError('Invalid current input: '+n)
    return {n:sha(ROOT/n) for n in sorted(names)}

def verify(output,dotnet):
    output=output.resolve()
    if output.is_relative_to(ROOT):raise ValueError('Keep execution outside maintained sources')
    output.mkdir(parents=True,exist_ok=False)
    sdk=shutil.which(dotnet)
    if not sdk:raise ValueError('Actual SDK unavailable')
    before=inputs();commands=[]
    def run(command,cwd=ROOT,timeout=300):
        r=subprocess.run([str(x) for x in command],cwd=cwd,capture_output=True,text=True,timeout=timeout,
            env=dict(os.environ,DOTNET_PROCESSOR_COUNT='2',DOTNET_NOLOGO='1',DOTNET_CLI_TELEMETRY_OPTOUT='1'))
        commands.append({'command':[str(x) for x in command],'cwd':str(cwd),'exit_code':r.returncode,'stdout':r.stdout,'stderr':r.stderr})
        (output/'commands.json').write_text(json.dumps(commands,indent=2)+'\n')
        if r.returncode:raise ValueError((r.stdout+r.stderr)[-5000:])
        return r.stdout
    if run([sdk,'--version'],ROOT/'north-star/csharp').strip()!='10.0.401':raise ValueError('SDK differs from exercised pin')
    if run(['node','--version']).strip()!='v24.19.0':raise ValueError('Node differs from exercised pin')
    run(['python3',METHOD,'--dotnet',sdk,'--output',output/'method'])
    project=STUDY/'ConsumerChecks/NorthStar.ReputationConsumerChecks.csproj'
    run([sdk,'build',project,'-c','Release','-m:1','--disable-build-servers'],ROOT/'north-star/csharp')
    run([sdk,project.parent/'bin/Release/net10.0/NorthStar.ReputationConsumerChecks.dll',output/'consumer-native.json'])
    run(['node',STUDY/'tools/browser.mjs',sdk,output/'browser'])
    if inputs()!=before:raise ValueError('Consumer, source or instrument changed during execution')
    method=json.loads((output/'method/results.json').read_text());native=json.loads((output/'consumer-native.json').read_text());browser=json.loads((output/'browser/browser.json').read_text())
    result={'schema_version':1,'source_stable':True,'source_sha256':before,'commands':commands,
        'same_source_cases':method['same_python_csharp_cases'],'typed_source_only_effect_rows':method['source_assay']['typed_source_effect_rows'],
        'rules_native':method['native']['passed'],'consumer_native':native['passed'],'chromium':browser['checks']['passed'],'http':browser['http_checks']['passed'],
        'scope':'ONE corrective legacy/laboratory unit with an actual original finite C# consumer. No Ruby/RMXP, imported source effects/defaults, human assessment, Unity/Windows/Steam, persistent or shared-world claim.'}
    (output/'results.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS: '+json.dumps({k:result[k] for k in ('same_source_cases','typed_source_only_effect_rows','rules_native','consumer_native','chromium','http','source_stable')}))
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--dotnet',required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    try:verify(a.output,a.dotnet)
    except(OSError,ValueError,subprocess.SubprocessError)as e:p.exit(1,'FAIL: '+str(e)+'\n')
