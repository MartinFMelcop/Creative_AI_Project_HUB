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
import socket
import subprocess
import tempfile
import time

import verify_authority as authority
from verify_routes_input import X, T, window, x_error, x_errors

ROOT = authority.ROOT
PLAY = ROOT / 'authority/play.gd'


def require(value, message):
    if not value:raise ValueError(message)


def wait_window(display, process, log_path, timeout=15):
    deadline = time.monotonic()+timeout
    while time.monotonic()<deadline:
        require(process.poll() is None,'Remote window stopped before discovery: '+log_path.read_text()[-4000:])
        target = window(display)
        if target:return target
        time.sleep(.03)
    raise ValueError('Remote window unavailable after bounded startup: '+log_path.read_text()[-4000:])


def input_ready(snapshot):
    """Transport-live is earlier than neutral rearm; do not poll semantic costs/ranges."""
    rows = snapshot.get('actions', [])
    return (snapshot.get('status') == 'live' and bool(snapshot.get('confirmed'))
            and snapshot.get('focused') is True and snapshot.get('suspended') is False
            and snapshot.get('quarantined') is False and len(rows) == 3
            and not any(row.get('caption') in ('LAST CONFIRMED / INPUT BLOCKED',
                        'CONTROLS SUSPENDED', 'RELEASE TO REARM') for row in rows))


def wait_input_ready(capture, timeout=2):
    deadline = time.monotonic() + timeout
    latest = capture()
    while not input_ready(latest) and time.monotonic() < deadline:
        require(latest.get('status') not in ('error', 'closed', 'terminal'),
                'Remote failed before neutral input readiness: ' + json.dumps(latest))
        time.sleep(.03)
        latest = capture()
    require(input_ready(latest), 'Remote input not ready after bounded neutral rearm: ' + json.dumps(latest))
    return latest


def preserve_diagnostics(scratch, output):
    destination = output/'failure';destination.mkdir(exist_ok=True)
    # Known native/display logs only, bounded tails; never persist session traffic.
    for name in ('display.log','Xorg.log','source-window.log','pack-window.log','source/server.log','pack/server.log'):
        source = scratch/name
        if not source.is_file():continue
        with source.open('rb') as stream:
            stream.seek(max(0,source.stat().st_size-65536))
            (destination/name.replace('/','-')).write_bytes(stream.read(65536))


