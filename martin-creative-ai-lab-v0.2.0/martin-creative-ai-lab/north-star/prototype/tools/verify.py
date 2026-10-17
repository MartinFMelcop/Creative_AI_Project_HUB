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


def verify(godot, output, compare=None):
    executable = shutil.which(godot)
    if not executable:
        raise ValueError("Godot executable unavailable")
    with tempfile.TemporaryDirectory(prefix="north-star-check-") as folder:
        scratch = Path(folder)
        env = os.environ.copy()
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
        if result.get("checks", {}).get("failed") != 0 or result.get("checks", {}).get("passed", 0) != 35:
            raise ValueError("Native checks failed or incomplete")
        if [r["mode"] for r in result["outcomes"]] != ["won", "lost", "won", "lost"]:
            raise ValueError("Completion and neutral controls are incomplete")
        for name, digest in result["consumer_hashes"].items():
            if hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != digest:
                raise ValueError("Native execution source identity differs: " + name)
        if compare and result != json.loads(Path(compare).read_text()):
            raise ValueError("Native observations differ from the recorded comparison")
        output = Path(output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
        print(f"PASS: {result['checks']['passed']} native checks; two approaches complete; neutral controls fail; source/PCK identical.")
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
