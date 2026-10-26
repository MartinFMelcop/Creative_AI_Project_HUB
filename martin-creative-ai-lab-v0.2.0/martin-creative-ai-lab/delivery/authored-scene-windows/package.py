#!/usr/bin/env python3
"""Adapt the unchanged verified managed Linux delivery to a private Windows runtime."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import stat
import tempfile
import zipfile

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
PREFIX='AuthoredSceneWindows/'
LINUX_SHA256='d829b1b59ee2dd22f87ab007c4db96bfe1655731b38d02f5085f0b8d30e043e4'
RUNTIME_SHA512='844fa99e16fd6f44e0a7c29def7a82d7846902334d6a955248a9519a4dddb3f5acceb9c9223bef69f8c83b8ae2417537e5b76dddf79fb7117dc85b5039bc1297'

def load_linux():
    spec=importlib.util.spec_from_file_location('linux_delivery_check',HERE.parent/'authored-scene/check.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module

def digest(data,algorithm='sha256'):return hashlib.new(algorithm,data).hexdigest()

def runtime_payload(archive):
    data=Path(archive).read_bytes()
    if digest(data,'sha512')!=RUNTIME_SHA512:raise ValueError('Official Windows runtime archive SHA512 mismatch')
    lock=json.loads((HERE/'runtime-lock.json').read_text())
    if lock.get('runtime_archive_sha512')!=RUNTIME_SHA512 or lock.get('runtime_version')!='10.0.12' or lock.get('target')!='win-x64':raise ValueError('Runtime lock identity mismatch')
    result={};linux=load_linux()
    with zipfile.ZipFile(archive) as source:
        for item in source.infolist():
            linux.safe_name(item.filename)
            if item.is_dir() or stat.S_ISLNK(item.external_attr>>16) or item.flag_bits&1:raise ValueError('Unsupported runtime member')
            name='runtime/'+item.filename
            if name in result:raise ValueError('Duplicate runtime member')
            result[name]=source.read(item)
    if {n:digest(v) for n,v in result.items()}!=lock.get('files'):raise ValueError('Runtime bytes differ from trusted lock')
    return result

def managed_payload(archive):
    if digest(Path(archive).read_bytes())!=LINUX_SHA256:raise ValueError('Linux continuity archive identity mismatch')
    payload,_=load_linux().inspect(archive)
    result={n:v for n,v in payload.items() if n.startswith(('app/','web/','source/'))}
    lock=json.loads((HERE/'runtime-lock.json').read_text())
    if {n:digest(v) for n,v in result.items()}!=lock['managed_sha256'] or digest(payload['BUILDINFO.json'])!=lock['linux_buildinfo_sha256']:raise ValueError('Managed identity differs from trusted lock')
    result['LINUX_BUILDINFO.json']=payload['BUILDINFO.json']
    return result

def package(linux_archive,runtime_archive,output,work=None):
    output=Path(output).resolve()
    if output.is_relative_to(ROOT) or output.exists() or output.is_symlink():raise ValueError('Output must be new and outside maintained workspace')
    if work is None:work=Path(tempfile.mkdtemp(prefix='windows-delivery-'))
    else:
        work=Path(work).resolve()
        if work.is_relative_to(ROOT):raise ValueError('Work must be outside maintained workspace')
        work.mkdir(parents=True,exist_ok=False)
    inputs=['package.py','check.py','runtime-lock.json','bundle/run-demo.ps1','bundle/README.txt']
    initial={n:digest((HERE/n).read_bytes()) for n in inputs}
    payload=managed_payload(linux_archive);payload.update(runtime_payload(runtime_archive))
    for n in ('run-demo.ps1','README.txt'):payload[n]=(HERE/'bundle'/n).read_bytes()
    info={'schema_version':1,'kind':'authored_scene_windows_recipient','target':'win-x64','runtime_version':'10.0.12','runtime_archive_sha512':RUNTIME_SHA512,'linux_archive_sha256':LINUX_SHA256,'managed_closure_sha256':{n:digest(v) for n,v in payload.items() if n.startswith(('app/','web/','source/'))},'build_inputs_sha256':initial,'scope':'Unchanged managed application and source closure; Windows execution is separately observed. No Unity, Steam, commercial clearance or human validation.'}
    payload['BUILDINFO.json']=(json.dumps(info,sort_keys=True,indent=2)+'\n').encode()
    payload['payload.sha256']=''.join(digest(v)+'  '+n+'\n' for n,v in sorted(payload.items())).encode()
    if initial!={n:digest((HERE/n).read_bytes()) for n in inputs}:raise ValueError('Packaging inputs changed')
    # Reinspect the original to reject concurrent source changes during adaptation.
    managed_payload(linux_archive)
    staged=work/'archive.zip'
    with zipfile.ZipFile(staged,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as out:
        for n,v in sorted(payload.items()):
            item=zipfile.ZipInfo(PREFIX+n,(1980,1,1,0,0,0));item.create_system=3;item.external_attr=0o100644<<16;item.compress_type=zipfile.ZIP_DEFLATED;out.writestr(item,v,compresslevel=9)
    output.parent.mkdir(parents=True,exist_ok=True)
    with staged.open('rb') as src,output.open('xb') as dst:shutil.copyfileobj(src,dst)
    result={'archive_sha256':digest(output.read_bytes()),'bytes':output.stat().st_size,'files':len(payload),'managed_bytes_unchanged':True,'windows_executed':False}
    print(json.dumps(result,sort_keys=True));return result

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--linux-archive',required=True,type=Path);p.add_argument('--runtime-archive',required=True,type=Path);p.add_argument('--output',required=True,type=Path);p.add_argument('--work',type=Path);a=p.parse_args()
    try:package(a.linux_archive,a.runtime_archive,a.output,a.work)
    except (OSError,ValueError,KeyError,zipfile.BadZipFile) as e:p.exit(1,str(e)+'\n')
