"""Real consumer checks for authoring, malformed content and safe rejection."""
import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from export_linux import ROOT, digest
from fittings import check, store


class FittingAuthorTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="fitting-test-")
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)
        self.catalog = json.loads((ROOT / "data/fittings.json").read_text())

    def run_candidate(self, value=None, raw=None):
        candidate = self.folder / "candidate.json"
        candidate.write_text(raw if raw is not None else json.dumps(value))
        output = self.folder / "result.json"
        before = digest(ROOT / "data/fittings.json")
        result = subprocess.run([sys.executable, str(ROOT / "tools/fittings.py"), "check",
                                 "--catalog", str(candidate), "--output", str(output),
                                 "--godot", os.environ.get("CROSSING_GODOT", "godot")],
                                capture_output=True, text=True, timeout=60)
        self.assertEqual(digest(ROOT / "data/fittings.json"), before)
        self.assertNotIn("SCRIPT ERROR:", result.stderr)
        self.assertTrue(output.exists(), result.stdout + result.stderr)
        return result, json.loads(output.read_text())

    def reject(self, value=None, raw=None):
        result, report = self.run_candidate(value, raw)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertFalse(report["valid"])
        self.assertTrue(report["errors"])
        self.assertEqual(report["journeys"], [])
        self.assertEqual(report["checks"], {"passed": 1, "failed": 0})
        self.assertIn("Invalid data blocks the actual scene and workshop", report["labels"])

    def test_new_identity_and_values_execute_without_code_changes(self):
        self.catalog["fittings"][-1].update(id="probe_weave", name="Probe weave", health=3,
                                               movement=1.1, recovery=22)
        result, report = self.run_candidate(self.catalog)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(report["valid"])
        self.assertEqual(len(report["journeys"]), 8)
        authored = [j for j in report["journeys"] if j["id"] == "probe_weave"]
        self.assertEqual({j["role"] for j in authored}, {"Guardian", "Duelist"})
        for journey in authored:
            self.assertEqual(journey["escort"]["health_limit"], 3)
            self.assertEqual(journey["return_gate"]["movement"], 1.1)
            self.assertEqual(journey["return_gate"]["recovery"], 22)
            self.assertEqual(journey["return_gate"]["mode"], "won")

    def test_malformed_json(self):
        self.reject(raw="{broken")

    def test_non_object(self):
        self.reject([])

    def test_unsupported_schema(self):
        self.catalog["schema_version"] = 2
        self.reject(self.catalog)

    def test_unknown_fields(self):
        self.catalog["fittings"][-1]["script"] = "untrusted.gd"
        self.reject(self.catalog)

    def test_duplicate_ids(self):
        self.catalog["fittings"][-1]["id"] = "trail"
        self.reject(self.catalog)

    def test_unsafe_identifier(self):
        self.catalog["fittings"][-1]["id"] = "../other"
        self.reject(self.catalog)

    def test_structural_types_never_escape_as_script_errors(self):
        original = copy.deepcopy(self.catalog)
        for field, value in (("id", []), ("health", {}), ("visual", []), ("station", {})):
            with self.subTest(field=field):
                candidate = copy.deepcopy(original)
                candidate["fittings"][0][field] = value
                self.reject(candidate)

    def test_invalid_numeric_values(self):
        original = copy.deepcopy(self.catalog)
        for field, value in (("health", True), ("health", 4.5), ("movement", 0),
                             ("recovery", -1), ("recovery", float("nan"))):
            with self.subTest(field=field, value=value):
                candidate = copy.deepcopy(original)
                candidate["fittings"][-1][field] = value
                self.reject(candidate)

    def test_invalid_visual(self):
        self.catalog["fittings"][-1]["visual"] = "arbitrary-resource"
        self.reject(self.catalog)

    def test_overlapping_stations(self):
        self.catalog["fittings"][-1]["station"] = [330, 420]
        self.reject(self.catalog)

    def test_unreachable_station(self):
        self.catalog["fittings"][-1]["station"] = [575, 100]
        self.reject(self.catalog)

    def test_multiline_name(self):
        self.catalog["fittings"][-1]["name"] = "Field\nsash"
        self.reject(self.catalog)

    def test_missing_standard(self):
        self.catalog["fittings"] = self.catalog["fittings"][1:]
        self.reject(self.catalog)

    def test_changed_unfitted_baseline(self):
        self.catalog["fittings"][0]["health"] = 7
        self.reject(self.catalog)

    def test_oversized_content(self):
        self.reject(raw=json.dumps(self.catalog) + " " * 16384)

    def test_report_cannot_overwrite_input_or_consumer(self):
        candidate = self.folder / "input.json"
        candidate.write_text(json.dumps(self.catalog))
        before = candidate.read_bytes()
        with self.assertRaisesRegex(ValueError, "replace its input"):
            check(candidate, candidate)
        self.assertEqual(candidate.read_bytes(), before)
        with self.assertRaisesRegex(ValueError, "outside the maintained consumer"):
            store(ROOT / "data/fittings.json", {})


if __name__ == "__main__":
    unittest.main()
