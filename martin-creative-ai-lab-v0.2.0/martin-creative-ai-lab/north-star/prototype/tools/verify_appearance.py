#!/usr/bin/env python3
"""Execute local appearance migration, failure recovery and real process restarts."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
from verify import ROOT, invoke

EXPECTED_CHECKS = 52
CUSTOM = {"skin": 2, "hair": 2, "dye": 1}
DEFAULTS = {"skin": 0, "hair": 0, "dye": 0}
OPERATIONS = ("apply", "read", "cancel", "read", "earn", "read", "journey", "read", "defaults", "read")


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def verify(output, godot="godot", compare=None):
    engine = shutil.which(godot)
    if not engine:
        raise ValueError("Godot executable unavailable")
    with tempfile.TemporaryDirectory(prefix="appearance-continuity-") as folder:
        scratch = Path(folder)
        env = os.environ.copy()
        for name in ("CROSSING_PROFILE", "CROSSING_CONTROLS", "CROSSING_CAPTURE"):
            env.pop(name, None)
        env.update({name: str(scratch / name) for name in ("XDG_DATA_HOME", "XDG_CONFIG_HOME", "XDG_CACHE_HOME")})
        if not invoke([engine, "--version"], env).strip().startswith("4.6.3."):
            raise ValueError("Reproduction requires Godot 4.6.3")
        units, restarts = [], []
        for label, delivery in (("source", ["--path", str(ROOT)]),
                                ("pack", ["--main-pack", str(ROOT / "dist/crossing-drill.pck")])):
            base = [engine, "--headless", "--audio-driver", "Dummy", *delivery]
            target = scratch / (label + "-checks.json")
            invoke([*base, "--script", "res://tests/appearance_profile_checks.gd", "--", str(target)], env)
            unit = json.loads(target.read_text())
            if (unit["checks"] != {"passed": EXPECTED_CHECKS, "failed": 0}
                    or len(unit["labels"]) != EXPECTED_CHECKS or len(set(unit["labels"])) != EXPECTED_CHECKS):
                raise ValueError("Appearance migration/failure controls are incomplete or duplicate")
            for name, identity in unit["consumer_hashes"].items():
                if hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != identity:
                    raise ValueError("Executed source changed: " + name)
            units.append(unit)
            profile = scratch / (label + "-profile.json")
            rows = []
            for index, operation in enumerate(OPERATIONS):
                target = scratch / f"{label}-restart-{index}.json"
                invoke([*base, "--script", "res://tests/appearance_restart.gd", "--", operation, str(profile), str(target)], env)
                row = json.loads(target.read_text())
                expected = CUSTOM if index < 8 else DEFAULTS
                if (row["look"] != expected or row["profile"]["look"] != expected or row["stored"]["look"] != expected
                        or row["stored"]["schema_version"] != 2 or row["profile"]["dirty"] or row["profile"]["blocked"]):
                    raise ValueError("Applied appearance failed process continuity: " + operation)
                marks = [] if index < 4 else (["held_line"] if index < 6 else ["held_line", "drew_danger"])
                if row["profile"]["earned"] != marks or row["profile"]["equipped"] != "":
                    raise ValueError("Appearance operations changed reward ownership or wear")
                if operation in ("read", "cancel") and (not row["unchanged_bytes"] or row["mode"] != "title" or row["tick"] != 0):
                    raise ValueError("Read/cancel wrote the profile or restored a gameplay session")
                if operation == "journey":
                    obs = row["observations"]
                    if (obs["crossing_look"] != CUSTOM or obs["return_look"] != CUSTOM
                            or obs["crossing"]["mode"] != "won" or obs["return_gate"]["game"]["mode"] != "won"):
                        raise ValueError("Reloaded appearance did not survive actual two-goal play")
                rows.append(row)
            restarts.append(rows)
        if units[0] != units[1] or restarts[0] != restarts[1]:
            raise ValueError("Source/PCK appearance or restart observations differ")
        result = {"schema_version": 1, "checks": units[0]["checks"], "consumer_hashes": units[0]["consumer_hashes"],
                  "unit_observation_sha256": digest(units[0]), "restart_observation_sha256": digest(restarts[0]),
                  "restart_processes": 20, "operations_per_delivery": list(OPERATIONS),
                  "restarts": [{"operation": r["operation"], "look": r["look"], "profile": r["profile"],
                                "unchanged_bytes": r["unchanged_bytes"], "mode": r["mode"], "tick": r["tick"]} for r in restarts[0]],
                  "actual_journey": restarts[0][6]["observations"],
                  "scope": "Editable local cosmetic profile, migration/recovery, twenty real restarts and source/PCK two-goal execution; no account, saved power, power-loss or concurrent-writer guarantee."}
        if compare and result != json.loads(Path(compare).read_text()):
            raise ValueError("Appearance continuity observations changed")
        output = Path(output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
        print(f"PASS: {EXPECTED_CHECKS} appearance controls; twenty real restarts; source/PCK identical")
        return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--godot", default="godot")
    parser.add_argument("--compare", type=Path)
    args = parser.parse_args()
    try:
        verify(args.output, args.godot, args.compare)
    except (OSError, ValueError, KeyError, subprocess.TimeoutExpired) as error:
        parser.exit(1, f"FAIL: {error}\n")
