#!/usr/bin/env python3
"""Bounded native source/PCK verification. No remote services or third-party packages."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def invoke(command, env, timeout=60):
    process = subprocess.run(command, env=env, capture_output=True, text=True, timeout=timeout)
    log = process.stdout + process.stderr
    if process.returncode or any(error in log for error in ("SCRIPT ERROR:", "Parse Error:", "ERROR:")):
        raise ValueError(f"Native check failed ({process.returncode}): {log[-3000:]}")
    return log


def continuity(executable, scratch, env, packed):
    label = "pack" if packed else "source"
    profile = scratch / (label + "-profile.json")
    observations = []
    base = [executable, "--headless"]
    base += ["--main-pack", str(ROOT / "dist/crossing-drill.pck")] if packed else ["--path", str(ROOT)]
    for index, operation in enumerate(("earn", "read", "remove", "read")):
        output = scratch / f"{label}-restart-{index}.json"
        invoke(base + ["--script", "res://tests/keepsake_restart.gd", "--", operation, str(profile), str(output)], env)
        report = json.loads(output.read_text())
        expected = "drew_danger" if index < 2 else ""
        state = report["profile"]
        if (state["earned"] != ["held_line", "drew_danger"] or state["equipped"] != expected
                or state["dirty"] or state["blocked"]):
            raise ValueError("Restart failed to retain earned marks or explicit equipment choice")
        if operation != "earn" and (report["game"]["mode"] != "title" or report["game"]["tick"] != 0):
            raise ValueError("A profile restart must not restore a combat session")
        observations.append(report)
    return observations


def control_continuity(executable, scratch, env, packed, defaults):
    label = "controls-pack" if packed else "controls-source"
    profile = scratch / (label + ".json")
    observations = []
    base = [executable, "--headless"]
    base += ["--main-pack", str(ROOT / "dist/crossing-drill.pck")] if packed else ["--path", str(ROOT)]
    for index, operation in enumerate(("apply", "read", "restore", "read")):
        output = scratch / f"{label}-{index}.json"
        invoke(base + ["--script", "res://tests/controls_restart.gd", "--", operation, str(profile), str(output)], env)
        report = json.loads(output.read_text())
        expected = dict(defaults)
        if index < 2:
            expected.update(strike=71, skill=72, step=66, interact=70, move_up=73)
        state = report["profile"]
        if state["keys"] != expected or state["dirty"] or state["blocked"]:
            raise ValueError("Control restart failed to retain applied/restored bindings")
        if report["game"]["mode"] != "title" or report["game"]["tick"] != 0:
            raise ValueError("Editing controls must not start or advance a crossing")
        observations.append(report)
    return observations


def verify(godot, output, compare=None):
    executable = shutil.which(godot)
    if not executable:
        raise ValueError("Godot executable unavailable")
    with tempfile.TemporaryDirectory(prefix="north-star-check-") as folder:
        scratch = Path(folder)
        env = os.environ.copy()
        env.pop("CROSSING_PROFILE", None)
        env.pop("CROSSING_CAPTURE", None)
        env.pop("CROSSING_CONTROLS", None)
        env.update({key: str(scratch / key) for key in ("XDG_DATA_HOME", "XDG_CONFIG_HOME", "XDG_CACHE_HOME")})
        version = invoke([executable, "--version"], env).strip()
        if not version.startswith("4.6.3."):
            raise ValueError("Reproduction requires Godot 4.6.3; final MMO engine remains undecided")
        # This project uses source scripts/built-in fonts, with no import-dependent media.
        source = scratch / "source.json"
        packed = scratch / "pack.json"
        invoke([executable, "--headless", "--path", str(ROOT), "--script", "tests/run_checks.gd", "--", str(source)], env)
        invoke([executable, "--headless", "--main-pack", str(ROOT / "dist/crossing-drill.pck"),
                "--script", "res://tests/run_checks.gd", "--", str(packed)], env)
        result = json.loads(source.read_text())
        if result != json.loads(packed.read_text()):
            raise ValueError("Delivered PCK differs from current source observations or embedded source hashes")
        if result.get("checks", {}).get("failed") != 0 or result.get("checks", {}).get("passed", 0) != 208:
            raise ValueError("Native checks failed or incomplete")
        if [r["mode"] for r in result["outcomes"]] != ["won", "lost", "won", "lost"]:
            raise ValueError("Completion and neutral controls are incomplete")
        if [r["role"] for r in result["rehearsals"]] != ["Guardian", "Duelist"] or any(
                len(r["results"]) != 3 or [v["stage"] for v in r["results"]] != [0, 1, 2]
                or not all(v["passed"] for v in r["results"]) for r in result["rehearsals"]):
            raise ValueError("Rehearsal responses are incomplete")
        if [r["role"] for r in result["errands"]] != ["Guardian", "Duelist"] or any(
                r["direct"]["combat"]["mode"] != "won" or r["recovered"]["combat"]["mode"] != "won"
                or r["direct"]["errand"]["state"] != "available"
                or r["recovered"]["errand"]["state"] != "delivered" for r in result["errands"]):
            raise ValueError("Actual escort/recovery alternatives are incomplete")
        for name, digest in result["consumer_hashes"].items():
            if hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != digest:
                raise ValueError("Native execution source identity differs: " + name)
        result["continuity"] = continuity(executable, scratch, env, False)
        if result["continuity"] != continuity(executable, scratch, env, True):
            raise ValueError("Source/PCK restart observations differ")
        defaults = result["controls"]["restored_profile"]["keys"]
        result["control_continuity"] = control_continuity(executable, scratch, env, False, defaults)
        if result["control_continuity"] != control_continuity(executable, scratch, env, True, defaults):
            raise ValueError("Source/PCK control restart observations differ")
        if compare and result != json.loads(Path(compare).read_text()):
            raise ValueError("Native observations differ from the recorded comparison")
        output = Path(output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
        print(f"PASS: {result['checks']['passed']} native checks; source/PCK identical; both approach routes complete; sixteen restart processes preserve keepsake/control choices.")
        return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--godot", default="godot")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--compare", type=Path, help="Require exact recorded observations and code identities")
    args = parser.parse_args()
    try:
        verify(args.godot, args.output, args.compare)
    except (OSError, ValueError, KeyError, subprocess.TimeoutExpired) as error:
        parser.exit(1, f"FAIL: {error}\n")


if __name__ == "__main__":
    main()
