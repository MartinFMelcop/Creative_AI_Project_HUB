#!/usr/bin/env python3
"""Check a real transport study for independent neutral-heartbeat lease continuity.

Gameplay losses remain valid. This checks the server lease and actual stale exposure,
not a win target, human tolerance or a relaxation of the stale-action gate.
"""
import argparse
import json
from pathlib import Path
import evaluate_transport as study


def check_rows(observations):
    rows=[row for row in observations if row['profile']=='batch_400']
    study.a.require(rows and {row['role'] for row in rows}=={'Guardian','Duelist'},'Both roles must experience the grouped-delivery condition')
    for row in rows:
        study.a.require(row['client_observation']['frame_visits'].get('stale',0)>0,'No observed stale interval; heartbeat recovery was not exercised')
        # Server counts include the terminal grace, during which input stops.
        study.a.require(0<=row['authority']['stale_clears']<=1,'Repeated server lease expiry under grouped delivery')
        study.a.require(row['terminal_retained'],'Terminal retention failed')
    return len(rows)


def check(path):
    data=json.loads(Path(path).read_text())
    study.a.require(data['schema_version']==1 and data['runtime']==study.a.VERSION,'Unsupported study/runtime')
    study.a.require(data['identities']==study.identities(),'Heartbeat study source identity changed')
    study.a.require(data['checks']['execution_errors']==0 and data['checks']['terminal_and_stream_contracts_passed']==len(data['observations']),'Study did not complete its execution/stream checks')
    protocol=data['protocol'];repetitions=protocol['repetitions']
    study.a.require(type(repetitions) is int and 1<=repetitions<=3,'Invalid study repetitions')
    expected={(role,profile,take) for role in ['Guardian','Duelist'] for profile in protocol['profiles'] for take in range(1,repetitions+1)}
    actual=[(row['role'],row['profile'],row['repetition']) for row in data['observations']]
    study.a.require(len(actual)==len(expected) and set(actual)==expected,'Study omitted or duplicated a requested take')
    if data['delivery']=='pack':study.a.require(data['pack_sha256']==study.a.digest(study.a.ROOT/'dist/crossing-drill.pck'),'Heartbeat PCK identity changed')
    else:study.a.require(data['delivery']=='source','Unknown study delivery')
    count=check_rows(data['observations'])
    print(f'PASS: {count} grouped-delivery takes retain a bounded neutral lease through actual stale intervals')
    return count


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('input',type=Path);args=parser.parse_args()
    try:check(args.input)
    except (OSError,ValueError,KeyError,TypeError) as error:parser.exit(1,f'FAIL: {error}\n')
