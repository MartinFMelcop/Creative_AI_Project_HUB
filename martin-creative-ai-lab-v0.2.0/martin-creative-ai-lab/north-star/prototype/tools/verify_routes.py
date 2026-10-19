#!/usr/bin/env python3
"""Execute actual source/PCK route commitment and cover contracts; keep compact evidence."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
from verify import ROOT, invoke

def verify(output, godot="godot", pack=None, compare=None):
    executable=shutil.which(godot)
    if not executable:raise ValueError("Godot executable unavailable")
    with tempfile.TemporaryDirectory(prefix="north-star-routes-") as folder:
        scratch=Path(folder);env=os.environ.copy()
        for name in ("CROSSING_PROFILE","CROSSING_CONTROLS","CROSSING_CAPTURE"):env.pop(name,None)
        env.update({k:str(scratch/k) for k in ("XDG_DATA_HOME","XDG_CONFIG_HOME","XDG_CACHE_HOME")})
        if not invoke([executable,"--version"],env).strip().startswith("4.6.3."):
            raise ValueError("Reproduction requires Godot 4.6.3")
        reports=[]
        for name,args in [("source",["--path",str(ROOT)]),("pack",["--main-pack",str(pack or ROOT/"dist/crossing-drill.pck")])]:
            report=scratch/(name+".json")
            invoke([executable,"--headless",*args,"--script","res://tests/route_checks.gd","--",str(report)],env)
            reports.append(json.loads(report.read_text()))
        if reports[0]!=reports[1]:raise ValueError("Source/PCK route observations differ")
        data=reports[0]
        if data["checks"]!={"passed":49,"failed":0}:raise ValueError("Incomplete or failed route controls")
        if len(data["routes"])!=4 or any(r["combat"]["mode"]!="won" for r in data["routes"]):
            raise ValueError("Missing complete route alternatives")
        for name,digest in data["consumer_hashes"].items():
            if hashlib.sha256((ROOT/name).read_bytes()).hexdigest()!=digest:raise ValueError("Changed executed source: "+name)
        # Full native traces are compared above; retain outcomes and trace identities only.
        raw=json.dumps(data,ensure_ascii=False,sort_keys=True).encode()
        result={"schema_version":1,"checks":data["checks"],"consumer_hashes":data["consumer_hashes"],
                "native_observation_sha256":hashlib.sha256(raw).hexdigest(),"routes":[
                    {"role":r["role"],"choice":r["choice"],"mode":r["combat"]["mode"],
                     "tick":r["combat"]["tick"],"hp":r["combat"]["hp"],"cargo":r["combat"]["cargo"],
                     "covered_bolts":r["route"]["covered_bolts"],"visited_upper":r["visited_upper"]} for r in data["routes"]],
                "scope":"Fixed complete policies and native scene controls; partial geometric cover, not invulnerability, participants or general balance."}
        if compare and result!=json.loads(Path(compare).read_text()):raise ValueError("Route comparison changed")
        output=Path(output);output.parent.mkdir(parents=True,exist_ok=True)
        output.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
        print("PASS: 49 route controls, 4 complete alternative routes; source/PCK identical")
        return result

if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output",type=Path,required=True)
    parser.add_argument("--godot",default="godot")
    parser.add_argument("--pack",type=Path,help="Explicit comparison pack; mismatch is an error")
    parser.add_argument("--compare",type=Path)
    args=parser.parse_args()
    try:verify(args.output,args.godot,args.pack,args.compare)
    except (OSError,ValueError,KeyError,subprocess.TimeoutExpired) as error:parser.exit(1,f"FAIL: {error}\n")
