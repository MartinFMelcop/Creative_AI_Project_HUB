#!/usr/bin/env python3
"""Build one recoverable, SDK-free local authored-scene demonstration archive."""
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import subprocess
import tarfile
import tempfile
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
SDK_VERSION = '10.0.401'
RUNTIME_VERSION = '10.0.12'
SDK_SHA512 = '51c8b999af9e8dd9998c9edc5944e19a90788862068acd38694e098889054ce8c23d4f0c5cccfa16bf187d044562359e5ee69a9f8ad0bbe913ba90311fbce25b'
SDK_URL = 'https://builds.dotnet.microsoft.com/dotnet/Sdk/10.0.401/dotnet-sdk-10.0.401-linux-x64.tar.gz'
HOST = ROOT / 'north-star/authored-scene/Host/NorthStar.AuthoredScene.csproj'
GLOBAL = ROOT / 'north-star/csharp/global.json'
APP_FILES = {'NorthStar.AuthoredScene.dll','NorthStar.Narrative.dll','NorthStar.Crossing.dll','NorthStar.Domain.dll','NorthStar.AuthoredScene.deps.json','NorthStar.AuthoredScene.runtimeconfig.json','NorthStar.Narrative.deps.json','NorthStar.Narrative.runtimeconfig.json','NorthStar.Crossing.deps.json','NorthStar.Crossing.runtimeconfig.json'}


def digest(path, algorithm='sha256'):
    h=hashlib.new(algorithm)
    with path.open('rb') as stream:
        while data:=stream.read(1024*1024):h.update(data)
    return h.hexdigest()


def checked(path):
    path=Path(path)
    if path.is_symlink() or not path.is_file() or not path.resolve().is_relative_to(ROOT):
        raise ValueError('Missing, linked or external source: '+str(path))
    return path


def closure():
    files={GLOBAL};pending=[HOST];seen=set()
    while pending:
        project=pending.pop().resolve()
        if project in seen:continue
        checked(project);seen.add(project);files.add(project)
        # These projects use SDK default compile inclusion; all compile inputs are copied.
        for p in project.parent.rglob('*.cs'):
            if not {'bin','obj'} & set(p.parts):files.add(checked(p))
        for item in ET.parse(project).iter():
            tag=item.tag.split('}')[-1]
            if tag=='ProjectReference':pending.append((project.parent/item.attrib['Include']).resolve())
            if tag in {'Import','Compile','PackageReference'}:raise ValueError('Unsupported implicit build dependency: '+tag)
        for name in ('README.md','SCENE.md'):
            if (project.parent/name).exists():files.add(checked(project.parent/name))
    # No inherited build customization exists in this closure; fail if that changes.
    for project in seen:
        for parent in (project.parent,*project.parent.parents):
            if not parent.is_relative_to(ROOT):break
            for name in ('Directory.Build.props','Directory.Build.targets','Directory.Packages.props','NuGet.Config','nuget.config'):
                if (parent/name).exists():raise ValueError('Uninventoried inherited build input: '+str(parent/name))
    files.add(checked(ROOT/'north-star/authored-scene/README.md'))
    for p in (ROOT/'north-star/authored-scene/web').iterdir():files.add(checked(p))
    return sorted(files)


def runtime_files(archive, dotnet, destination):
    lock=json.loads((HERE/'runtime-lock.json').read_text())
    if lock.get('sdk_archive_sha512')!=SDK_SHA512 or lock.get('runtime_version')!=RUNTIME_VERSION:
        raise ValueError('Unexpected runtime lock identity')
    expected=lock['files']
    if archive is not None:
        if digest(archive,'sha512')!=SDK_SHA512:raise ValueError('SDK archive differs from official SHA512 pin')
        observed={}
        with tarfile.open(archive,'r:gz') as source:
            for member in source:
                name=member.name.removeprefix('./');candidate='runtime/'+name
                if candidate not in expected:continue
                if not member.isfile() or candidate in observed:raise ValueError('Linked/duplicate runtime member')
                with source.extractfile(member) as stream:observed[candidate]=hashlib.sha256(stream.read()).hexdigest()
        if observed!=expected:raise ValueError('Runtime lock differs from verified official archive')
    for name,identity in sorted(expected.items()):
        path=PurePosixPath(name)
        if path.is_absolute() or '..' in path.parts or not name.startswith('runtime/'):
            raise ValueError('Unsafe runtime lock path')
        installed=dotnet.parent/name.removeprefix('runtime/')
        if installed.is_symlink() or not installed.is_file() or digest(installed)!=identity:
            raise ValueError('Installed runtime differs from official archive lock: '+name)
        target=destination/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(installed,target)
        if digest(target)!=identity:raise ValueError('Copied runtime changed: '+name)
    return dict(sorted(expected.items()))


def verify_copies(stage, identities):
    if any(not (stage/name).is_file() or (stage/name).is_symlink() or digest(stage/name)!=identity for name,identity in identities.items()):
        raise ValueError('Copied source changed during staging/build')


def exclusive_copy(source, output):
    # Claim the output only after building; never overwrite a concurrent creator.
    with source.open('rb') as reader, output.open('xb') as writer:
        shutil.copyfileobj(reader,writer)


