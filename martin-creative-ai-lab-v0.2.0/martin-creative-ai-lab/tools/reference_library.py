#!/usr/bin/env python3
"""Validate local historical references and discover sources without executing them."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import sys
from zipfile import ZipFile, BadZipFile

ROOT = Path(__file__).resolve().parents[1]
CONTROL_NAMES = {"AGENTS.md", ".gitignore", ".gitattributes", ".gitmodules"}
TEXT_SUFFIXES = {"", ".md", ".csv", ".json", ".jsonl", ".rb", ".py", ".yml",
                 ".txt", ".ini", ".rxproj", ".sha256"}
CONTRIBUTION_STATES = {"candidate", "verified_in_origin", "adapted",
                       "integrated_into_north_star", "externally_validated"}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def relative(value):
    require(isinstance(value, str) and value and "\\" not in value and "\0" not in value,
            f"Invalid reference path: {value!r}")
    p = PurePosixPath(value)
    require(not p.is_absolute() and ".." not in p.parts and p.as_posix() == value
            and not re.match(r"^[A-Za-z][A-Za-z0-9+.-]*:", value),
            f"Noncanonical reference path: {value!r}")
    return p


def local(root, value, *, directory=False):
    p = relative(value)
    target = root / p
    require(not any((root / Path(*p.parts[:i])).is_symlink()
                    for i in range(1, len(p.parts) + 1)), f"Linked reference: {value}")
    require(target.resolve().is_relative_to(root.resolve()), f"Reference escapes root: {value}")
    require(target.is_dir() if directory else target.is_file(), f"Missing reference: {value}")
    return target


def obj(path):
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        raise ValueError(f"Cannot read reference metadata {path.name}: {e}") from e
    require(isinstance(data, dict) and type(data.get("schema_version")) is int and data["schema_version"] == 1,
            f"Invalid reference schema: {path.name}")
    return data


def rows(data, key, label):
    result = data.get(key)
    require(isinstance(result, list), f"{label}: {key} must be a list")
    require(all(isinstance(item, dict) for item in result), f"{label}: invalid {key} entry")
    return result


def unique(items, key, label):
    names = [item.get(key) for item in items]
    require(all(isinstance(n, str) and n for n in names), f"{label}: missing {key}")
    require(len(names) == len(set(names)), f"{label}: duplicate {key}")
    return set(names)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_library(root=ROOT, project_ids=None):
    root = Path(root).resolve()
    if project_ids is None:
        projects = obj(root / "registry/projects.json")
        project_ids = {p["id"] for p in rows(projects, "projects", "projects")}
    catalog = obj(root / "references/catalog.json")
    collections = rows(catalog, "collections", "catalog")
    collection_ids = unique(collections, "id", "catalog")
    old = obj(root / "registry/legacy_sources.json")
    # This remains the existing archive's contract, rather than a replacement.
    require(catalog.get("legacy_archive") == old.get("source_archive"),
            "Previous legacy archive metadata differs")
    old_archive = local(root, old["source_archive"]["path"])
    require(digest(old_archive) == old["source_archive"]["sha256"],
            "Previous legacy archive hash differs")
    source_roots, inventories, topics = [], {}, {}
    imported_total = excluded_total = 0
    for collection in collections:
        cid = collection["id"]
        kind = collection.get("kind")
        if kind == "attachment":
            require(collection.get("status") == "unavailable", f"{cid}: unsupported attachment state")
            require(collection.get("imported_count") == 0
                    and collection.get("full_archive_preserved") is False
                    and all(collection.get(k) is None for k in
                            ["sha256", "detected_version", "file_count", "inventory_path", "source_root"]),
                    f"{cid}: unavailable attachment claims preserved content")
            require(bool(collection.get("blocker")) and collection.get("authority_status") == "unverified",
                    f"{cid}: unavailable literary authority must remain unverified")
            continue
        if kind == "historical_report":
            require(collection.get("status") == "documented_only"
                    and collection.get("imported_count") == 0
                    and collection.get("source_root") is None
                    and collection.get("full_archive_preserved") is False,
                    f"{cid}: historical report claims imported payload")
            local(root, collection.get("report_path"))
            local(root, collection.get("reported_details_path"))
            continue
        require(kind == "repository_snapshot", f"{cid}: unknown collection kind")
        commit = collection.get("source_commit")
        require(isinstance(commit, str) and re.fullmatch(r"[0-9a-f]{40}", commit),
                f"{cid}: invalid source commit")
        require(isinstance(collection.get("source_tree"), str)
                and re.fullmatch(r"[0-9a-f]{40}", collection["source_tree"]), f"{cid}: invalid source tree")
        source_name = relative(collection.get("source_root"))
        require(source_name.parts[0] == "references" and len(source_name.parts) >= 5
                and source_name.parts[-3:] == ("snapshots", commit, "source"),
                f"{cid}: invalid snapshot root")
        source_root = local(root, str(source_name), directory=True)
        require(source_root not in source_roots, f"{cid}: duplicate source root")
        source_roots.append(source_root)
        inventory_path = local(root, collection.get("inventory_path"))
        require(inventory_path == source_root.parent / "inventory.json", f"{cid}: inventory location differs")
        inventory = obj(inventory_path)
        require(inventory.get("source_commit") == commit and inventory.get("collection_id") == cid
                and inventory.get("source_tree") == collection.get("source_tree"),
                f"{cid}: snapshot provenance differs")
        files = rows(inventory, "files", cid)
        unique(files, "source_path", cid)
        imported, excluded, actual_paths = [], [], set()
        for item in files:
            name = item["source_path"]
            original = relative(name)
            require(item.get("classification") == "historical_reference", f"{cid}: source is not historical")
            require(re.fullmatch(r"[0-9a-f]{64}", str(item.get("sha256", "")))
                    and re.fullmatch(r"[0-9a-f]{40}", str(item.get("git_blob_sha", "")))
                    and type(item.get("size_bytes")) is int and item["size_bytes"] >= 0
                    and item.get("source_mode") in {"100644", "100755"}, f"{cid}: invalid file metadata: {name}")
            if item.get("status") == "excluded":
                require(item.get("local_path") is None and bool(item.get("exclusion_reason")),
                        f"{cid}: excluded source has payload or no reason: {name}")
                excluded.append(item)
                continue
            require(item.get("status") == "imported" and item.get("exclusion_reason") is None,
                    f"{cid}: invalid preservation state: {name}")
            mapped = name + ".reference" if original.name in CONTROL_NAMES else name
            expected = (source_name / mapped).as_posix()
            require(item.get("local_path") == expected, f"{cid}: original/local path mapping differs: {name}")
            target = local(root, expected)
            raw = target.read_bytes()
            require(original.suffix.lower() in TEXT_SUFFIXES and b"\0" not in raw,
                    f"{cid}: imported payload is not eligible reference text: {name}")
            try:
                raw.decode("utf-8-sig")
            except UnicodeDecodeError as e:
                raise ValueError(f"{cid}: imported payload is not UTF-8 text: {name}") from e
            require(len(raw) == item["size_bytes"] and hashlib.sha256(raw).hexdigest() == item["sha256"],
                    f"{cid}: source hash or size differs: {name}")
            blob = hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()
            require(blob == item["git_blob_sha"], f"{cid}: Git blob differs: {name}")
            require(target not in actual_paths, f"{cid}: duplicate local payload")
            actual_paths.add(target)
            imported.append(item)
        on_disk = {p for p in source_root.rglob("*") if p.is_file() or p.is_symlink()}
        require(on_disk == actual_paths, f"{cid}: unlisted or missing snapshot payload")
        for key, count in [("file_count", len(files)), ("imported_count", len(imported)),
                           ("excluded_count", len(excluded))]:
            require(type(collection.get(key)) is int and collection[key] == count, f"{cid}: {key} differs")
        require(collection.get("status") == ("partial_import" if excluded else "imported")
                and collection.get("full_archive_preserved") is False
                and collection.get("git_history_preserved") is False, f"{cid}: unsupported completeness claim")
        previous_id = collection.get("legacy_source_id")
        if previous_id:
            previous = next((s for s in old["sources"] if s["id"] == previous_id), None)
            require(previous is not None and previous["commit"] == commit, f"{cid}: previous source differs")
            by_name = {f["source_path"]: f for f in files}
            require(set(by_name) == {f["path"] for f in previous["inventory"]}, f"{cid}: previous tree differs")
            identical = 0
            with ZipFile(old_archive) as archive:
                for item in previous["inventory"]:
                    current = by_name[item["path"]]
                    require(current["git_blob_sha"] == item["git_blob_sha"]
                            and current["size_bytes"] == item["size_bytes"], f"{cid}: previous inventory differs")
                    if item["preserved"]:
                        raw = archive.read(previous["archive_prefix"] + "/" + item["path"])
                        require(current["status"] == "imported" and
                                hashlib.sha256(raw).hexdigest() == current["sha256"] == item["sha256"],
                                f"{cid}: previous selected bytes differ: {item['path']}")
                        identical += 1
                    elif item["content_inspected"]:
                        require(current["status"] == "excluded", f"{cid}: previously withheld source was imported: {item['path']}")
            require(identical == collection.get("prior_selected_identical"), f"{cid}: previous selection count differs")
        discovery = obj(local(root, collection.get("discovery_path")))
        require(discovery.get("collection_id") == cid, f"{cid}: discovery collection differs")
        entries = rows(discovery, "topics", "discovery")
        unique(entries, "id", "discovery")
        available = {f["source_path"] for f in imported}
        for topic in entries:
            paths = topic.get("source_paths")
            require(isinstance(paths, list) and paths and all(isinstance(p, str) for p in paths)
                    and len(paths) == len(set(paths)) and set(paths) <= available,
                    f"{cid}: invalid discovery reference: {topic['id']}")
        inventories[cid], topics[cid] = files, entries
        imported_total += len(imported)
        excluded_total += len(excluded)

    program = obj(root / "north-star/capabilities.json")
    require(program.get("name") == "North Star" and program.get("kind") == "program"
            and program.get("stage") == "foundation_only" and program.get("consumer_paths") == []
            and program.get("engine_selection") == "undecided", "Invalid North Star foundation state")
    capabilities = rows(program, "capabilities", "North Star")
    unique(capabilities, "id", "North Star")
    for cap in capabilities:
        label = cap["id"]
        state = cap.get("contribution_status")
        require(isinstance(state, str) and state in CONTRIBUTION_STATES, f"{label}: invalid contribution status")
        require(state in {"candidate", "verified_in_origin"}, f"{label}: foundation has no implemented North Star consumer")
        origins = cap.get("origin_projects")
        require(isinstance(origins, list) and all(isinstance(p, str) for p in origins)
                and len(origins) == len(set(origins)) and set(origins) <= project_ids,
                f"{label}: invalid origin project")
        refs = cap.get("reference_collections", [])
        require(isinstance(refs, list) and all(isinstance(p, str) for p in refs)
                and len(refs) == len(set(refs)) and set(refs) <= collection_ids, f"{label}: invalid origin reference")
        for key in ["scope", "applicability_hypothesis", "limits", "next_validation"]:
            require(isinstance(cap.get(key), str) and cap[key].strip(), f"{label}: missing {key}")
        evidence = cap.get("origin_evidence")
        require(isinstance(evidence, list), f"{label}: invalid evidence list")
        for name in evidence:
            local(root, name)
        require(state != "verified_in_origin" or (evidence and cap.get("origin_validation") == "execution_record_inspected"),
                f"{label}: origin verification needs a recorded execution, not source discovery")
    return {"catalog": catalog, "collection_ids": collection_ids, "source_roots": source_roots,
            "inventories": inventories, "topics": topics, "imported": imported_total,
            "excluded": excluded_total, "capabilities": len(capabilities)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("check")
    find = sub.add_parser("find")
    find.add_argument("--collection", default="REF-RAVE-36AF165")
    find.add_argument("--topic")
    find.add_argument("--module")
    find.add_argument("--name", default="")
    find.add_argument("--include-excluded", action="store_true")
    find.add_argument("--limit", type=int, default=12)
    args = parser.parse_args()
    try:
        library = validate_library(args.root)
        if args.command == "check":
            print(f"PASS: {len(library['collection_ids'])} reference records; {library['imported']} local files, "
                  f"{library['excluded']} explicit exclusions; {library['capabilities']} North Star capabilities.")
            print("Integrity and structured evidence boundaries only; no legacy scripts, engine or rights review executed.")
        else:
            require(1 <= args.limit <= 100, "Limit must be 1–100")
            require(args.collection in library["collection_ids"], "Unknown reference collection")
            files = library["inventories"].get(args.collection, [])
            if args.topic:
                topic = next((t for t in library["topics"].get(args.collection, []) if t["id"] == args.topic), None)
                require(topic is not None, "Unknown discovery topic")
                files = [f for f in files if f["source_path"] in topic["source_paths"]]
            files = [f for f in files if (args.include_excluded or f["status"] == "imported")
                     and (not args.module or f["source_path"].split("/")[0] == args.module)
                     and args.name.casefold() in f["source_path"].casefold()]
            collection = next(c for c in library["catalog"]["collections"] if c["id"] == args.collection)
            print(json.dumps({"collection": args.collection, "status": collection["status"],
                              "matches": len(files), "files": files[:args.limit]}, indent=2, ensure_ascii=False))
    except (OSError, ValueError, KeyError, TypeError, BadZipFile) as e:
        print(f"FAIL: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
