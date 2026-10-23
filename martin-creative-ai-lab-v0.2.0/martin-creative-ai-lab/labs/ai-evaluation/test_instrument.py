"""Negative controls for attribution, calibration and frozen artifact ownership."""

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

spec = importlib.util.spec_from_file_location("destination", Path(__file__).with_name("run.py"))
method = importlib.util.module_from_spec(spec)
spec.loader.exec_module(method)


def declaration():
    return {"schema_version": 1, "study_id": "controlled-test", "task": "EVAL-001", "attempt": 1,
            "candidate": {"identity": "test double", "context": "test only", "tools": ["none"],
                          "attribution": "not an independent candidate"},
            "constraints": {"single_attempt": True, "no_evaluator_feedback": True,
                            "context_separation": "declared_not_sandboxed"}}


def outcome(name):
    passed = 15 if name == "baseline" else 17
    return {"status": "rejected" if name == "baseline" else "accepted",
            "failed_checks": ["a connected form submission waits behind an in-flight polling write",
                              "a stale connected state does not retain a message for reconnect replay"] if name == "baseline" else [],
            "gate": "behavior_and_regressions", "counts": {"tests": 17, "pass": passed,
            "fail": 17-passed, "cancelled": 0, "skipped": 0, "todo": 0}}


class InstrumentControls(unittest.TestCase):
    def test_missing_provenance_rejected(self):
        for key in ("identity", "context", "tools", "attribution"):
            value = declaration()
            del value["candidate"][key]
            with self.subTest(key=key), self.assertRaises(ValueError):
                method.protocol(json.dumps(value))

    def test_retry_and_false_sandbox_claim_rejected(self):
        for key, replacement in (("attempt", 2), ("attempt", True),
                                  ("constraints", {"context_separation": "sandboxed"})):
            value = declaration()
            value[key] = replacement
            with self.subTest(key=key), self.assertRaises(ValueError):
                method.protocol(json.dumps(value))

    def test_false_calibration_cannot_accept_candidate(self):
        for name in ("baseline", "reference"):
            value = outcome(name)
            value["counts"]["skipped"] = 1
            self.assertFalse(method.calibration_matches(value, name))
        self.assertEqual(method.decide({"baseline": False, "reference": True},
                                      outcome("candidate"))[0], "inconclusive")
        wrong_pair = outcome("baseline")
        wrong_pair["failed_checks"] = ["unrelated failure", "another unrelated failure"]
        self.assertFalse(method.calibration_matches(wrong_pair, "baseline"))

    def test_valid_rejection_and_environment_failure_distinct(self):
        calibration = {"baseline": True, "reference": True}
        self.assertEqual(method.decide(calibration, {"status": "rejected"})[0], "rejected")
        self.assertEqual(method.decide(calibration, {"status": "inconclusive"})[0], "inconclusive")

    def test_frozen_artifact_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            candidate = root / "submitted"
            method.origin.prepare(candidate)
            client = candidate / "public/client.js"
            client.write_bytes(b"// controlled candidate\n")
            protocol = root / "protocol.json"
            protocol.write_text(json.dumps(declaration()))
            observed = []

            def check(export):
                name = export.name
                observed.append(name)
                record = outcome(name)
                record["artifact_sha256"] = method.digest((export / "public/client.js").read_bytes())
                if name == "baseline":
                    client.write_bytes(b"// concurrent change must not replace frozen input\n")
                if name == "candidate":
                    self.assertEqual((export / "public/client.js").read_bytes(), b"// controlled candidate\n")
                return record

            output = root / "result"
            with patch.object(method.origin, "check", side_effect=check):
                record = method.run(protocol, candidate, output)
                self.assertEqual(record["status"], "accepted")
                self.assertEqual(observed, ["baseline", "reference", "candidate"])
                self.assertTrue(all(record["controls"].values()))
                self.assertIsNone(record["model_score"])
                with self.assertRaises(FileExistsError):
                    method.run(protocol, candidate, output)
            self.assertEqual((output / "candidate-client.js").read_bytes(), b"// controlled candidate\n")

    def test_support_tampering_stops_before_any_execution(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            candidate = root / "submitted"
            method.origin.prepare(candidate)
            (candidate / "server.cjs").write_text("// tampered")
            protocol = root / "protocol.json"
            protocol.write_text(json.dumps(declaration()))
            with patch.object(method.origin, "check") as check, self.assertRaises(ValueError):
                method.run(protocol, candidate, root / "result")
            check.assert_not_called()
            self.assertFalse((root / "result").exists())

    def test_concurrent_instrument_edit_cannot_bind_success_to_new_bytes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            candidate = root / "submitted"
            method.origin.prepare(candidate)
            protocol = root / "protocol.json"
            protocol.write_text(json.dumps(declaration()))
            copied_source = root / "instrument.py"
            initial = Path(method.__file__).read_bytes()
            copied_source.write_bytes(initial)

            def check(export):
                record = outcome(export.name)
                record["artifact_sha256"] = method.digest((export / "public/client.js").read_bytes())
                if export.name == "baseline":
                    copied_source.write_bytes(initial + b"\n# concurrent edit\n")
                return record

            with patch.object(method, "__file__", str(copied_source)), patch.object(
                    method.origin, "check", side_effect=check):
                record = method.run(protocol, candidate, root / "result")
            self.assertEqual(record["status"], "inconclusive")
            self.assertFalse(record["controls"]["instrument_sources_stable"])
            self.assertEqual(record["identities"]["instrument_sha256"], method.digest(initial))
            self.assertNotEqual(record["identities"]["instrument_sha256"],
                                method.digest(copied_source.read_bytes()))


if __name__ == "__main__":
    unittest.main()
