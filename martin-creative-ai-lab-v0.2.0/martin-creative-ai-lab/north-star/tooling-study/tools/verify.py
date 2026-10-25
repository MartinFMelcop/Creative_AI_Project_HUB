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
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[3]
STUDY=ROOT/'north-star/tooling-study'
METHOD=ROOT/'labs/economy-simulation/tooling/run.py'

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def inputs():
    spec=importlib.util.spec_from_file_location('tooling_method',METHOD)
    method=importlib.util.module_from_spec(spec);spec.loader.exec_module(method)
    names=set(method.SOURCES)|{'north-star/csharp/global.json','projects/realtime-integration-lab/package.json','projects/realtime-integration-lab/package-lock.json'}
    pending=[STUDY/'Checks/NorthStar.ToolingChecks.csproj',STUDY/'ConsumerChecks/NorthStar.ToolingConsumerChecks.csproj'];projects=set()
    while pending:
        project=pending.pop().resolve()
        if project in projects:continue
        if not project.is_relative_to(ROOT):raise ValueError('Project dependency escapes maintained workspace')
        projects.add(project);names.add(str(project.relative_to(ROOT)))
        names.update(str(p.relative_to(ROOT)) for p in project.parent.rglob('*.cs') if not {'bin','obj'}&set(p.parts))
        for node in ET.parse(project).iter():
            tag=node.tag.split('}')[-1]
            if tag=='ProjectReference':pending.append((project.parent/node.attrib['Include']).resolve())
            elif tag=='Compile' and 'Include' in node.attrib:
                value=node.attrib['Include']
                if '*' in value:raise ValueError('Explicit wildcard needs bounded source inventory')
                target=(project.parent/value).resolve()
                if not target.is_relative_to(ROOT):raise ValueError('Compile dependency escapes maintained workspace')
                names.add(str(target.relative_to(ROOT)))
    for folder in (STUDY/'web',STUDY/'tools',METHOD.parent):
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
    project=STUDY/'ConsumerChecks/NorthStar.ToolingConsumerChecks.csproj'
    run([sdk,'build',project,'-c','Release','-m:1','--disable-build-servers'],ROOT/'north-star/csharp')
    run([sdk,project.parent/'bin/Release/net10.0/NorthStar.ToolingConsumerChecks.dll',output/'consumer-native.json'])
    run(['node',STUDY/'tools/browser.mjs',sdk,output/'browser'])
    if inputs()!=before:raise ValueError('Consumer, source or instrument changed during execution')
    method=json.loads((output/'method/results.json').read_text());native=json.loads((output/'consumer-native.json').read_text());browser=json.loads((output/'browser/browser.json').read_text())
    result={'schema_version':1,'source_stable':True,'source_sha256':before,'commands':commands,
        'same_identity_cases':method['same_identity_cases'],'actual_source_references':method['actual_source_references'],'known_ids':method['source_assay']['structurally_valid_identity_records'],'quarantined':len(method['source_assay']['quarantined_records']),
        'rules_native':method['native']['passed'],'consumer_native':native['passed'],'chromium':browser['checks']['passed'],'http':browser['http_checks']['passed'],
        'scope':'ONE legacy/laboratory item-tool contract unit with an actual original C# output consumer and unchanged inventory/Crossing. No source repair, unlock/effect import, historical runtime, Unity/Windows/Steam or human validation.'}
    (output/'results.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS: '+json.dumps({k:result[k] for k in ('same_identity_cases','actual_source_references','known_ids','quarantined','rules_native','consumer_native','chromium','http','source_stable')}))
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--dotnet',required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    try:verify(a.output,a.dotnet)
    except(OSError,ValueError,subprocess.SubprocessError)as e:p.exit(1,'FAIL: '+str(e)+'\n')
