#!/usr/bin/env python3
"""Execute all offered preparation tuples against actual source/PCK authority."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import time
import verify_authority as a

FILES=('authority/server.gd','authority/remote.gd','authority/view.gd','tests/preparation_checks.gd','tools/verify_preparation.py','tools/verify_authority.py',*a.CONSUMERS,'dist/crossing-drill.pck')
def identities():return {n:a.digest(a.ROOT/n) for n in FILES}
def verify(output,godot='godot',compare=None):
    output=Path(output).resolve();a.require(a.ROOT not in output.parents,'Do not overwrite prototype inputs')
    engine=shutil.which(godot);a.require(engine,'Godot executable unavailable')
    before=identities();observations={};controls=[]
    with tempfile.TemporaryDirectory(prefix='preparation-') as folder:
        root=Path(folder)
        version=subprocess.run([engine,'--version'],capture_output=True,text=True,timeout=10)
        a.require(version.returncode==0 and version.stdout.strip()==a.VERSION,'Pinned Godot required')
        for delivery,packed in [('source',False),('pack',True)]:
            def check(value,label):a.require(value,delivery+': '+label);controls.append(delivery+': '+label)
            with a.server(engine,root/delivery/'inspect',packed,seconds=2) as (port,report,process):
                peer=a.Peer(port)
                try:
                    peer.send({'v':1,'kind':'catalog','hp':999});check(peer.receive(lambda m:m.get('kind')=='reject')['reason']=='schema','forged catalog request rejected')
                    peer.send({'v':1,'kind':'catalog'});catalog=peer.receive(lambda m:m.get('kind')=='catalog')
                    peer.send({'v':1,'kind':'catalog'});check(peer.receive(lambda m:m.get('kind')=='reject')['reason']=='catalog_already_sent','duplicate catalog cannot amplify replies')
                    peer.send(a.intent('unstarted',0));check(peer.receive(lambda m:m.get('kind')=='reject')['reason']=='session','inspection cannot admit an input')
                finally:peer.close()
            data=json.loads(report.read_text());a.check_report(data)
            check(data['model']['mode']=='title' and data['model']['tick']==0,'inspection leaves model unstarted')
            rows=[]
            for item in catalog['outfits']:
                for role,techniques in catalog['techniques'].items():
                    for technique in techniques:
                        with a.server(engine,root/delivery/(item['id']+'-'+role+'-'+technique['id']),packed,seconds=2) as (port,report,process):
                            peer=a.Peer(port)
                            try:
                                peer.send({'v':1,'kind':'catalog'});offered=peer.receive(lambda m:m.get('kind')=='catalog')
                                check(offered==catalog,'preparation catalog stable for '+item['id']+'/'+role+'/'+technique['id'])
                                hello={'v':1,'kind':'hello','role':role,'style':technique['id'],'outfit':item['id']}
                                peer.send({**hello,'health':999});check(peer.receive(lambda m:m.get('kind')=='reject')['reason']=='schema','client cannot assign prepared health')
                                peer.send(hello);welcome=peer.receive(lambda m:m.get('kind')=='welcome');state=peer.state()
                                expected={'role':role,'style':technique['id'],'outfit':item['id'],**{k:item[k] for k in ('health','movement','recovery')}}
                                check(state['state']['preparation']==expected and state['state']['hp']==item['health'],'actual tuple agrees with preview')
                                peer.send(a.intent(welcome['session'],0));peer.state(lambda m:m['ack']==0)
                                peer.send(a.intent(welcome['session'],1,step=True,move=[1000,0]));paid=peer.state(lambda m:m['ack']==1)
                                check(paid['state']['counters']['dodges']==1 and paid['state']['energy']<100,'prepared tuple executes actual paid action')
                                peer.send({'v':1,'kind':'catalog'});check(peer.receive(lambda m:m.get('kind')=='reject')['reason']=='already_started','catalog cannot reopen a started session')
                                peer.send({**hello,'outfit':'standard'});check(peer.receive(lambda m:m.get('kind')=='reject')['reason']=='already_started','preparation cannot be changed after entry')
                                seq=2
                                for _ in range(6):
                                    time.sleep(.08);peer.send(a.intent(welcome['session'],seq,guard=True));peer.state(lambda m:m['ack']==seq);seq+=1
                                guarded=peer.state()
                                expected_guard='DOWN' if role=='Duelist' else ('STALE' if technique['id']=='Riposte' else 'LIVE')
                                check(guarded['state']['guard_state']==expected_guard,'actual technique retains its guard consequence')
                            finally:peer.close()
                        a.check_report(json.loads(report.read_text()))
                        rows.append({'preparation':expected,'paid_step':True,'held_guard_state':expected_guard,'entry_locked':True})
            check(len(rows)==12,'all offered tuples executed')
            observations[delivery]=rows
    a.require(before==identities(),'Preparation inputs changed during execution')
    contract={'schema_version':1,'runtime':a.VERSION,'identities':before,'tuples_per_delivery':12,'passed_controls':len(controls),'scope':'Existing experiment choices, server-owned preparation and paid actions. No new class, ability, canon, shipped network player or player validation.'}
    if compare:a.require(json.loads(Path(compare).read_text())['contract']==contract,'Preparation source/contract comparison changed')
    result={'contract':contract,'controls':controls,'observations':observations}
    output.parent.mkdir(parents=True,exist_ok=True);output.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(f'PASS: {len(controls)} actual preparation controls; 12 tuples per source/PCK delivery')
    return result
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);p.add_argument('--godot',default='godot');p.add_argument('--compare',type=Path);args=p.parse_args()
    try:verify(args.output,args.godot,args.compare)
    except (OSError,ValueError,KeyError,TypeError,subprocess.SubprocessError) as error:p.exit(1,f'FAIL: {error}\n')
