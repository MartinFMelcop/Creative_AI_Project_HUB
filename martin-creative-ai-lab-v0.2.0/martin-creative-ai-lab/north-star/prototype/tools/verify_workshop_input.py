#!/usr/bin/env python3
"""Navigate and craft in the actual native source/PCK window using synthetic XTest keys.

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

def verify(output):
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="workshop-input-") as folder:
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
                    def walk(x,y):
                        for _ in range(24):
                            state=shot("walking")["workshop"];px,py=state["player"]
                            if (px-x)**2+(py-y)**2<30**2:return
                            delta=x-px if abs(x-px)>20 else y-py
                            button=("d" if delta>0 else "a") if abs(x-px)>20 else ("s" if delta>0 else "w")
                            key(button);time.sleep(min(.45,max(.06,abs(delta)/250*.8)));key(button,False)
                        raise ValueError("Real navigation did not reach station")
                    def craft(name):
                        key("e");time.sleep(.1);samples=[]
                        for _ in range(20):
                            state=shot(name);samples.append(state["workshop"])
                            if state["workshop"]["blank"]==0:break
                            time.sleep(.1)
                        key("e",False)
                        if state["workshop"]["blank"]!=0:raise ValueError("Received craft input did not complete")
                        return state,samples
                    tap("F2");empty=shot("entered")
                    assert empty["workshop"]["active"] and empty["tick"]==0
                    tap("e");outside=shot("outside")
                    assert outside["workshop"]["progress"]==0 and outside["workshop"]["blank"]==1
                    walk(330,420);heavy,heavy_samples=craft("coat")
                    assert heavy["workshop"]["outfit"]=="riveted" and heavy["workshop"]["made"]==1
                    tap("Return");live_heavy=shot("coat-crossing")
                    assert live_heavy["outfit"]["id"]=="riveted" and live_heavy["hp"]==6 and live_heavy["mode"]=="play"
                    tap("Escape");tap("r");tap("2");tap("F2");tap("c")
                    undone=shot("recycled");assert undone["workshop"]["blank"]==1 and undone["workshop"]["outfit"]=="standard"
                    walk(820,420);light,light_samples=craft("wrap")
                    assert light["workshop"]["outfit"]=="trail" and light["workshop"]["made"]==2
                    tap("Return");live_light=shot("wrap-crossing")
                    assert live_light["role"]=="Duelist" and live_light["outfit"]["id"]=="trail" and live_light["hp"]==4
                    tap("Escape");tap("r");tap("F2");tap("c")
                    walk(575,420);sash,sash_samples=craft("sash")
                    assert sash["workshop"]["outfit"]=="field_sash" and sash["workshop"]["made"]==3
                    tap("Return");live_sash=shot("sash-crossing")
                    assert live_sash["outfit"]["recovery_rate"]==26 and live_sash["hp"]==4
                    assert live_sash["outfit"]["movement_scale"]==1
                    records[delivery]={"heavy":heavy["workshop"],"light":light["workshop"],"sash":sash["workshop"],"recycled":undone["workshop"],"heavy_samples":heavy_samples,"light_samples":light_samples,"sash_samples":sash_samples,"crossings":[{"role":s["role"],"outfit":s["outfit"],"hp":s["hp"]} for s in [live_heavy,live_light,live_sash]]}
                    game.terminate();game.wait(timeout=3);game=None
                    for _ in range(60):
                        X.XSync(d,0)
                        if window(d) is None:break
                        time.sleep(.05)
            finally:
                if d:X.XCloseDisplay(d)
                for child in (game,server):
                    if child:
                        child.terminate()
                        try:child.wait(timeout=3)
                        except subprocess.TimeoutExpired:child.kill();child.wait()
        text=(scratch/"engine.log").read_text()
        if any(e in text for e in ("SCRIPT ERROR:","Parse Error:","ERROR:")):raise ValueError(text[-2000:])
        result={"kind":"synthetic_os_input","deliveries":records,"scope":"Actual native keyboard navigation, range rejection, craft, undo and equipped crossing. Not a human study or physical timing claim."}
        (output/"keyboard.json").write_text(json.dumps(result,sort_keys=True,indent=2)+"\n")
        print("PASS: actual source/PCK window navigation, crafting, undo and fitted crossings")
        return result

if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument("--output",type=Path,required=True);args=parser.parse_args()
    try:verify(args.output)
    except (AssertionError,OSError,ValueError,subprocess.TimeoutExpired) as error:parser.exit(1,f"FAIL: {error}\n")
