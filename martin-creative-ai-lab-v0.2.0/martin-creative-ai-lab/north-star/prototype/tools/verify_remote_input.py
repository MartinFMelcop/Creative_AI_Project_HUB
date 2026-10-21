#!/usr/bin/env python3
"""Exercise the remote window through XTest, an actual TCP server and snapshots.

Requires the pinned standard Godot and Xorg dummy/libX11/libXtst. Synthetic OS input,
not independent players, performance measurements or a shipped network game.
"""
import argparse
import ctypes as C
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import time

import verify_authority as authority
from verify_routes_input import X, T, window, x_error, x_errors

ROOT = authority.ROOT
PLAY = ROOT / 'authority/play.gd'


def require(value, message):
    if not value:raise ValueError(message)


def verify(output, godot='godot'):
    engine = shutil.which(godot);require(engine, 'Godot executable unavailable')
    output = Path(output).resolve()
    require(ROOT not in output.parents, 'Do not overwrite prototype inputs')
    require(not output.exists() or not any(output.iterdir()), 'Use an empty result directory')
    output.mkdir(parents=True, exist_ok=True)
    inputs = {name:authority.digest(ROOT/name) for name in ('authority/server.gd','authority/play.gd','authority/view.gd','authority/remote.gd','authority/intent.gd','dist/crossing-drill.pck')}
    previous_handler = X.XSetErrorHandler(C.cast(x_error,C.c_void_p));x_errors.clear()
    X.XWarpPointer.argtypes = [C.c_void_p,C.c_ulong,C.c_ulong,C.c_int,C.c_int,C.c_uint,C.c_uint,C.c_int,C.c_int]
    checks = [];observations = {}
    def check(value, label, context=None):
        require(value, label + (': ' + json.dumps(context) if context is not None and not value else ''));checks.append(label)
    with tempfile.TemporaryDirectory(prefix='remote-input-') as temporary:
        scratch = Path(temporary);env = authority.environment(scratch)
        version = subprocess.run([engine,'--version'],env=env,capture_output=True,text=True,timeout=10)
        require(version.returncode==0 and version.stdout.strip()==authority.VERSION,'Pinned standard Godot 4.6.3 required')
        display = next((n for n in range(280,300) if not Path(f'/tmp/.X11-unix/X{n}').exists() and not Path(f'/tmp/.X{n}-lock').exists()),None)
        require(display is not None,'No unused local display');env['DISPLAY']=f':{display}'
        display_process = game = d = None
        with (scratch/'display.log').open('w') as log:
            try:
                display_process = subprocess.Popen(['Xorg',env['DISPLAY'],'-config',str(ROOT/'tests/dummy-display.conf'),'-logfile',str(scratch/'Xorg.log'),'-noreset','-nolisten','tcp'],env=env,stdout=log,stderr=log)
                for _ in range(80):
                    d = X.XOpenDisplay(env['DISPLAY'].encode())
                    if d:break
                    require(display_process.poll() is None,'Owned Xorg stopped');time.sleep(.05)
                require(d,'Owned Xorg unavailable')
                for delivery, packed in (('source',False),('pack',True)):
                    capture = scratch/(delivery+'-frame');env['NORTH_STAR_REMOTE_CAPTURE']=str(capture)
                    with authority.server(engine,scratch/delivery,packed,seconds=9) as (port,report,process):
                        location = ['--main-pack',str(ROOT/'dist/crossing-drill.pck')] if packed else ['--path',str(ROOT)]
                        game_log = scratch/(delivery+'-window.log')
                        with game_log.open('w') as stream:
                            game = subprocess.Popen([engine,*location,'--script',str(PLAY),'--audio-driver','Dummy','--',str(port)],env=env,stdout=stream,stderr=stream)
                            deadline = time.monotonic()+20;target = None
                            for _ in range(150):
                                target = window(d)
                                if target:break
                                require(game.poll() is None,'Remote window stopped before discovery');time.sleep(.03)
                            require(target,'Remote window unavailable')
                            X.XSetInputFocus(d,target,1,0);X.XWarpPointer(d,0,target,0,0,0,0,790,390);X.XSync(d,0);time.sleep(.2)
                            def key(name,on=True):
                                require(time.monotonic()<deadline,'Owned input journey exceeded its bound')
                                code = X.XKeysymToKeycode(d,X.XStringToKeysym(name.encode()));require(code,'Missing XTest key')
                                T.XTestFakeKeyEvent(d,code,on,0);X.XSync(d,0)
                            def tap(name):key(name);time.sleep(.025);key(name,False);time.sleep(.035)
                            def shot(label, retain=False):
                                record = Path(str(capture)+'.json');prior = json.loads(record.read_text())['capture'] if record.exists() else 0
                                tap('F12')
                                for _ in range(80):
                                    if record.exists():
                                        try:
                                            value = json.loads(record.read_text())
                                            if value['capture']>prior:
                                                if retain:shutil.copyfile(str(capture)+'.png',output/(delivery+'-'+label+'.png'))
                                                return value
                                        except json.JSONDecodeError:pass
                                    require(game.poll() is None,'Remote window stopped before capture');time.sleep(.02)
                                raise ValueError('Window omitted capture acknowledgement')
                            tap('Return');initial = shot('initial')
                            ready_until = time.monotonic()+2
                            while initial['status']=='connecting' and time.monotonic()<ready_until:
                                time.sleep(.05);initial = shot('initial')
                            check(initial['status']=='live' and initial['confirmed']['role']=='Guardian',delivery+': actual Enter starts remote catalog session',initial)
                            key('d');time.sleep(.25);walking = shot('walking',True);key('d',False)
                            check(walking['confirmed']['player'][0]-initial['confirmed']['player'][0]>30,delivery+': OS movement changes authoritative position')
                            key('space');time.sleep(.7);stepped = shot('step');key('space',False)
                            check(stepped['confirmed']['counters']['dodges']==1 and stepped['confirmed']['energy']<100,delivery+': held step spends once in actual model')
                            key('k');time.sleep(.15);guarded = shot('guard')
                            check(guarded['confirmed']['guard'],delivery+': OS guard reaches server')
                            tap('Escape');time.sleep(.15);suspended = shot('suspended',True)
                            check(suspended['suspended'] and not suspended['confirmed']['guard'] and suspended['confirmed']['tick']>guarded['confirmed']['tick'],delivery+': suspension neutralizes while server time advances')
                            tap('Escape');time.sleep(.1);held = shot('held')
                            check(not held['suspended'] and held['quarantined'] and not held['confirmed']['guard'],delivery+': resume cannot rearm held guard')
                            key('k',False);time.sleep(.06);key('k');time.sleep(.15);rearmed = shot('rearmed')
                            check(rearmed['confirmed']['guard'],delivery+': release and fresh press rearm')
                            X.XSetInputFocus(d,X.XDefaultRootWindow(d),1,0);X.XSync(d,0);time.sleep(.2)
                            key('k',False)
                            X.XSetInputFocus(d,target,1,0);X.XSync(d,0);time.sleep(.15);unfocused = shot('focus')
                            check(unfocused['suspended'] and not unfocused['confirmed']['guard'] and unfocused['confirmed']['tick']>rearmed['confirmed']['tick'],delivery+': actual focus loss neutralizes without world pause',unfocused)
                            tap('Escape');time.sleep(.1);resumed = shot('focus-resumed')
                            check(not resumed['suspended'] and not resumed['quarantined'] and not resumed['confirmed']['guard'],delivery+': release outside focus permits neutral explicit resume')
                            key('d');time.sleep(.2);recovered = shot('focus-moved');key('d',False)
                            check(recovered['confirmed']['player'][0]>resumed['confirmed']['player'][0]+20,delivery+': fresh input works after outside-window release')
                            tap('Escape')
                            # Leave controls suspended until bounded server exit; no reconnect/local simulation.
                            process.wait(timeout=10);time.sleep(.2);closed = shot('closed',True);time.sleep(.15);frozen = shot('frozen')
                            check(closed['status']=='error' and closed['confirmed']==frozen['confirmed'] and closed['position']==frozen['position'],delivery+': disconnect freezes confirmed presentation')
                            observations[delivery] = {label:value for label,value in (('initial',initial),('walking',walking),('step',stepped),('suspended',suspended),('held',held),('rearmed',rearmed),('focus',unfocused),('focus_resumed',resumed),('focus_moved',recovered),('closed',closed))}
                            tap('q');game.wait(timeout=3);check(game.returncode==0,delivery+': explicit close exits cleanly');game=None
                        native = game_log.read_text();require(not any(term in native for term in ('SCRIPT ERROR:','Parse Error:','ERROR:')),'Native window error: '+native[-2500:])
                    authority.check_report(json.loads(report.read_text()))
            finally:
                if d:X.XCloseDisplay(d)
                X.XSetErrorHandler(previous_handler)
                for owned in (game,display_process):
                    if owned and owned.poll() is None:
                        owned.terminate()
                        try:owned.wait(timeout=3)
                        except subprocess.TimeoutExpired:owned.kill();owned.wait()
    require(not x_errors,'Unexpected X11 errors: '+str(x_errors))
    require(inputs=={name:authority.digest(ROOT/name) for name in inputs},'Remote inputs changed during execution')
    result = {'schema_version':1,'kind':'synthetic_os_input','runtime':authority.VERSION,'identities':inputs,
              'checks':{'passed':len(checks),'failed':0},'controls':checks,'observations':observations,
              'scope':'Actual source/PCK remote window, XTest keyboard/focus, TCP authority, costs and fail-closed presentation. No independent human, latency benchmark or complete network player journey claim.'}
    (output/'keyboard.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(f'PASS: {len(checks)} source/PCK remote-window OS controls')
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True);parser.add_argument('--godot',default='godot');args=parser.parse_args()
    try:verify(args.output,args.godot)
    except (OSError,ValueError,KeyError,subprocess.SubprocessError) as error:parser.exit(1,f'FAIL: {error}\n')
