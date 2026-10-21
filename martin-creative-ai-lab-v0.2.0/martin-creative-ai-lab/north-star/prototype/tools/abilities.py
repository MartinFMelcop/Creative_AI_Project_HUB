#!/usr/bin/env python3
"""Check a candidate rush catalog through the source-only native ability bench.

No live replacement, generated code, release rebuild, or balance approval.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

ROOT=Path(__file__).resolve().parents[1]
VERSION='4.6.3.stable.official.7d41c59c4'
INPUTS=('combat.gd','route.gd','fittings.gd','data/fittings.json','tests/policy.gd',
        'project.godot','abilities/catalog.gd','abilities/model.gd','abilities/probe.gd',
        'tools/abilities.py')

def identities():
    return {name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in INPUTS}

def check(catalog,output,godot='godot'):
    catalog=Path(catalog).resolve();output=Path(output).resolve()
    if output==ROOT or ROOT in output.parents or output==catalog:
        raise ValueError('Keep results outside prototype inputs and candidate data')
    engine=shutil.which(godot)
    if not engine:raise ValueError('Godot executable unavailable')
    before=identities();candidate=hashlib.sha256(catalog.read_bytes()).hexdigest()
    with tempfile.TemporaryDirectory(prefix='ability-candidate-') as folder:
        scratch=Path(folder);env=os.environ.copy()
        env.update({key:str(scratch/key) for key in ('XDG_DATA_HOME','XDG_CONFIG_HOME','XDG_CACHE_HOME')})
        version=subprocess.run([engine,'--version'],capture_output=True,text=True,timeout=10,env=env)
        if version.returncode or version.stdout.strip()!=VERSION:raise ValueError('Pinned Godot 4.6.3 required')
        report=scratch/'report.json'
        result=subprocess.run([engine,'--headless','--path',str(ROOT),'--script','abilities/probe.gd','--',str(catalog),str(report)],env=env,capture_output=True,text=True,timeout=15)
        if result.returncode not in (0,2) or not report.exists() or any(term in result.stdout+result.stderr for term in ('SCRIPT ERROR:','Parse Error:','ERROR:')):
            raise ValueError('Native candidate execution failed: '+(result.stdout+result.stderr)[-3000:])
        data=json.loads(report.read_text())
        if not isinstance(data.get('valid'),bool) or result.returncode!=(0 if data['valid'] else 2):raise ValueError('Invalid native verdict')
        if identities()!=before or hashlib.sha256(catalog.read_bytes()).hexdigest()!=candidate:raise ValueError('Inputs changed during execution')
        data.update(runtime=VERSION,identities=before,candidate_sha256=candidate,
                    scope='Actual source-only rush model and fixed-policy journeys. No independent player, balance, complete talent system or shipped ability claim.')
        output.parent.mkdir(parents=True,exist_ok=True)
        output.write_text(json.dumps(data,indent=2,sort_keys=True)+'\n')
        print(('PASS: candidate executed' if data['valid'] else 'REJECTED: '+data['error']))
        return 0 if data['valid'] else 2

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--catalog',type=Path,default=ROOT/'abilities/catalog.json')
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--godot',default='godot');args=parser.parse_args()
    try:raise SystemExit(check(args.catalog,args.output,args.godot))
    except (OSError,ValueError,subprocess.SubprocessError) as error:parser.exit(1,f'FAIL: {error}\n')
