"""Actual failure controls: missing inputs and a baseline already containing shutdown."""
import importlib.util
import os
from pathlib import Path
import tempfile
import unittest

SPEC = importlib.util.spec_from_file_location('resolution_verify', Path(__file__).with_name('verify_resolution.py'))
runner = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(runner)


class ResolutionVerificationTests(unittest.TestCase):
    def test_missing_engine(self):
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder) / 'result.json'
            with self.assertRaisesRegex(ValueError, 'unavailable'):
                runner.verify('no-such-resolution-engine', runner.ROOT / 'dist/crossing-drill.pck', output)
            self.assertFalse(output.exists())

    def test_missing_baseline(self):
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder) / 'result.json'
            with self.assertRaisesRegex(ValueError, 'Baseline PCK unavailable'):
                runner.verify(os.environ.get('CROSSING_GODOT', 'godot'), Path(folder) / 'missing.pck', output)
            self.assertFalse(output.exists())

    def test_current_feature_is_not_a_valid_before_control(self):
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder) / 'result.json'
            # Execute the current PCK as the alleged earlier control. Identical
            # completion is not evidence of an improvement; require actual rejection.
            with self.assertRaisesRegex(ValueError, 'Shutdown or its bounded consequence is missing'):
                runner.verify(os.environ.get('CROSSING_GODOT', 'godot'), runner.ROOT / 'dist/crossing-drill.pck', output)
            self.assertFalse(output.exists())


if __name__ == '__main__':
    unittest.main()
