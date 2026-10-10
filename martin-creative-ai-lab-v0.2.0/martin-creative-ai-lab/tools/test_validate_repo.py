"""Regression checks for maintained-document ownership after installing P11."""

import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class DocumentOwnershipTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.fixture = Path(self.temporary.name)
        (self.fixture / "tools").mkdir()
        shutil.copy2(ROOT / "tools/validate_repo.py", self.fixture / "tools/validate_repo.py")
        shutil.copytree(ROOT / "registry", self.fixture / "registry")
        shutil.copytree(ROOT / "archive", self.fixture / "archive")
        project = self.fixture / "projects/example"
        project.mkdir(parents=True)
        (project / "README.md").write_text("[Registry](../../registry/projects.json)\n")

    def run_validator(self):
        return subprocess.run(
            [sys.executable, "tools/validate_repo.py"],
            cwd=self.fixture, capture_output=True, text=True, check=False,
        )

    def test_installed_dependency_docs_are_not_lab_docs(self):
        dependency = self.fixture / "projects/example/node_modules/upstream/node_modules/nested"
        dependency.mkdir(parents=True)
        (dependency / "README.md").write_text("[Upstream](unshipped-file.md)\n")
        result = self.run_validator()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("1 local file links", result.stdout)

    def test_working_project_broken_links_still_fail(self):
        (self.fixture / "projects/example/README.md").write_text("[Missing](missing.md)\n")
        result = self.run_validator()
        self.assertEqual(result.returncode, 1)
        self.assertIn("projects/example/README.md: missing target: missing.md", result.stderr)

    def test_archive_integrity_is_still_required(self):
        archive = self.fixture / "archive/legacy-source-extracts-v0.2.0.zip"
        archive.write_bytes(archive.read_bytes() + b"modified")
        result = self.run_validator()
        self.assertEqual(result.returncode, 1)
        self.assertIn("legacy source archive hash mismatch", result.stderr)


if __name__ == "__main__":
    unittest.main()
