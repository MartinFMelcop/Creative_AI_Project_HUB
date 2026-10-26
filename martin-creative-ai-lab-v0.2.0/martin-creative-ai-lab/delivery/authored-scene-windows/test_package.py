#!/usr/bin/env python3
"""Targeted Windows adapter boundaries; no claim of Windows execution."""
import argparse
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import zipfile

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('windows_check_test',HERE/'check.py');check=importlib.util.module_from_spec(spec);spec.loader.exec_module(check)

def run(linux,runtime,work):
    work=Path(work).absolute();work.mkdir(parents=True,exist_ok=False);passed=[]
    def yes(name,condition):
        if not condition:raise AssertionError(name)
        passed.append(name)
    def no(name,action):
        try:action()
        except (OSError,ValueError,KeyError,zipfile.BadZipFile):passed.append(name);return
        raise AssertionError('Accepted negative: '+name)
    first=work/'first.zip';second=work/'second.zip'
    with contextlib.redirect_stdout(io.StringIO()):
        check.package.package(linux,runtime,first,work/'first')
        check.package.package(linux,runtime,second,work/'second')
    yes('two separate adaptations reproduce bytes',first.read_bytes()==second.read_bytes())
    payload,report=check.inspect(first,linux,runtime)
    yes('all193 official Windows runtime files',report['runtime_files']==193)
    original=check.package.managed_payload(linux)
    yes('all managed app source web provenance bytes unchanged',all(payload[n]==v for n,v in original.items()))
    yes('structural check does not claim Windows execution',report['windows_executed'] is False)
    check.extract(payload,work/'extracted')
    yes('extracted Windows executable and notices',(work/'extracted/AuthoredSceneWindows/runtime/dotnet.exe').is_file() and (work/'extracted/AuthoredSceneWindows/runtime/ThirdPartyNotices.txt').is_file())
    no('existing archive never overwritten',lambda:check.package.package(linux,runtime,first,work/'unused'))
    no('existing extraction never overwritten',lambda:check.extract(payload,work/'extracted'))
    def forged(name,mutate):
        changed=dict(payload);mutate(changed)
        # Recreate hashes as an attacker could: trusted identity must still reject.
        info=json.loads(changed['BUILDINFO.json']);info['managed_closure_sha256']={n:check.package.digest(v) for n,v in changed.items() if n.startswith(('app/','web/','source/'))};changed['BUILDINFO.json']=(json.dumps(info,sort_keys=True,indent=2)+'\n').encode()
        changed['payload.sha256']=''.join(check.package.digest(v)+'  '+n+'\n' for n,v in sorted(changed.items()) if n!='payload.sha256').encode()
        path=work/(name+'.zip')
        with zipfile.ZipFile(path,'w') as z:
            for n,v in sorted(changed.items()):
                item=zipfile.ZipInfo(check.package.PREFIX+n);item.create_system=3;item.external_attr=0o100644<<16;item.compress_type=zipfile.ZIP_DEFLATED;z.writestr(item,v)
        no(name,lambda:check.inspect(path))
    forged('forged managed payload with rehashed manifests',lambda p:p.__setitem__('app/NorthStar.AuthoredScene.dll',b'forged'))
    forged('missing required notices with rehashed manifests',lambda p:p.pop('runtime/ThirdPartyNotices.txt'))
    forged('runtime drift with rehashed manifests',lambda p:p.__setitem__('runtime/dotnet.exe',b'forged'))
    forged('unexpected archive file with rehashed manifests',lambda p:p.__setitem__('extra.txt',b'forged'))
    bad=work/'bad-runtime.zip';bad.write_bytes(Path(runtime).read_bytes()+b'changed')
    no('official runtime archive SHA512 mismatch',lambda:check.package.runtime_payload(bad))
    bad=work/'bad-linux.zip';bad.write_bytes(b'changed')
    no('Linux compiled continuity identity mismatch',lambda:check.package.managed_payload(bad))
    result={'passed':len(passed),'controls':passed,'windows_executed':False,'scope':'Targeted packaging/identity controls only; launcher/HTTP/storage require actual Windows execution.'};(work/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result));return result

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--linux-archive',required=True,type=Path);p.add_argument('--runtime-archive',required=True,type=Path);p.add_argument('--work',required=True,type=Path);a=p.parse_args();run(a.linux_archive,a.runtime_archive,a.work)
