#!/usr/bin/env python3
"""Native OS interaction at a fixture-positioned lever after a real policy escort."""
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
    with tempfile.TemporaryDirectory(prefix="grounding-input-") as folder:
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
                    game=subprocess.Popen(["godot",*args,"--audio-driver","Dummy","--script","res://tests/grounding_input_fixture.gd"],env=env,stdout=log,stderr=log)
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
                    entry=shot("entry")
                    assert entry["mode"]=="paused" and entry["return_gate"]["entry"]["hp"]==4
                    tap("Escape");key("e");time.sleep(.35)
                    partial=shot("partial")
                    assert partial["return_gate"]["channel"] and 0<partial["return_gate"]["progress"]<1.5 and partial["cargo"]==2
                    tap("Escape");key("e",False);cancelled=shot("cancelled")
                    assert cancelled["return_gate"]["progress"]==0 and cancelled["cargo"]==2
                    tap("Escape");key("e");time.sleep(1.55);key("e",False)
                    grounded=shot("grounded")
                    assert grounded["mode"]=="play" and grounded["return_gate"].get("grounded") and grounded["cargo"]==1
                    assert grounded["enemy_focus"]==0 and grounded["return_gate"]["raised"]==[False,False]
                    tap("Escape");tap("r");left=shot("left")
                    assert left["mode"]=="title" and "return_gate" not in left
                    records[delivery]={"entry":entry["return_gate"]["entry"],"partial_seconds":partial["return_gate"]["progress"],
                        "pause_cancelled":cancelled["return_gate"]["progress"]==0,"grounded":grounded["return_gate"].get("grounded"),
                        "winch":grounded["cargo"],"ward_focus":grounded["enemy_focus"],"raised":grounded["return_gate"]["raised"],"abandoned":True}
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
    for path in output.glob("*.png"):
        if path.name not in ("source-partial.png","source-grounded.png"):path.unlink()
    result={"kind":"synthetic_os_input","deliveries":records,"scope":"Policy-executed wounded escort and fixture placement at lever; actual OS E hold, progress, pause cancellation, grounding cost and abandon in source/PCK windows. No human or full OS-driven journey."}
    (output/"keyboard.json").write_text(json.dumps(result,sort_keys=True,indent=2)+"\n")
    print("PASS: source/PCK native grounding, hold, pause cancellation, cost and abandon")
    return result

if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument("--output",type=Path,required=True);args=parser.parse_args()
    try:verify(args.output)
    except (AssertionError,OSError,ValueError,subprocess.TimeoutExpired) as error:parser.exit(1,f"FAIL: {error}\n")
