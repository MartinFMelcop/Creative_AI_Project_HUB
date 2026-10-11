#!/usr/bin/env python3
"""Validate this lab's registries and local Markdown file targets; stdlib only.

This checks documentary structure, not runtime, creative quality or link anchors.
"""

import hashlib
import json
import os
import re
import sys
from datetime import date
from pathlib import Path
from urllib.parse import unquote, urlparse
from zipfile import ZipFile, BadZipFile

ROOT = Path(__file__).resolve().parents[1]
ERRORS = []
STATUSES = {"seed", "triage", "active", "paused", "archived", "retired"}
MATURITIES = {f"M{i}" for i in range(7)}


def fail(message):
    ERRORS.append(message)


def read_registry(filename, key):
    path = ROOT / "registry" / filename
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        fail(f"{filename}: {exc}")
        return []
    if not isinstance(data, dict) or data.get("schema_version") != 1:
        fail(f"{filename}: expected object with schema_version 1")
        return []
    try:
        date.fromisoformat(data.get("updated_at", ""))
    except (TypeError, ValueError):
        fail(f"{filename}: invalid updated_at")
    rows = data.get(key)
    if not isinstance(rows, list):
        fail(f"{filename}: {key} must be a list")
        return []
    valid_rows = []
    seen = set()
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            fail(f"{filename}[{index}]: expected object")
            continue
        item_id = row.get("id")
        if not isinstance(item_id, str) or not item_id:
            fail(f"{filename}[{index}]: missing string id")
        elif item_id in seen:
            fail(f"{filename}: duplicate id {item_id}")
        else:
            seen.add(item_id)
        valid_rows.append(row)
    return valid_rows


def list_refs(row, field, valid_ids, label):
    refs = row.get(field, [])
    if not isinstance(refs, list):
        fail(f"{label}: {field} must be a list")
        return
    for ref in refs:
        if not isinstance(ref, str) or ref not in valid_ids:
            fail(f"{label}: unknown project in {field}: {ref!r}")


def local_reference(value, label, *, directory=False):
    """Registry paths are literal lab-relative paths, never URLs or anchors."""
    if not isinstance(value, str) or not value.strip():
        fail(f"{label}: expected nonempty local path")
        return
    path = Path(value)
    if path.is_absolute() or re.match(r"^[A-Za-z][A-Za-z0-9+.-]*:", value):
        fail(f"{label}: expected relative path: {value}")
        return
    try:
        destination = (ROOT / path).resolve()
    except (OSError, ValueError, RuntimeError) as exc:
        fail(f"{label}: invalid path: {value!r}: {exc}")
        return
    if not destination.is_relative_to(ROOT):
        fail(f"{label}: target leaves repository: {value}")
    elif not (destination.is_dir() if directory else destination.is_file()):
        kind = "directory" if directory else "file"
        fail(f"{label}: missing {kind}: {value}")


def evidence_refs(row, label):
    refs = row.get("evidence")
    if not isinstance(refs, list):
        fail(f"{label}: evidence must be a list")
        return
    for index, ref in enumerate(refs):
        local_reference(ref, f"{label}: evidence[{index}]")


