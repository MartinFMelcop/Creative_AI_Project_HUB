#!/usr/bin/env python3
"""Actual source/PCK keyboard continuation after an explicitly scripted wounded escort.

The escort setup is native policy execution, not OS input or an independent player.
Navigation, work, natural winch failure and checkpoint retry use the real window.
"""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import time
from verify_routes_input import C, X, T, window, ROOT, x_error, x_errors

def verify(output):
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    records={};x_errors.clear()
    previous=X.XSetErrorHandler(C.cast(x_error,C.c_void_p))
    with tempfile.TemporaryDirectory(prefix="gate-input-") as folder:
        scratch=Path(folder);env=os.environ.copy()
        env.update({k:str(scratch/k) for k in ("XDG_DATA_HOME","XDG_CONFIG_HOME","XDG_CACHE_HOME")})
        display=next((n for n in range(170,190) if not Path(f"/tmp/.X11-unix/X{n}").exists() and not Path(f"/tmp/.X{n}-lock").exists()),None)
        if display is None:raise ValueError("No unused local display")
        env["DISPLAY"]=f":{display}";server=game=d=None;deadline=time.monotonic()+240
        with (scratch/"engine.log").open("w") as log:
            try:
                server=subprocess.Popen(["Xorg",env["DISPLAY"],"-config",str(ROOT/"tests/dummy-display.conf"),"-logfile",str(scratch/"Xorg.log"),"-noreset","-nolisten","tcp"],env=env,stdout=log,stderr=log)
                for _ in range(60):
                    d=X.XOpenDisplay(env["DISPLAY"].encode())
                    if d:break
                    time.sleep(.05)
                if not d:raise ValueError("Owned Xorg unavailable")
                for delivery,args in [("source",["--path",str(ROOT)]),("pack",["--main-pack",str(ROOT/"dist/crossing-drill.pck")])]:
                    capture=scratch/(delivery+".png");env["CROSSING_CAPTURE"]=str(capture)
                    env["CROSSING_PROFILE"]=str(scratch/(delivery+"-keepsakes.json"))
                    env["CROSSING_CONTROLS"]=str(scratch/(delivery+"-controls.json"))
                    game=subprocess.Popen(["godot",*args,"--audio-driver","Dummy","--script","res://tests/gate_input_fixture.gd"],env=env,stdout=log,stderr=log)
                    target=None
                    for _ in range(350):
                        target=window(d)
                        if target:break
                        if game.poll() is not None:raise ValueError("Native setup stopped before window")
                        time.sleep(.05)
                    if not target:raise ValueError("Native consumer window unavailable")
                    X.XSetInputFocus(d,target,1,0);X.XSync(d,0);time.sleep(.3)
                    def key(name,on=True):
                        if time.monotonic()>deadline:raise ValueError("Input verification exceeded 240s")
                        code=X.XKeysymToKeycode(d,X.XStringToKeysym(name.encode()))
                        if not code:raise ValueError("Unavailable XTest key: "+name)
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
                        raise ValueError("Consumer did not acknowledge capture")
                    arrival=shot("arrival")
                    assert arrival["mode"]=="won" and arrival["hp"]==4,delivery+": real wounded setup missing"
                    tap("F2");tap("Escape");entry=shot("entry")
                    assert entry["mode"]=="paused" and entry["return_gate"]["entry"]["hp"]==4,delivery+": F2 did not continue"
                    samples=[]
                    for _ in range(24):
                        state=shot("walk");px,py=state["player_position"];samples.append({"tick":state["tick"],"player":[px,py]})
                        if (px-330)**2+(py-270)**2<24**2:break
                        dx,dy=330-px,270-py;delta=dx if abs(dx)>14 else dy
                        button=("d" if delta>0 else "a") if abs(dx)>14 else ("s" if delta>0 else "w")
                        tap("Escape");key(button);time.sleep(min(.4,max(.06,abs(delta)/250*.7)));key(button,False);tap("Escape")
                    else:raise ValueError("Real navigation did not reach catch")
                    tap("Escape");key("e")
                    for _ in range(50):
                        worked=shot("work")
                        if worked["return_gate"]["raised"][0]:break
                        assert worked["mode"]=="play",delivery+": work failed before completion"
                    else:raise ValueError("Received hold did not finish real work")
                    key("e",False);tap("Escape");raised=shot("raised")
                    assert raised["return_gate"]["raised"]==[True,False] and raised["mode"]=="paused"
                    tap("Escape")
                    for _ in range(70):
                        failed=shot("failure")
                        if failed["mode"]=="lost":break
                    else:raise ValueError("Ignoring winch did not produce bounded failure")
                    assert failed["cargo"]==0,delivery+": failure did not belong to exposed winch"
                    tap("Return");tap("Escape");retry=shot("retry")
                    assert retry["hp"]==4 and retry["cargo"]==2 and retry["return_gate"]["raised"]==[False,False],delivery+": checkpoint mismatch"
                    tap("r");left=shot("left")
                    assert left["mode"]=="title" and "return_gate" not in left
                    records[delivery]={"entry":entry["return_gate"]["entry"],"movement":samples,"first_catch":raised["return_gate"]["raised"],"failure":{"hp":failed["hp"],"winch":failed["cargo"]},"retry":{"hp":retry["hp"],"winch":retry["cargo"],"raised":retry["return_gate"]["raised"]},"abandoned":True}
                    game.terminate();game.wait(timeout=3);game=None
                    for _ in range(60):
                        X.XSync(d,0)
                        if window(d) is None:break
                        time.sleep(.05)
            finally:
                if d:X.XCloseDisplay(d)
                X.XSetErrorHandler(previous)
                for child in (game,server):
                    if child:
                        child.terminate()
                        try:child.wait(timeout=3)
                        except subprocess.TimeoutExpired:child.kill();child.wait()
        text=(scratch/"engine.log").read_text()
        if x_errors or any(e in text for e in ("SCRIPT ERROR:","Parse Error:","ERROR:")):raise ValueError(str(x_errors)+text[-2500:])
    result={"kind":"synthetic_os_input","deliveries":records,"scope":"Policy-executed wounded first encounter; actual F2, movement/work, natural failure, retry and abandon in both native windows. No full OS-driven first escort or human study."}
    (output/"keyboard.json").write_text(json.dumps(result,sort_keys=True,indent=2)+"\n")
    print("PASS: source/PCK native continuation, navigation, real work, failure and retry")
    return result

if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument("--output",type=Path,required=True);args=parser.parse_args()
    try:verify(args.output)
    except (AssertionError,OSError,ValueError,subprocess.TimeoutExpired) as error:parser.exit(1,f"FAIL: {error}\n")
