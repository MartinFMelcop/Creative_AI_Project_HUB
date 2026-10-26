#!/usr/bin/env python3
"""Bind assessment inputs and unchanged recipient bytes across actual execution."""
import argparse
import hashlib
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent

def snapshot():
    inputs={p for p in HERE.rglob('*') if p.is_file() and not {'bin','obj','__pycache__'} & set(p.parts)}
    for directory in ('delivery/authored-scene','delivery/authored-scene-windows','north-star/authored-scene/Host','north-star/csharp/Domain','north-star/csharp/Narrative','north-star/csharp/Crossing'):
        inputs.update(p for p in (ROOT/directory).rglob('*') if p.is_file() and not {'bin','obj','__pycache__'} & set(p.parts))
    inputs.add(ROOT.parents[1]/'.github/workflows/windows-access.yml')
    inputs.add(ROOT/'evidence/windows-access/protocol.json')
    inputs.add(ROOT/'evidence/windows-access/consumer-protocol.json')
    protocol=json.loads((ROOT/'evidence/windows-access/protocol.json').read_text(encoding='utf8'))
    baseline=protocol['baseline']
    archive=(ROOT/baseline['archive_path']).resolve()
    if not archive.is_relative_to(ROOT) or archive.is_symlink() or not archive.is_file():raise ValueError('Declared baseline archive unavailable')
    with archive.open('rb') as stream:identity=hashlib.file_digest(stream,'sha256').hexdigest()
    if identity!=baseline['archive_sha256'] or archive.stat().st_size!=baseline['archive_bytes']:raise ValueError('Recipient differs from predeclared baseline')
    identities={}
    for p in sorted(inputs):
        if p.is_symlink():raise ValueError('Linked assessment input')
        with p.open('rb') as f:h=hashlib.file_digest(f,'sha256').hexdigest()
        identities[p.relative_to(ROOT.parents[1]).as_posix()]=h
    return {'schema_version':1,'sha256':identities,'scope':'Exact source/artifact stability only; actual Windows access and child identity are separate observations.'}

if __name__=='__main__':
    a=argparse.ArgumentParser(description=__doc__);a.add_argument('output',type=Path);a.add_argument('--compare',type=Path);args=a.parse_args()
    j=snapshot()
    if args.compare and json.loads(args.compare.read_text(encoding='utf-8-sig'))!=j:raise SystemExit('Assessment source/artifact changed during execution')
    with args.output.open('x',encoding='utf8',newline='\n') as f:f.write(json.dumps(j,indent=2)+'\n')
    print('Bound',len(j['sha256']),'exact assessment inputs; no runtime claim')