def package(dotnet, archive, output, work=None):
    dotnet=Path(shutil.which(str(dotnet)) or dotnet).resolve();archive=Path(archive).resolve() if archive else None;output=Path(output).resolve()
    if output.is_relative_to(ROOT):raise ValueError('Archive must be outside maintained workspace')
    if output.exists():raise ValueError('Refusing to overwrite existing output')
    if not dotnet.is_file() or archive is not None and not archive.is_file():raise ValueError('SDK executable/archive unavailable')
    if work is None:work=Path(tempfile.mkdtemp(prefix='authored-delivery-'))
    else:
        work=Path(work).resolve()
        if work.is_relative_to(ROOT):raise ValueError('Work must be outside maintained workspace')
        work.mkdir(parents=True,exist_ok=False)
    sources=closure();identities={str(p.relative_to(ROOT)):digest(p) for p in sources}
    support=[checked(HERE/'package.py'),checked(HERE/'runtime-lock.json'),checked(HERE/'bundle/run-demo.sh'),checked(HERE/'bundle/README.txt')]
    support_hashes={str(p.relative_to(ROOT)):digest(p) for p in support}
    stage=work/'source';bundle=work/'AuthoredSceneDemo';bundle.mkdir()
    for p in sources:
        relative=p.relative_to(ROOT);target=stage/relative;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,target)
        recovery=bundle/'source'/relative;recovery.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,recovery)
    verify_copies(stage,identities)
    verify_copies(bundle/'source',identities)
    # The SDK resolver starts from cwd, so a staging-root global.json pins every project.
    shutil.copyfile(GLOBAL,stage/'global.json')
    logs=[];env=dict(os.environ,DOTNET_NOLOGO='1',DOTNET_CLI_TELEMETRY_OPTOUT='1',DOTNET_PROCESSOR_COUNT='2',DOTNET_MULTILEVEL_LOOKUP='0',DOTNET_ROOT=str(dotnet.parent),DOTNET_CLI_HOME=str(work/'cli-home'))
    def run(args):
        r=subprocess.run([str(dotnet),*map(str,args)],cwd=stage,env=env,capture_output=True,text=True,timeout=240)
        logs.append({'arguments':list(map(str,args)),'exit_code':r.returncode,'stdout':r.stdout,'stderr':r.stderr})
        (work/'commands.json').write_text(json.dumps(logs,indent=2)+'\n')
        if r.returncode:raise ValueError('Build command failed; see '+str(work/'commands.json'))
        return r.stdout.strip()
    if run(['--version'])!=SDK_VERSION:raise ValueError('Pinned SDK required')
    published=work/'published'
    run(['publish',stage/HOST.relative_to(ROOT),'-c','Release','--self-contained','false','-p:UseAppHost=false','-p:RuntimeFrameworkVersion='+RUNTIME_VERSION,'-p:DebugType=None','-p:DebugSymbols=false','-p:ContinuousIntegrationBuild=true','-p:PathMap='+str(stage)+'=/_/source','-o',published,'-m:1','--disable-build-servers'])
    verify_copies(stage,identities)
    verify_copies(bundle/'source',identities)
    actual={p.name for p in published.iterdir() if p.is_file()}
    if actual!=APP_FILES or any(not p.is_file() or p.is_symlink() for p in published.iterdir()):raise ValueError('Unexpected published closure: '+repr(sorted(actual)))
    for p in published.iterdir():(bundle/'app').mkdir(exist_ok=True);shutil.copyfile(p,bundle/'app'/p.name)
    shutil.copytree(stage/'north-star/authored-scene/web',bundle/'web')
    for name in ('run-demo.sh','README.txt'):shutil.copyfile(HERE/'bundle'/name,bundle/name)
    runtime=runtime_files(archive,dotnet,bundle)
    if identities!={str(p.relative_to(ROOT)):digest(p) for p in closure()} or support_hashes!={str(p.relative_to(ROOT)):digest(p) for p in support}:raise ValueError('Source changed during packaging')
    buildinfo={'schema_version':1,'kind':'authored_scene_local_demo','target':'linux-x64','sdk_version':SDK_VERSION,'runtime_version':RUNTIME_VERSION,'sdk_archive_sha512':SDK_SHA512,'sdk_archive_url':SDK_URL,'source_sha256':identities,'runtime_sha256':runtime,'build_inputs_sha256':support_hashes,'scope':'Local .NET/Linux/browser demonstration. No Unity, Windows, Steam, commercial clearance or human validation.'}
    (bundle/'BUILDINFO.json').write_text(json.dumps(buildinfo,sort_keys=True,indent=2)+'\n')
    payload=sorted(p for p in bundle.rglob('*') if p.is_file())
    (bundle/'payload.sha256').write_text(''.join(digest(p)+'  '+p.relative_to(bundle).as_posix()+'\n' for p in payload))
    output.parent.mkdir(parents=True,exist_ok=True);temporary=work/'archive.zip'
    with zipfile.ZipFile(temporary,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as archive_out:
        for p in sorted(p for p in bundle.rglob('*') if p.is_file()):
            rel=p.relative_to(bundle).as_posix();entry=zipfile.ZipInfo('AuthoredSceneDemo/'+rel,(1980,1,1,0,0,0));entry.create_system=3;entry.compress_type=zipfile.ZIP_DEFLATED;entry.external_attr=((0o100755 if rel in {'run-demo.sh','runtime/dotnet'} else 0o100644)<<16);archive_out.writestr(entry,p.read_bytes(),compresslevel=9)
    exclusive_copy(temporary,output)
    result={'archive_sha256':digest(output),'bytes':output.stat().st_size,'files':len(payload)+1,'work':str(work),'source_stable':True}
    (work/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result));return result

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--dotnet',required=True);parser.add_argument('--sdk-archive',type=Path);parser.add_argument('--output',required=True,type=Path);parser.add_argument('--work',type=Path);args=parser.parse_args()
    try:package(args.dotnet,args.sdk_archive,args.output,args.work)
    except (OSError,ValueError,subprocess.SubprocessError,tarfile.TarError,ET.ParseError) as error:parser.exit(1,str(error)+'\n')
