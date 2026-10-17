#!/usr/bin/env python3
"""Regression checks for exact consultation, not the truth of the source books."""
import contextlib
import hashlib
import io
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

import brain_query as query


class BrainQueryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.collection = query.Collection()

    def fixture(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        target = Path(directory.name)
        for name in (*query.SOURCES, "integrity.json"):
            shutil.copyfile(query.DEFAULT_BRAINS / name, target / name)
        return target

    def repin_fixture(self, directory, name, data):
        """Only temporary adversarial fixtures may change pins to reach structure checks."""
        (directory / name).write_bytes(data)
        pins = json.loads((directory / "integrity.json").read_text())
        pins["files"][name] = {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}
        (directory / "integrity.json").write_text(json.dumps(pins))

    def mutate_catalog(self, change):
        directory = self.fixture()
        catalog = json.loads((directory / query.CATALOG).read_text())
        change(catalog)
        self.repin_fixture(directory, query.CATALOG, json.dumps(catalog, ensure_ascii=False).encode())
        return directory

    def test_complete_supplied_collection(self):
        report = self.collection.report()
        self.assertEqual(report["chapters"], {"ENG": 49, "SCI": 85, "CRE": 100})
        self.assertEqual(report["total_chapters"], 234)
        self.assertEqual(report["local_links"], 422)
        self.assertEqual(len(report["source_warnings"]), 44)
        self.assertEqual([v["file"] for v in self.collection.indexes()], list(query.VOLUMES))

    def test_exact_content_and_boundaries(self):
        for chapter in self.collection.chapters.values():
            source_lines = self.collection.texts[chapter["path"]].splitlines(keepends=True)
            actual = "".join(source_lines[chapter["line_start"] - 1:chapter["line_end"]])
            self.assertEqual(actual, chapter["content"], chapter["id"])
            self.assertTrue(actual.startswith(f"### {chapter['chapter']}. {chapter['title']}\n"))
            self.assertEqual(sum(1 for m in query.HEADINGS.finditer(actual) if len(m[1]) <= 3), 1)
        self.assertNotIn("## Parte II", self.collection.get("ENG-006")["content"])
        self.assertIn("Cinco classes de afirmação", self.collection.get("ENG-027")["content"])

    def test_ids_and_editorial_categories(self):
        self.assertEqual(self.collection.get("cre-001")["editorial_status"], "D")
        self.assertEqual(self.collection.get("CRE-008")["editorial_status"], "A")
        self.assertEqual(self.collection.get("CRE-099")["editorial_status"], "H")
        self.assertIsNone(self.collection.get("ENG-027")["editorial_status"])
        self.assertEqual(self.collection.search("sci-053")[0]["id"], "SCI-053")

    def test_search_unicode_and_stable_ranking(self):
        first = self.collection.search("PROVENIÊNCIA", 20)
        self.assertTrue(first)
        self.assertEqual(first, self.collection.search("proveniencia", 20))
        self.assertEqual(first, self.collection.search("provENIE\u0302NCIA", 20))
        self.assertEqual(first, query.Collection().search("proveniência", 20))
        self.assertIn("ENG-027", [item["id"] for item in first])

    def test_title_and_question_search_returns_source(self):
        chapter = self.collection.get("SCI-053")
        for value in (chapter["title"], chapter["question"]):
            hit = self.collection.search(value)[0]
            self.assertEqual(hit["id"], "SCI-053")
            self.assertEqual(hit["content"], chapter["content"])
            self.assertEqual(hit["path"], "SCIENTIFIC_BRAIN.md")
            self.assertEqual(hit["section"], chapter["section"])

    def test_negative_queries_and_clear_errors(self):
        self.assertEqual(self.collection.search("zzzznonexistentcapability"), [])
        self.assertEqual(self.collection.search("proveniência zzzznonexistentcapability"), [])
        for text in ("", "   ", "a e de"):
            with self.assertRaises(query.BrainError):
                self.collection.search(text)
        for limit in (0, -1, 235):
            with self.assertRaisesRegex(query.BrainError, "limit"):
                self.collection.search("proveniência", limit)
        with self.assertRaisesRegex(query.BrainError, "Unknown chapter ID"):
            self.collection.get("ENG-999")

    def test_inherited_fragments_are_reported_without_repair(self):
        chapter = self.collection.get("ENG-034")
        self.assertIn("a--um", chapter["source_fragment"])
        self.assertIn("a-um", chapter["anchor"])
        text = self.collection.texts[chapter["path"]]
        self.assertIn("](#" + chapter["anchor"] + ")", text)
        self.assertTrue(all(w["kind"] == "inherited_heading_fragment_difference"
                            for w in self.collection.warnings))

    def test_cli_json_and_error_status(self):
        stdout, stderr = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            status = query.main(["get", "ENG-027", "CRE-008"])
        self.assertEqual(status, 0)
        self.assertEqual(stderr.getvalue(), "")
        self.assertIn("proveniência", stdout.getvalue())
        self.assertEqual([c["id"] for c in json.loads(stdout.getvalue())], ["ENG-027", "CRE-008"])
        stdout, stderr = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            status = query.main(["get", "ENG-999"])
        self.assertEqual(status, 2)
        self.assertEqual(stdout.getvalue(), "")
        self.assertIn("Unknown chapter ID", stderr.getvalue())

    def test_cli_is_independent_of_working_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            result = subprocess.run([sys.executable, str(Path(query.__file__).resolve()),
                                     "search", "zzzznonexistentcapability"], cwd=directory,
                                    capture_output=True, text=True, timeout=10, check=False)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout), [])

    def test_changed_source_denies_consultation(self):
        directory = self.fixture()
        source = directory / "CREATIVE_BRAIN.md"
        source.write_bytes(source.read_bytes() + b"\n")
        with self.assertRaisesRegex(query.BrainError, "integrity mismatch: CREATIVE"):
            query.Collection(directory)

    def test_missing_source_and_symlink_rejected(self):
        directory = self.fixture()
        source = directory / "CREATIVE_BRAIN.md"
        source.unlink()
        with self.assertRaisesRegex(query.BrainError, "Cannot read CREATIVE"):
            query.Collection(directory)
        source.symlink_to(query.DEFAULT_BRAINS / "CREATIVE_BRAIN.md")
        with self.assertRaisesRegex(query.BrainError, "not a symlink"):
            query.Collection(directory)

    def test_invalid_utf8_is_not_silently_replaced(self):
        directory = self.fixture()
        name = "ENGINEERING_BRAIN.md"
        self.repin_fixture(directory, name, (directory / name).read_bytes() + b"\xff")
        with self.assertRaisesRegex(query.BrainError, "not valid UTF-8"):
            query.Collection(directory)

    def test_catalog_title_question_status_and_anchor_mismatches(self):
        for key, value, message in (("title", "Wrong title", "heading"),
                                    ("question", "Wrong question", "question"),
                                    ("editorial_status", "V", "editorial-status"),
                                    ("anchor", "wrong-anchor", "anchor")):
            with self.subTest(key=key):
                directory = self.mutate_catalog(lambda c: c["volumes"][0]["chapters"][0].__setitem__(key, value))
                with self.assertRaisesRegex(query.BrainError, message):
                    query.Collection(directory)

    def test_catalog_missing_duplicate_or_unsafe_volume(self):
        changes = (
            lambda c: c["volumes"][0]["chapters"].pop(),
            lambda c: c["volumes"][0]["chapters"][1].__setitem__("id", "ENG-001"),
            lambda c: c["volumes"][0].__setitem__("file", "../outside.md"),
            lambda c: c["volumes"].__setitem__(1, c["volumes"][0]),
        )
        for change in changes:
            with self.subTest(change=change):
                with self.assertRaises(query.BrainError):
                    query.Collection(self.mutate_catalog(change))

    def test_invalid_source_json(self):
        directory = self.fixture()
        self.repin_fixture(directory, query.CATALOG, b"{not-json}")
        with self.assertRaisesRegex(query.BrainError, "Invalid JSON"):
            query.Collection(directory)

    def test_unrecognized_internal_link_is_error(self):
        directory = self.fixture()
        raw = (directory / query.LIBRARY).read_bytes() + b"\n[broken](CREATIVE_BRAIN.md#missing-chapter)\n"
        self.repin_fixture(directory, query.LIBRARY, raw)
        with self.assertRaisesRegex(query.BrainError, "Broken local link"):
            query.Collection(directory)

    def test_malformed_pin_registry_is_error(self):
        directory = self.fixture()
        path = directory / "integrity.json"
        pins = json.loads(path.read_text())
        pins["files"].pop(query.LIBRARY)
        path.write_text(json.dumps(pins))
        with self.assertRaisesRegex(query.BrainError, "exactly the five"):
            query.Collection(directory)


if __name__ == "__main__":
    unittest.main()
