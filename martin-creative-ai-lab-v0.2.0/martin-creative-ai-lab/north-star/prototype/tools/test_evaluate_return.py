"""Real native failures and report boundaries for the encounter instrument."""
import copy
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

import evaluate_return as r

SMALL = {"schema_version": 1, "approaches": ["steady"], "outfits": ["standard"],
         "aids": ["none"], "strategies": ["ground"], "delay_ticks": [0], "repetitions": 2, "max_ticks": 3600}


class EnvelopeChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.storage = tempfile.TemporaryDirectory(prefix="envelope-tests-")
        cls.folder = Path(cls.storage.name)
        cls.engine = os.environ.get("CROSSING_GODOT", "godot")
        config = cls.folder / "small.json";config.write_text(json.dumps(SMALL))
        cls.config = config
        env = os.environ.copy()
        for name in ("CROSSING_PROFILE", "CROSSING_CONTROLS", "CROSSING_CAPTURE"):env.pop(name, None)
        env.update({k: str(cls.folder / k) for k in ("XDG_DATA_HOME", "XDG_CONFIG_HOME", "XDG_CACHE_HOME")})
        path = cls.folder / "raw.json"
        r.invoke([cls.engine, "--headless", "--path", str(r.ROOT), "--script", str(r.PROBE), "--", str(config), str(path)], env, 30)
        cls.raw = r.read_json(path)

    @classmethod
    def tearDownClass(cls):
        cls.storage.cleanup()

    def test_actual_source_and_pack_repeat(self):
        result = r.evaluate(self.folder / "valid.json", self.config, self.engine, report=self.folder / "valid.md")
        self.assertEqual(result["checks"], {"passed": 9, "failed": 0})
        self.assertEqual(result["outcomes"][0]["mode"], "won")
        self.assertEqual(result["outcomes"][0]["integrity"], 1)
        self.assertIn("W 4 / 1", (self.folder / "valid.md").read_text())

    def test_invalid_axes_types_and_bounds(self):
        changes = [("schema_version", True), ("approaches", ["typo"]), ("aids", []), ("outfits", ["../combat"]),
                   ("strategies", ["work", "work"]), ("delay_ticks", [True]), ("delay_ticks", [1.0]),
                   ("delay_ticks", [30, 0]), ("delay_ticks", [601]), ("repetitions", 1), ("max_ticks", 59),
                   ("max_ticks", 7201), ("unexpected", "field")]
        for key, value in changes:
            with self.subTest(key=key, value=value):
                data = copy.deepcopy(SMALL);data[key] = value
                path = self.folder / "bad.json";path.write_text(json.dumps(data))
                with self.assertRaises(ValueError):r.protocol(path)
        data = copy.deepcopy(SMALL);data.update(delay_ticks=[60], max_ticks=60)
        path.write_text(json.dumps(data))
        with self.assertRaisesRegex(ValueError, "leave observation"):r.protocol(path)
        data = r.read_json(r.PROTOCOL);data["delay_ticks"] = list(range(6))
        path.write_text(json.dumps(data))
        with self.assertRaisesRegex(ValueError, "600 conditions"):r.protocol(path)

    def test_duplicate_and_overflow_json(self):
        path = self.folder / "invalid.json"
        for value in ('{"schema_version":1,"schema_version":1}', '{"value":NaN}', '{"value":1e999}'):
            path.write_text(value)
            with self.assertRaises(ValueError):r.read_json(path)

    def test_missing_engine_preserves_outputs(self):
        output = self.folder / "keep.json";report = self.folder / "keep.md"
        output.write_text("keep JSON");report.write_text("keep Markdown")
        with self.assertRaisesRegex(ValueError, "unavailable"):
            r.evaluate(output, self.config, "no-such-envelope-engine", report=report)
        self.assertEqual(output.read_text(), "keep JSON");self.assertEqual(report.read_text(), "keep Markdown")

    def test_compare_failure_preserves_outputs(self):
        output = self.folder / "compare-output.json";output.write_text("keep")
        comparison = self.folder / "comparison.json";comparison.write_text("{}")
        with self.assertRaisesRegex(ValueError, "comparison changed"):
            r.evaluate(output, self.config, self.engine, compare=comparison)
        self.assertEqual(output.read_text(), "keep")

    def test_inputs_cannot_be_output(self):
        before = self.config.read_bytes()
        with self.assertRaisesRegex(ValueError, "replace prototype inputs"):
            r.evaluate(self.config, self.config, self.engine)
        self.assertEqual(self.config.read_bytes(), before)
        output = self.folder / "same.json"
        with self.assertRaisesRegex(ValueError, "outputs must differ"):
            r.evaluate(output, self.config, self.engine, report=output)

    def test_missing_matrix_or_repeat_is_rejected(self):
        for change in (lambda d: d["cases"].clear(), lambda d: d["cases"][0]["takes"].pop()):
            raw = copy.deepcopy(self.raw);change(raw)
            with self.assertRaises(ValueError):r.validate(raw, SMALL)

    def test_nonrepeatable_observation_is_rejected(self):
        raw = copy.deepcopy(self.raw);raw["cases"][0]["takes"][1]["energy"] = 99
        raw["cases"][0]["takes"][1]["min_energy"] = 99
        with self.assertRaisesRegex(ValueError, "Nonrepeatable"):r.validate(raw, SMALL)

    def test_false_success_without_survival_is_rejected(self):
        raw = copy.deepcopy(self.raw);raw["cases"][0]["takes"][0]["hp"] = 0
        with self.assertRaisesRegex(ValueError, "survival"):r.validate(raw, SMALL)

    def test_fabricated_identity_is_rejected(self):
        raw = copy.deepcopy(self.raw);raw["consumer_hashes"]["combat.gd"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "identity mismatch"):r.validate(raw, SMALL)

    def test_changed_source_rejects_unchanged_pack(self):
        original = r.ROOT
        with tempfile.TemporaryDirectory() as folder:
            staged = Path(folder) / "prototype"
            for name in (*r.CONSUMERS, "project.godot"):
                target = staged / name;target.parent.mkdir(parents=True, exist_ok=True);shutil.copyfile(original / name, target)
            with (staged / "combat.gd").open("a") as stream:stream.write("\n# Identity mutation, same behavior.\n")
            r.ROOT = staged
            output = self.folder / "stale.json"
            try:
                with self.assertRaisesRegex(ValueError, "identity mismatch"):
                    r.evaluate(output, self.config, self.engine, pack=original / "dist/crossing-drill.pck")
                self.assertFalse(output.exists())
            finally:r.ROOT = original

    def test_budget_and_policy_loss_are_retained(self):
        for label, change, expected in [("short", {"max_ticks": 60}, "play"), ("late", {"delay_ticks": [120]}, "lost")]:
            data = copy.deepcopy(SMALL);data.update(change)
            path = self.folder / (label + ".json");path.write_text(json.dumps(data))
            result = r.evaluate(self.folder / (label + "-result.json"), path, self.engine)
            self.assertEqual(result["outcomes"][0]["mode"], expected)

    def test_broken_policy_fails_positive_control(self):
        original = r.PROBE
        probe = self.folder / "broken.gd"
        probe.write_text(original.read_text().replace('"interact":offset.length()<=20', '"interact":false'))
        r.PROBE = probe
        try:
            output = self.folder / "broken.json"
            with self.assertRaisesRegex(ValueError, "control failures"):
                r.evaluate(output, self.config, self.engine)
            self.assertFalse(output.exists())
        finally:r.PROBE = original

    def test_concurrent_input_edit_preserves_existing_result(self):
        configuration = self.folder / "concurrent.json";configuration.write_text(json.dumps(SMALL))
        output = self.folder / "concurrent-result.json";output.write_text("keep")
        original = r.invoke
        def edit_after_pack(command, env, timeout):
            result = original(command, env, timeout)
            if "--main-pack" in command:configuration.write_text(configuration.read_text() + "\n")
            return result
        r.invoke = edit_after_pack
        try:
            with self.assertRaisesRegex(ValueError, "Inputs changed during execution"):
                r.evaluate(output, configuration, self.engine)
            self.assertEqual(output.read_text(), "keep")
        finally:r.invoke = original

    def test_real_timeout_and_script_error(self):
        with self.assertRaises(subprocess.TimeoutExpired):
            r.invoke([sys.executable, "-c", "import time; time.sleep(3)"], os.environ.copy(), .05)
        with self.assertRaisesRegex(ValueError, "Native instrument failed"):
            r.invoke([sys.executable, "-c", "print('SCRIPT ERROR: injected')"], os.environ.copy(), 5)


if __name__ == "__main__":unittest.main()
