#!/usr/bin/env python3
"""Run the portable rules, preserved source vectors and real C# practice consumer."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[3]
STUDY=ROOT/'north-star/combat-study'
CSHARP=ROOT/'north-star/csharp'

def inputs():
    files={CSHARP/'global.json',ROOT/'projects/realtime-integration-lab/package.json',ROOT/'projects/realtime-integration-lab/package-lock.json'}
    pending=[STUDY/'Checks/NorthStar.CombatChecks.csproj',STUDY/'TrialChecks/NorthStar.TrialChecks.csproj']
    seen=set()
    while pending:
        p=pending.pop().resolve()
        if p in seen: continue
        if not p.is_relative_to(STUDY): raise ValueError('Unexpected project dependency')
        seen.add(p);files.add(p)
        files.update(x for x in p.parent.rglob('*.cs') if not {'bin','obj'} & set(x.parts))
        for item in ET.parse(p).iter():
            tag=item.tag.split('}')[-1]
            if tag=='ProjectReference': pending.append((p.parent/item.attrib['Include']).resolve())
            if tag in {'Compile','Import','PackageReference'}: raise ValueError('Uninventoried compile/import/package dependency')
    for folder in (STUDY/'tools',STUDY/'Host/web',ROOT/'labs/combat-response/status'):
        files.update(p for p in folder.rglob('*') if p.suffix in {'.py','.mjs','.js','.html','.css','.json'} and '__pycache__' not in p.parts)
    if any(p.is_symlink() or not p.is_file() or not p.resolve().is_relative_to(ROOT) for p in files): raise ValueError('Invalid input')
    return {str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(files)}

def verify(output,dotnet):
    output=output.resolve()
    if output.is_relative_to(ROOT):raise ValueError('Outputs must stay outside maintained workspace')
    output.mkdir(parents=True,exist_ok=False)
    before=inputs();records=[]
    env=dict(os.environ,DOTNET_NOLOGO='1',DOTNET_CLI_TELEMETRY_OPTOUT='1',DOTNET_PROCESSOR_COUNT='2')
    sdk=shutil.which(dotnet)
    if not sdk:raise ValueError('SDK executable unavailable')
    def execute(command,cwd=CSHARP,timeout=240):
        r=subprocess.run([str(x) for x in command],cwd=cwd,env=env,capture_output=True,text=True,timeout=timeout)
        records.append(dict(command=[str(x) for x in command],exit_code=r.returncode,stdout=r.stdout,stderr=r.stderr))
        (output/'commands.json').write_text(json.dumps(records,indent=2)+'\n')
        if r.returncode:raise ValueError((r.stdout+r.stderr)[-4000:])
        return r.stdout.strip()
    version=execute([sdk,'--version'])
    node_version=execute(['node','--version'])
    if node_version!='v24.19.0':raise ValueError('Pinned Node24.19.0 required')
    if version!=json.loads((CSHARP/'global.json').read_text())['sdk']['version']:raise ValueError('Pinned SDK required')
    for project in ('Checks/NorthStar.CombatChecks.csproj','TrialChecks/NorthStar.TrialChecks.csproj'):
        execute([sdk,'build',STUDY/project,'-c','Release','-m:1','--disable-build-servers'])
    execute([sdk,STUDY/'Checks/bin/Release/net10.0/NorthStar.CombatChecks.dll'])
    execute([sdk,STUDY/'TrialChecks/bin/Release/net10.0/NorthStar.TrialChecks.dll',output/'native.json'])
    # Historical runner is reviewed/staged by this bounded instrument, never run in preservation.
    execute(['python3',ROOT/'labs/combat-response/status/run.py','--dotnet',sdk,'--output',output/'source'],ROOT)
    execute(['node',STUDY/'tools/browser.mjs',sdk,output/'browser'],ROOT)
    if before!=inputs():raise ValueError('Source changed during execution')
    result=dict(schema_version=1,sdk=version,node=node_version,input_hashes=before,commands='commands.json',native='native.json',source='source/summary.json',browser='browser/results.json',source_stable=True)
    (output/'results.json').write_text(json.dumps(result,indent=2)+'\n')
    print('Actual combat consumer and source instruments passed; stable inputs:',len(before))
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--dotnet',default='dotnet');p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    try:verify(a.output,a.dotnet)
    except (OSError,ValueError,subprocess.SubprocessError) as e:p.exit(1,str(e)+'\n')
