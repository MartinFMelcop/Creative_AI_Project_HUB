#!/usr/bin/env python3
"""Execute the same grounding controls and complete adventures in three deliveries."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import zipfile
from verify import ROOT, invoke
from check_linux import check
from export_linux import DEFAULT, BUNDLE

def verify(output, godot="godot", archive=DEFAULT, compare=None, baseline=None):
    executable=shutil.which(godot)
    if not executable:raise ValueError("Godot unavailable")
    check(archive)
    with tempfile.TemporaryDirectory(prefix="grounding-") as folder:
        scratch=Path(folder);env=os.environ.copy()
        for key in ("CROSSING_PROFILE","CROSSING_CONTROLS","CROSSING_CAPTURE"):env.pop(key,None)
        if not invoke([executable,"--version"],env).strip().startswith("4.6.3."):raise ValueError("Godot 4.6.3 required")
        with zipfile.ZipFile(archive) as bundle:bundle.extractall(scratch/"release")
        player=scratch/"release"/BUNDLE/"crossing-drill.x86_64";player.chmod(0o755)
        reports=[]
        for name,command in [("source",[executable,"--path",str(ROOT)]),
                             ("pack",[executable,"--main-pack",str(ROOT/"dist/crossing-drill.pck")]),
                             ("release",[str(player)])]:
            env.update({k:str(scratch/name/k) for k in ("XDG_DATA_HOME","XDG_CONFIG_HOME","XDG_CACHE_HOME")})
            path=scratch/(name+".json")
            invoke([*command,"--headless","--","--verify-grounding",str(path)],env)
            report=json.loads(path.read_text())
            if report["checks"]!={"passed":56,"failed":0} or len(report["journeys"])!=8:raise ValueError("Incomplete grounding controls")
            for source,digest in report["consumer_hashes"].items():
                if hashlib.sha256((ROOT/source).read_bytes()).hexdigest()!=digest:raise ValueError("Executed source mismatch: "+source)
            reports.append(report)
        if any(value!=reports[0] for value in reports[1:]):raise ValueError("Source/PCK/release grounding observations differ")
        report=reports[0]
        result={"schema_version":1,"checks":report["checks"],"consumer_hashes":report["consumer_hashes"],"labels":report["labels"],
                "native_observation_sha256":hashlib.sha256(json.dumps(report,sort_keys=True).encode()).hexdigest(),
                "journeys":[{"role":v["role"],"outfit":v["outfit"],"entry_hp":v["entry_hp"],
                    "hp":v["return_gate"]["game"]["hp"],"winch":v["return_gate"]["game"]["cargo"],
                    "mode":v["return_gate"]["game"]["mode"],"tick":v["return_gate"]["game"]["tick"],
                    "grounded":v["return_gate"]["grounded"],"counters":v["return_gate"]["game"]["counters"]["counters"]} for v in report["journeys"]],
                "scope":"Fixed policies in actual scene, source/PCK/official Linux release. No physical device, independent player, balance or final canon validation."}
        if compare and result!=json.loads(Path(compare).read_text()):raise ValueError("Grounding comparison changed")
        output=Path(output);output.parent.mkdir(parents=True,exist_ok=True)
        output.write_text(json.dumps(result,sort_keys=True,indent=2)+"\n")
        if baseline:
            values=[]
            for name,pack in [("before",Path(baseline)),("after",ROOT/"dist/crossing-drill.pck")]:
                path=scratch/(name+"-transition.json")
                invoke([executable,"--headless","--main-pack",str(pack),"--script",str(ROOT/"tests/grounding_transition.gd"),"--",str(path)],env)
                values.append(json.loads(path.read_text()))
            expected={"integrity":2,"ward_disabled":False,"counters":0,"mode":"play","raised":[False,False]}
            if values[0]!=expected or values[1]!={**expected,"integrity":1,"ward_disabled":True}:raise ValueError("Matched negative/positive action control failed")
            output.with_suffix(".before_after.json").write_text(json.dumps({"before":values[0],"after":values[1],
                "baseline_pck_sha256":hashlib.sha256(Path(baseline).read_bytes()).hexdigest(),
                "probe_sha256":hashlib.sha256((ROOT/"tests/grounding_transition.gd").read_bytes()).hexdigest(),
                "scope":"Same position, starting integrity, timed interaction and runtime; prior published delivery as negative control."},indent=2)+"\n")
    print("PASS: 56 grounding controls and 8 two-goal adventures; source/PCK/release identical")
    return result

if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output",type=Path,required=True);parser.add_argument("--godot",default="godot")
    parser.add_argument("--archive",type=Path,default=DEFAULT);parser.add_argument("--compare",type=Path);parser.add_argument("--baseline",type=Path)
    args=parser.parse_args()
    try:verify(args.output,args.godot,args.archive,args.compare,args.baseline)
    except (OSError,ValueError,KeyError,subprocess.SubprocessError,zipfile.BadZipFile) as error:parser.exit(1,f"FAIL: {error}\n")
