#!/usr/bin/env python3
"""Execute a bounded native P06 response experiment using Python's standard library."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

HERE = Path(__file__).resolve().parent
LAB = HERE.parents[1]
ORIGIN = LAB / "projects/veil-arena"
MARKER = "COMBAT_RESPONSE_RESULT "


def read_protocol(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict) or type(value.get("schema_version")) is not int or value["schema_version"] != 1:
        raise ValueError("Protocol must be an object with schema_version 1.")
    if set(value) != {"schema_version", "physics_hz", "duration_ticks", "counter_tick", "repetitions", "cases"}:
        raise ValueError("Protocol has missing or unknown fields.")
    for key, low, high in [("physics_hz", 60, 60), ("duration_ticks", 90, 180),
                           ("counter_tick", 1, 89), ("repetitions", 2, 5)]:
        if type(value.get(key)) is not int or not low <= value[key] <= high:
            raise ValueError(f"{key} must be an integer in {low}–{high}.")
    cases = value.get("cases")
    if not isinstance(cases, list) or not 1 <= len(cases) <= 100:
        raise ValueError("cases must contain 1–100 controlled inputs.")
    ids = set()
    for case in cases:
        if not isinstance(case, dict) or not isinstance(case.get("id"), str) or not case["id"]:
            raise ValueError("Every case needs a nonempty string id.")
        if case["id"] in ids:
            raise ValueError("Case ids must be unique.")
        ids.add(case["id"])
        if set(case) - {"id", "response", "lead_ticks", "distance_px", "resolve_at_press", "echo_at_contact", "counter_tick"}:
            raise ValueError(f"Unknown case field in {case['id']}.")
        if not isinstance(case.get("response", "none"), str) or case.get("response", "none") not in {"none", "parry", "dodge_away", "dodge_inward", "seal"}:
            raise ValueError(f"Unknown response in {case['id']}.")
        for key, low, high in [("lead_ticks", 0, 30), ("distance_px", 45, 250),
                               ("resolve_at_press", 0, 100), ("counter_tick", -1, 89)]:
            if key in case and (type(case[key]) is not int or not low <= case[key] <= high):
                raise ValueError(f"Invalid {key} in {case['id']}.")
        if "echo_at_contact" in case and type(case["echo_at_contact"]) is not bool:
            raise ValueError("echo_at_contact must be boolean.")
    return value


def validate_result(result: dict, protocol: dict) -> None:
    if result.get("schema_version") != 1 or result.get("physics_hz") != protocol["physics_hz"]:
        raise ValueError("Unexpected native result schema or physics rate.")
    rows = result.get("rows", [])
    if len(rows) != len(protocol["cases"]) * protocol["repetitions"]:
        raise ValueError("Native result omitted experimental outcomes.")
    expected = [c["id"] for c in protocol["cases"]]
    reference = []
    for repetition in range(1, protocol["repetitions"] + 1):
        group = rows[(repetition - 1) * len(expected): repetition * len(expected)]
        if [r.get("id") for r in group] != expected or any(r.get("repetition") != repetition for r in group):
            raise ValueError("Native outcomes changed input order or identity.")
        normalized = [{k: v for k, v in r.items() if k != "repetition"} for r in group]
        if reference and normalized != reference:
            raise ValueError("Repeated native inputs produced different observations.")
        reference = normalized
    if result.get("contact_tick", 0) <= 0 or result.get("calibration", {}).get("damage_taken") != 1:
        raise ValueError("Neutral collision calibration failed.")


def fingerprint(protocol_path: Path) -> dict:
    paths = [ORIGIN / n for n in ["arena.gd", "arena.tscn", "project.godot", "sound.gd", "motion.gd", "controls.gd"]]
    paths += sorted(p for p in (ORIGIN / "media").rglob("*") if p.is_file() and p.suffix in {".png", ".wav", ".ogg", ".json"})
    return {"protocol_sha256": hashlib.sha256(protocol_path.read_bytes()).hexdigest(),
            "instrument_sha256": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in [HERE / "run.py", HERE / "probe.gd"]},
            "origin_sha256": {p.relative_to(LAB).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}}


def invoke(command: list[str], env: dict, timeout: float) -> str:
    process = subprocess.run(command, env=env, text=True, capture_output=True, timeout=timeout)
    log = process.stdout + process.stderr
    if process.returncode or "SCRIPT ERROR:" in log or "Parse Error:" in log:
        raise ValueError(f"Native process failed ({process.returncode}):\n{log[-10000:]}")
    return log


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--godot", default="godot", help="Godot 4.6.3 standard or .NET executable")
    parser.add_argument("--protocol", type=Path, default=HERE / "scenarios.json")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--compare", type=Path, help="Require exact deterministic agreement with a prior result")
    parser.add_argument("--timeout", type=float, default=120, help="Seconds allowed for each owned native process")
    args = parser.parse_args(argv)
    try:
        if not 1 <= args.timeout <= 600:
            raise ValueError("timeout must be 1–600 seconds.")
        protocol = read_protocol(args.protocol)
        executable = shutil.which(args.godot)
        if not executable:
            raise ValueError(f"Godot executable unavailable: {args.godot}")
        with tempfile.TemporaryDirectory(prefix="combat-response-") as temp:
            env = os.environ.copy()
            for key, folder in [("XDG_DATA_HOME", "data"), ("XDG_CONFIG_HOME", "config"), ("XDG_CACHE_HOME", "cache")]:
                env[key] = str(Path(temp) / folder)
            version = invoke([executable, "--version"], env, args.timeout)
            if not re.search(r"^4\.6\.3(?:\.|-)", version, re.MULTILINE):
                raise ValueError("This protocol requires Godot 4.6.3; use a separately reviewed protocol for another engine version.")
            base = [executable, "--headless", "--path", str(ORIGIN)]
            invoke(base + ["--editor", "--import", "--quit"], env, args.timeout)
            log = invoke(base + ["--script", str(HERE / "probe.gd"), "--fixed-fps", "60", "--", str(args.protocol.resolve())], env, args.timeout)
        markers = [line[len(MARKER):] for line in log.splitlines() if line.startswith(MARKER)]
        if len(markers) != 1:
            raise ValueError("Native process did not produce exactly one complete result.")
        result = json.loads(markers[0])
        validate_result(result, protocol)
        result.update(fingerprint(args.protocol))
        if args.compare and json.loads(args.compare.read_text(encoding="utf-8")) != result:
            raise ValueError("Native observations differ from comparison artifact; inspect before replacing evidence.")
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(f"Verified {len(result['rows'])} native outcomes; contact tick {result['contact_tick']}; wrote {args.output}")
        return 0
    except (OSError, ValueError, subprocess.TimeoutExpired) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
