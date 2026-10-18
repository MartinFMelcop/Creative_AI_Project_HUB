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
from unittest import mock

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


    def test_overview_uses_only_supplied_names_counts_and_parts(self):
        rows = self.collection.overview()
        self.assertEqual([c["domain"] for c in rows], ["ENG", "SCI", "CRE"])
        self.assertEqual(sum(c["chapter_count"] for c in rows), 234)
        for row, volume in zip(rows, self.collection.catalog["volumes"]):
            self.assertEqual(row["title"], volume["title"])
            self.assertEqual(row["scope"], volume["scope"])
            self.assertEqual(row["sections"], list(dict.fromkeys(c["section"] for c in volume["chapters"])))
            self.assertNotIn("chapters", row)
        render = lambda data: json.dumps(data, ensure_ascii=False, indent=2).encode()
        self.assertLess(len(render(rows)), len(render(self.collection.indexes())) / 10)

    def test_strict_metadata_is_a_projection_not_a_new_search(self):
        for text in ("classes especializações", "identidade de personagem", "proveniência", "CRE-010", "combat", "zzz"):
            full = self.collection.search(text)
            compact = self.collection.search(text, metadata_only=True)
            self.assertEqual([c["id"] for c in compact], [c["id"] for c in full])
            for a, b in zip(full, compact):
                self.assertNotIn("content", b)
                self.assertNotIn("preview", b)
                self.assertEqual(a["question"], b["question"])
                self.assertEqual(a["source_fragment"], b["source_fragment"])
                self.assertEqual(a["editorial_status"], b["editorial_status"])
                self.assertEqual(a.get("search_score"), b["search_score"])

    def test_known_id_bypasses_vocabulary_and_preserves_full_get(self):
        with mock.patch.object(query, "vocabulary", side_effect=AssertionError("unnecessary vocabulary")):
            self.assertEqual(self.collection.search("CRE-010", relaxed=True), [self.collection.get("CRE-010")])
            row = self.collection.search("cre-010", metadata_only=True, relaxed=True)[0]
            self.assertEqual(row["match"]["kind"], "exact_id")
            self.assertEqual(row["editorial_status"], "H")

    def test_bilingual_queries_retrieve_declared_inspected_targets(self):
        cases = json.loads(Path(query.__file__).with_name("brain_retrieval_cases.json").read_text())
        for case in cases["cases"]:
            if case["kind"] not in ("primary", "extension"):
                continue
            with self.subTest(query=case["query"]):
                hits = self.collection.search(case["query"], metadata_only=True, relaxed=True)
                self.assertTrue(set(case["targets"]) & {c["id"] for c in hits})
                self.assertLessEqual(len(hits), 5)

    def test_translated_related_and_literal_matches_remain_distinct(self):
        literal = self.collection.search("classes especializações", metadata_only=True)[0]
        self.assertEqual(literal["match"]["kind"], "literal_all")
        translated = self.collection.search("combat", metadata_only=True, relaxed=True)
        self.assertTrue(any(c["match"]["kind"] == "expanded_all" for c in translated))
        related = self.collection.search("avatar customization", metadata_only=True, relaxed=True)
        self.assertEqual(related[0]["id"], "CRE-009")
        self.assertEqual(related[0]["match"]["kind"], "related")
        self.assertEqual(related[0]["editorial_status"], "H")

    def test_source_only_fallback_is_explicit_and_not_emitted(self):
        results = self.collection.search("personas escudo", metadata_only=True, relaxed=True)
        target = next(c for c in results if c["id"] == "CRE-020")
        self.assertTrue(any(t["field"] == "content" for t in target["match"]["terms"]))
        self.assertNotIn("content", target)
        self.assertIn("escudo", query.fold(self.collection.get(target["id"])["content"]))

    def test_unknown_words_and_typos_are_not_silently_dropped(self):
        for text in ("insurance mortgage", "combat quantumflux", "classes especializações quantumflux", "characterr"):
            self.assertEqual(self.collection.search(text, relaxed=True), [], text)
        row = self.collection.search("jogador que só usa defesa", metadata_only=True, relaxed=True)[0]
        self.assertIn("so", row["match"]["uninterpreted_qualifiers"])
        self.assertIn("usa", row["match"]["ignored"])
        self.assertIn("jogador", row["match"]["context"])
        self.assertNotIn("CRE-029", [c["id"] for c in self.collection.search("defesa", relaxed=True)])

    def test_broad_and_partial_candidates_cannot_claim_full_coverage(self):
        broad = self.collection.search("identidade", metadata_only=True, relaxed=True)
        self.assertTrue(broad and all(c["match"]["broad"] for c in broad))
        rows = self.collection.search("defesa montarias classes", 234, metadata_only=True, relaxed=True)
        partial = [c for c in rows if c["match"]["kind"] == "partial"]
        self.assertTrue(partial)
        self.assertTrue(all(c["match"]["unmatched"] for c in partial))
        self.assertTrue(all(len(c["match"]["terms"]) >= 2 for c in rows))

    def test_relaxed_ranking_is_stable_across_hash_seeds_and_unicode(self):
        import os
        values = []
        for seed in ("13", "31"):
            result = subprocess.run([sys.executable, query.__file__, "search", "defesa montarias classes",
                    "--metadata-only", "--relaxed"], env=dict(os.environ, PYTHONHASHSEED=seed),
                    capture_output=True, timeout=15)
            self.assertEqual(result.returncode, 0, result.stderr)
            values.append(result.stdout)
        self.assertEqual(*values)
        self.assertEqual(self.collection.search("PROFISSÕES ARTESANATO", relaxed=True),
                         self.collection.search("profissoes artesanato", relaxed=True))

    def test_compact_cli_corruption_blocks_all_new_paths(self):
        for name in query.SOURCES:
            directory = self.fixture()
            with (directory / name).open("ab") as file:
                file.write(b"\n")
            for args in (["overview"], ["search", "avatar customization", "--relaxed", "--metadata-only"]):
                out, err = io.StringIO(), io.StringIO()
                with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                    code = query.main(["--brains-dir", str(directory), *args])
                self.assertEqual(code, 2)
                self.assertEqual(out.getvalue(), "")
                self.assertIn("integrity mismatch", err.getvalue())

    def test_invalid_vocabulary_is_clear_and_does_not_change_strict_commands(self):
        for content in ('{', '{"schema_version":2}', json.dumps({"schema_version":1,
                "groups":[{"name":"bad","equivalents":[{}],"related":[]}],
                "context_terms":[],"stop_words":[],"qualifiers":[]})):
            with tempfile.TemporaryDirectory() as folder:
                path = Path(folder) / "vocabulary.json"
                path.write_text(content)
                with mock.patch.object(query, "DEFAULT_VOCABULARY", path):
                    with self.assertRaises(query.BrainError):
                        self.collection.search("combat", relaxed=True)
                    self.assertEqual(len(self.collection.indexes()), 3)
                    self.assertTrue(self.collection.search("proveniência"))

    def test_new_search_input_errors_remain_output_free(self):
        for args in (["search", "", "--relaxed"], ["search", "combat", "--relaxed", "--limit", "0"],
                     ["search", "a e de", "--metadata-only"], ["get", "CRE-010", "ENG-999"]):
            out, err = io.StringIO(), io.StringIO()
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                code = query.main(args)
            self.assertEqual(code, 2)
            self.assertFalse(out.getvalue())
            self.assertTrue(err.getvalue())


    def test_exploratory_query_work_is_bounded(self):
        for text in ("x" * 4097, " ".join("word" + str(i) for i in range(65))):
            with self.assertRaisesRegex(query.BrainError, "Relaxed query"):
                self.collection.search(text, relaxed=True)


    def test_benchmark_missing_revision_preserves_output(self):
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder) / "result.json"
            output.write_text("preserved")
            result = subprocess.run([sys.executable, str(Path(query.__file__).with_name("benchmark_brain_query.py")),
                    "--baseline-ref", "no-such-brain-baseline", "--output", str(output)],
                    capture_output=True, text=True, timeout=15)
            self.assertEqual(result.returncode, 1)
            self.assertIn("Baseline revision unavailable", result.stderr)
            self.assertEqual(output.read_text(), "preserved")


if __name__ == "__main__":
    unittest.main()
