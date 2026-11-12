"""Security, authority and lifecycle checks for the pinned VEA R09 adapter."""
from __future__ import annotations
import copy
import importlib.util
import tempfile
from pathlib import Path
import unittest

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('r10',HERE/'runner.py')
r10=importlib.util.module_from_spec(spec);spec.loader.exec_module(r10)

class R10Checks(unittest.TestCase):
    def test_pinned_archive(self):
        self.assertEqual(len(r10.PINNED_ARCHIVE_SHA256),64)
        self.assertEqual(len(r10.SOURCES),6)
        self.assertIn('input/EDITORIAL_DECISIONS_R08.json',r10.INPUT_FILES)
    def test_no_unsafe_output_overwrite(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaisesRegex(r10.IntegrationError,'MISSING_OR_OVERSIZED_R09_ARCHIVE'):
                r10.run(Path(td)/'missing.zip',Path(td)/'out')
    def test_wrong_archive_hash_denied(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'fake.zip';p.write_bytes(b'not the verified source')
            with self.assertRaisesRegex(r10.IntegrationError,'R09_ARCHIVE_HASH_MISMATCH'):
                r10.check_archive(p)
    def test_output_is_not_created_for_invalid_archive(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'fake.zip';p.write_bytes(b'forged')
            dst=Path(td)/'out'
            with self.assertRaises(r10.IntegrationError):r10.run(p,dst)
            self.assertFalse(dst.exists())
    def test_no_decision_promotions(self):
        self.assertTrue(all(x.endswith('.py') for x in r10.SOURCES))
        self.assertFalse(any('/output/' in x for x in r10.SOURCES))
    def test_no_external_tooling_dependency_in_adapter(self):
        # The adapter uses Python stdlib; the pinned R09 renderer owns its own dependencies.
        import ast
        tree=ast.parse((HERE/'runner.py').read_text(encoding='utf8'))
        modules={n.module for n in tree.body if isinstance(n,ast.ImportFrom)}
        self.assertNotIn('openai',modules)
        self.assertNotIn('requests',modules)

if __name__=='__main__':unittest.main()
