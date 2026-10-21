#!/usr/bin/env python3
"""Check authored fitting data in a fresh staged consumer, or verify delivery.

The Godot consumer owns validation. This tool never overwrites maintained content.
Fixed policies establish bounded execution, not balance or human understanding.
"""
import argparse
import copy
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import zipfile

from export_linux import BUNDLE, DEFAULT, ROOT, digest, source_paths, VERSION

EXECUTED_FILES = {"data/fittings.json", "fittings.gd", "combat.gd", "workshop.gd", "arena.gd",
                  "actors.gd", "character_look.gd", "tests/fittings_driver.gd", "tests/fittings_probe.gd"}


def environment(scratch):
    env = os.environ.copy()
    for name in ("CROSSING_PROFILE", "CROSSING_CONTROLS", "CROSSING_CAPTURE"):
        env.pop(name, None)
    for name in ("XDG_DATA_HOME", "XDG_CONFIG_HOME", "XDG_CACHE_HOME"):
        env[name] = str(scratch / name)
    return env


def engine_path(godot, env):
    engine = shutil.which(godot)
    if not engine:
        raise ValueError("Godot executable unavailable")
    result = subprocess.run([engine, "--version"], env=env, capture_output=True, text=True, timeout=10)
    if result.returncode or result.stdout.strip() != VERSION:
        raise ValueError("Use the pinned standard Godot 4.6.3 editor")
    return engine


def run_probe(command, env, output, expected_root):
    run = subprocess.run(command, env=env, capture_output=True, text=True, timeout=45)
    log = run.stdout + run.stderr
    if any(error in log for error in ("SCRIPT ERROR:", "Parse Error:", "ERROR:")):
        raise ValueError("Fitting consumer failed: " + log[-2000:])
    report = json.loads(Path(output).read_text())
    if set(report["consumer_hashes"]) != EXECUTED_FILES:
        raise ValueError("Incomplete executed fitting identity inventory")
    for name, sha in report["consumer_hashes"].items():
        if digest(expected_root / name) != sha:
            raise ValueError("Executed fitting source differs: " + name)
    if report["catalog_sha256"] != report["consumer_hashes"]["data/fittings.json"]:
        raise ValueError("Executed catalog identity differs")
    if report["failures"] or report["checks"]["failed"]:
        raise ValueError("Fitting execution failed: " + str(report["failures"]))
    if not report["valid"]:
        if run.returncode != 1 or report["journeys"] or not report["errors"]:
            raise ValueError("Incomplete invalid-content control")
        return report
    if run.returncode or report["errors"] or len(report["journeys"]) != len(report["items"]) * 2:
        raise ValueError("Incomplete fitting execution")
    return report


def store(output, report):
    output = Path(output)
    if output.resolve().is_relative_to(ROOT):
        raise ValueError("Write reports outside the maintained consumer")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n")


def check(catalog, output, godot="godot"):
    """Stage a candidate with unchanged code; validation and journeys use the real scene."""
    if Path(output).resolve() == Path(catalog).resolve():
        raise ValueError("A report cannot replace its input catalog")
    with tempfile.TemporaryDirectory(prefix="fitting-author-") as folder:
        scratch = Path(folder)
        env = environment(scratch)
        engine = engine_path(godot, env)
        stage = scratch / "project"
        stage.mkdir()
        for name in source_paths():
            destination = stage / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / name, destination)
        shutil.copyfile(catalog, stage / "data/fittings.json")
        raw = scratch / "report.json"
        report = run_probe([engine, "--headless", "--path", str(stage), "--script",
                            "res://tests/fittings_probe.gd", "--", str(raw)], env, raw, stage)
        store(output, report)
        return report


def observations(report):
    normalized = copy.deepcopy(report)
    normalized.pop("sources", None)
    normalized["labels"] = [label for label in normalized["labels"] if not label.startswith("Embedded identity: ")]
    normalized["checks"]["passed"] = len(normalized["labels"]) - len(normalized["failures"])
    return normalized


def verify(output, godot="godot", archive=DEFAULT, compare=None):
    from check_linux import check as check_archive
    check_archive(archive)
    with tempfile.TemporaryDirectory(prefix="fitting-delivery-") as folder:
        scratch = Path(folder)
        engine = engine_path(godot, environment(scratch))
        reports = []
        for label, selector in (("source", ["--path", str(ROOT)]),
                                ("pack", ["--main-pack", str(ROOT / "dist/crossing-drill.pck")])):
            raw = scratch / (label + ".json")
            reports.append(run_probe([engine, "--headless", *selector, "--script",
                                      "res://tests/fittings_probe.gd", "--", str(raw)],
                                     environment(scratch / label), raw, ROOT))
        with zipfile.ZipFile(archive) as package:
            package.extractall(scratch / "release")  # check_archive already enforces exact regular paths.
        binary = scratch / "release" / BUNDLE / "crossing-drill.x86_64"
        binary.chmod(0o755)
        raw = scratch / "release.json"
        release = run_probe([str(binary), "--headless", "--", "--verify-fittings", str(raw)],
                            environment(scratch / "release-profile"), raw, ROOT)
        if not release["sources"]:
            raise ValueError("Actual release source identities are missing")
        reports.append(release)
        report = observations(reports[0])
        if any(observations(other) != report for other in reports[1:]):
            raise ValueError("Authored source, PCK and actual release behavior differs")
        if not report["valid"]:
            raise ValueError("Maintained catalog is invalid")
        if compare and json.loads(Path(compare).read_text()) != report:
            raise ValueError("Fitting execution changed")
        store(output, report)
        return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="operation", required=True)
    author = sub.add_parser("check", help="Stage and execute a candidate catalog without editing the checkout")
    author.add_argument("--catalog", type=Path, default=ROOT / "data/fittings.json")
    delivery = sub.add_parser("verify", help="Require identical authored behavior in source, PCK and Linux release")
    delivery.add_argument("--archive", type=Path, default=DEFAULT)
    delivery.add_argument("--compare", type=Path)
    for command in (author, delivery):
        command.add_argument("--output", type=Path, required=True)
        command.add_argument("--godot", default="godot")
    args = parser.parse_args()
    try:
        if args.operation == "check":
            result = check(args.catalog, args.output, args.godot)
        else:
            result = verify(args.output, args.godot, args.archive, args.compare)
        print(json.dumps({"valid": result["valid"], "checks": result["checks"],
                          "journeys": len(result["journeys"]), "errors": result["errors"]}))
        raise SystemExit(0 if result["valid"] else 1)
    except (OSError, ValueError, KeyError, subprocess.SubprocessError, zipfile.BadZipFile) as error:
        parser.exit(1, "FAIL: " + str(error) + "\n")
