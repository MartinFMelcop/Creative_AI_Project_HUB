#!/usr/bin/env python3
"""Measure controlled transport interventions on the actual remote input consumer.

Loss is retained as an observation. This evaluates one scripted policy, not humans,
RTT tolerance, engine ranking, WAN behavior or population-level class balance.
"""
import argparse
from contextlib import nullcontext
import json
from pathlib import Path
import shutil
import subprocess
import tempfile

import verify_authority as a
from impairment import Relay, PROFILES

PROTOCOL = {'schema_version':1,'profiles':['direct','relay_zero','delay_60','batch_400'],
            'roles':['Guardian','Duelist'],'repetitions':2}
FILES = ('tools/impairment.py','tools/evaluate_transport.py','tools/verify_authority.py','tools/export_linux.py','tests/transport_probe.gd',
         'tests/remote_journey.gd','authority/server.gd','authority/remote.gd','authority/intent.gd',
         'authority/view.gd','combat.gd','route.gd','fittings.gd','data/fittings.json','project.godot')


def identities():return {name:a.digest(a.ROOT/name) for name in FILES}


def case(engine, folder, role, profile, packed=False):
    with a.server(engine,folder,packed,seconds=65) as (port,report,process):
        with (nullcontext(None) if profile=='direct' else Relay(port,profile,lifetime=70)) as relay:
            client_report = folder/'client.json'
            location = ['--main-pack',str(a.ROOT/'dist/crossing-drill.pck')] if packed else ['--path',str(a.ROOT)]
            result = subprocess.run([engine,'--headless',*location,'--script',str(a.ROOT/'tests/transport_probe.gd'),'--',
                                     str(port if relay is None else relay.port),role,str(client_report)],
                                    env=a.environment(folder/'client'),capture_output=True,text=True,timeout=68)
            text = result.stdout+result.stderr
            a.require(result.returncode in (0,1) and not any(s in text for s in ('SCRIPT ERROR:','Parse Error:','ERROR:')),'Native study error: '+text[-2500:])
            a.require(client_report.is_file(),'Study consumer omitted actual observation')
        transport = None if relay is None else relay.stats
    client = json.loads(client_report.read_text());server = json.loads(report.read_text());a.check_report(server)
    state = client['observation']['confirmed'];observation = client['transport_observation']
    a.require(state.get('mode') in ('won','lost') and state['mode']==server['model']['mode'] and state['tick']==server['model']['tick'],
              'Study did not observe a matching actual terminal')
    a.require(client['authority_closed'] and client['observation']['status']=='terminal','Study lost terminal retention')
    a.require(state['role']==role and (result.returncode==0)==client['success']==(state['mode']=='won'),'Study outcome/exit disagreement')
    if transport:
        a.require(transport['closed'] and transport['connected'],'Relay did not complete owned connection')
        for direction in transport['directions'].values():
            a.require(direction['frames_received']==direction['frames_forwarded'] and direction['bytes_received']==direction['bytes_forwarded'],'Relay lost/duplicated complete stream bytes')
        if profile=='delay_60':
            a.require(all(d['min_residence_ms'] is not None and d['min_residence_ms']>=59.9 for d in transport['directions'].values()),'Configured delay was not actually applied')
        if profile=='batch_400':a.require(transport['directions']['down']['max_frames_per_send_turn']>=2,'Batch intervention did not group actual frames')
    return {'role':role,'profile':profile,'mode':state['mode'],'hp':state['hp'],'cargo':state['cargo'],'model_ticks':state['tick'],
            'counters':state['counters'],'input_events':client['input_events'],'client_observation':observation,
            'authority':{key:server[key] for key in ('accepted','rejected','stale_clears','active_ticks')},'relay':transport,
            'terminal_retained':True}


