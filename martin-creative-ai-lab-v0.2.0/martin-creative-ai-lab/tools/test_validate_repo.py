"""Regression checks for maintained-document ownership after installing P11."""

import json
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
        # Supply the registry's referenced files without copying runtime dependencies.
        for filename, key in (("projects.json", "projects"), ("transfers.json", "transfers")):
            rows = json.loads((self.fixture / "registry" / filename).read_text())[key]
            for row in rows:
                for name in row["evidence"]:
                    path = self.fixture / name
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.touch()
                if "working_path" in row:
                    (self.fixture / row["working_path"]).mkdir(parents=True, exist_ok=True)
        project = self.fixture / "projects/example"
        project.mkdir(parents=True)
        (project / "README.md").write_text("[Registry](../../registry/projects.json)\n")

    def run_validator(self):
        return subprocess.run(
            [sys.executable, "tools/validate_repo.py"],
            cwd=self.fixture, capture_output=True, text=True, check=False,
        )

    def edit_row(self, filename, key, **changes):
        path = self.fixture / "registry" / filename
        data = json.loads(path.read_text())
        data[key][0].update(changes)
        path.write_text(json.dumps(data))

    def assert_invalid(self, message):
        result = self.run_validator()
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn(message, result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_missing_project_evidence_fails(self):
        self.edit_row("projects.json", "projects", evidence=["evidence/missing.json"])
        self.assert_invalid("P01: evidence[0]: missing file: evidence/missing.json")

    def test_evidence_requires_files_and_local_relative_paths(self):
        outside = self.fixture.parent / (self.fixture.name + "-outside.json")
        outside.write_text("{}")
        self.addCleanup(outside.unlink)
        for target, message in ((None, "expected nonempty local path"),
                                ([], "expected nonempty local path"),
                                ("", "expected nonempty local path"),
                                ("registry", "missing file"),
                                (str(outside), "expected relative path"),
                                ("../" + outside.name, "target leaves repository"),
                                ("https://example.com/report.json", "expected relative path"),
                                ("https://[", "expected relative path"),
                                ("bad\x00path", "invalid path")):
            with self.subTest(target=target):
                self.edit_row("projects.json", "projects", evidence=[target])
                self.assert_invalid(message)

    def test_symlink_evidence_cannot_escape_repository(self):
        (self.fixture / "escape").symlink_to(self.fixture.parent, target_is_directory=True)
        self.edit_row("projects.json", "projects", evidence=["escape/report.json"])
        self.assert_invalid("target leaves repository")
        (self.fixture / "loop").symlink_to("loop")
        self.edit_row("projects.json", "projects", evidence=["loop"])
        self.assert_invalid("invalid path")

    def test_missing_transfer_evidence_fails(self):
        self.edit_row("transfers.json", "transfers", evidence=["missing.json"])
        self.assert_invalid("TR-001: evidence[0]: missing file")

    def test_transfer_evidence_must_be_list(self):
        self.edit_row("transfers.json", "transfers", evidence="README.md")
        self.assert_invalid("TR-001: evidence must be a list")

    def test_asset_evidence_is_checked_when_present(self):
        path = self.fixture / "registry/assets.json"
        data = json.loads(path.read_text())
        data["assets"] = [{"id": "A01", "consumer_projects": ["P11"],
                           "evidence": ["missing.json"]}]
        path.write_text(json.dumps(data))
        self.assert_invalid("A01: evidence[0]: missing file")

    def test_working_path_requires_directory(self):
        for target in ("missing", "registry/projects.json", ""):
            with self.subTest(target=target):
                self.edit_row("projects.json", "projects", working_path=target)
                self.assert_invalid("P01: working_path:")

    def test_source_id_requires_known_string(self):
        for target in ("LEGACY-missing", None, []):
            with self.subTest(target=target):
                self.edit_row("projects.json", "projects", source_id=target)
                self.assert_invalid("P01: unknown source_id")

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
