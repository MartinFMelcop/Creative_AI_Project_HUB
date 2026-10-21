"""Regression checks for source ownership and the origin/laboratory transition."""

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from test_reference_library import make_fixture

ROOT = Path(__file__).resolve().parents[1]


class DocumentOwnershipTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.fixture = Path(self.temporary.name)
        (self.fixture / "tools").mkdir()
        shutil.copy2(ROOT / "tools/validate_repo.py", self.fixture / "tools/validate_repo.py")
        shutil.copy2(ROOT / "tools/reference_library.py", self.fixture / "tools/reference_library.py")
        shutil.copy2(ROOT / "tools/brain_query.py", self.fixture / "tools/brain_query.py")
        brains = self.fixture / "brains"
        brains.mkdir()
        for name in ("ENGINEERING_BRAIN.md", "SCIENTIFIC_BRAIN.md", "CREATIVE_BRAIN.md",
                     "CATALOGO_DE_CONSULTA.json", "BIBLIOTECA_DE_CONHECIMENTO_APLICADO.md", "integrity.json"):
            shutil.copy2(ROOT / "brains" / name, brains / name)
        shutil.copytree(ROOT / "registry", self.fixture / "registry")
        path = self.fixture / "registry/projects.json"
        data = json.loads(path.read_text())
        for row in data["projects"]:
            row.update(role="historical_origin", status="transition")
        path.write_text(json.dumps(data))
        shutil.copytree(ROOT / "archive", self.fixture / "archive")
        # Supply the registry's referenced files without copying runtime dependencies.
        for filename, key in (("projects.json", "projects"), ("transfers.json", "transfers"),
                              ("assets.json", "assets")):
            rows = json.loads((self.fixture / "registry" / filename).read_text())[key]
            for row in rows:
                for name in row.get("evidence", []):
                    path = self.fixture / name
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.touch()
                if "working_path" in row:
                    (self.fixture / row["working_path"]).mkdir(parents=True, exist_ok=True)
        project = self.fixture / "projects/example"
        project.mkdir(parents=True)
        (project / "README.md").write_text("[Registry](../../registry/projects.json)\n")
        self.make_origin_fixture(data["projects"])
        make_fixture(self.fixture)

    def make_origin_fixture(self, projects):
        """Small real paths and records exercise the migration, not runtime claims."""
        pilot = self.fixture / "labs/test-pilot"
        pilot.mkdir(parents=True)
        (pilot / "instrument.py").write_text("# Fixture instrument; never executed as research.\n")
        (pilot / "result.json").write_text('{"fixture":true}\n')
        data = {"schema_version": 1, "updated_at": "2026-10-17",
                "baseline_commit": "a" * 40, "scope": "Structural migration test fixture only.",
                "origins": [], "labs": [{"id": "test-pilot", "status": "implemented",
                    "origin_projects": ["P06"], "question": "Does the validator enforce a real instrument path?",
                    "path": "labs/test-pilot", "instrument": "labs/test-pilot/instrument.py",
                    "evidence": ["labs/test-pilot/result.json"]}]}
        for row in projects:
            seed = row["id"] == "P09"
            data["origins"].append({"id": row["id"],
                "transition_status": "seed_only" if seed else "pilot_instrumented" if row["id"] == "P06" else "preserved_pending_extraction",
                "reusable_capabilities": [] if seed else ["Fixture capability"],
                "source_paths": [] if seed else ["projects/example"],
                "execution_evidence": [] if seed else ["labs/test-pilot/result.json"],
                "existing_consumers": [], "candidate_destinations": ["Candidate question, not a lab claim"],
                "dependencies": [], "preservation_risks": ["Do not erase original evidence"],
                "extraction_next": "Inspect the actual origin before extracting."})
        (self.fixture / "labs/origins.json").write_text(json.dumps(data))

    def run_validator(self):
        return subprocess.run(
            [sys.executable, "tools/validate_repo.py"],
            cwd=self.fixture, capture_output=True, text=True, check=False,
        )

    def test_wrapped_hub_entry_links_and_backlinks_are_owned(self):
        hub = self.fixture / "wrapped-hub"
        lab = hub / "martin-creative-ai-lab-v0.2.0/martin-creative-ai-lab"
        # Copy only prepared fixture files; the destination is inside the temp
        # fixture, so create it after copytree's source inventory is captured.
        staging = self.fixture.parent / (self.fixture.name + "-wrapped-lab")
        self.addCleanup(lambda: shutil.rmtree(staging, ignore_errors=True))
        shutil.copytree(self.fixture, staging)
        shutil.copytree(staging, lab)
        readme = hub / "README.md"
        readme.write_text("[Project](martin-creative-ai-lab-v0.2.0/martin-creative-ai-lab/projects/example/README.md)\n")
        (lab / "README.md").write_text("[HUB](../../README.md)\n")
        command = [sys.executable, "tools/validate_repo.py"]
        result = subprocess.run(command, cwd=lab, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        for target, message in [("missing.md", "README.md: missing target: missing.md"),
                                ("../outside.md", "README.md: target leaves repository: ../outside.md")]:
            with self.subTest(target=target):
                readme.write_text(f"[Bad]({target})\n")
                result = subprocess.run(command, cwd=lab, capture_output=True, text=True)
                self.assertEqual(result.returncode, 1, result.stdout)
                self.assertIn(message, result.stderr)
                self.assertNotIn("Traceback", result.stderr)

    def edit_row(self, filename, key, **changes):
        path = self.fixture / "registry" / filename
        data = json.loads(path.read_text())
        data[key][0].update(changes)
        path.write_text(json.dumps(data))

    def edit_origins(self, change):
        path = self.fixture / "labs/origins.json"
        data = json.loads(path.read_text())
        change(data)
        path.write_text(json.dumps(data))

    def assert_invalid(self, message):
        result = self.run_validator()
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn(message, result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_missing_project_evidence_fails(self):
        self.edit_row("projects.json", "projects", evidence=["evidence/missing.json"])
        self.assert_invalid("P01: evidence[0]: missing file: evidence/missing.json")

    def test_origin_role_is_required(self):
        for role in (None, "active_product", [], ""):
            with self.subTest(role=role):
                self.edit_row("projects.json", "projects", role=role)
                self.assert_invalid("P01: role must be historical_origin")

    def test_transition_is_an_explicit_status(self):
        result = self.run_validator()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.edit_row("projects.json", "projects", status="laboratory_ready")
        self.assert_invalid("P01: invalid status")

    def test_brain_bytes_are_still_required(self):
        path = self.fixture / "brains/CREATIVE_BRAIN.md"
        path.write_bytes(path.read_bytes() + b"\nUnapproved update.\n")
        self.assert_invalid("brain collection: Source integrity mismatch: CREATIVE_BRAIN.md")

    def test_maintained_brain_links_are_owned(self):
        (self.fixture / "brains/README.md").write_text("[Missing](missing.md)\n")
        self.assert_invalid("brains/README.md: missing target: missing.md")

    def test_transition_inventory_is_required_and_complete(self):
        self.edit_origins(lambda data: data["origins"].pop())
        self.assert_invalid("inventory must contain exactly one row for each P01–P11")

    def test_duplicate_origins_are_rejected(self):
        self.edit_origins(lambda data: data["origins"].append(data["origins"][0]))
        self.assert_invalid("P01: duplicate origin")

    def test_unimplemented_lab_cannot_be_renamed_implemented(self):
        self.edit_origins(lambda data: data["labs"][0].update(instrument="labs/test-pilot/missing.py"))
        self.assert_invalid("instrument: missing file")

    def test_candidate_lab_does_not_claim_execution(self):
        self.edit_origins(lambda data: data["labs"].append({"id": "unbuilt", "status": "candidate",
            "origin_projects": ["P01"], "question": "Pending question", "evidence": []}))
        self.assert_invalid("a candidate cannot claim implemented path, instrument or evidence")

    def test_valid_candidate_stays_distinct_from_implemented_pilot(self):
        self.edit_origins(lambda data: data["labs"].append({"id": "unbuilt", "status": "candidate",
            "origin_projects": ["P01"], "question": "Pending question"}))
        result = self.run_validator()
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_pilot_origin_requires_an_implemented_consumer(self):
        self.edit_origins(lambda data: data["labs"][0].update(origin_projects=["P01"]))
        self.assert_invalid("pilot_instrumented origins require an implemented lab consumer")

    def test_empty_labs_reject_a_remaining_instrumented_origin_claim(self):
        self.edit_origins(lambda data: data.update(labs=[]))
        self.assert_invalid("pilot_instrumented origins require an implemented lab consumer")

    def test_all_labs_can_retire_when_no_instrumented_origin_claim_remains(self):
        def retire(data):
            data["labs"] = []
            next(row for row in data["origins"] if row["id"] == "P06")["transition_status"] = "preserved_pending_extraction"
        self.edit_origins(retire)
        result = self.run_validator()
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_candidates_only_do_not_require_a_manufactured_implementation(self):
        def retain_candidates(data):
            data["labs"] = [{"id": "unbuilt", "status": "candidate",
                             "origin_projects": ["P06"], "question": "A useful future question"}]
            next(row for row in data["origins"] if row["id"] == "P06")["transition_status"] = "preserved_pending_extraction"
        self.edit_origins(retain_candidates)
        result = self.run_validator()
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_candidate_cannot_satisfy_an_instrumented_origin_claim(self):
        self.edit_origins(lambda data: data.update(labs=[{"id": "unbuilt", "status": "candidate",
            "origin_projects": ["P06"], "question": "An unimplemented replacement"}]))
        self.assert_invalid("pilot_instrumented origins require an implemented lab consumer")

    def test_origin_evidence_and_source_paths_must_exist(self):
        self.edit_origins(lambda data: data["origins"][0].update(execution_evidence=["missing.json"]))
        self.assert_invalid("P01: execution_evidence: missing file")

    def test_origin_fields_and_consumers_are_typed(self):
        self.edit_origins(lambda data: data["origins"][0].update(existing_consumers=["P99"]))
        self.assert_invalid("unknown existing_consumer P99")

    def test_seed_status_cannot_hide_demonstrated_origin(self):
        self.edit_origins(lambda data: data["origins"][0].update(transition_status="seed_only"))
        self.assert_invalid("seed_only requires an M0 origin")

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

    def test_historical_links_are_data_but_maintained_reference_links_still_fail(self):
        result = self.run_validator()
        self.assertEqual(result.returncode, 0, result.stderr)
        (self.fixture / "references/README.md").write_text("[Missing](missing.md)\n")
        result = self.run_validator()
        self.assertEqual(result.returncode, 1)
        self.assertIn("references/README.md: missing target: missing.md", result.stderr)

    def test_archive_integrity_is_still_required(self):
        archive = self.fixture / "archive/legacy-source-extracts-v0.2.0.zip"
        archive.write_bytes(archive.read_bytes() + b"modified")
        result = self.run_validator()
        self.assertEqual(result.returncode, 1)
        self.assertIn("legacy source archive hash mismatch", result.stderr)


if __name__ == "__main__":
    unittest.main()
