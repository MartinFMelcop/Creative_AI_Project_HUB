"""Actual missing-engine, timeout and stale delivered-consumer failure checks."""
import importlib.util
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

SPEC = importlib.util.spec_from_file_location('crossing_verify',Path(__file__).with_name('verify.py'))
runner=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(runner)

class DeliveryChecks(unittest.TestCase):
    def test_missing_engine_does_not_write_a_result(self):
        with tempfile.TemporaryDirectory() as folder:
            output=Path(folder)/'result.json'
            with self.assertRaisesRegex(ValueError,'unavailable'):
                runner.verify('no-such-crossing-engine',output)
            self.assertFalse(output.exists())

    def test_owned_process_timeout_is_real(self):
        with self.assertRaises(subprocess.TimeoutExpired):
            runner.invoke([sys.executable,'-c','import time; time.sleep(3)'],os.environ.copy(),timeout=.05)

    def test_changed_source_rejects_stale_pack(self):
        original=runner.ROOT
        with tempfile.TemporaryDirectory() as folder:
            copy=Path(folder)/'prototype'
            shutil.copytree(original,copy,ignore=shutil.ignore_patterns('.godot','__pycache__'))
            with (copy/'combat.gd').open('a') as file:file.write('\n# A changed consumer must require a rebuilt pack.\n')
            runner.ROOT=copy
            try:
                with self.assertRaisesRegex(ValueError,'Delivered PCK differs'):
                    runner.verify(os.environ.get('CROSSING_GODOT','godot'),Path(folder)/'rejected.json')
                self.assertFalse((Path(folder)/'rejected.json').exists())
            finally:runner.ROOT=original

if __name__=='__main__':unittest.main()
