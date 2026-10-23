#!/usr/bin/env python3
"""Evaluate one attributed practice artifact with fresh pinned calibration."""

import argparse
import hashlib
import importlib.util
import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path

LAB = Path(__file__).resolve().parents[2]
SOURCE = LAB / "evaluations/chat-send-buffering/run.py"
spec = importlib.util.spec_from_file_location("origin_evaluator", SOURCE)
origin = importlib.util.module_from_spec(spec)
spec.loader.exec_module(origin)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def protocol(data):
    value = json.loads(data)
    if not isinstance(value, dict):
        raise ValueError("Protocol must be an object")
    if value.get("schema_version") != 1 or value.get("task") != origin.TASK:
        raise ValueError("Protocol schema/task mismatch")
    if not isinstance(value.get("study_id"), str) or not value["study_id"].strip():
        raise ValueError("Study identity required")
    if type(value.get("attempt")) is not int or value["attempt"] != 1:
        raise ValueError("This method records one first attempt")
    candidate = value.get("candidate", {})
    if not isinstance(candidate, dict) or any(
            not isinstance(candidate.get(key), str) or not candidate[key].strip()
            for key in ("identity", "context", "attribution")):
        raise ValueError("Candidate identity, context and attribution required")
    tools = candidate.get("tools")
    if not isinstance(tools, list) or not tools or any(
            not isinstance(tool, str) or not tool.strip() for tool in tools):
        raise ValueError("Explicit candidate tools required")
    constraints = value.get("constraints", {})
    if not isinstance(constraints, dict) or any(constraints.get(key) is not True
            for key in ("single_attempt", "no_evaluator_feedback")) or constraints.get(
                "context_separation") != "declared_not_sandboxed":
        raise ValueError("Explicit first-attempt and context limits required")
    return value


def calibration_matches(record, name):
    passed, failed, status = (15, 2, "rejected") if name == "baseline" else (17, 0, "accepted")
    expected_failures = [
        "a connected form submission waits behind an in-flight polling write",
        "a stale connected state does not retain a message for reconnect replay",
    ] if name == "baseline" else []
    return (record.get("status") == status and record.get("gate") == "behavior_and_regressions"
            and record.get("failed_checks") == expected_failures
            and record.get("counts") == {"tests": 17, "pass": passed, "fail": failed,
                                        "cancelled": 0, "skipped": 0, "todo": 0})


def decide(calibration, candidate):
    if not all(calibration.values()):
        return "inconclusive", "Calibration did not reproduce both known outcomes"
    if candidate.get("status") not in ("accepted", "rejected"):
        return "inconclusive", "Candidate execution was inconclusive"
    return candidate["status"], "Artifact decision only; no model score or human validation"


def write(path, value):
    with path.open("x", encoding="utf-8") as handle:
        json.dump(value, handle, indent=2)
        handle.write("\n")


def run(protocol_path, workspace, output):
    instrument_path = Path(__file__)
    source_hashes = {"instrument_sha256": digest(instrument_path.read_bytes()),
                     "origin_runner_sha256": digest(SOURCE.read_bytes())}
    raw = protocol_path.read_bytes()
    declared = protocol(raw)
    # Validate every support byte before freezing a copy. npm outputs are ignored.
    artifact = origin.read_submission(workspace)
    output = output.absolute()
    if output.resolve().is_relative_to(workspace.resolve()):
        raise ValueError("Output must be outside the submission")
    output.mkdir(parents=True, exist_ok=False)
    (output / "protocol.json").write_bytes(raw)
    (output / "candidate-client.js").write_bytes(artifact)
    records = {}
    calibration = {}
    with tempfile.TemporaryDirectory(prefix="ai-evaluation-") as scratch:
        for name in ("baseline", "reference", "candidate"):
            exported = Path(scratch) / name
            origin.prepare(exported)
            if name != "baseline":
                (exported / "public/client.js").write_bytes(artifact if name == "candidate"
                    else origin.git_bytes(origin.SUITE_COMMIT, "public/client.js"))
            record = origin.check(exported)
            record["run_kind"] = "independent_context_practice_artifact" if name == "candidate" else "controlled_calibration"
            records[name] = record
            if name != "candidate":
                calibration[name] = calibration_matches(record, name)
                record["calibration_matched"] = calibration[name]
            write(output / (name + ".json"), record)
    status, reason = decide(calibration, records["candidate"])
    try:
        sources_stable = (digest(instrument_path.read_bytes()) == source_hashes["instrument_sha256"]
                          and digest(SOURCE.read_bytes()) == source_hashes["origin_runner_sha256"])
    except OSError:
        sources_stable = False
    record = {
        "schema_version": 1, "method": "attributed-first-attempt-v1",
        "study_id": declared["study_id"], "task": origin.TASK,
        "started_at": records["baseline"].get("started_at"),
        "completed_at": datetime.now(timezone.utc).isoformat(),
        "status": status, "reason": reason, "calibration": calibration,
        "candidate_status": records["candidate"]["status"],
        "candidate_counts": records["candidate"].get("counts"),
        "candidate": declared["candidate"], "constraints": declared["constraints"],
        "context_limit": "Declared context separation; shared filesystem is not a sandbox. Public task/history cannot establish secrecy, unseen training data or general model performance.",
        "model_score": None, "human_validation": False,
        "identities": {"protocol_sha256": digest(raw), "client_sha256": digest(artifact),
                       **source_hashes,
                       "baseline_commit": origin.BASELINE, "suite_commit": origin.SUITE_COMMIT},
        "controls": {"export_support_verified": True, "client_frozen_before_checks": True,
                     "instrument_sources_stable": sources_stable,
                     "fresh_pinned_baseline": calibration["baseline"],
                     "fresh_pinned_reference": calibration["reference"],
                     "candidate_hash_bound": records["candidate"].get("artifact_sha256") == digest(artifact)},
        "records": {name: name + ".json" for name in records},
    }
    if not record["controls"]["candidate_hash_bound"]:
        record.update(status="inconclusive", reason="Candidate artifact identity was not established")
    if not sources_stable:
        record.update(status="inconclusive", reason="Instrument or origin source changed during execution")
    write(output / "RUN.json", record)
    return record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--protocol", type=Path, required=True)
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        record = run(args.protocol, args.workspace, args.output)
    except (OSError, ValueError) as exc:
        parser.exit(2, f"Study error: {exc}\n")
    print(json.dumps({key: record[key] for key in ("status", "reason", "candidate_counts")}, indent=2))
    return {"accepted": 0, "rejected": 1, "inconclusive": 2}[record["status"]]


if __name__ == "__main__":
    raise SystemExit(main())
