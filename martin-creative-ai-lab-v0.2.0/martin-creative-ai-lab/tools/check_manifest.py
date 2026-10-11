#!/usr/bin/env python3
"""Require complete maintained-lab coverage and matching SHA-256 hashes."""

import argparse
import hashlib
import os
import re
import subprocess
import sys
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = "MANIFEST.sha256"


def git_output(root, *args):
    result = subprocess.run(["git", "-C", str(root), *args], capture_output=True)
    if result.returncode:
        raise ValueError("Git inventory unavailable; use a working Git checkout.")
    return result.stdout


def maintained_files(root):
    repo = Path(os.fsdecode(git_output(root, "rev-parse", "--show-toplevel")).strip()).resolve()
    prefix = root.relative_to(repo)
    inventory = git_output(repo, "ls-files", "--cached", "--others", "--exclude-standard",
                           "--full-name", "-z", "--", prefix.as_posix())
    paths = {Path(os.fsdecode(name)).relative_to(prefix).as_posix()
             for name in inventory.split(b"\0") if name}
    return paths - {MANIFEST}


def read_manifest(path):
    entries = {}
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        match = re.fullmatch(r"([0-9a-f]{64})  (.+)", line)
        if not match:
            raise ValueError(f"Malformed manifest line {number}.")
        digest, name = match.groups()
        relative = PurePosixPath(name)
        if (relative.is_absolute() or ".." in relative.parts or
                relative.as_posix() != name or "\\" in name or name == MANIFEST):
            raise ValueError(f"Invalid manifest path on line {number}: {name!r}.")
        if name in entries:
            raise ValueError(f"Duplicate manifest entry: {name}.")
        entries[name] = digest
    return entries


def check(root, manifest=None):
    root = Path(root).resolve()
    expected = maintained_files(root)
    entries = read_manifest(Path(manifest) if manifest else root / MANIFEST)
    missing = expected - entries.keys()
    extra = entries.keys() - expected
    if missing:
        raise ValueError("Unlisted maintained files: " + ", ".join(sorted(missing)))
    if extra:
        raise ValueError("Unmaintained manifest entries: " + ", ".join(sorted(extra)))
    for name, digest in entries.items():
        path = root / name
        if path.is_symlink() or not path.is_file() or not path.resolve().is_relative_to(root):
            raise ValueError(f"Missing, linked or out-of-root file: {name}.")
        if hashlib.sha256(path.read_bytes()).hexdigest() != digest:
            raise ValueError(f"Hash mismatch: {name}.")
    return len(entries)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT, help="Lab directory in a Git checkout.")
    parser.add_argument("--manifest", type=Path, help="Alternative manifest to inspect without replacing the maintained file.")
    args = parser.parse_args()
    try:
        count = check(args.root, args.manifest)
    except (OSError, ValueError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    print(f"PASS: {count} maintained lab files covered exactly once; all SHA-256 hashes match.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
