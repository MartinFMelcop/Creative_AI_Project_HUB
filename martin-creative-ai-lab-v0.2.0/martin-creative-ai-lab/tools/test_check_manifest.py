"""Manifest acceptance checks using real nested Git checkout fixtures."""

import hashlib
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from check_manifest import MANIFEST, check

TOOL = Path(__file__).with_name("check_manifest.py")


class ManifestTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.repo = Path(temporary.name)
        self.root = self.repo / "wrapper/lab"
        self.root.mkdir(parents=True)
        self.git("init", "--quiet")
        (self.repo / ".gitignore").write_text("node_modules/\n__pycache__/\n")
        (self.repo / "outside.md").write_text("Outside the lab's manifest scope.\n")
        (self.root / "scene.py").write_bytes(b"print('scene')\n")
        (self.root / "docs").mkdir()
        (self.root / "docs/a b.md").write_text("A maintained untracked document.\n")
        (self.root / "node_modules").mkdir()
        (self.root / "node_modules/cache.txt").write_text("Ignored installation output.\n")
        self.git("add", ".gitignore", "outside.md", "wrapper/lab/scene.py")
        self.names = ["docs/a b.md", "scene.py"]
        self.write_manifest()

    def git(self, *args):
        return subprocess.run(["git", "-C", str(self.repo), *args], check=True, capture_output=True)

    def write_manifest(self, names=None):
        names = self.names if names is None else names
        lines = [hashlib.sha256((self.root / name).read_bytes()).hexdigest() + "  " + name + "\n"
                 for name in names]
        (self.root / MANIFEST).write_text("".join(lines))

    def run_cli(self, *args):
        return subprocess.run([sys.executable, str(TOOL), "--root", str(self.root), *args],
                              cwd=self.repo, capture_output=True, text=True)

    def test_complete_nested_checkout_accepts_tracked_and_untracked_files(self):
        self.assertEqual(check(self.root), 2)
        result = self.run_cli()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("2 maintained lab files", result.stdout)

    def test_omitted_tracked_file_is_rejected(self):
        self.write_manifest(["docs/a b.md"])
        result = self.run_cli()
        self.assertEqual(result.returncode, 1)
        self.assertIn("Unlisted maintained files: scene.py", result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_new_file_requires_coverage_before_and_after_staging(self):
        (self.root / "new.txt").write_text("New maintained content.\n")
        for staged in [False, True]:
            with self.subTest(staged=staged):
                if staged:
                    self.git("add", "wrapper/lab/new.txt")
                with self.assertRaisesRegex(ValueError, "Unlisted maintained files: new.txt"):
                    check(self.root)

    def test_ignored_outputs_are_excluded_but_tracked_ignored_files_remain_required(self):
        self.assertEqual(check(self.root), 2)
        self.git("add", "-f", "wrapper/lab/node_modules/cache.txt")
        with self.assertRaisesRegex(ValueError, "Unlisted maintained files: node_modules/cache.txt"):
            check(self.root)
        self.write_manifest(self.names + ["node_modules/cache.txt"])
        self.assertEqual(check(self.root), 3)

    def test_hash_tampering_is_rejected(self):
        (self.root / "scene.py").write_bytes(b"\0changed\xff")
        with self.assertRaisesRegex(ValueError, "Hash mismatch: scene.py"):
            check(self.root)

    def test_deleted_tracked_file_is_rejected_until_deletion_and_manifest_are_updated(self):
        (self.root / "scene.py").unlink()
        with self.assertRaisesRegex(ValueError, "Missing, linked or out-of-root file: scene.py"):
            check(self.root)
        self.git("add", "-u")
        with self.assertRaisesRegex(ValueError, "Unmaintained manifest entries: scene.py"):
            check(self.root)
        self.write_manifest(["docs/a b.md"])
        self.assertEqual(check(self.root), 1)

    def test_duplicate_entries_are_rejected(self):
        path = self.root / MANIFEST
        path.write_text(path.read_text() + path.read_text().splitlines()[0] + "\n")
        with self.assertRaisesRegex(ValueError, "Duplicate manifest entry"):
            check(self.root)

    def test_malformed_and_noncanonical_paths_are_rejected(self):
        original = (self.root / MANIFEST).read_text()
        for row in ["not a hash", "0" * 64 + " scene.py", "0" * 64 + "  ../outside.md",
                    "0" * 64 + "  /scene.py", "0" * 64 + "  ./scene.py",
                    "0" * 64 + "  docs//a b.md", "0" * 64 + "  " + MANIFEST]:
            with self.subTest(row=row):
                (self.root / MANIFEST).write_text(original + row + "\n")
                with self.assertRaisesRegex(ValueError, "Malformed manifest line|Invalid manifest path"):
                    check(self.root)

    def test_symlink_entry_is_rejected_even_with_matching_content(self):
        path = self.root / "scene.py"
        outside = self.repo / "same.py"
        outside.write_bytes(path.read_bytes())
        path.unlink()
        path.symlink_to(outside)
        with self.assertRaisesRegex(ValueError, "Missing, linked or out-of-root file: scene.py"):
            check(self.root)

    def test_alternative_manifest_does_not_replace_the_maintained_file(self):
        original = (self.root / MANIFEST).read_bytes()
        alternative = self.repo / "omitted.sha256"
        alternative.write_bytes(original.splitlines(keepends=True)[0])
        result = self.run_cli("--manifest", str(alternative))
        self.assertEqual(result.returncode, 1)
        self.assertIn("Unlisted maintained files: scene.py", result.stderr)
        self.assertEqual((self.root / MANIFEST).read_bytes(), original)

    def test_missing_git_inventory_fails_without_a_traceback(self):
        result = subprocess.run([sys.executable, str(TOOL), "--root", str(self.repo.parent)],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 1)
        self.assertIn("Git inventory unavailable", result.stderr)
        self.assertNotIn("Traceback", result.stderr)


if __name__ == "__main__":
    unittest.main()
