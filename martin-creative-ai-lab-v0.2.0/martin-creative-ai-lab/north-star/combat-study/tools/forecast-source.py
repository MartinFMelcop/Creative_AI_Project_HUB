#!/usr/bin/env python3
"""Execute preserved P05 domain checks in a copied tree, without importing its fiction."""
import argparse,hashlib,json,os,shutil,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
def main():
    p=argparse.ArgumentParser();p.add_argument('--dotnet',required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    out=a.output.resolve()
    if out.is_relative_to(ROOT) or out.exists():p.error('New output outside maintained sources required')
    out.mkdir(parents=True);source=ROOT/'projects/cinderwatch';stage=out/'source';stage.mkdir()
    files=[x for d in ['Core','Checks'] for x in (source/d).rglob('*') if x.is_file() and not {'bin','obj'}.intersection(x.parts)]
    files += [source/'Directory.Build.props',source/'global.json']
    identities=[]
    for f in sorted(files):
        target=stage/f.relative_to(source);target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(f,target)
        identities.append({'local_path':f.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'size_bytes':f.stat().st_size})
    commands=[]
    for cmd in [[a.dotnet,'--version'],[a.dotnet,'build','Checks/Cinder.Checks.csproj','-c','Release','-m:1','--disable-build-servers'],[a.dotnet,'Checks/bin/Release/net10.0/Cinder.Checks.dll']]:
        r=subprocess.run(cmd,cwd=stage,capture_output=True,text=True,timeout=180,env=dict(os.environ,DOTNET_PROCESSOR_COUNT='2',DOTNET_NOLOGO='1',DOTNET_CLI_TELEMETRY_OPTOUT='1'))
        commands.append({'command':cmd,'exit_code':r.returncode,'stdout':r.stdout,'stderr':r.stderr});(out/'commands.json').write_text(json.dumps(commands,indent=2)+'\n')
        if r.returncode:raise RuntimeError('Actual copied P05 command failed')
    for row in identities:
        if hashlib.sha256((ROOT/row['local_path']).read_bytes()).hexdigest()!=row['sha256']:raise RuntimeError('P05 source changed during assay')
    (out/'source.json').write_text(json.dumps({'kind':'actual_copied_P05_domain_execution','source_artifacts':identities,'commands':'commands.json','scope':'Actual existing source checks include bounded forecasts versus actual branch execution. Full campaign check count is not new North Star forecast count or human evidence. No Cinder fiction/statistics imported.'},indent=2)+'\n')
    print('PASS: actual copied P05 domain and response forecasts; original sources stable')
if __name__=='__main__':main()
