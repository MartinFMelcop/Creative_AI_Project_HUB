#!/usr/bin/env python3
"""Execute the actual character-look workflow and equal-mechanics journey controls."""
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
    engine=shutil.which(godot)
    if not engine:raise ValueError("Godot executable unavailable")
    with tempfile.TemporaryDirectory(prefix="character-look-") as folder:
        scratch=Path(folder);env=os.environ.copy()
        for name in ("CROSSING_PROFILE","CROSSING_CONTROLS","CROSSING_CAPTURE"):env.pop(name,None)
        env.update({k:str(scratch/k) for k in ("XDG_DATA_HOME","XDG_CONFIG_HOME","XDG_CACHE_HOME")})
        if not invoke([engine,"--version"],env).strip().startswith("4.6.3."):raise ValueError("Reproduction requires Godot 4.6.3")
        values=[]
        for name,args in [("source",["--path",str(ROOT)]),("pack",["--main-pack",str(pack or ROOT/"dist/crossing-drill.pck")])]:
            path=scratch/(name+".json")
            invoke([engine,"--headless",*args,"--script","res://tests/look_checks.gd","--",str(path)],env)
            values.append(json.loads(path.read_text()))
        if values[0]!=values[1]:raise ValueError("Source/PCK look observations differ")
        data=values[0]
        if data["checks"]!={"passed":48,"failed":0} or len(data["journeys"])!=4:raise ValueError("Incomplete look controls")
        for name,digest in data["consumer_hashes"].items():
            if hashlib.sha256((ROOT/name).read_bytes()).hexdigest()!=digest:raise ValueError("Executed source changed: "+name)
        for i in (0,2):
            a,b=data["journeys"][i:i+2]
            if a["crossing"]!=b["crossing"] or a["return_gate"]!=b["return_gate"] or a["return_gate"]["game"]["mode"]!="won":raise ValueError("Appearance changed actual mechanics or completion")
        result={"schema_version":1,"checks":data["checks"],"consumer_hashes":data["consumer_hashes"],
                "native_observation_sha256":hashlib.sha256(json.dumps(data,sort_keys=True).encode()).hexdigest(),
                "journeys":[{"role":r["role"],"custom":r["custom"],"look":r["look"],"crossing_tick":r["crossing"]["tick"],"return_tick":r["return_gate"]["game"]["tick"],"hp":r["return_gate"]["game"]["hp"],"mode":r["return_gate"]["game"]["mode"]} for r in data["journeys"]],
                "scope":"Native editor and equal complete journeys; visual/identity quality requires actual inspection and independent people."}
        if compare and result!=json.loads(Path(compare).read_text()):raise ValueError("Look golden comparison changed")
        output=Path(output);output.parent.mkdir(parents=True,exist_ok=True);output.write_text(json.dumps(result,sort_keys=True,indent=2)+"\n")
        print("PASS: 48 look controls; four complete equal-mechanics journeys; source/PCK identical")
        return result

if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument("--output",type=Path,required=True);parser.add_argument("--godot",default="godot");parser.add_argument("--pack",type=Path);parser.add_argument("--compare",type=Path);args=parser.parse_args()
    try:verify(args.output,args.godot,args.pack,args.compare)
    except (OSError,ValueError,KeyError,subprocess.TimeoutExpired) as error:parser.exit(1,f"FAIL: {error}\n")
