#!/usr/bin/env python3
"""Build twice, independently inspect and execute the relocated recipient archive."""
import argparse
import hashlib
import importlib.util
import json
import os
import shutil
from pathlib import Path
import subprocess
ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent

def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def verify(output,dotnet,sdk_archive=None,compare=None):
    output=output.resolve()
    if output.is_relative_to(ROOT):raise ValueError('Keep execution outside maintained workspace')
    output.mkdir(parents=True,exist_ok=False)
    names=['package.py','check.py','test_delivery.py','browser.mjs','verify.py','runtime-lock.json','bundle/run-demo.sh','bundle/README.txt']
    identities={str((HERE/n).relative_to(ROOT)):sha(HERE/n) for n in names}
    commands=[]
    env=dict(os.environ,DOTNET_PROCESSOR_COUNT='2',DOTNET_CLI_TELEMETRY_OPTOUT='1',DOTNET_NOLOGO='1')
    def run(command,timeout=300,cwd=ROOT):
        r=subprocess.run([str(x) for x in command],cwd=cwd,env=env,capture_output=True,text=True,timeout=timeout)
        commands.append({'cwd':str(cwd),'command':[str(x) for x in command],'exit_code':r.returncode,'stdout':r.stdout,'stderr':r.stderr})
        (output/'commands.json').write_text(json.dumps(commands,indent=2)+'\n')
        if r.returncode:raise ValueError((r.stdout+r.stderr)[-4000:])
        return r.stdout
    if run(['node','--version']).strip()!='v24.19.0':raise ValueError('Pinned Node24.19.0 required for instrument')
    first=output/'authored-scene-demo-linux-x64.zip';second=output/'repeat.zip'
    for archive,work in [(first,'first build'),(second,'second build')]:
        args=['python3',HERE/'package.py','--dotnet',dotnet,'--output',archive,'--work',output/work]
        if sdk_archive:args+=['--sdk-archive',sdk_archive]
        run(args)
    if sha(first)!=sha(second):raise ValueError('Independent staging builds did not reproduce archive bytes')
    if compare:
        spec=importlib.util.spec_from_file_location('independent_delivery_check',HERE/'check.py')
        checker=importlib.util.module_from_spec(spec);spec.loader.exec_module(checker)
        def payload_identity(archive):
            payload,_=checker.inspect(Path(archive))
            return {name:hashlib.sha256(data).hexdigest() for name,data in payload.items()}
        if payload_identity(compare)!=payload_identity(first):raise ValueError('Rebuilt payload differs from delivered artifact')
    args=['python3',HERE/'check.py',first,'--extract',output/'recipient path with spaces']
    if sdk_archive:args+=['--sdk-archive',sdk_archive]
    inspection=json.loads(run(args));(output/'inspection.json').write_text(json.dumps(inspection,indent=2)+'\n')
    recipient=output/'recipient path with spaces/AuthoredSceneDemo'
    recovered=output/'recovered source';shutil.copytree(recipient/'source',recovered)
    rebuilt=output/'recovered application'
    run([dotnet,'publish',recovered/'north-star/authored-scene/Host/NorthStar.AuthoredScene.csproj','-c','Release','--self-contained','false','-p:UseAppHost=false','-p:RuntimeFrameworkVersion=10.0.12','-p:DebugType=None','-p:DebugSymbols=false','-p:ContinuousIntegrationBuild=true','-p:PathMap='+str(recovered)+'=/_/source','-o',rebuilt,'-m:1','--disable-build-servers'],cwd=recovered/'north-star/csharp')
    app_identity=lambda folder:{p.name:sha(p) for p in folder.iterdir() if p.is_file()}
    if app_identity(rebuilt)!=app_identity(recipient/'app'):raise ValueError('Recovered source did not reproduce delivered application')
    faults=['python3',HERE/'test_delivery.py',first]
    if sdk_archive:faults.append(sdk_archive)
    run(faults)
    run(['node',HERE/'browser.mjs',output/'recipient path with spaces/AuthoredSceneDemo',output/'browser'],timeout=180)
    if identities!={str((HERE/n).relative_to(ROOT)):sha(HERE/n) for n in names}:raise ValueError('Delivery instrument changed during execution')
    result={'input_hashes':identities,'source_stable':True,'recovered_application_identical':True,'archive_sha256':sha(first),'archive_bytes':first.stat().st_size,'repeated_archive_sha256':sha(second),'reproducible':True,'inspection':inspection,'browser':json.loads((output/'browser/results.json').read_text()),'commands':'commands.json','scope':'One local Linuxx64 demonstration; no Unity, Windows, Steam or human experience execution.'}
    (output/'results.json').write_text(json.dumps(result,indent=2)+'\n');print('Reproducible archive, independent checks and actual extracted recipient execution passed:',result['archive_sha256'])
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);p.add_argument('--dotnet',required=True);p.add_argument('--sdk-archive',type=Path);p.add_argument('--compare',type=Path);a=p.parse_args()
    try:verify(a.output,a.dotnet,a.sdk_archive,a.compare)
    except (OSError,ValueError,subprocess.SubprocessError) as e:p.exit(1,str(e)+'\n')