def verify(output, godot='godot'):
    engine = shutil.which(godot);require(engine, 'Godot executable unavailable')
    output = Path(output).resolve()
    require(ROOT not in output.parents, 'Do not overwrite prototype inputs')
    require(not output.exists() or not any(output.iterdir()), 'Use an empty result directory')
    output.mkdir(parents=True, exist_ok=True)
    inputs = {name:authority.digest(ROOT/name) for name in ('authority/server.gd','authority/play.gd','authority/view.gd','authority/remote.gd','authority/intent.gd','dist/crossing-drill.pck','tools/verify_remote_input.py','tools/verify_authority.py')}
    previous_handler = X.XSetErrorHandler(C.cast(x_error,C.c_void_p));x_errors.clear()
    X.XWarpPointer.argtypes = [C.c_void_p,C.c_ulong,C.c_ulong,C.c_int,C.c_int,C.c_uint,C.c_uint,C.c_int,C.c_int]
    checks = [];observations = {};startup = {}
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
                    with socket.socket() as reservation:
                        reservation.bind(('127.0.0.1',0));port = reservation.getsockname()[1]
                        location = ['--main-pack',str(ROOT/'dist/crossing-drill.pck')] if packed else ['--path',str(ROOT)]
                        game_log = scratch/(delivery+'-window.log')
                        started_at = time.monotonic()
                        with game_log.open('w') as stream:
                            game = subprocess.Popen([engine,*location,'--script',str(PLAY),'--audio-driver','Dummy','--',str(port)],env=env,stdout=stream,stderr=stream)
                            deadline = time.monotonic()+25
                            target = wait_window(d,game,game_log)
                            X.XSetInputFocus(d,target,1,0);X.XWarpPointer(d,0,target,0,0,0,0,790,390);X.XSync(d,0);time.sleep(.2)
                            def key(name,on=True):
                                require(time.monotonic()<deadline,'Owned input journey exceeded its bound')
                                code = X.XKeysymToKeycode(d,X.XStringToKeysym(name.encode()));require(code,'Missing XTest key')
                                T.XTestFakeKeyEvent(d,code,on,0);X.XSync(d,0)
                            def tap(name):key(name);time.sleep(.025);key(name,False);time.sleep(.035)
                            def shot(label, retain=False, timeout=3):
                                record = Path(str(capture)+'.json');prior = json.loads(record.read_text())['capture'] if record.exists() else 0
                                tap('F12')
                                capture_deadline = time.monotonic()+timeout
                                while time.monotonic()<capture_deadline:
                                    if record.exists():
                                        try:
                                            value = json.loads(record.read_text())
                                            if value['capture']>prior:
                                                if retain:shutil.copyfile(str(capture)+'.png',output/(delivery+'-'+label+'.png'))
                                                return value
                                        except json.JSONDecodeError:pass
                                    require(game.poll() is None,'Remote window stopped before capture');time.sleep(.02)
                                raise ValueError('Window omitted capture acknowledgement')
                        prepared = shot('prepared',timeout=10)
                        check(prepared['status']=='closed' and not prepared['confirmed'],delivery+': rendered input-ready window precedes authority startup')
                        startup[delivery] = {'rendered_input_ready_ms':round((time.monotonic()-started_at)*1000,3),'authority_started_after_preflight':True}
                        reservation.close()
                        with authority.server(engine,scratch/delivery,packed,seconds=9,port=port) as (port,report,process):
                            deadline = time.monotonic()+20
                            tap('Return');offered = shot('catalog')
                            catalog_until = time.monotonic()+2
                            while offered['status']=='connecting' and time.monotonic()<catalog_until:
                                time.sleep(.05);offered = shot('catalog')
                            check(offered['status']=='preparing' and not offered['confirmed'] and len(offered['catalog']['outfits'])==4,delivery+': server catalog precedes committed session',offered)
                            for expected in ['riveted','trail','field_sash','standard']:
                                tap('c');choice = shot('choice',expected=='riveted')
                                check(choice['preview']['id']==expected and choice['status']=='preparing' and not choice['confirmed'],delivery+': inspect actual outfit trade-off '+expected)
                            tap('Tab');technique = shot('technique')
                            check(technique['preview']['style']=='Riposte' and not technique['confirmed'],delivery+': inspect technique before commitment')
                            tap('Tab')
                            tap('Return');initial = wait_input_ready(lambda: shot('initial'))
                            check(initial['status']=='live' and initial['confirmed']['role']=='Guardian',delivery+': actual Enter starts remote catalog session',initial)
                            check(initial['actions'][1]['available'] and initial['actions'][1]['cost']==25 and not initial['actions'][2]['available'] and initial['actions'][2]['status']=='range',delivery+': actual window receives paid step and out-of-range counter advice',initial)
                            key('d');time.sleep(.25);walking = shot('walking',True);key('d',False)
                            check(walking['confirmed']['player'][0]-initial['confirmed']['player'][0]>30,delivery+': OS movement changes authoritative position')
                            key('space');time.sleep(.7);stepped = shot('step');key('space',False)
                            check(stepped['confirmed']['counters']['dodges']==1 and stepped['confirmed']['energy']<100,delivery+': held step spends once in actual model')
                            key('k');time.sleep(.15);guarded = shot('guard',True)
                            guard_until = time.monotonic()+1
                            while (guarded['confirmed']['guard_state']!='LIVE' or guarded['confirmed']['phase']=='pulse') and time.monotonic()<guard_until:
                                time.sleep(.03);guarded = shot('guard',True)
                            check(guarded['confirmed']['guard'],delivery+': OS guard reaches server')
                            check(guarded['actions'][0]['status']=='live' and guarded['actions'][0]['cost']==22 and guarded['actions'][0]['drain']==12 and not guarded['actions'][2]['available'],delivery+': authoritative guard advice retains drain/contact cost and blocks counter',guarded)
                            tap('Escape');time.sleep(.15);suspended = shot('suspended',True)
                            check(suspended['suspended'] and not suspended['confirmed']['guard'] and suspended['confirmed']['tick']>guarded['confirmed']['tick'],delivery+': suspension neutralizes while server time advances')
                            check(all(not row['available'] for row in suspended['actions']),delivery+': suspended window masks ready advice')
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
                            check(all(not row['available'] for row in closed['actions']),delivery+': disconnected window masks ready advice')
                            observations[delivery] = {label:value for label,value in (('catalog',offered),('initial',initial),('walking',walking),('step',stepped),('suspended',suspended),('held',held),('rearmed',rearmed),('focus',unfocused),('focus_resumed',resumed),('focus_moved',recovered),('closed',closed))}
                            tap('q');game.wait(timeout=3);check(game.returncode==0,delivery+': explicit close exits cleanly');game=None
                        native = game_log.read_text();require(not any(term in native for term in ('SCRIPT ERROR:','Parse Error:','ERROR:')),'Native window error: '+native[-2500:])
                    authority.check_report(json.loads(report.read_text()))
            except Exception:
                preserve_diagnostics(scratch,output)
                raise
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
              'checks':{'passed':len(checks),'failed':0},'controls':checks,'observations':observations,'startup':startup,
              'scope':'Actual source/PCK remote window, XTest keyboard/focus, TCP authority, costs and fail-closed presentation. No independent human, latency benchmark or complete network player journey claim.'}
    (output/'keyboard.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(f'PASS: {len(checks)} source/PCK remote-window OS controls')
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True);parser.add_argument('--godot',default='godot');args=parser.parse_args()
    try:verify(args.output,args.godot)
    except (OSError,ValueError,KeyError,subprocess.SubprocessError) as error:parser.exit(1,f'FAIL: {error}\n')
