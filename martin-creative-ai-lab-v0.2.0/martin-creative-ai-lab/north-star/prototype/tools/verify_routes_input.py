#!/usr/bin/env python3
"""Navigate and signal a route in the actual native source/PCK window using synthetic XTest keys.

Requires Xorg dummy/libX11/libXtst. No teleported scene, participant or latency claim.
"""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import time
from verify_toggle_input import C, X, T, window, ROOT

class XErrorEvent(C.Structure):
    _fields_=[("type",C.c_int),("display",C.c_void_p),("resourceid",C.c_ulong),
              ("serial",C.c_ulong),("error_code",C.c_ubyte),
              ("request_code",C.c_ubyte),("minor_code",C.c_ubyte)]

# A startup splash may disappear between XQueryTree and XFetchName. Ignore only
# BadWindow during discovery; actual input must still be acknowledged by the game.
XHandler=C.CFUNCTYPE(C.c_int,C.c_void_p,C.POINTER(XErrorEvent))
X.XSetErrorHandler.argtypes=[C.c_void_p];X.XSetErrorHandler.restype=C.c_void_p
x_errors=[]
@XHandler
def x_error(_display,event):
    if event.contents.error_code!=3 or event.contents.request_code not in (15,20):
        x_errors.append({"code":event.contents.error_code,"request":event.contents.request_code})
    return 0

def verify(output):
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    x_errors.clear()
    previous_handler=X.XSetErrorHandler(C.cast(x_error,C.c_void_p))
    with tempfile.TemporaryDirectory(prefix="route-input-") as folder:
        scratch=Path(folder);env=os.environ.copy()
        env.update({k:str(scratch/k) for k in ("XDG_DATA_HOME","XDG_CONFIG_HOME","XDG_CACHE_HOME")})
        env.pop("CROSSING_PROFILE",None);env.pop("CROSSING_CONTROLS",None)
        display=next((n for n in range(130,150) if not Path(f"/tmp/.X11-unix/X{n}").exists() and not Path(f"/tmp/.X{n}-lock").exists()),None)
        if display is None:raise ValueError("No unused local display")
        env["DISPLAY"]=f":{display}"
        server=game=d=None;records={};deadline=time.monotonic()+240
        with (scratch/"engine.log").open("w") as log:
            try:
                server=subprocess.Popen(["Xorg",env["DISPLAY"],"-config",str(ROOT/"tests/dummy-display.conf"),"-logfile",str(scratch/"Xorg.log"),"-noreset","-nolisten","tcp"],env=env,stdout=log,stderr=log)
                for _ in range(40):
                    d=X.XOpenDisplay(env["DISPLAY"].encode())
                    if d:break
                    time.sleep(.05)
                if not d:raise ValueError("Owned Xorg unavailable")
                for delivery in ("source","pack"):
                    capture=scratch/(delivery+".png");env["CROSSING_CAPTURE"]=str(capture)
                    base=["godot","--path",str(ROOT)] if delivery=="source" else ["godot","--main-pack",str(ROOT/"dist/crossing-drill.pck")]
                    game=subprocess.Popen(base+["--audio-driver","Dummy"],env=env,stdout=log,stderr=log)
                    target=None
                    for _ in range(300):
                        target=window(d)
                        if target:break
                        if game.poll() is not None:raise ValueError("Native consumer stopped before window")
                        time.sleep(.05)
                    if not target:raise ValueError("Native consumer window unavailable")
                    X.XSetInputFocus(d,target,1,0);X.XSync(d,0);time.sleep(.3)
                    def key(name,on=True):
                        if time.monotonic()>deadline:raise ValueError("Owned input journey exceeded 240 seconds")
                        code=X.XKeysymToKeycode(d,X.XStringToKeysym(name.encode()))
                        T.XTestFakeKeyEvent(d,code,on,0);X.XSync(d,0)
                    def tap(name):
                        key(name);time.sleep(.06);key(name,False);time.sleep(.06)
                    def shot(name):
                        record=Path(str(capture)+".json");prior=record.stat().st_mtime_ns if record.exists() else 0
                        tap("F12")
                        for _ in range(100):
                            if record.exists() and record.stat().st_mtime_ns!=prior:
                                try:
                                    value=json.loads(record.read_text());shutil.copyfile(capture,output/(delivery+"-"+name+".png"));return value
                                except json.JSONDecodeError:pass
                            time.sleep(.03)
                        raise ValueError("Consumer did not acknowledge capture input")
                    tap("Return");tap("Escape");fresh=shot("fresh")
                    assert fresh["mode"]=="paused" and fresh["route"]["kind"]=="road"
                    tap("Escape");tap("e");tap("Escape");outside=shot("outside")
                    assert outside["route"]["kind"]=="road"
                    samples=[]
                    for _ in range(20):
                        state=shot("walking");px,py=state["player_position"];samples.append({"tick":state["tick"],"player":[px,py]})
                        if (px-350)**2+(py-260)**2<25**2:break
                        dx,dy=350-px,260-py
                        delta=dx if abs(dx)>15 else dy
                        button=("d" if delta>0 else "a") if abs(dx)>15 else ("s" if delta>0 else "w")
                        tap("Escape");key(button);time.sleep(min(.4,max(.07,abs(delta)/250*.7)));key(button,False);tap("Escape")
                    else:raise ValueError("Real navigation did not reach the signal board")
                    tap("e");paused=shot("paused-signal")
                    assert paused["route"]["kind"]=="road"
                    tap("Escape");key("e");time.sleep(.25);key("e",False);tap("Escape")
                    chosen=shot("ridge-signalled")
                    assert chosen["route"]["kind"]=="ridge" and not chosen["route"]["locked"]
                    tap("Escape");tap("e");tap("Escape");revised=shot("road-revised")
                    assert revised["route"]["kind"]=="road"
                    tap("r");tap("Return");tap("Escape");retry=shot("retry")
                    assert retry["route"]["kind"]=="road" and retry["route"]["covered_bolts"]==0
                    records[delivery]={"outside":outside["route"],"paused":paused["route"],"chosen":chosen["route"],"revised":revised["route"],"retry":retry["route"],"movement_samples":samples}
                    game.terminate();game.wait(timeout=3);game=None
                    for _ in range(60):
                        X.XSync(d,0)
                        if window(d) is None:break
                        time.sleep(.05)
            finally:
                if d:X.XCloseDisplay(d)
                X.XSetErrorHandler(previous_handler)
                for child in (game,server):
                    if child:
                        child.terminate()
                        try:child.wait(timeout=3)
                        except subprocess.TimeoutExpired:child.kill();child.wait()
        text=(scratch/"engine.log").read_text()
        if x_errors:raise ValueError("Unexpected X11 errors: "+str(x_errors))
        if any(e in text for e in ("SCRIPT ERROR:","Parse Error:","ERROR:")):raise ValueError(text[-2000:])
        result={"kind":"synthetic_os_input","deliveries":records,"scope":"Actual native keyboard navigation, outside/paused rejection, route signal, revision and clean retry. Paused observations avoid timing interference; not a full OS-input escort or human study."}
        (output/"keyboard.json").write_text(json.dumps(result,sort_keys=True,indent=2)+"\n")
        print("PASS: source/PCK actual keyboard navigation, route signal, revision and reset")
        return result

if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument("--output",type=Path,required=True);args=parser.parse_args()
    try:verify(args.output)
    except (AssertionError,OSError,ValueError,subprocess.TimeoutExpired) as error:parser.exit(1,f"FAIL: {error}\n")
