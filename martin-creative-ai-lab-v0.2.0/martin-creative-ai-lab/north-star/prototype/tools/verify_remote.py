#!/usr/bin/env python3
"""Verify the actual interactive remote consumer using native events and real TCP.

Contract comparison binds code/controls, not nondeterministic packet timing. OS-level
input and image inspection are separate: see verify_remote_input.py.
"""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import tempfile

import verify_authority as a

SCRIPTS = ('authority/server.gd','authority/remote.gd','authority/intent.gd','authority/intent_checks.gd',
           'authority/view.gd','authority/play.gd','tests/remote_checks.gd','tests/remote_visual_checks.gd','tests/remote_journey.gd',
           'tools/verify_remote.py','tools/verify_remote_input.py')


def identities():
    return {name:a.digest(a.ROOT/name) for name in (*SCRIPTS,*a.CONSUMERS,'dist/crossing-drill.pck')}


def invoke(engine, script, folder, packed=False, args=(), timeout=10):
    location = ['--main-pack',str(a.ROOT/'dist/crossing-drill.pck')] if packed else ['--path',str(a.ROOT)]
    result = subprocess.run([engine,'--headless',*location,'--script',str(a.ROOT/script),'--',*map(str,args)],
                            env=a.environment(folder),capture_output=True,text=True,timeout=timeout)
    log = result.stdout+result.stderr
    a.require(result.returncode==0 and not any(s in log for s in ('SCRIPT ERROR:','Parse Error:','ERROR:')),'Remote native consumer failed: '+log[-2500:])
    return result.stdout


def verify(output, godot='godot', compare=None):
    output = Path(output).resolve();a.require(a.ROOT not in output.parents,'Do not overwrite prototype inputs')
    engine = shutil.which(godot);a.require(engine,'Godot executable unavailable')
    before = identities();observations = {}
    with tempfile.TemporaryDirectory(prefix='north-star-remote-') as temporary:
        scratch = Path(temporary)
        version = subprocess.run([engine,'--version'],env=a.environment(scratch),capture_output=True,text=True,timeout=10)
        a.require(version.returncode==0 and version.stdout.strip()==a.VERSION,'Pinned standard Godot 4.6.3 required')
        for delivery, packed in (('source',False),('pack',True)):
            native = {}
            for script,key in (('authority/intent_checks.gd','intent'),('tests/remote_checks.gd','transport'),('tests/remote_visual_checks.gd','visual')):
                text = invoke(engine,script,scratch/delivery,packed)
                lines = [line[line.index('{'):] for line in text.splitlines() if '{' in line]
                a.require(lines,'Native controls omitted their result');observed = json.loads(lines[-1])
                a.require(observed['failed']==0 and observed['passed']>0,'Remote native controls failed');native[key] = observed
            journeys = []
            for role in ('Guardian','Duelist'):
                folder = scratch/delivery/role
                with a.server(engine,folder,packed,seconds=65) as (port,report,process):
                    client_report = folder/'client.json'
                    invoke(engine,'tests/remote_journey.gd',folder/'client',packed,(port,role,client_report),timeout=66)
                client = json.loads(client_report.read_text());server = json.loads(report.read_text());a.check_report(server)
                state = client['observation']['confirmed']
                a.require(client['success'] and client['input_events']>0 and client['authority_closed'] and client['observation']['status']=='terminal','Remote input consumer did not retain an actual terminal')
                a.require(state['mode']==server['model']['mode']=='won' and state['role']==server['model']['role']==role and state['tick']==server['model']['tick'] and state['hp']>0 and state['cargo']>0 and server['model']['courier_x']>=1000,'Interactive consumer did not confirm a living remote goal')
                journeys.append({'role':role,'hp':state['hp'],'cargo':state['cargo'],'model_ticks':state['tick'],
                                 'counters':state['counters'],'input_events':client['input_events'],'snapshots':client['snapshots'],
                                 'terminal_retained_after_authority_close':True})
            observations[delivery] = {'native':native,'journeys':journeys}
    a.require(before==identities(),'Remote consumer inputs changed during execution')
    contract = {'schema_version':1,'runtime':a.VERSION,'identities':before,'native_controls':{key:value['passed'] for key,value in native.items()},
                'living_remote_journeys_per_delivery':2,'terminal_after_socket_close':True,
                'scope':'Separate developer window and fixed keyboard/mouse input. Snapshot interpolation only, no local Combat or prediction. Source/PCK real authority and synthetic native events. No shipped multiplayer, authentication, WAN, persistence, player, latency or capacity claim.'}
    if compare:a.require(json.loads(Path(compare).read_text())['contract']==contract,'Remote consumer contract/source comparison changed')
    result = {'contract':contract,'observations':observations,'observation_limits':'Packet schedules, model completion times and event counts vary. Comparison binds identities and protected behavior, not exact raw observation equality. Synthetic input is not independent human evidence.'}
    output.parent.mkdir(parents=True,exist_ok=True);output.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print('PASS: native intent/transport controls and four interactive remote living wins with retained terminal state')
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True);parser.add_argument('--godot',default='godot');parser.add_argument('--compare',type=Path);args=parser.parse_args()
    try:verify(args.output,args.godot,args.compare)
    except (OSError,ValueError,KeyError,TypeError,subprocess.SubprocessError) as error:parser.exit(1,f'FAIL: {error}\n')
