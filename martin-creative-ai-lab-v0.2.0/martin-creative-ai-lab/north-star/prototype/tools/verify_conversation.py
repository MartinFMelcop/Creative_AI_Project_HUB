#!/usr/bin/env python3
"""Execute optional courier conversation and matched complete source/PCK journeys."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
from verify import ROOT, invoke

EXPECTED_CHECKS = 110


def verify(output, godot="godot", pack=None, compare=None):
    executable = shutil.which(godot)
    if not executable:
        raise ValueError("Godot executable unavailable")
    with tempfile.TemporaryDirectory(prefix="courier-conversation-") as folder:
        scratch = Path(folder)
        env = os.environ.copy()
        for name in ("CROSSING_PROFILE", "CROSSING_CONTROLS", "CROSSING_CAPTURE"):
            env.pop(name, None)
        env.update({name: str(scratch / name) for name in ("XDG_DATA_HOME", "XDG_CONFIG_HOME", "XDG_CACHE_HOME")})
        if not invoke([executable, "--version"], env).strip().startswith("4.6.3."):
            raise ValueError("Reproduction requires Godot 4.6.3")
        reports = []
        for label, args in [("source", ["--path", str(ROOT)]),
                            ("pack", ["--main-pack", str(pack or ROOT / "dist/crossing-drill.pck")])]:
            target = scratch / (label + ".json")
            invoke([executable, "--headless", *args, "--script", "res://tests/conversation_checks.gd", "--", str(target)], env)
            reports.append(json.loads(target.read_text()))
        if reports[0] != reports[1]:
            raise ValueError("Source/PCK conversation observations differ")
        data = reports[0]
        if (data["checks"] != {"passed": EXPECTED_CHECKS, "failed": 0}
                or data["checks"]["passed"] != len(data["assertions"])
                or len(data["assertions"]) != len(set(data["assertions"]))):
            raise ValueError("Failed or duplicate conversation controls")
        expected = [(role, choice) for role in ("Guardian", "Duelist") for choice in ("", "heal", "brace", "keep")]
        actual = [(row["role"], row["choice"]) for row in data["journeys"]]
        if actual != expected or any(row["return_gate"]["game"]["mode"] != "won" for row in data["journeys"]):
            raise ValueError("Missing complete role/aid control journeys")
        for name, digest in data["consumer_hashes"].items():
            if hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != digest:
                raise ValueError("Executed source changed: " + name)
        for start in (0, 4):
            ordinary, heal, brace, keep = data["journeys"][start:start + 4]
            if any(row["crossing"] != ordinary["crossing"] for row in (heal, brace, keep)):
                raise ValueError("Conversation comparison did not hold actual escort constant")
            if (keep["entry"] != ordinary["entry"] or keep["return_gate"] != ordinary["return_gate"]
                    or heal["entry"]["game"]["hp"] != ordinary["entry"]["game"]["hp"] + 1
                    or brace["entry"]["game"]["cargo"] != ordinary["entry"]["game"]["cargo"] + 1):
                raise ValueError("Executed aid consequences differ from their bounded contract")
        result = {
            "schema_version": 1,
            "checks": data["checks"],
            "consumer_hashes": data["consumer_hashes"],
            "assertion_labels_sha256": hashlib.sha256(json.dumps(data["assertions"], sort_keys=True).encode()).hexdigest(),
            "native_observation_sha256": hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest(),
            "journeys": [{
                "role": row["role"], "choice": row["choice"], "crossing_tick": row["crossing"]["tick"],
                "arrival_hp": row["crossing"]["hp"], "prepared_hp": row["entry"]["game"]["hp"],
                "prepared_winch": row["entry"]["game"]["cargo"], "return_tick": row["return_gate"]["game"]["tick"],
                "hp": row["return_gate"]["game"]["hp"], "winch": row["return_gate"]["game"]["cargo"],
                "mode": row["return_gate"]["game"]["mode"], "conversation": row["conversation"],
            } for row in data["journeys"]],
            "scope": "Eight matched native two-goal journeys and actual conversation keys; not OS input, participant comprehension, preference or narrative quality validation.",
        }
        if compare and result != json.loads(Path(compare).read_text()):
            raise ValueError("Conversation golden comparison changed")
        output = Path(output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
        print(f"PASS: {data['checks']['passed']} conversation controls; eight complete matched journeys; source/PCK identical")
        return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--godot", default="godot")
    parser.add_argument("--pack", type=Path, help="Explicit comparison pack; stale or mismatched delivery is an error")
    parser.add_argument("--compare", type=Path)
    args = parser.parse_args()
    try:
        verify(args.output, args.godot, args.pack, args.compare)
    except (OSError, ValueError, KeyError, subprocess.TimeoutExpired) as error:
        parser.exit(1, f"FAIL: {error}\n")
