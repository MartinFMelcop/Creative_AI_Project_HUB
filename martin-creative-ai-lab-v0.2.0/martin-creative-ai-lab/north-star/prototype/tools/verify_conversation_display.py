#!/usr/bin/env python3
"""Inspect the real conversation and acknowledge source/PCK OS keyboard choices.

The external fixture completes an actual escort and freezes its arrival/gate entry.
OS keys then own dialogue, selection, cancellation, confirmation and departure.
This does not claim unassisted gameplay, participant feedback or input latency.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import time
from verify import invoke
from verify_routes_input import C, X, T, window, ROOT, x_error, x_errors


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def stop(process):
    if process is None:
        return
    process.terminate()
    try:
        process.wait(timeout=3)
    except subprocess.TimeoutExpired:
        process.kill();process.wait()


def verify(output):
    output=Path(output).resolve();output.mkdir(parents=True,exist_ok=True)
    records={};pixels={};keyboard={};server=game=d=None
    x_errors.clear();previous=X.XSetErrorHandler(C.cast(x_error,C.c_void_p))
    with tempfile.TemporaryDirectory(prefix="courier-display-") as folder:
        scratch=Path(folder);env=os.environ.copy()
        for name in ("CROSSING_PROFILE","CROSSING_CONTROLS","CROSSING_CAPTURE"):
            env.pop(name,None)
        env.update({k:str(scratch/k) for k in ("XDG_DATA_HOME","XDG_CONFIG_HOME","XDG_CACHE_HOME")})
        if not invoke(["godot","--version"],env).strip().startswith("4.6.3."):
            raise ValueError("Reproduction requires Godot 4.6.3")
        display=next((n for n in range(210,230) if not Path(f"/tmp/.X11-unix/X{n}").exists() and not Path(f"/tmp/.X{n}-lock").exists()),None)
        if display is None:raise ValueError("No unused local display")
        env["DISPLAY"]=f":{display}"
        modes=[("source",["--path",str(ROOT)]),("pack",["--main-pack",str(ROOT/"dist/crossing-drill.pck")])]
        with (output/"display.log").open("w") as log:
            try:
                server=subprocess.Popen(["Xorg",env["DISPLAY"],"-config",str(ROOT/"tests/dummy-display.conf"),"-logfile",str(scratch/"Xorg.log"),"-noreset","-nolisten","tcp"],env=env,stdout=log,stderr=log)
                for _ in range(60):
                    d=X.XOpenDisplay(env["DISPLAY"].encode())
                    if d:break
                    time.sleep(.05)
                if not d:raise ValueError("Owned display unavailable")
                for delivery,args in modes:
                    env.update(CROSSING_PROFILE=str(scratch/(delivery+"-marks.json")),CROSSING_CONTROLS=str(scratch/(delivery+"-keys.json")))
                    target=output/delivery;target.mkdir(exist_ok=True)
                    log.write(invoke(["godot",*args,"--audio-driver","Dummy","--script",str(ROOT/"tests/conversation_capture.gd"),"--",str(target)],env));log.flush()
                    records[delivery]=json.loads((target/"frames.json").read_text())
                    pixels[delivery]={p.stem:digest(p) for p in sorted(target.glob("*.png"))}
                expected={"courier-offer","courier-road","courier-heal-selected","courier-heal-confirmed","healed-return","braced-return","full-health-offer","full-health-brace-confirmed"}
                if set(pixels["source"])!=expected:raise ValueError("Incomplete conversation scene samples")
                if records["source"]!=records["pack"] or pixels["source"]!=pixels["pack"]:
                    raise ValueError("Conversation source/PCK rendered states or pixels differ")
                for delivery,args in modes:
                    deadline=time.monotonic()+180
                    fixture=scratch/(delivery+"-os");fixture.mkdir()
                    capture=fixture/"capture.png";path=Path(str(capture)+".json")
                    env.update(CROSSING_PROFILE=str(fixture/"marks.json"),CROSSING_CONTROLS=str(fixture/"keys.json"),CROSSING_CAPTURE=str(capture))
                    game=subprocess.Popen(["godot",*args,"--audio-driver","Dummy","--script",str(ROOT/"tests/conversation_capture.gd"),"--",str(fixture),"--os"],env=env,stdout=log,stderr=log)
                    target=None
                    for _ in range(350):
                        if game.poll() is not None:raise ValueError("Consumer exited before assisted arrival")
                        target=window(d)
                        if target and (fixture/"os-ready.json").is_file():break
                        time.sleep(.05)
                    else:raise ValueError("Actual escort fixture did not acknowledge arrival")
                    X.XSetInputFocus(d,target,1,0);X.XSync(d,0);time.sleep(.25)

                    def key(name,on=True):
                        if time.monotonic()>deadline:raise ValueError("OS conversation exceeded 180s")
                        code=X.XKeysymToKeycode(d,X.XStringToKeysym(name.encode()))
                        if not code:raise ValueError("Unavailable key: "+name)
                        T.XTestFakeKeyEvent(d,code,on,0);X.XSync(d,0)

                    def tap(name):
                        key(name);time.sleep(.06);key(name,False);time.sleep(.06)

                    def shot(label):
                        prior=path.stat().st_mtime_ns if path.exists() else 0;tap("F12")
                        for _ in range(100):
                            if path.exists() and path.stat().st_mtime_ns!=prior:
                                try:value=json.loads(path.read_text())
                                except json.JSONDecodeError:time.sleep(.03);continue
                                shutil.copyfile(capture,output/(delivery+"-os-"+label+".png"))
                                (output/(delivery+"-os-"+label+".json")).write_text(json.dumps(value,sort_keys=True,indent=2)+"\n")
                                return value
                            time.sleep(.03)
                        raise ValueError("Consumer did not acknowledge capture")

                    initial=None
                    for attempts in range(1,9):
                        current=window(d)
                        if current:X.XSetInputFocus(d,current,1,0);X.XSync(d,0)
                        try:initial=shot("arrival");break
                        except ValueError as error:
                            if str(error)!="Consumer did not acknowledge capture":raise
                    if initial is None:raise ValueError("Consumer never acknowledged startup capture")
                    ready=json.loads((fixture/"os-ready.json").read_text())
                    assert initial["mode"]=="won" and initial["hp"]==ready["hp"]<ready["health_limit"]
                    tap("F4");offer=shot("offer");assert offer["courier_talk"]["active"]
                    tap("Tab");road=shot("road");assert road["courier_talk"]["page"]=="road"
                    tap("Tab");tap("1");draft=shot("draft")
                    assert draft["courier_talk"]["draft"]=="heal" and draft["courier_talk"]["choice"]==""
                    tap("Escape");cancelled=shot("cancelled")
                    assert not cancelled["courier_talk"]["active"] and cancelled["courier_talk"]["choice"]=="" and cancelled["hp"]==initial["hp"]
                    tap("F4");tap("2");selected=shot("brace-selected");assert selected["courier_talk"]["draft"]=="brace"
                    tap("Return");confirmed=shot("confirmed")
                    assert confirmed["courier_talk"]["choice"]=="brace" and confirmed["hp"]==initial["hp"]
                    tap("F2");departed=shot("departed")
                    assert departed["return_gate"]["active"] and departed["cargo"]==3 and departed["hp"]==initial["hp"]
                    assert departed["return_gate"]["entry"]["aid"]=="brace"
                    tap("Escape");tap("r");left=shot("left");tap("F4");rejected=shot("title-rejection")
                    assert left["mode"]=="title" and left["courier_talk"]["choice"]=="" and not rejected["courier_talk"]["active"]
                    keyboard[delivery]={"startup_capture_attempts":attempts,"arrival_hp":initial["hp"],"read_road":True,
                        "cancelled_unconfirmed_heal":True,"confirmed":"brace","gate_hp":departed["hp"],"gate_integrity":departed["cargo"],
                        "abandon_reset":True,"title_rejected":True}
                    stop(game);game=None
                    for _ in range(60):
                        X.XSync(d,0)
                        if window(d) is None:break
                        time.sleep(.05)
            finally:
                if d:X.XCloseDisplay(d)
                X.XSetErrorHandler(previous);stop(game);stop(server)
        logtext=(output/"display.log").read_text()
        if x_errors or any(marker in logtext for marker in ("SCRIPT ERROR:","Parse Error:","ERROR:","instances leaked")):
            raise ValueError(str(x_errors)+logtext[-2500:])
    result={"kind":"native_conversation_render_and_assisted_os_input","rendered_frames_per_delivery":8,
        "source_pack_pixel_state_parity":True,"pixels":pixels,"keyboard":keyboard,
        "scope":"Eight actual scene samples after complete wounded and unwounded policy escorts; full-health healing rejection and brace agreement. Real OS conversation/read/draft/cancel/confirm/depart/reset; assisted fixture freezes arrival and gate entry. No unassisted escort, participant identity/recognition, preference or latency claim."}
    (output/"display.json").write_text(json.dumps(result,sort_keys=True,indent=2)+"\n")
    print("PASS: eight source/PCK conversation frames and assisted real OS choice consequences")
    return result


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument("--output",type=Path,required=True);args=parser.parse_args()
    try:verify(args.output)
    except (AssertionError,OSError,ValueError,KeyError,subprocess.TimeoutExpired) as error:parser.exit(1,f"FAIL: {error}\n")
