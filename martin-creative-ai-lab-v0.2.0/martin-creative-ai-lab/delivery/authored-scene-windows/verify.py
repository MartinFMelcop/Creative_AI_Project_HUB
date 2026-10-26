#!/usr/bin/env python3
"""Verify Windows recipient identity twice; execute only on the actual Windows host."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]

def sha(path):
    with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()

def load(name):
    spec=importlib.util.spec_from_file_location('windows_'+name,HERE/(name+'.py'))
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module

def verify(output,runtime_archive,compare=None,dotnet=None):
    output=output.resolve()
    if output.is_relative_to(ROOT):raise ValueError('Execution must remain outside maintained workspace')
    output.mkdir(parents=True,exist_ok=False)
    linux=ROOT/'delivery/authored-scene/dist/authored-scene-demo-linux-x64.zip'
    original=load('package').load_linux()
    inherited=[ROOT/'delivery/authored-scene'/name for name in ('check.py','package.py','runtime-lock.json','bundle/run-demo.sh','bundle/README.txt')]
    dependencies={ROOT/name for name in original.source_minimum(ROOT)}|set(inherited)|{linux}
    def identities():
        owned={p for p in HERE.rglob('*') if p.is_file() and not {'__pycache__','dist'} & set(p.parts)}
        return {p.relative_to(ROOT).as_posix():sha(p) for p in sorted(owned|dependencies)}
    inputs=identities()
    commands=[]
    def run(args,cwd=ROOT,timeout=240):
        r=subprocess.run(list(map(str,args)),cwd=cwd,capture_output=True,text=True,timeout=timeout)
        commands.append({'arguments':list(map(str,args)),'cwd':str(cwd),'exit_code':r.returncode,'stdout':r.stdout,'stderr':r.stderr})
        (output/'commands.json').write_text(json.dumps(commands,indent=2)+'\n',encoding='utf8')
        if r.returncode:raise ValueError('Actual command failed: '+r.stdout[-3000:]+r.stderr[-3000:])
        return r.stdout
    linux=ROOT/'delivery/authored-scene/dist/authored-scene-demo-linux-x64.zip'
    archives=[output/'authored-scene-demo-win-x64.zip',output/'repeat.zip']
    for i,p in enumerate(archives):run([sys.executable,HERE/'package.py','--linux-archive',linux,'--runtime-archive',runtime_archive,'--output',p,'--work',output/('stage '+str(i))])
    if sha(archives[0])!=sha(archives[1]):raise ValueError('Separate staging archives differ')
    checker=load('check');payload,inspection=checker.inspect(archives[0],linux_archive=linux,runtime_archive=runtime_archive)
    if compare:
        reference,_=checker.inspect(compare,linux_archive=linux,runtime_archive=runtime_archive)
        if payload!=reference:raise ValueError('Payload differs from published Windows delivery')
    extract=output/'recipient path with spaces';checker.extract(payload,extract)
    # Recoverable managed application identity is a separate source build check.
    # Running it on Linux does not claim Windows compilation or Unity compatibility.
    recovered_identical=None
    if dotnet:
        source=extract/'AuthoredSceneWindows/source';build=output/'recovered application'
        env_old=os.environ.copy()
        os.environ.update(DOTNET_CLI_TELEMETRY_OPTOUT='1',DOTNET_PROCESSOR_COUNT='2',DOTNET_NOLOGO='1')
        try:
            version=run([dotnet,'--version'],cwd=source/'north-star/csharp').strip()
            if version!='10.0.401':raise ValueError('Pinned SDK10.0.401 required')
            run([dotnet,'publish',source/'north-star/authored-scene/Host/NorthStar.AuthoredScene.csproj','-c','Release','--self-contained','false','-p:UseAppHost=false','-p:RuntimeFrameworkVersion=10.0.12','-p:DebugType=None','-p:DebugSymbols=false','-p:ContinuousIntegrationBuild=true','-p:PathMap='+str(source)+'=/_/source','-o',build,'-m:1','--disable-build-servers'],cwd=source/'north-star/csharp')
        finally:os.environ.clear();os.environ.update(env_old)
        identity=lambda d:{p.name:sha(p) for p in d.iterdir() if p.is_file()}
        recovered_identical=identity(build)==identity(extract/'AuthoredSceneWindows/app')
        if not recovered_identical:raise ValueError('Recovered source differs from exact delivered managed files')
    browser=None
    if platform.system()=='Windows':
        if run(['node','--version']).strip()!='v24.19.0':raise ValueError('Pinned Node24.19.0 required')
        run(['node',HERE/'browser.mjs',extract/'AuthoredSceneWindows',output/'browser'],timeout=240)
        browser=json.loads((output/'browser/results.json').read_text(encoding='utf8'))
    checker.inspect(archives[0],linux_archive=linux,runtime_archive=runtime_archive)
    stable=inputs==identities()
    if not stable:raise ValueError('Instrument changed during execution')
    result={'schema_version':1,'platform':platform.platform(),'machine':platform.machine(),'source_stable':stable,'input_sha256':inputs,'archive_sha256':sha(archives[0]),'archive_bytes':archives[0].stat().st_size,'repeat_sha256':sha(archives[1]),'reproducible':True,'inspection':inspection,'recovered_application_identical':recovered_identical,'browser':browser,'windows_executed':browser is not None,'unity_executed':False,'steam_executed':False,'scope':'Windows software execution is only true when this instrument ran its extracted consumer on actual Windows. No human/device, normal-user, Unity or Steam validation.'}
    (output/'results.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
    print(json.dumps({k:result[k] for k in ('platform','archive_sha256','archive_bytes','reproducible','recovered_application_identical','windows_executed')}))

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--runtime-archive',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--compare',type=Path);p.add_argument('--dotnet');a=p.parse_args()
    try:verify(a.output,a.runtime_archive,a.compare,a.dotnet)
    except (OSError,ValueError,subprocess.SubprocessError) as e:p.exit(1,str(e)+'\n')