def evaluate(output, godot='godot', repetitions=2, profiles=None, packed=False):
    output=Path(output).resolve();a.require(a.ROOT not in output.parents,'Do not overwrite prototype inputs')
    engine=shutil.which(godot);a.require(engine,'Godot executable unavailable')
    a.require(type(repetitions) is int and 1<=repetitions<=3,'Repetitions must be 1..3')
    profiles=list(PROTOCOL['profiles'] if profiles is None else profiles)
    a.require(profiles and len(profiles)==len(set(profiles)) and all(p in PROTOCOL['profiles'] for p in profiles),'Unsupported/duplicate profiles')
    before=identities();observed=[]
    with tempfile.TemporaryDirectory(prefix='north-star-transport-') as temporary:
        scratch=Path(temporary)
        version=subprocess.run([engine,'--version'],env=a.environment(scratch),capture_output=True,text=True,timeout=10)
        a.require(version.returncode==0 and version.stdout.strip()==a.VERSION,'Pinned standard Godot 4.6.3 required')
        for repetition in range(repetitions):
            # Reverse blocked profile order on alternating takes; retain exact order.
            order=profiles if repetition%2==0 else list(reversed(profiles))
            for role in PROTOCOL['roles']:
                for profile in order:
                    data=case(engine,scratch/f'{repetition}-{role}-{profile}',role,profile,packed)
                    data['repetition']=repetition+1;observed.append(data)
                    print(f"{len(observed)}: {role} {profile} take{repetition+1}: {data['mode']} HP{data['hp']} cargo{data['cargo']}",flush=True)
    a.require(before==identities(),'Study inputs changed during execution')
    grouped=[]
    for role in PROTOCOL['roles']:
        for profile in profiles:
            rows=[r for r in observed if r['role']==role and r['profile']==profile]
            grouped.append({'role':role,'profile':profile,'takes':len(rows),'wins':sum(r['mode']=='won' for r in rows),
                            'losses':sum(r['mode']=='lost' for r in rows),'hp':[r['hp'] for r in rows],'cargo':[r['cargo'] for r in rows],
                            'stale_clears':[r['authority']['stale_clears'] for r in rows],
                            'max_observed_tick_gaps':[r['client_observation']['max_observed_tick_gap'] for r in rows]})
    baselines=[r for r in observed if r['profile'] in ('direct','relay_zero')]
    calibration={'baseline_takes':len(baselines),'all_baseline_living_wins':bool(baselines) and all(r['mode']=='won' and r['hp']>0 and r['cargo']>0 for r in baselines),
                 'limits':'A failed/missing baseline makes comparative interpretation inconclusive; retain it. No equivalence or human inference follows from wins alone.'}
    result={'schema_version':1,'runtime':a.VERSION,'delivery':'pack' if packed else 'source','identities':before,
            'pack_sha256':a.digest(a.ROOT/'dist/crossing-drill.pck') if packed else None,
            'protocol':{'schema_version':1,'profiles':profiles,'roles':PROTOCOL['roles'],'repetitions':repetitions,
                        'interventions':PROFILES,'order':'Role-blocked, profile order reversed on alternating repetitions; no randomized assignment.'},
            'checks':{'terminal_and_stream_contracts_passed':len(observed),'execution_errors':0},'calibration':calibration,'summary':grouped,'observations':observed,
            'limits':'Synthetic fixed native-input policy, real loopback TCP and unchanged gameplay. Complete-frame scheduling is not TCP loss/reordering, WAN emulation, RTT, player latency tolerance, capacity, balance or production engine evidence. Repetitions measure this instrument under observed host scheduling, not independent participants. Outcomes and timing are observations, not golden equality gates.'}
    output.parent.mkdir(parents=True,exist_ok=True);output.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(f'PASS: {len(observed)} actual intervention takes retained, including losses')
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True);parser.add_argument('--godot',default='godot')
    parser.add_argument('--repetitions',type=int,default=2);parser.add_argument('--profiles',nargs='+',choices=PROTOCOL['profiles']);parser.add_argument('--packed',action='store_true');args=parser.parse_args()
    try:evaluate(args.output,args.godot,args.repetitions,args.profiles,args.packed)
    except (OSError,ValueError,KeyError,TypeError,subprocess.SubprocessError) as error:parser.exit(1,f'FAIL: {error}\n')
