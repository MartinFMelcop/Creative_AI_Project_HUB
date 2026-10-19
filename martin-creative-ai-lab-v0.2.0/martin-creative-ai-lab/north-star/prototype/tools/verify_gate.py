#!/usr/bin/env python3
"""Execute actual source/PCK two-stage return-gate contracts; keep compact evidence."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
from verify import ROOT, invoke

def verify(output, godot="godot", pack=None, compare=None, baseline=None):
    executable=shutil.which(godot)
    if not executable:raise ValueError("Godot executable unavailable")
    with tempfile.TemporaryDirectory(prefix="north-star-return-") as folder:
        scratch=Path(folder);env=os.environ.copy()
        for name in ("CROSSING_PROFILE","CROSSING_CONTROLS","CROSSING_CAPTURE"):env.pop(name,None)
        env.update({k:str(scratch/k) for k in ("XDG_DATA_HOME","XDG_CONFIG_HOME","XDG_CACHE_HOME")})
        if not invoke([executable,"--version"],env).strip().startswith("4.6.3."):
            raise ValueError("Reproduction requires Godot 4.6.3")
        reports=[]
        for name,args in [("source",["--path",str(ROOT)]),("pack",["--main-pack",str(pack or ROOT/"dist/crossing-drill.pck")])]:
            report=scratch/(name+".json")
            invoke([executable,"--headless",*args,"--script","res://tests/gate_checks.gd","--",str(report)],env)
            reports.append(json.loads(report.read_text()))
        if reports[0]!=reports[1]:raise ValueError("Source/PCK return-gate observations differ")
        data=reports[0]
        if data["checks"]!={"passed":67,"failed":0}:raise ValueError("Incomplete or failed return-gate controls")
        if len(data["journeys"])!=4 or any(r["return_gate"]["game"]["mode"]!="won" for r in data["journeys"]):
            raise ValueError("Missing complete two-stage journeys")
        for name,digest in data["consumer_hashes"].items():
            if hashlib.sha256((ROOT/name).read_bytes()).hexdigest()!=digest:raise ValueError("Changed executed source: "+name)
        # Full native traces are compared above; retain outcomes and trace identities only.
        raw=json.dumps(data,ensure_ascii=False,sort_keys=True).encode()
        result={"schema_version":1,"checks":data["checks"],"consumer_hashes":data["consumer_hashes"],
                "native_observation_sha256":hashlib.sha256(raw).hexdigest(),"journeys":[
                    {"role":r["role"],"strategy":r["strategy"],"crossing_tick":r["crossing"]["tick"],
                     "entry_hp":r["crossing"]["hp"],"return_tick":r["return_gate"]["game"]["tick"],
                     "hp":r["return_gate"]["game"]["hp"],"winch":r["return_gate"]["game"]["cargo"],
                     "ward_disabled":r["return_gate"]["game"]["enemy_focus"]==0,
                     "responses":r["return_gate"]["game"]["counters"],"raised":r["return_gate"]["raised"],
                     "mode":r["return_gate"]["game"]["mode"]} for r in data["journeys"]],
                "scope":"Actual wounded crossing then optional return objective, four fixed policies; source/PCK equality is not human comprehension, preference or balance."}
        if compare and result!=json.loads(Path(compare).read_text()):raise ValueError("Return-gate comparison changed")
        transition=None
        if baseline:
            before=Path(baseline)
            if not before.is_file():raise ValueError("Baseline PCK unavailable")
            values=[]
            for label,delivery in [("before",before),("after",Path(pack or ROOT/"dist/crossing-drill.pck"))]:
                path=scratch/(label+"-transition.json")
                invoke([executable,"--headless","--main-pack",str(delivery),"--script",str(ROOT/"tests/gate_transition.gd"),"--",str(path)],env)
                values.append(json.loads(path.read_text()))
            a,b=values
            if (a["first_mode"]!="won" or b["first_mode"]!="won" or a["first_hp"]!=4 or b["first_hp"]!=4
                or a["first_tick"]!=b["first_tick"] or a["after_mode"]!="won" or a["model_replaced"]
                or b["after_mode"]!="play" or not b["model_replaced"] or b["after_hp"]!=4):
                raise ValueError("Before/after control does not demonstrate a new continuation")
            transition={"before":a,"after":b,"baseline_pck_sha256":hashlib.sha256(before.read_bytes()).hexdigest(),
                        "current_pck_sha256":hashlib.sha256(Path(pack or ROOT/"dist/crossing-drill.pck").read_bytes()).hexdigest(),
                        "probe_sha256":hashlib.sha256((ROOT/"tests/gate_transition.gd").read_bytes()).hexdigest(),
                        "scope":"Same real wounded escort and native F2 event against both deliveries; not OS input or human evidence."}
        output=Path(output);output.parent.mkdir(parents=True,exist_ok=True)
        output.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
        if transition:output.with_suffix(".before_after.json").write_text(json.dumps(transition,indent=2,sort_keys=True)+"\n")
        print("PASS: 67 return-gate controls, 4 complete two-stage journeys; source/PCK identical")
        return result

if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output",type=Path,required=True)
    parser.add_argument("--godot",default="godot")
    parser.add_argument("--pack",type=Path,help="Explicit comparison pack; mismatch is an error")
    parser.add_argument("--compare",type=Path)
    parser.add_argument("--baseline",type=Path,help="Preserved prior PCK; must lack the executed continuation")
    args=parser.parse_args()
    try:verify(args.output,args.godot,args.pack,args.compare,args.baseline)
    except (OSError,ValueError,KeyError,subprocess.TimeoutExpired) as error:parser.exit(1,f"FAIL: {error}\n")
