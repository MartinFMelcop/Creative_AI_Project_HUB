#!/usr/bin/env python3
"""Drive the source-only ability bench through actual XTest keyboard/focus events."""
import argparse
import ctypes as C
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import time

import abilities
from verify_remote_input import wait_window, require
from verify_routes_input import X,T,x_error,x_errors,window
ROOT=abilities.ROOT

def verify(output,godot='godot'):
    output=Path(output).resolve()
    require(ROOT not in output.parents and output!=ROOT,'Keep outputs outside consumer inputs')
    require(not output.exists() or not any(output.iterdir()),'Use an empty output directory')
    output.mkdir(parents=True,exist_ok=True)
    engine=shutil.which(godot);require(engine,'Godot executable unavailable')
    inputs=abilities.identities()
    extra=('abilities/catalog.json','abilities/view.gd','abilities/play.gd','tools/verify_ability_input.py')
    inputs.update({name:abilities.hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in extra})
    checks=[];records={}
    def check(value,label):require(value,label+(': '+json.dumps(list(records.values())[-1]) if not value and records else ''));checks.append(label)
    previous=X.XSetErrorHandler(C.cast(x_error,C.c_void_p));x_errors.clear()
    X.XWarpPointer.argtypes=[C.c_void_p,C.c_ulong,C.c_ulong,C.c_int,C.c_int,C.c_uint,C.c_uint,C.c_int,C.c_int]
    with tempfile.TemporaryDirectory(prefix='ability-window-') as folder:
        scratch=Path(folder);env=os.environ.copy()
        env.update({key:str(scratch/key) for key in ('XDG_DATA_HOME','XDG_CONFIG_HOME','XDG_CACHE_HOME')})
        version=subprocess.run([engine,'--version'],capture_output=True,text=True,timeout=10,env=env)
        require(version.returncode==0 and version.stdout.strip()==abilities.VERSION,'Pinned Godot 4.6.3 required')
        display=next((n for n in range(300,320) if not Path(f'/tmp/.X11-unix/X{n}').exists() and not Path(f'/tmp/.X{n}-lock').exists()),None)
        require(display is not None,'No unused local display');env['DISPLAY']=f':{display}'
        capture=scratch/'capture';env['NORTH_STAR_ABILITY_CAPTURE']=str(capture)
        server=game=d=None
        with (scratch/'engine.log').open('w') as log:
            try:
                server=subprocess.Popen(['Xorg',env['DISPLAY'],'-config',str(ROOT/'tests/dummy-display.conf'),'-logfile',str(scratch/'Xorg.log'),'-noreset','-nolisten','tcp'],env=env,stdout=log,stderr=log)
                for _ in range(80):
                    d=X.XOpenDisplay(env['DISPLAY'].encode())
                    if d:break
                    require(server.poll() is None,'Owned Xorg stopped');time.sleep(.05)
                require(d,'Owned Xorg unavailable')
                game=subprocess.Popen([engine,'--path',str(ROOT),'--script','abilities/play.gd','--audio-driver','Dummy'],env=env,stdout=log,stderr=log)
                target=wait_window(d,game,scratch/'engine.log')
                X.XSetInputFocus(d,target,1,0);X.XWarpPointer(d,0,target,0,0,0,0,790,390);X.XSync(d,0)
                deadline=time.monotonic()+45
                def key(name,on=True):
                    require(time.monotonic()<deadline,'Owned journey exceeded bound')
                    code=X.XKeysymToKeycode(d,X.XStringToKeysym(name.encode()));require(code,'Missing key')
                    T.XTestFakeKeyEvent(d,code,on,0);X.XSync(d,0)
                def tap(name):key(name);time.sleep(.025);key(name,False);time.sleep(.035)
                def shot(label,retain=False):
                    record=Path(str(capture)+'.json');prior=json.loads(record.read_text())['capture'] if record.exists() else 0
                    tap('F12');until=time.monotonic()+10;retry_at=time.monotonic()+.3
                    while time.monotonic()<until:
                        if record.exists():
                            try:
                                value=json.loads(record.read_text())
                                if value['capture']>prior:
                                    records[label]=value
                                    if retain:shutil.copyfile(str(capture)+'.png',output/(label+'.png'))
                                    return value
                            except json.JSONDecodeError:pass
                        require(game.poll() is None,'Window stopped before capture')
                        if label=='baseline' and time.monotonic()>=retry_at:
                            current=window(d)
                            if current:X.XSetInputFocus(d,current,1,0);X.XSync(d,0)
                            tap('F12');retry_at=time.monotonic()+.3
                        time.sleep(.02)
                    raise ValueError('Missing rendered input acknowledgement')
                initial=shot('baseline');check(initial['selected']=='none' and initial['combat']['tick']==0,'read-only initial preparation')
                tap('Tab');snap=shot('snap');check(snap['selected']=='snap' and snap['combat']['tick']==0,'select actual snap profile before entry')
                tap('Tab');reach=shot('preparation',True);check(reach['selected']=='reach' and reach['starts']==0,'select actual reach profile without spending')
                tap('Return');live=shot('live');check(live['combat']['mode']=='play','explicit Enter starts real crossing')
                tap('Tab');locked=shot('locked');check(locked['selected']=='reach','active selection is locked')
                key('e');time.sleep(.05);committed=shot('committed',True)
                check(committed['status']=='COMMITTED' and committed['starts']==1,'E starts paid committed travel')
                check(committed['combat']['energy']==70,'actual single upfront 30 resolve cost')
                time.sleep(.8);arrived=shot('arrived',True);key('e',False)
                check(arrived['starts']==1,'held E and key repeats cannot retrigger')
                check(abs(arrived['player'][0]-live['player'][0]-240)<1,'actual window travels the selected 240px')
                check(arrived['combat']['counters']['dodges']==0 and arrived['combat']['counters']['counters']==0,'rush is neither existing step nor free counter')
                time.sleep(.6);key('k');time.sleep(.1);guarded=shot('guarded');check(guarded['combat']['energy']<100,'guard spends actual energy')
                tap('e');refused=shot('refused');key('k',False)
                check(refused['starts']==1 and refused['refusals']>=1,'held guard blocks a new rush')
                X.XSetInputFocus(d,X.XDefaultRootWindow(d),1,0);X.XSync(d,0);time.sleep(.1)
                X.XSetInputFocus(d,target,1,0);X.XSync(d,0);paused=shot('paused',True);time.sleep(.15);still=shot('still')
                check(paused['paused'] and still['combat']['tick']==paused['combat']['tick'],'local focus loss pauses and freezes model')
                tap('Escape');resumed=shot('resumed');check(not resumed['paused'] and resumed['combat']['tick']>still['combat']['tick'],'explicit resume advances model')
                key('w');time.sleep(.18);moved=shot('moved');key('w',False)
                check(moved['player'][1]<resumed['player'][1]-20,'fresh movement works after focus recovery')
                tap('q');game.wait(timeout=3);check(game.returncode==0,'explicit close exits cleanly');game=None
            finally:
                log.flush()
                (output/'native.log').write_text((scratch/'engine.log').read_text()[-65536:])
                (output/'partial.json').write_text(json.dumps(records,indent=2,sort_keys=True)+'\n')
                if d:X.XCloseDisplay(d)
                X.XSetErrorHandler(previous)
                for child in (game,server):
                    if child and child.poll() is None:
                        child.terminate()
                        try:child.wait(timeout=3)
                        except subprocess.TimeoutExpired:child.kill();child.wait()
        native=(scratch/'engine.log').read_text()
        require(not any(term in native for term in ('SCRIPT ERROR:','Parse Error:','ERROR:')),'Native error: '+native[-3000:])
    require(not x_errors,'Unexpected X11 errors')
    require(inputs=={name:abilities.hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in inputs},'Inputs changed during execution')
    result={'schema_version':1,'kind':'synthetic_os_input','runtime':abilities.VERSION,'identities':inputs,'checks':{'passed':len(checks),'failed':0},'controls':checks,'observations':records,'scope':'Actual source-only window, synthetic keyboard/focus and model consequences. No physical device, human reception or shipping claim.'}
    (output/'keyboard.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(f'PASS: {len(checks)} ability-window OS controls');return result

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True);parser.add_argument('--godot',default='godot');args=parser.parse_args()
    try:verify(args.output,args.godot)
    except (OSError,ValueError,subprocess.SubprocessError) as error:parser.exit(1,f'FAIL: {error}\n')