def main():
    projects = read_registry("projects.json", "projects")
    transfers = read_registry("transfers.json", "transfers")
    assets = read_registry("assets.json", "assets")
    sources = read_registry("legacy_sources.json", "sources")
    ids = {r["id"] for r in projects if isinstance(r.get("id"), str)}
    source_ids = {r["id"] for r in sources if isinstance(r.get("id"), str)}
    slugs = set()
    for row in projects:
        label = str(row.get("id", "<missing-id>"))
        for field in ("name", "slug", "phase", "origin", "next_action"):
            if not isinstance(row.get(field), str) or not row[field].strip():
                fail(f"{label}: missing nonempty {field}")
        slug = row.get("slug")
        if isinstance(slug, str):
            if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", slug):
                fail(f"{label}: invalid slug {slug!r}")
            if slug in slugs:
                fail(f"{label}: duplicate slug {slug!r}")
            slugs.add(slug)
        if not isinstance(row.get("status"), str) or row["status"] not in STATUSES:
            fail(f"{label}: invalid status")
        if not isinstance(row.get("maturity"), str) or row["maturity"] not in MATURITIES:
            fail(f"{label}: invalid maturity")
        evidence_refs(row, label)
        if "working_path" in row:
            local_reference(row["working_path"], f"{label}: working_path", directory=True)
        if "source_id" in row:
            source_id = row["source_id"]
            if not isinstance(source_id, str) or source_id not in source_ids:
                fail(f"{label}: unknown source_id: {source_id!r}")
        list_refs(row, "related_projects", ids, label)
    for row in transfers:
        label = str(row.get("id", "<missing-id>"))
        evidence_refs(row, label)
        for field in ("source_project", "target_project"):
            if not isinstance(row.get(field), str) or row[field] not in ids:
                fail(f"{label}: unknown {field}")
        if row.get("source_project") == row.get("target_project"):
            fail(f"{label}: transfer requires different projects")
    for row in assets:
        if "evidence" in row:
            evidence_refs(row, str(row.get("id")))
        list_refs(row, "consumer_projects", ids, str(row.get("id")))

    try:
        source_data = json.loads((ROOT / "registry/legacy_sources.json").read_text())
        archive_meta = source_data["source_archive"]
        archive_path = (ROOT / archive_meta["path"]).resolve()
        if not archive_path.is_relative_to(ROOT):
            raise ValueError("source archive leaves repository")
        if hashlib.sha256(archive_path.read_bytes()).hexdigest() != archive_meta["sha256"]:
            fail("legacy source archive hash mismatch")
        with ZipFile(archive_path) as archive:
            for source in sources:
                if source.get("project_id") not in ids:
                    fail(f"{source['id']}: unknown source project")
                inventory = source["inventory"]
                if len(inventory) != source["file_count"]:
                    fail(f"{source['id']}: inventory count mismatch")
                if sum(bool(f["preserved"]) for f in inventory) != source["preserved_file_count"]:
                    fail(f"{source['id']}: preservation count mismatch")
                if sum(bool(f["content_inspected"]) for f in inventory) != source["inspected_file_count"]:
                    fail(f"{source['id']}: inspection count mismatch")
                for item in inventory:
                    if not item["preserved"]:
                        continue
                    content = archive.read(source["archive_prefix"] + "/" + item["path"])
                    if hashlib.sha256(content).hexdigest() != item["sha256"]:
                        fail(f"{source['id']}: preserved content differs: {item['path']}")
    except (OSError, ValueError, KeyError, TypeError, BadZipFile) as exc:
        fail(f"legacy source validation: {exc}")

    # npm dependencies contain upstream documentation outside this lab's ownership.
    documents = []
    for directory, subdirectories, files in os.walk(ROOT):
        subdirectories[:] = sorted(name for name in subdirectories if name not in {".git", "node_modules"})
        documents.extend(Path(directory) / name for name in files if name.endswith(".md"))
    documents.sort()
    checked_links = 0
    for path in documents:
        if ".git" in path.parts:
            continue
        body = path.read_text(encoding="utf-8")
        # Ignore fenced code examples. This supports simple inline Markdown links.
        body = re.sub(r"```.*?```", "", body, flags=re.S)
        for match in re.finditer(r"\[[^\]\n]+\]\(([^)\n]+)\)", body):
            target = match.group(1).strip()
            parsed = urlparse(target)
            if parsed.scheme or target.startswith("#"):
                continue
            relative = unquote(parsed.path)
            if not relative:
                continue
            destination = (path.parent / relative).resolve()
            if not destination.is_relative_to(ROOT):
                fail(f"{path.relative_to(ROOT)}: target leaves repository: {target}")
            elif not destination.exists():
                fail(f"{path.relative_to(ROOT)}: missing target: {target}")
            checked_links += 1

    if ERRORS:
        for error in ERRORS:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(
        f"PASS: {len(projects)} projects, {len(transfers)} transfers, "
        f"{len(assets)} assets, {len(sources)} legacy sources; {checked_links} local file links."
    )
    print("Documentary checks only; no game, model benchmark or media runtime executed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
