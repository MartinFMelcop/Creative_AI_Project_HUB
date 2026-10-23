#!/usr/bin/env python3
"""Fault-inject real recipient archives without changing maintained inputs."""
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import warnings
import zipfile
HERE=Path(__file__).resolve().parent

def module(name):
    spec=importlib.util.spec_from_file_location(name,HERE/(name+'.py'));value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value
check=module('check');pack=module('package')

def main(archive):
    payload,report=check.inspect(archive);controls=[{'id':'actual-positive-archive','passed':True,'evidence':report}]
    with tempfile.TemporaryDirectory(prefix='recipient-fault-') as temporary:
        work=Path(temporary)
        def negative(name,change,expected,refresh=True,extra=None,mode=None):
            changed=dict(payload);change(changed)
            if refresh:changed['payload.sha256']=''.join(hashlib.sha256(data).hexdigest()+'  '+key+'\n' for key,data in sorted(changed.items()) if key!='payload.sha256').encode()
            path=work/(name+'.zip')
            with warnings.catch_warnings():
                warnings.simplefilter('ignore',UserWarning)
                with zipfile.ZipFile(path,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=1) as target:
                    entries=[(check.PREFIX+key,data) for key,data in sorted(changed.items())]
                    if extra:entries.append(extra)
                    entries.sort(key=lambda item:item[0])
                    for key,data in entries:
                        info=zipfile.ZipInfo(key,(1980,1,1,0,0,0));info.create_system=3;info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=((0o100755 if key in (check.PREFIX+'run-demo.sh',check.PREFIX+'runtime/dotnet') else 0o100644)<<16)
                        if mode and key==check.PREFIX+mode:info.external_attr=0o100644<<16
                        target.writestr(info,data,compresslevel=1)
            try:check.inspect(path)
            except ValueError as error:
                if expected not in str(error):raise AssertionError(name+': wrong rejection: '+str(error))
                controls.append({'id':name,'passed':True,'rejection':str(error)});return
            raise AssertionError('Not rejected: '+name)
        negative('changed-dll',lambda p:p.__setitem__('app/NorthStar.AuthoredScene.dll',p['app/NorthStar.AuthoredScene.dll']+b'changed'),'Payload manifest differs',False)
        negative('missing-notice',lambda p:p.pop('runtime/ThirdPartyNotices.txt'),'Missing required')
        negative('missing-web',lambda p:p.pop('web/app.js'),'Missing required')
        key='runtime/shared/Microsoft.NETCore.App/10.0.12/System.Text.Json.dll'
        def forged_runtime(p):
            p[key]+=b'changed';info=json.loads(p['BUILDINFO.json']);info['runtime_sha256'][key]=hashlib.sha256(p[key]).hexdigest();p['BUILDINFO.json']=json.dumps(info).encode()
        negative('self-consistent-forged-runtime',forged_runtime,'trusted official runtime lock')
        key_source='north-star/authored-scene/Host/Room.cs'
        def forged_source(p):
            p['source/'+key_source]+=b'\n';info=json.loads(p['BUILDINFO.json']);info['source_sha256'][key_source]=hashlib.sha256(p['source/'+key_source]).hexdigest();p['BUILDINFO.json']=json.dumps(info).encode()
        negative('self-consistent-wrong-source',forged_source,'Source binding mismatch')
        def missing_authority(p):
            key='north-star/csharp/Narrative/SCENE.md';p.pop('source/'+key);info=json.loads(p['BUILDINFO.json']);info['source_sha256'].pop(key);p['BUILDINFO.json']=json.dumps(info).encode()
        negative('missing-creative-provenance',missing_authority,'Incomplete source/runtime')
        negative('unsafe-path',lambda p:None,'Unsafe archive path',extra=(check.PREFIX+'../escape',b'bad'))
        duplicate=check.PREFIX+'web/index.html'
        negative('duplicate-path',lambda p:None,'Duplicate, unordered',extra=(duplicate,payload['web/index.html']))
        negative('lost-executable-permission',lambda p:None,'Unexpected member type or permissions',mode='runtime/dotnet')
        negative('bundled-sdk-rejected',lambda p:p.__setitem__('runtime/sdk/unwanted.dll',b'SDK'),'Runtime inventory mismatch')
        candidate=work/'candidate';candidate.write_bytes(b'new');concurrent=work/'concurrent';concurrent.write_bytes(b'preserve')
        try:pack.exclusive_copy(candidate,concurrent)
        except FileExistsError:
            if concurrent.read_bytes()!=b'preserve':raise AssertionError('Concurrent output changed')
            controls.append({'id':'concurrent-output-preserved','passed':True})
        else:raise AssertionError('Concurrent output overwritten')
        stage=work/'stage';stage.mkdir();relative='Room.cs';original=(pack.ROOT/key_source).read_bytes();(stage/relative).write_bytes(original)
        identities={relative:hashlib.sha256(original).hexdigest()};pack.verify_copies(stage,identities);(stage/relative).write_bytes(original+b'\n')
        try:pack.verify_copies(stage,identities)
        except ValueError as error:controls.append({'id':'source-stage-mutation','passed':True,'rejection':str(error)})
        else:raise AssertionError('Stage mutation not rejected')
    result={'passed':len(controls),'failed':0,'controls':controls,'scope':'Actual archive faults and copied-source mutation; no participant or platform generalization.'}
    archive.with_name('negative-results.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
if __name__=='__main__':
    if len(sys.argv)!=2:raise SystemExit('Usage: test_delivery.py ACTUAL_ARCHIVE')
    main(Path(sys.argv[1]))
