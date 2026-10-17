"""Protocol and observation-contract regressions; native execution is separate."""
from __future__ import annotations

import copy
from contextlib import redirect_stderr
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("combat_response_runner", HERE / "run.py")
runner = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(runner)


class ProtocolChecks(unittest.TestCase):
    def setUp(self):
        self.protocol = json.loads((HERE / "scenarios.json").read_text())

    def read(self, value):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "protocol.json"
            path.write_text(json.dumps(value), encoding="utf-8")
            return runner.read_protocol(path)

    def test_committed_protocol_and_coverage(self):
        p = self.read(self.protocol)
        self.assertEqual(len(p["cases"]), 28)
        self.assertEqual({c["response"] for c in p["cases"]}, {"none", "parry", "dodge_away", "dodge_inward", "seal"})
        self.assertEqual(p["repetitions"], 2)

    def test_unknown_fields_and_responses_are_errors(self):
        for modify in [lambda p: p.update(extra=True), lambda p: p["cases"][0].update(extra=True),
                       lambda p: p["cases"][0].update(response="block"),
                       lambda p: p["cases"][0].update(response={}), lambda p: p.update(schema_version=True)]:
            p = copy.deepcopy(self.protocol)
            modify(p)
            with self.assertRaises(ValueError):
                self.read(p)

    def test_nonfinite_or_unbounded_inputs_are_rejected(self):
        for key, value in [("lead_ticks", True), ("lead_ticks", 31), ("distance_px", 251),
                           ("distance_px", float("nan")), ("resolve_at_press", -1), ("echo_at_contact", 1)]:
            p = copy.deepcopy(self.protocol)
            p["cases"][0][key] = value
            with self.assertRaises(ValueError):
                self.read(p)

    def test_identity_and_runtime_bounds(self):
        for modify in [lambda p: p["cases"].append(p["cases"][0]), lambda p: p.update(repetitions=1),
                       lambda p: p.update(duration_ticks=10000), lambda p: p.update(physics_hz=120)]:
            p = copy.deepcopy(self.protocol)
            modify(p)
            with self.assertRaises(ValueError):
                self.read(p)

    def test_unicode_ids_preserved(self):
        self.protocol["cases"][0]["id"] = "defesa — início"
        self.assertEqual(self.read(self.protocol)["cases"][0]["id"], "defesa — início")


class ObservationChecks(unittest.TestCase):
    def setUp(self):
        self.protocol = {"physics_hz": 60, "cases": [{"id": "control"}], "repetitions": 2}
        self.result = {"schema_version": 1, "physics_hz": 60, "contact_tick": 52,
                       "calibration": {"damage_taken": 1}, "rows": [
                           {"id": "control", "repetition": 1, "hp": 5},
                           {"id": "control", "repetition": 2, "hp": 5}]}

    def test_matching_repetitions_accepted(self):
        runner.validate_result(self.result, self.protocol)

    def test_missing_or_reordered_observations_fail(self):
        for result in [{**self.result, "rows": self.result["rows"][:1]},
                       {**self.result, "rows": list(reversed(self.result["rows"]))}]:
            with self.assertRaises(ValueError):
                runner.validate_result(result, self.protocol)

    def test_nondeterminism_is_visible(self):
        self.result["rows"][1]["hp"] = 4
        with self.assertRaisesRegex(ValueError, "different observations"):
            runner.validate_result(self.result, self.protocol)

    def test_failed_calibration_is_visible(self):
        self.result["calibration"]["damage_taken"] = 0
        with self.assertRaisesRegex(ValueError, "calibration"):
            runner.validate_result(self.result, self.protocol)

    def test_missing_engine_is_clear_and_writes_no_result(self):
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder) / "result.json"
            error = io.StringIO()
            with redirect_stderr(error):
                self.assertEqual(runner.main(["--godot", "no-such-godot-combat-response", "--output", str(output)]), 1)
            self.assertIn("Godot executable unavailable", error.getvalue())
            self.assertFalse(output.exists())

    def test_wrong_engine_is_rejected_before_import(self):
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder) / "result.json"
            error = io.StringIO()
            with patch.object(runner.shutil, "which", return_value="/fake/godot"), \
                    patch.object(runner, "invoke", return_value="4.5.1.stable.official.fake\n") as invoked, \
                    redirect_stderr(error):
                self.assertEqual(runner.main(["--output", str(output)]), 1)
            self.assertEqual(invoked.call_count, 1)
            self.assertIn("requires Godot 4.6.3", error.getvalue())
            self.assertFalse(output.exists())

    def test_owned_native_process_has_a_real_deadline(self):
        with self.assertRaises(subprocess.TimeoutExpired):
            runner.invoke([sys.executable, "-c", "import time; time.sleep(5)"], os.environ.copy(), 0.05)


if __name__ == "__main__":
    unittest.main()
