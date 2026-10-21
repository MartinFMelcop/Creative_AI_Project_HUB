#!/usr/bin/env python3
"""Validate lab registries and maintained HUB/lab Markdown targets; stdlib only.

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

from reference_library import validate_library
from brain_query import Collection, SOURCES

ROOT = Path(__file__).resolve().parents[1]
# The original wrapper is maintained. Standalone validator fixtures stay bounded
# to their lab; a wrapped HUB also owns its root README/AGENTS and backlinks.
WRAPPED_HUB = ROOT.name == "martin-creative-ai-lab" and ROOT.parent.name == "martin-creative-ai-lab-v0.2.0"
DOCUMENT_ROOT = ROOT.parent.parent if WRAPPED_HUB else ROOT
ERRORS = []
STATUSES = {"seed", "triage", "active", "paused", "archived", "retired", "transition"}
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
    elif not ((destination.is_file() or destination.is_dir()) if directory is None else
              destination.is_dir() if directory else destination.is_file()):
        kind = "file or directory" if directory is None else "directory" if directory else "file"
        fail(f"{label}: missing {kind}: {value}")


def evidence_refs(row, label):
    refs = row.get("evidence")
    if not isinstance(refs, list):
        fail(f"{label}: evidence must be a list")
        return
    for index, ref in enumerate(refs):
        local_reference(ref, f"{label}: evidence[{index}]")


def string_list(row, field, label, *, nonempty=False):
    values = row.get(field)
    if (not isinstance(values, list) or (nonempty and not values)
            or any(not isinstance(value, str) or not value.strip() for value in values)):
        fail(f"{label}: {field} must be a {'nonempty ' if nonempty else ''}list of nonempty strings")
        return []
    if len(values) != len(set(values)):
        fail(f"{label}: duplicate {field}")
    return values


def validate_origin_transition(projects, ids):
    """An origin inventory is not a list of eleven implemented laboratories."""
    path = ROOT / "labs/origins.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        fail(f"origin transition: {exc}")
        return
    if not isinstance(data, dict) or data.get("schema_version") != 1:
        fail("origin transition: expected object with schema_version 1")
        return
    try:
        date.fromisoformat(data.get("updated_at", ""))
    except (TypeError, ValueError):
        fail("origin transition: invalid updated_at")
    if not isinstance(data.get("baseline_commit"), str) or not re.fullmatch(r"[0-9a-f]{40}", data["baseline_commit"]):
        fail("origin transition: baseline_commit must identify the inspected Git baseline")
    if not isinstance(data.get("scope"), str) or not data["scope"].strip():
        fail("origin transition: missing scope")
    origins, labs = data.get("origins"), data.get("labs")
    if not isinstance(origins, list) or not isinstance(labs, list):
        fail("origin transition: origins and labs must be lists")
        return
    expected_ids = {f"P{index:02d}" for index in range(1, 12)}
    if ids != expected_ids:
        fail("origin transition: the preserved registry must contain exactly P01–P11")
    origin_ids, instrumented = set(), set()
    project_by_id = {row.get("id"): row for row in projects if isinstance(row.get("id"), str)}
    for row in origins:
        if not isinstance(row, dict):
            fail("origin transition: origin must be an object")
            continue
        item_id = row.get("id")
        label = f"origin transition {item_id}"
        if not isinstance(item_id, str) or item_id not in ids:
            fail(f"{label}: unknown origin")
        elif item_id in origin_ids:
            fail(f"{label}: duplicate origin")
        else:
            origin_ids.add(item_id)
        status = row.get("transition_status")
        if status not in ("preserved_pending_extraction", "pilot_instrumented", "seed_only"):
            fail(f"{label}: invalid transition_status")
        if status == "pilot_instrumented" and isinstance(item_id, str):
            instrumented.add(item_id)
        if status == "seed_only" and (not isinstance(item_id, str)
                or project_by_id.get(item_id, {}).get("maturity") != "M0"):
            fail(f"{label}: seed_only requires an M0 origin")
        for field in ("candidate_destinations", "preservation_risks"):
            string_list(row, field, label, nonempty=True)
        string_list(row, "reusable_capabilities", label, nonempty=status != "seed_only")
        string_list(row, "dependencies", label)
        for value in string_list(row, "source_paths", label, nonempty=status != "seed_only"):
            local_reference(value, f"{label}: source_paths", directory=None)
        for value in string_list(row, "execution_evidence", label, nonempty=status != "seed_only"):
            local_reference(value, f"{label}: execution_evidence")
        for consumer in string_list(row, "existing_consumers", label):
            if consumer not in ids:
                fail(f"{label}: unknown existing_consumer {consumer}")
        if not isinstance(row.get("extraction_next"), str) or not row["extraction_next"].strip():
            fail(f"{label}: missing extraction_next")
    if origin_ids != expected_ids or len(origins) != 11:
        fail("origin transition: inventory must contain exactly one row for each P01–P11")

    lab_ids, implemented_origins = set(), set()
    for row in labs:
        if not isinstance(row, dict):
            fail("origin transition: lab must be an object")
            continue
        item_id = row.get("id")
        label = f"origin transition lab {item_id}"
        if not isinstance(item_id, str) or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", item_id):
            fail(f"{label}: invalid lab id")
        elif item_id in lab_ids:
            fail(f"{label}: duplicate lab")
        else:
            lab_ids.add(item_id)
        origin_projects = string_list(row, "origin_projects", label, nonempty=True)
        if any(value not in ids for value in origin_projects):
            fail(f"{label}: unknown origin_projects")
        if not isinstance(row.get("question"), str) or not row["question"].strip():
            fail(f"{label}: missing question")
        if row.get("status") == "implemented":
            implemented_origins.update(origin_projects)
            local_reference(row.get("path"), f"{label}: path", directory=True)
            local_reference(row.get("instrument"), f"{label}: instrument")
            refs = string_list(row, "evidence", label, nonempty=True)
            for value in refs:
                local_reference(value, f"{label}: evidence")
            if isinstance(row.get("path"), str) and isinstance(row.get("instrument"), str):
                try:
                    lab_path = (ROOT / row["path"]).resolve()
                    if not lab_path.is_relative_to(ROOT / "labs"):
                        fail(f"{label}: implemented path must be inside labs/")
                    if not (ROOT / row["instrument"]).resolve().is_relative_to(lab_path):
                        fail(f"{label}: instrument must belong to its lab path")
                except (OSError, ValueError, RuntimeError) as exc:
                    fail(f"{label}: invalid lab path: {exc}")
        elif row.get("status") == "candidate":
            if any(field in row for field in ("path", "instrument", "evidence")):
                fail(f"{label}: a candidate cannot claim implemented path, instrument or evidence")
        else:
            fail(f"{label}: invalid lab status")
    # Labs may be retired without manufacturing a replacement. Existing origin
    # claims still require a real implemented consumer and its evidence above.
    if not instrumented.issubset(implemented_origins):
        fail("origin transition: pilot_instrumented origins require an implemented lab consumer")


def main():
    projects = read_registry("projects.json", "projects")
    transfers = read_registry("transfers.json", "transfers")
    assets = read_registry("assets.json", "assets")
    sources = read_registry("legacy_sources.json", "sources")
    ids = {r["id"] for r in projects if isinstance(r.get("id"), str)}
    source_ids = {r["id"] for r in sources if isinstance(r.get("id"), str)}
    reference_ids, historical_roots = set(), set()
    brain_sources = {ROOT / "brains" / name for name in SOURCES}
    try:
        Collection(ROOT / "brains")
    except (OSError, ValueError, KeyError, TypeError) as exc:
        fail(f"brain collection: {exc}")
    try:
        library = validate_library(ROOT, ids)
        reference_ids = library["collection_ids"]
        historical_roots = set(library["source_roots"])
    except (OSError, ValueError, KeyError, TypeError, BadZipFile) as exc:
        fail(f"reference library: {exc}")
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
        if row.get("role") != "historical_origin":
            fail(f"{label}: role must be historical_origin")
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
        if "reference_collection_ids" in row:
            references = row["reference_collection_ids"]
            if not isinstance(references, list) or not all(isinstance(v, str) and v in reference_ids for v in references):
                fail(f"{label}: unknown reference_collection_ids")
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
    validate_origin_transition(projects, ids)

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

    # Dependencies, validated snapshots and exact supplied brain sources are data,
    # not maintained navigation. Owned READMEs/AGENTS/program docs stay checked.
    documents = []
    if WRAPPED_HUB:
        documents.extend(DOCUMENT_ROOT / name for name in ("README.md", "AGENTS.md")
                         if (DOCUMENT_ROOT / name).is_file())
    for directory, subdirectories, files in os.walk(ROOT):
        subdirectories[:] = sorted(name for name in subdirectories if name not in {".git", "node_modules"}
                                   and Path(directory) / name not in historical_roots)
        documents.extend(Path(directory) / name for name in files
                         if name.endswith(".md") and Path(directory) / name not in brain_sources)
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
            label = path.relative_to(DOCUMENT_ROOT)
            if not destination.is_relative_to(DOCUMENT_ROOT):
                fail(f"{label}: target leaves repository: {target}")
            elif not destination.exists():
                fail(f"{label}: missing target: {target}")
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
