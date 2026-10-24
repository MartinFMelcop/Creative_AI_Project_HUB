#!/usr/bin/env python3
"""Execute source eligibility, portable owner and actual original browser consumer."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[3]
STUDY=ROOT/'north-star/availability-study'
LAB=ROOT/'labs/world-gameplay/availability'
CSHARP=ROOT/'north-star/csharp'

def inputs():
    files={CSHARP/'global.json',ROOT/'projects/realtime-integration-lab/package.json',ROOT/'projects/realtime-integration-lab/package-lock.json'}
    spec=importlib.util.spec_from_file_location('availability_assay',LAB/'run.py');assay=importlib.util.module_from_spec(spec);spec.loader.exec_module(assay)
    files.update(ROOT/name for name in assay.PATHS.values())
    pending=list(STUDY.rglob('*.csproj'));seen=set()
    while pending:
        p=pending.pop().resolve()
        if p in seen:continue
        if not p.is_relative_to(STUDY):raise ValueError('Unexpected project dependency')
        seen.add(p);files.add(p)
        files.update(x for x in p.parent.glob('*.cs'))
        for e in ET.parse(p).iter():
            tag=e.tag.split('}')[-1]
            if tag=='ProjectReference':pending.append((p.parent/e.attrib['Include']).resolve())
            if tag in {'Compile','Import','PackageReference'}:raise ValueError('Uninventoried build dependency')
    for base in (STUDY/'tools',STUDY/'Host/web',LAB):
        files.update(p for p in base.rglob('*') if p.suffix in {'.py','.mjs','.js','.html','.css','.json'} and '__pycache__' not in p.parts)
    for p in list(files):
        for parent in (p.parent,*p.parents):
            if parent==ROOT.parent:break
            for name in ('Directory.Build.props','Directory.Build.targets','Directory.Packages.props','NuGet.Config','nuget.config'):
                if (parent/name).exists():raise ValueError('Inherited build configuration requires explicit inventory: '+str(parent/name))
    if any(p.is_symlink() or not p.is_file() for p in files):raise ValueError('Non-regular input')
    return {str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(files)}

def verify(output,dotnet):
    output=output.resolve()
    if output.is_relative_to(ROOT):raise ValueError('Outputs must stay outside maintained workspace')
    output.mkdir(parents=True,exist_ok=False)
    before=inputs();records=[]
    sdk=shutil.which(dotnet)
    if not sdk:raise ValueError('SDK executable unavailable')
    env=dict(os.environ,DOTNET_NOLOGO='1',DOTNET_CLI_TELEMETRY_OPTOUT='1',DOTNET_PROCESSOR_COUNT='2')
    def run(command,cwd=CSHARP,timeout=180):
        r=subprocess.run([str(x) for x in command],cwd=cwd,env=env,capture_output=True,text=True,timeout=timeout)
        records.append(dict(command=[str(x) for x in command],exit_code=r.returncode,stdout=r.stdout,stderr=r.stderr));(output/'commands.json').write_text(json.dumps(records,indent=2)+'\n')
        if r.returncode:raise ValueError((r.stdout+r.stderr)[-5000:])
        return r.stdout.strip()
    version=run([sdk,'--version']);node=run(['node','--version'])
    if version!=json.loads((CSHARP/'global.json').read_text())['sdk']['version']:raise ValueError('Pinned SDK required')
    if node!='v24.19.0':raise ValueError('Pinned Node24.19.0 required')
    run(['python3',LAB/'run.py','--output',output/'source.json'],ROOT)
    run(['python3',LAB/'test_instrument.py'],ROOT)
    for folder in ('Checks','Host'):
        projects=list((STUDY/folder).glob('*.csproj'))
        if len(projects)!=1:raise ValueError('One explicit project per consumer required')
        run([sdk,'build',projects[0],'-c','Release','-m:1','--disable-build-servers'])
    run([sdk,STUDY/'Checks/bin/Release/net10.0/NorthStar.AvailabilityChecks.dll',output/'native.json',output/'source.json'])
    report=run([sdk,STUDY/'Checks/bin/Release/net10.0/NorthStar.AvailabilityChecks.dll','--source-cases',output/'source.json'])
    (output/'native-source.json').write_text(report+'\n')
    run(['python3',LAB/'run.py','--responses',output/'native-source.json','--output',output/'verified-source.json'],ROOT)
    run(['node',STUDY/'tools/browser.mjs',sdk,output/'browser'],ROOT)
    if before!=inputs():raise ValueError('Instrument or consumer changed during execution')
    result=dict(schema_version=1,sdk=version,node=node,input_hashes=before,source_stable=True,scope='Source masks and original local service authority; no historical schedule runtime, Unity, Windows, Steam or participant execution.')
    (output/'results.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS: stable actual availability consumer and source controls')
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--dotnet',default='dotnet');p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    try:verify(a.output,a.dotnet)
    except (OSError,ValueError,subprocess.SubprocessError) as e:p.exit(1,str(e)+'\n')
