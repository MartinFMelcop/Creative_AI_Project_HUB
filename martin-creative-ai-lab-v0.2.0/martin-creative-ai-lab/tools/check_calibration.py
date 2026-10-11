#!/usr/bin/env python3
"""Require EVAL-001's known artifact outcomes; this is not a model evaluation."""

import argparse
import importlib.util
import json
import tempfile
from pathlib import Path

LAB = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "task_runner", LAB / "evaluations/chat-send-buffering/run.py")
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path, help="New directory for diagnostic records")
    args = parser.parse_args()
    # Never replace an existing run or create diagnostics inside a submission.
    try:
        args.output.mkdir(parents=True, exist_ok=False)
    except OSError as exc:
        parser.exit(2, f"Calibration output error: {exc}\n")
    success = True
    with tempfile.TemporaryDirectory(prefix="eval-calibration-") as scratch:
        for name, status, passed, failed in (
                ("baseline", "rejected", 15, 2), ("reference", "accepted", 17, 0)):
            workspace = Path(scratch) / name
            runner.prepare(workspace)
            if name == "reference":
                (workspace / "public/client.js").write_bytes(
                    runner.git_bytes(runner.SUITE_COMMIT, "public/client.js"))
            record = runner.check(workspace)
            record["run_kind"] = "controlled_calibration"
            record["calibration_artifact"] = name
            expected = {"tests": 17, "pass": passed, "fail": failed,
                        "cancelled": 0, "skipped": 0, "todo": 0}
            matched = (record["status"] == status and
                       record["gate"] == "behavior_and_regressions" and
                       record.get("counts") == expected)
            record["calibration_matched"] = matched
            with (args.output / f"{name}.json").open("x", encoding="utf-8") as output:
                json.dump(record, output, indent=2)
                output.write("\n")
            print(f"{name}: {record['status']}, {record.get('counts')}; expected match: {matched}")
            success = success and matched
    return 0 if success else 1


if __name__ == "__main__":
    raise SystemExit(main())
