#!/usr/bin/env python3
"""Consult the immutable brain collection using only its supplied catalog.

The catalog locates text; it does not establish truth or authorize execution.
No network, generated summaries, embeddings or source-file writes are involved.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
import unicodedata
from urllib.parse import unquote


DEFAULT_BRAINS = Path(__file__).resolve().parents[1] / "brains"
VOLUMES = {"ENGINEERING_BRAIN.md": ("ENG", 49),
           "SCIENTIFIC_BRAIN.md": ("SCI", 85),
           "CREATIVE_BRAIN.md": ("CRE", 100)}
CATALOG = "CATALOGO_DE_CONSULTA.json"
LIBRARY = "BIBLIOTECA_DE_CONHECIMENTO_APLICADO.md"
SOURCES = (*VOLUMES, CATALOG, LIBRARY)
HEADINGS = re.compile(r"^(#{1,6}) (.+)$", re.MULTILINE)
CHAPTER = re.compile(r"^(\d+)\. (.+)$")
LINK = re.compile(r"\[[^\]\n]*\]\(([^\s)]+)\)")
STOP_WORDS = set("a an and as at com como da das de do dos e em for how is na nas no nos o of os ou para por que the to um uma what which with".split())


class BrainError(ValueError):
    """A missing, corrupted or inconsistent collection, or an invalid query."""


def fold(text: str) -> str:
    """Case- and accent-insensitive matching; source text is never normalized."""
    return "".join(c for c in unicodedata.normalize("NFKD", text.casefold())
                   if not unicodedata.combining(c))


def heading_anchor(heading: str, *, collapsed: bool = False) -> str:
    """GitHub-style Unicode heading fragment, or the supplied catalog convention."""
    anchor = re.sub(r"[^\w\s-]", "", heading.lower())
    anchor = re.sub(r"\s", "-", anchor)
    return re.sub(r"-+", "-", anchor) if collapsed else anchor


def read_json(text: str, filename: str):
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise BrainError(f"Invalid JSON in {filename}: {exc.msg} at line {exc.lineno}") from exc


class Collection:
    def __init__(self, directory: Path = DEFAULT_BRAINS):
        self.directory = Path(directory)
        self.texts: dict[str, str] = {}
        self.chapters: dict[str, dict] = {}
        self.warnings: list[dict] = []
        self.counts: dict[str, int] = {}
        self._check_pins()
        self.catalog = read_json(self.texts[CATALOG], CATALOG)
        self._check_catalog()
        self._check_links()

    def _read(self, filename: str) -> bytes:
        try:
            path = self.directory / filename
            if path.is_symlink():
                raise BrainError(f"Source must be a regular file, not a symlink: {filename}")
            return path.read_bytes()
        except OSError as exc:
            raise BrainError(f"Cannot read {filename}: {exc.strerror}") from exc

    def _check_pins(self):
        try:
            raw = self._read("integrity.json").decode("utf-8")
        except UnicodeDecodeError as exc:
            raise BrainError("integrity.json is not valid UTF-8") from exc
        pins = read_json(raw, "integrity.json")
        if (not isinstance(pins, dict) or pins.get("schema_version") != 1
                or not isinstance(pins.get("files"), dict)
                or set(pins["files"]) != set(SOURCES)):
            raise BrainError("integrity.json must pin exactly the five supplied source files (schema 1)")
        self.pins = pins
        for name in SOURCES:
            data = self._read(name)
            pin = pins["files"][name]
            if (not isinstance(pin, dict) or set(pin) != {"bytes", "sha256"}
                    or type(pin["bytes"]) is not int or pin["bytes"] < 1
                    or not isinstance(pin["sha256"], str)
                    or not re.fullmatch(r"[0-9a-f]{64}", pin["sha256"])):
                raise BrainError(f"Invalid size/hash pin for {name}")
            if len(data) != pin["bytes"] or hashlib.sha256(data).hexdigest() != pin["sha256"]:
                raise BrainError(f"Source integrity mismatch: {name}; preserve the supplied bytes, do not repin automatically")
            try:
                self.texts[name] = data.decode("utf-8")
            except UnicodeDecodeError as exc:
                raise BrainError(f"Source is not valid UTF-8: {name}") from exc
            if self.texts[name].startswith("\ufeff"):
                raise BrainError(f"Unexpected UTF-8 BOM in {name}")

    def _check_catalog(self):
        catalog = self.catalog
        if (not isinstance(catalog, dict) or not isinstance(catalog.get("purpose"), str)
                or not isinstance(catalog.get("volumes"), list)
                or len(catalog["volumes"]) != len(VOLUMES)):
            raise BrainError("Catalog must contain its purpose and the three supplied volumes")
        seen_files = set()
        for volume in catalog["volumes"]:
            if not isinstance(volume, dict) or volume.get("file") not in VOLUMES:
                raise BrainError("Catalog contains an unknown or unsafe volume path")
            filename = volume["file"]
            if filename in seen_files:
                raise BrainError(f"Duplicate catalog volume: {filename}")
            seen_files.add(filename)
            prefix, expected_count = VOLUMES[filename]
            if not all(isinstance(volume.get(key), str) and volume[key] for key in ("title", "scope")):
                raise BrainError(f"Missing volume title/scope: {filename}")
            entries = volume.get("chapters")
            if not isinstance(entries, list) or len(entries) != expected_count:
                raise BrainError(f"Expected {expected_count} catalog chapters in {filename}")
            text = self.texts[filename]
            headings = list(HEADINGS.finditer(text))
            source_chapters = []
            section = None
            for index, match in enumerate(headings):
                level, title = match.groups()
                if len(level) == 2:
                    section = title
                number = CHAPTER.fullmatch(title) if len(level) == 3 else None
                if not number:
                    continue
                end = next((h.start() for h in headings[index + 1:] if len(h[1]) <= 3), len(text))
                source_chapters.append((int(number[1]), number[2], section, match.start(), end))
            if len(source_chapters) != expected_count:
                raise BrainError(f"Expected {expected_count} actual chapter headings in {filename}")
            for ordinal, (entry, actual) in enumerate(zip(entries, source_chapters), 1):
                number, title, section, start, end = actual
                chapter_id = f"{prefix}-{ordinal:03d}"
                if not isinstance(entry, dict) or set(entry) != {"id", "chapter", "title", "section", "question", "anchor", "editorial_status", "preview"}:
                    raise BrainError(f"Invalid catalog fields for {chapter_id}")
                content = text[start:end]
                question = re.search(r"^\*\*Pergunta-chave:\*\* (.+)$", content, re.MULTILINE)
                status = re.search(r"^\*\*Estatuto editorial:\*\* ([DAHEV])(?: |$)", content, re.MULTILINE)
                actual_status = status[1] if status else None
                if (entry["id"] != chapter_id or type(entry["chapter"]) is not int
                        or entry["chapter"] != ordinal or number != ordinal
                        or entry["title"] != title or entry["section"] != section):
                    raise BrainError(f"Catalog/heading/section mismatch for {chapter_id}")
                if not question or entry["question"] != question[1]:
                    raise BrainError(f"Catalog/question mismatch for {chapter_id}")
                if (entry["editorial_status"] != actual_status
                        or (prefix == "CRE" and actual_status is None)):
                    raise BrainError(f"Catalog/editorial-status mismatch for {chapter_id}")
                if entry["anchor"] != heading_anchor(f"{number}. {title}", collapsed=True):
                    raise BrainError(f"Catalog/anchor mismatch for {chapter_id}")
                if not isinstance(entry["preview"], str):
                    raise BrainError(f"Invalid catalog preview for {chapter_id}")
                self.chapters[chapter_id] = {
                    **entry, "path": filename,
                    "source_fragment": heading_anchor(f"{number}. {title}"),
                    "line_start": text.count("\n", 0, start) + 1,
                    "line_end": text.count("\n", 0, end),
                    "content": content,
                }
            self.counts[prefix] = expected_count

    def _check_links(self):
        """Check local targets; retain and report inherited renderer differences."""
        anchors = {}
        aliases = {}
        for name, text in self.texts.items():
            if name.endswith(".md"):
                anchors[name] = {heading_anchor(m[2]) for m in HEADINGS.finditer(text)}
                aliases[name] = {heading_anchor(m[2], collapsed=True): heading_anchor(m[2])
                                 for m in HEADINGS.finditer(text)}
        link_count = 0
        for filename, text in self.texts.items():
            if not filename.endswith(".md"):
                continue
            for match in LINK.finditer(text):
                target = unquote(match[1])
                if re.match(r"^[A-Za-z][A-Za-z0-9+.-]*:", target):
                    continue  # External references are not fetched or rights-cleared by this check.
                name, _, fragment = target.partition("#")
                name = name or filename
                if name not in SOURCES:
                    raise BrainError(f"Unknown local link in {filename}: {target}")
                link_count += 1
                if fragment and fragment not in anchors.get(name, set()):
                    if fragment in aliases.get(name, {}):
                        self.warnings.append({
                            "file": filename, "line": text.count("\n", 0, match.start()) + 1,
                            "target": target, "source_fragment": aliases[name][fragment],
                            "kind": "inherited_heading_fragment_difference",
                        })
                    else:
                        raise BrainError(f"Broken local link in {filename}: {target}")
        self.link_count = link_count

    def report(self):
        return {"ok": True, "files": self.pins["files"], "chapters": self.counts,
                "total_chapters": len(self.chapters), "local_links": self.link_count,
                "source_warnings": self.warnings,
                "limits": "Pins detect byte changes, not factual accuracy, rights or independent validation. Inherited fragment differences are reported, not repaired."}

    def indexes(self):
        return [{"file": v["file"], "title": v["title"], "scope": v["scope"],
                 "chapters": [{k: c[k] for k in ("id", "chapter", "title", "question", "editorial_status")}
                              for c in v["chapters"]]} for v in self.catalog["volumes"]]

    def get(self, chapter_id: str):
        key = chapter_id.upper()
        if key not in self.chapters:
            raise BrainError(f"Unknown chapter ID: {chapter_id}; use indexes or search")
        return self.chapters[key].copy()

    def search(self, query: str, limit: int = 5):
        if not query.strip():
            raise BrainError("Search query must not be empty")
        if not 1 <= limit <= 234:
            raise BrainError("Search limit must be between 1 and 234")
        normalized = fold(query)
        if normalized.upper() in self.chapters:
            return [self.get(normalized)]
        terms = [word for word in re.findall(r"\w+", normalized) if word not in STOP_WORDS]
        if not terms:
            raise BrainError("Search query needs an ID or a meaningful title/question/keyword")
        ranked = []
        for ordinal, chapter in enumerate(self.chapters.values()):
            fields = {key: fold(chapter[key]) for key in ("title", "question", "section", "preview")}
            tokens = {key: set(re.findall(r"\w+", value)) for key, value in fields.items()}
            if not all(any(term in words for words in tokens.values()) for term in terms):
                continue
            score = sum(weight for key, weight in (("title", 10), ("question", 5), ("section", 1), ("preview", 1))
                        for term in terms if term in tokens[key])
            score += 100 if normalized == fields["title"] else 0
            score += 50 if normalized == fields["question"] else 0
            ranked.append((-score, ordinal, chapter))
        return [dict(chapter, search_score=-score) for score, _, chapter in sorted(ranked)[:limit]]


def parser():
    command = argparse.ArgumentParser(description=__doc__)
    command.add_argument("--brains-dir", type=Path, default=DEFAULT_BRAINS,
                         help="Collection directory (defaults beside this repository's tools)")
    sub = command.add_subparsers(dest="command", required=True)
    sub.add_parser("check", help="Verify supplied bytes, UTF-8, catalog, chapters and local links")
    sub.add_parser("indexes", help="Read all three supplied catalog indices")
    get = sub.add_parser("get", help="Retrieve exact complete source chapters by ID")
    get.add_argument("ids", nargs="+")
    search = sub.add_parser("search", help="Stable accent-insensitive catalog search; returns full chapters")
    search.add_argument("query")
    search.add_argument("--limit", type=int, default=5)
    return command


def main(argv=None):
    args = parser().parse_args(argv)
    try:
        collection = Collection(args.brains_dir)
        result = (collection.report() if args.command == "check" else collection.indexes()
                  if args.command == "indexes" else [collection.get(key) for key in args.ids]
                  if args.command == "get" else collection.search(args.query, args.limit))
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except BrainError as exc:
        print(f"brain_query: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
