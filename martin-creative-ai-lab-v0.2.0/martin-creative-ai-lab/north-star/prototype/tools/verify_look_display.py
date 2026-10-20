#!/usr/bin/env python3
"""Render the actual look workflow and execute real source/PCK keyboard choices.

Optional prior PCK proves unchanged default gameplay pixels. Requires owned Xorg
dummy display, libX11/libXtst and Godot 4.6.3. No participant or hardware-latency claim.
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

def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def verify(output, baseline=None):
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    if baseline and not Path(baseline).is_file():raise ValueError("Prior PCK unavailable")
    records={};pixels={};keyboard={};x_errors.clear();previous=X.XSetErrorHandler(C.cast(x_error,C.c_void_p))
    server=game=d=None
    with tempfile.TemporaryDirectory(prefix="look-display-") as folder:
        scratch=Path(folder);env=os.environ.copy()
        for name in ("CROSSING_PROFILE","CROSSING_CONTROLS","CROSSING_CAPTURE"):env.pop(name,None)
        env.update({k:str(scratch/k) for k in ("XDG_DATA_HOME","XDG_CONFIG_HOME","XDG_CACHE_HOME")})
        if not invoke(["godot","--version"],env).strip().startswith("4.6.3."):raise ValueError("Reproduction requires Godot 4.6.3")
        display=next((n for n in range(190,210) if not Path(f"/tmp/.X11-unix/X{n}").exists() and not Path(f"/tmp/.X{n}-lock").exists()),None)
        if display is None:raise ValueError("No unused local display")
        env["DISPLAY"]=f":{display}";deadline=time.monotonic()+240
        with (output/"display.log").open("w") as log:
            try:
                server=subprocess.Popen(["Xorg",env["DISPLAY"],"-config",str(ROOT/"tests/dummy-display.conf"),"-logfile",str(scratch/"Xorg.log"),"-noreset","-nolisten","tcp"],env=env,stdout=log,stderr=log)
                for _ in range(60):
                    d=X.XOpenDisplay(env["DISPLAY"].encode())
                    if d:break
                    time.sleep(.05)
                if not d:raise ValueError("Owned display unavailable")
                modes=[("source",["--path",str(ROOT)]),("pack",["--main-pack",str(ROOT/"dist/crossing-drill.pck")])]
                if baseline:modes.append(("baseline",["--main-pack",str(Path(baseline).resolve())]))
                for mode,args in modes:
                    env["CROSSING_PROFILE"]=str(scratch/(mode+"-marks.json"));env["CROSSING_CONTROLS"]=str(scratch/(mode+"-keys.json"))
                    target=output/mode;target.mkdir(exist_ok=True)
                    log.write(invoke(["godot",*args,"--audio-driver","Dummy","--script",str(ROOT/"tests/look_capture.gd"),"--",str(target.resolve())],env));log.flush()
                    records[mode]=json.loads((target/"frames.json").read_text())
                    pixels[mode]={p.stem:digest(p) for p in sorted(target.glob("*.png"))}
                if records["source"]!=records["pack"] or pixels["source"]!=pixels["pack"]:raise ValueError("Rendered source/PCK states or pixels differ")
                if len(pixels["source"])!=13:raise ValueError("Incomplete actual look/persistence scenes")
                if baseline:
                    if set(pixels["baseline"])!={"guardian-original","duelist-original"}:raise ValueError("Incomplete prior default-art controls")
                    for name in pixels["baseline"]:
                        current=records["source"][name].copy();current.pop("look",None)
                        if pixels["source"][name]!=pixels["baseline"][name] or current!=records["baseline"][name]:raise ValueError("Default gameplay artwork or state changed: "+name)
                # Rendering has its own per-process bounds. Give OS input a separate
                # bounded phase so cold rendering cannot consume its receipt deadline.
                deadline=time.monotonic()+240
                for delivery,args in modes:
                    profile=scratch/(delivery+"-os-marks.json");controls=scratch/(delivery+"-os-keys.json")
                    env.update(CROSSING_PROFILE=str(profile),CROSSING_CONTROLS=str(controls),CROSSING_CAPTURE=str(scratch/(delivery+".png")))
                    observations={}
                    for fresh in ([True] if delivery=="baseline" else [False,True]):
                        game=subprocess.Popen(["godot",*args,"--audio-driver","Dummy"],env=env,stdout=log,stderr=log)
                        target=None
                        for _ in range(350):
                            target=window(d)
                            if target:break
                            if game.poll() is not None:raise ValueError("Consumer exited before native window")
                            time.sleep(.05)
                        if not target:raise ValueError("Native consumer window unavailable")
                        X.XSetInputFocus(d,target,1,0);X.XSync(d,0);time.sleep(.25)
                        def key(name,on=True):
                            if time.monotonic()>deadline:raise ValueError("Display/input verification exceeded 240s")
                            code=X.XKeysymToKeycode(d,X.XStringToKeysym(name.encode()))
                            if not code:raise ValueError("Unavailable key: "+name)
                            T.XTestFakeKeyEvent(d,code,on,0);X.XSync(d,0)
                        def tap(name):key(name);time.sleep(.06);key(name,False);time.sleep(.06)
                        def shot(label):
                            capture=Path(env["CROSSING_CAPTURE"]);path=Path(str(capture)+".json")
                            prior=path.stat().st_mtime_ns if path.exists() else 0;tap("F12")
                            for _ in range(100):
                                if path.exists() and path.stat().st_mtime_ns!=prior:
                                    try:value=json.loads(path.read_text())
                                    except json.JSONDecodeError:
                                        time.sleep(.03);continue
                                    shutil.copyfile(capture,output/(delivery+"-"+label+".png"))
                                    (output/(delivery+"-"+label+".json")).write_text(json.dumps(value,sort_keys=True,indent=2)+"\n")
                                    return value
                                time.sleep(.03)
                            raise ValueError("Consumer did not acknowledge capture")
                        initial=None;attempts=0
                        # A native window can precede scene readiness. Only this
                        # idempotent capture request is retried, never gameplay keys.
                        for attempts in range(1,9):
                            current=window(d)
                            if current:X.XSetInputFocus(d,current,1,0);X.XSync(d,0)
                            try:
                                initial=shot("fresh" if fresh else "title");break
                            except ValueError as error:
                                if str(error)!="Consumer did not acknowledge capture":raise
                        if initial is None:raise ValueError("Consumer never acknowledged startup capture")
                        if delivery=="baseline":
                            assert initial["mode"]=="title";observations["startup_capture_attempts"]=attempts
                            game.terminate();game.wait(timeout=3);game=None
                            break
                        expected_fresh={"skin":3,"hair":2,"dye":1} if fresh else {"skin":0,"hair":0,"dye":0}
                        assert initial["mode"]=="title" and initial["character_look"]["applied"]==expected_fresh
                        if fresh:observations["fresh_process_retained"]=expected_fresh
                        else:
                            tap("F3");tap("Right");tap("Down");tap("Right");tap("Down");tap("Right")
                            draft=shot("draft");assert draft["character_look"]["draft"]=={"skin":1,"hair":1,"dye":1} and draft["character_look"]["applied"]=={"skin":0,"hair":0,"dye":0}
                            tap("Escape");cancelled=shot("cancelled");assert not cancelled["character_look"]["active"] and cancelled["character_look"]["applied"]==initial["character_look"]["applied"]
                            tap("F3");assert shot("editor-ready")["character_look"]["active"],delivery+": editor did not open"
                            # Acknowledge each discrete edit before the next one.
                            # Poll captures if delayed; never replay a gameplay/edit key.
                            for button,field,expected_value in [("Right","skin",1),("Right","skin",2),("Down","row",1),("Right","hair",1),("Right","hair",2),("Down","row",2),("Right","dye",1)]:
                                tap(button)
                                for _ in range(5):
                                    receipt=shot("edit-"+field+"-"+str(expected_value))["character_look"]
                                    observed=receipt["row"] if field=="row" else receipt["draft"][field]
                                    if observed==expected_value:break
                                else:raise ValueError(delivery+": edit receipt mismatch for "+field+": "+str(receipt))
                            tap("Return")
                            applied=shot("applied");expected={"skin":2,"hair":2,"dye":1}
                            assert applied["character_look"]["applied"]==expected and applied["mode"]=="title",delivery+": applied look differs: "+str(applied["character_look"])
                            tap("2");tap("Return");live=shot("live");assert live["mode"]=="play" and live["role"]=="Duelist" and live["character_look"]["applied"]==expected
                            tap("F3");assert not shot("title-only")["character_look"]["active"]
                            tap("Escape");tap("r");left=shot("retained");assert left["mode"]=="title" and left["character_look"]["applied"]==expected
                            # Unknown primary bytes remain untouched while an actual
                            # applied look stays usable. F5 retries only committed data.
                            profile.write_text("{")
                            tap("F3");assert shot("repair-editor")["character_look"]["active"]
                            tap("Right");assert shot("repair-draft")["character_look"]["draft"]["skin"]==3
                            tap("Return");pending=shot("save-pending")
                            retained={"skin":3,"hair":2,"dye":1}
                            assert pending["character_look"]["applied"]==retained and pending["keepsakes"]["blocked"] and pending["keepsakes"]["dirty"] and profile.read_text()=="{"
                            profile.write_text(json.dumps({"schema_version":1,"earned":[],"equipped":""}))
                            tap("F5");repaired=shot("save-repaired")
                            stored=json.loads(profile.read_text())
                            assert not repaired["keepsakes"]["dirty"] and not repaired["keepsakes"]["blocked"] and repaired["character_look"]["applied"]==retained
                            assert stored["schema_version"]==2 and stored["look"]==retained
                            observations["unknown_bytes_preserved_and_repaired"]=True
                            observations["repaired_look"]=retained
                            observations.update({"startup_capture_attempts":attempts,"draft":draft["character_look"]["draft"],"cancelled":True,"applied":expected,"live_role":live["role"],"retained_on_abandon":True,"live_editor_rejected":True})
                        game.terminate();game.wait(timeout=3);game=None
                        for _ in range(60):
                            X.XSync(d,0)
                            if window(d) is None:break
                            time.sleep(.05)
                    keyboard[delivery]=observations
            finally:
                if d:X.XCloseDisplay(d)
                X.XSetErrorHandler(previous)
                for child in (game,server):
                    if child:
                        child.terminate()
                        try:child.wait(timeout=3)
                        except subprocess.TimeoutExpired:child.kill();child.wait()
        logtext=(output/"display.log").read_text()
        if x_errors or any(s in logtext for s in ["SCRIPT ERROR:","Parse Error:","ERROR:","instances leaked"]):raise ValueError(str(x_errors)+logtext[-2500:])
    result={"kind":"native_render_and_synthetic_os_input","rendered_frames_per_delivery":13,"source_pack_pixel_state_parity":True,"default_prior_pixel_controls":2 if baseline else 0,"baseline_pck_sha256":digest(Path(baseline)) if baseline else None,"pixels":pixels,"keyboard":keyboard,"scope":"Actual shared actor drawing, controlled action samples, real OS editor/apply/cancel/gameplay, unknown-file repair and fresh-process retention. Agent inspection and fixed controls are not participant identity recognition, taste or accessibility."}
    (output/"display.json").write_text(json.dumps(result,sort_keys=True,indent=2)+"\n")
    print("PASS: thirteen source/PCK scene samples and real keyboard edit/play/repair/restart")
    return result

if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument("--output",type=Path,required=True);parser.add_argument("--baseline",type=Path);args=parser.parse_args()
    try:verify(args.output,args.baseline)
    except (AssertionError,OSError,ValueError,KeyError,subprocess.TimeoutExpired) as error:parser.exit(1,f"FAIL: {error}\n")
