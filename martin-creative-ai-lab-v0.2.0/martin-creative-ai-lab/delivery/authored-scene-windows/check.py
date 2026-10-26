#!/usr/bin/env python3
"""Inspect the Windows recipient inventory before extraction; execution is separate."""
import argparse
import importlib.util
import json
from pathlib import Path
import re
import stat
import zipfile

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('windows_delivery_package',HERE/'package.py')
package=importlib.util.module_from_spec(spec);spec.loader.exec_module(package)
ROOT=package.ROOT

def inspect(archive,linux_archive=None,runtime_archive=None):
    linux=package.load_linux();payload={}
    with zipfile.ZipFile(archive) as source:
        entries=source.infolist();names=[i.filename for i in entries]
        if len(names)>3000 or names!=sorted(set(names)) or sum(i.file_size for i in entries)>300_000_000:raise ValueError('Invalid archive inventory')
        for item in entries:
            linux.safe_name(item.filename)
            if not item.filename.startswith(package.PREFIX):raise ValueError('Unexpected archive root')
            n=item.filename[len(package.PREFIX):];linux.safe_name(n)
            if item.create_system!=3 or item.external_attr>>16!=0o100644 or item.flag_bits&1 or item.compress_type!=zipfile.ZIP_DEFLATED:raise ValueError('Unsupported archive member')
            payload[n]=source.read(item)
    declared={}
    for line in payload.get('payload.sha256',b'').decode().splitlines():
        if not re.fullmatch(r'[0-9a-f]{64}  .+',line):raise ValueError('Malformed inventory')
        value,n=line.split('  ',1);linux.safe_name(n)
        if n in declared or n=='payload.sha256':raise ValueError('Duplicate manifest entry')
        declared[n]=value
    actual={n:package.digest(v) for n,v in payload.items() if n!='payload.sha256'}
    if actual!=declared or list(declared)!=sorted(declared):raise ValueError('Exact payload inventory mismatch')
    info=linux.json_object(payload.get('BUILDINFO.json',b'{}'))
    if info.get('schema_version')!=1 or info.get('kind')!='authored_scene_windows_recipient' or info.get('target')!='win-x64' or info.get('runtime_archive_sha512')!=package.RUNTIME_SHA512 or info.get('linux_archive_sha256')!=package.LINUX_SHA256 or info.get('runtime_version')!='10.0.12':raise ValueError('Build identity mismatch')
    lock=linux.json_object((HERE/'runtime-lock.json').read_bytes())
    runtime={n:package.digest(v) for n,v in payload.items() if n.startswith('runtime/')}
    if runtime!=lock['files'] or lock['runtime_archive_sha512']!=package.RUNTIME_SHA512:raise ValueError('Runtime identity mismatch')
    inputs=['package.py','check.py','runtime-lock.json','bundle/run-demo.ps1','bundle/README.txt']
    if info.get('build_inputs_sha256')!={n:package.digest((HERE/n).read_bytes()) for n in inputs}:raise ValueError('Packaging input changed')
    for n in ('run-demo.ps1','README.txt'):
        if payload.get(n)!=(HERE/'bundle'/n).read_bytes():raise ValueError('Recipient support changed')
    managed={n:package.digest(v) for n,v in payload.items() if n.startswith(('app/','web/','source/'))}
    if managed!=lock.get('managed_sha256') or package.digest(payload.get('LINUX_BUILDINFO.json',b''))!=lock.get('linux_buildinfo_sha256') or managed!=info.get('managed_closure_sha256'):raise ValueError('Managed closure mismatch')
    original=linux.json_object(payload.get('LINUX_BUILDINFO.json',b'{}'))
    if original.get('source_sha256')!={n.removeprefix('source/'):package.digest(v) for n,v in payload.items() if n.startswith('source/')}:raise ValueError('Recovered source inventory mismatch')
    if set(original.get('source_sha256',{}))!=linux.source_minimum(ROOT):raise ValueError('Source closure mismatch')
    for n,h in original['source_sha256'].items():
        local=ROOT/n
        if local.is_symlink() or not local.is_file() or not local.resolve().is_relative_to(ROOT) or package.digest(local.read_bytes())!=h:raise ValueError('Current source identity mismatch')
    required={'BUILDINFO.json','LINUX_BUILDINFO.json','README.txt','run-demo.ps1','payload.sha256'}|set(runtime)|set(managed)
    if set(payload)!=required or not all(payload[n] for n in required):raise ValueError('Unexpected/empty payload')
    if linux_archive is not None:
        expected=package.managed_payload(linux_archive)
        if any(payload.get(n)!=v for n,v in expected.items()) or set(expected)-{'LINUX_BUILDINFO.json'}!=set(managed):raise ValueError('Original managed delivery differs')
    if runtime_archive is not None and {n:payload[n] for n in runtime}!=package.runtime_payload(runtime_archive):raise ValueError('Official runtime differs')
    return payload,{'files':len(payload),'runtime_files':len(runtime),'source_files':len(original['source_sha256']),'managed_archive_verified':linux_archive is not None,'runtime_archive_verified':runtime_archive is not None,'windows_executed':False,'unity_executed':False}

def extract(payload,output):
    output=Path(output).resolve()
    if output.is_relative_to(ROOT) or output.exists() or output.is_symlink():raise ValueError('Extraction must be new and external')
    output.mkdir(parents=True)
    for n,v in payload.items():
        target=output/'AuthoredSceneWindows'/n;target.parent.mkdir(parents=True,exist_ok=True)
        with target.open('xb') as f:f.write(v)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('archive',type=Path);p.add_argument('--linux-archive',type=Path);p.add_argument('--runtime-archive',type=Path);p.add_argument('--extract',type=Path);a=p.parse_args()
    try:
        payload,report=inspect(a.archive,a.linux_archive,a.runtime_archive)
        if a.extract:extract(payload,a.extract)
        print(json.dumps(report,sort_keys=True))
    except (OSError,ValueError,KeyError,zipfile.BadZipFile) as e:p.exit(1,str(e)+'\n')
