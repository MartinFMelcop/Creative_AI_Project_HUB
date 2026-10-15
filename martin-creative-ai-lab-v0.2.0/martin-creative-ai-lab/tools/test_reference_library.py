"""Real temporary reference fixtures exercise integrity, discovery and claim boundaries."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from zipfile import ZipFile

from reference_library import validate_library

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools/reference_library.py"


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data))


def make_fixture(root):
    """Also used by the existing repo-validator fixtures; no product dependencies."""
    registry = root / "registry"
    registry.mkdir(exist_ok=True)
    if not (registry / "projects.json").exists():
        write_json(registry / "projects.json", {"schema_version": 1, "projects": [{"id": "P01"}]})
    if not (registry / "legacy_sources.json").exists():
        (root / "archive").mkdir()
        (root / "archive/old.zip").write_bytes(b"unchanged fixture archive")
        write_json(registry / "legacy_sources.json", {"schema_version": 1, "sources": [],
                   "source_archive": {"path": "archive/old.zip", "sha256": hashlib.sha256(b"unchanged fixture archive").hexdigest()}})
    old = json.loads((registry / "legacy_sources.json").read_text())["source_archive"]
    commit = "a" * 40
    name = "references/rave-master/snapshots/" + commit
    source = root / name / "source"
    source.mkdir(parents=True)
    raw = b"Historical data: [Old link](not-shipped.md)\n"
    (source / "README.md").write_bytes(raw)
    item = {"source_path": "README.md", "git_blob_sha": hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest(),
            "sha256": hashlib.sha256(raw).hexdigest(), "size_bytes": len(raw), "source_mode": "100644",
            "classification": "historical_reference", "status": "imported", "local_path": name + "/source/README.md", "exclusion_reason": None}
    write_json(root / name / "inventory.json", {"schema_version": 1, "collection_id": "REF-RAVE-36AF165",
               "source_commit": commit, "source_tree": "b" * 40, "files": [item]})
    write_json(root / name / "discovery.json", {"schema_version": 1, "collection_id": "REF-RAVE-36AF165",
               "topics": [{"id": "combat", "source_paths": ["README.md"]}]})
    report = root / "docs/report.md"
    report.parent.mkdir(exist_ok=True)
    report.write_text("Historical inspection report, no source payload.\n")
    catalog = {"schema_version": 1, "legacy_archive": old, "collections": [
        {"id": "REF-RAVE-36AF165", "kind": "repository_snapshot", "status": "imported", "source_commit": commit,
         "source_tree": "b" * 40, "source_root": name + "/source", "inventory_path": name + "/inventory.json",
         "discovery_path": name + "/discovery.json", "file_count": 1, "imported_count": 1, "excluded_count": 0,
         "full_archive_preserved": False, "git_history_preserved": False},
        {"id": "REF-LICH-ATTACHMENT", "kind": "attachment", "status": "unavailable", "imported_count": 0,
         "full_archive_preserved": False, "blocker": "fixture transfer unavailable", "authority_status": "unverified"},
        {"id": "REF-LICH-REPORT-0448", "kind": "historical_report", "status": "documented_only", "imported_count": 0,
         "full_archive_preserved": False, "report_path": "docs/report.md", "reported_details_path": "docs/report.md"}]}
    write_json(root / "references/catalog.json", catalog)
    write_json(root / "north-star/capabilities.json", {"schema_version": 1, "name": "North Star", "kind": "program",
               "stage": "foundation_only", "engine_selection": "undecided", "consumer_paths": [], "capabilities": [
                   {"id": "NS-TEST", "contribution_status": "candidate", "origin_projects": ["P01"],
                    "scope": "fixture scope", "applicability_hypothesis": "test hypothesis", "limits": "no consumer",
                    "next_validation": "actual destination", "origin_evidence": []}]})
    return name


class ReferenceLibraryTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.snapshot = make_fixture(self.root)

    def edit(self, name, mutate):
        path = self.root / name
        data = json.loads(path.read_text())
        mutate(data)
        write_json(path, data)

    def run_cli(self, *args):
        return subprocess.run([sys.executable, str(TOOL), "--root", str(self.root), *args],
                              capture_output=True, text=True)

    def assert_invalid(self, message):
        result = self.run_cli("check")
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn(message, result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_complete_library_and_topic_query_open_actual_bytes(self):
        result = validate_library(self.root)
        self.assertEqual((result["imported"], result["excluded"]), (1, 0))
        output = self.run_cli("find", "--topic", "combat")
        self.assertEqual(output.returncode, 0, output.stderr)
        data = json.loads(output.stdout)
        self.assertEqual(data["matches"], 1)
        row = data["files"][0]
        self.assertEqual(hashlib.sha256((self.root / row["local_path"]).read_bytes()).hexdigest(), row["sha256"])

    def test_unavailable_attachment_query_has_no_local_payload(self):
        result = self.run_cli("find", "--collection", "REF-LICH-ATTACHMENT")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["files"], [])
        self.assertEqual(json.loads(result.stdout)["status"], "unavailable")

    def test_missing_source_fails(self):
        (self.root / self.snapshot / "source/README.md").unlink()
        self.assert_invalid("Missing reference")

    def test_changed_source_fails(self):
        (self.root / self.snapshot / "source/README.md").write_text("tampered")
        self.assert_invalid("source hash or size differs")

    def test_control_names_must_remain_inert(self):
        source = self.root / self.snapshot / "source/README.md"
        source.rename(source.with_name("AGENTS.md.reference"))
        self.edit(self.snapshot + "/inventory.json", lambda d: d["files"][0].update(
            source_path="AGENTS.md", local_path=self.snapshot + "/source/AGENTS.md.reference"))
        self.edit(self.snapshot + "/discovery.json", lambda d: d["topics"][0].update(source_paths=["AGENTS.md"]))
        self.assertEqual(validate_library(self.root)["imported"], 1)
        self.edit(self.snapshot + "/inventory.json", lambda d: d["files"][0].update(
            local_path=self.snapshot + "/source/AGENTS.md"))
        self.assert_invalid("original/local path mapping differs")

    def test_binary_cannot_become_an_imported_reference(self):
        source = self.root / self.snapshot / "source/README.md"
        source.rename(source.with_name("Game.exe"))
        self.edit(self.snapshot + "/inventory.json", lambda d: d["files"][0].update(
            source_path="Game.exe", local_path=self.snapshot + "/source/Game.exe"))
        self.assert_invalid("not eligible reference text")

    def test_previously_withheld_digest_stays_excluded(self):
        archive = self.root / "archive/old.zip"
        with ZipFile(archive, "w") as z:
            z.writestr("unrelated.txt", "old fixture")
        old = json.loads((self.root / "registry/legacy_sources.json").read_text())
        old["source_archive"]["sha256"] = hashlib.sha256(archive.read_bytes()).hexdigest()
        item = json.loads((self.root / self.snapshot / "inventory.json").read_text())["files"][0]
        old["sources"] = [{"id": "OLD", "commit": "a" * 40, "archive_prefix": "old", "inventory": [
            {"path": "README.md", "git_blob_sha": item["git_blob_sha"], "size_bytes": item["size_bytes"],
             "preserved": False, "content_inspected": True}]}]
        write_json(self.root / "registry/legacy_sources.json", old)
        self.edit("references/catalog.json", lambda d: d.update(legacy_archive=old["source_archive"]))
        self.edit("references/catalog.json", lambda d: d["collections"][0].update(legacy_source_id="OLD", prior_selected_identical=0))
        self.assert_invalid("previously withheld source was imported")

    def test_git_blob_mismatch_fails_even_if_sha256_matches(self):
        self.edit(self.snapshot + "/inventory.json", lambda d: d["files"][0].update(git_blob_sha="0" * 40))
        self.assert_invalid("Git blob differs")

    def test_unlisted_payload_fails(self):
        (self.root / self.snapshot / "source/extra.txt").write_text("unlisted")
        self.assert_invalid("unlisted or missing snapshot payload")

    def test_duplicate_source_and_collection_ids_fail(self):
        for filename, key, message in [(self.snapshot + "/inventory.json", "files", "duplicate source_path"),
                                       ("references/catalog.json", "collections", "duplicate id")]:
            with self.subTest(filename=filename):
                path = self.root / filename
                original = path.read_bytes()
                self.edit(filename, lambda d: d[key].append(d[key][0]))
                self.assert_invalid(message)
                path.write_bytes(original)

    def test_invalid_discovery_reference_fails(self):
        self.edit(self.snapshot + "/discovery.json", lambda d: d["topics"][0].update(source_paths=["missing.csv"]))
        self.assert_invalid("invalid discovery reference")

    def test_source_path_escape_and_symlink_fail(self):
        metadata = self.root / self.snapshot / "inventory.json"
        original = metadata.read_bytes()
        self.edit(self.snapshot + "/inventory.json", lambda d: d["files"][0].update(source_path="../escape"))
        self.assert_invalid("Noncanonical reference path")
        metadata.write_bytes(original)
        source = self.root / self.snapshot / "source/README.md"
        outside = self.root / "outside.md"
        outside.write_bytes(source.read_bytes())
        source.unlink();source.symlink_to(outside)
        self.assert_invalid("Linked reference")

    def test_counts_and_full_preservation_claims_fail(self):
        for changes, message in [({"imported_count": 2}, "imported_count differs"),
                                 ({"full_archive_preserved": True}, "unsupported completeness claim")]:
            with self.subTest(changes=changes):
                path = self.root / "references/catalog.json"
                original = path.read_bytes()
                self.edit("references/catalog.json", lambda d: d["collections"][0].update(changes))
                self.assert_invalid(message)
                path.write_bytes(original)

    def test_exclusion_cannot_supply_a_payload_or_omit_reason(self):
        self.edit(self.snapshot + "/inventory.json", lambda d: d["files"][0].update(status="excluded"))
        self.assert_invalid("excluded source has payload or no reason")

    def test_attachment_cannot_invent_a_hash_or_ratified_policy(self):
        for changes, message in [({"sha256": "0" * 64}, "unavailable attachment claims preserved content"),
                                 ({"authority_status": "ratified"}, "literary authority must remain unverified")]:
            with self.subTest(changes=changes):
                path = self.root / "references/catalog.json";original = path.read_bytes()
                self.edit("references/catalog.json", lambda d: d["collections"][1].update(changes))
                self.assert_invalid(message);path.write_bytes(original)

    def test_unknown_origin_and_false_integration_fail(self):
        for changes, message in [({"origin_projects": ["P12"]}, "invalid origin project"),
                                 ({"reference_collections": ["missing"]}, "invalid origin reference"),
                                 ({"contribution_status": "integrated_into_north_star"}, "no implemented North Star consumer"),
                                 ({"contribution_status": "adapted"}, "no implemented North Star consumer"),
                                 ({"contribution_status": "externally_validated"}, "no implemented North Star consumer"),
                                 ({"contribution_status": "verified_in_origin"}, "origin verification needs a recorded execution")]:
            with self.subTest(changes=changes):
                path = self.root / "north-star/capabilities.json";original = path.read_bytes()
                self.edit("north-star/capabilities.json", lambda d: d["capabilities"][0].update(changes))
                self.assert_invalid(message);path.write_bytes(original)

    def test_old_archive_tampering_fails(self):
        (self.root / "archive/old.zip").write_bytes(b"changed")
        self.assert_invalid("Previous legacy archive hash differs")

    def test_unknown_topic_and_malformed_schema_report_failures(self):
        result = self.run_cli("find", "--topic", "missing")
        self.assertEqual(result.returncode, 1)
        self.assertIn("Unknown discovery topic", result.stderr)
        self.edit("references/catalog.json", lambda d: d.update(schema_version=2))
        self.assert_invalid("Invalid reference schema")


if __name__ == "__main__":
    unittest.main()
