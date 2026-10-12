#!/usr/bin/env python3
"""Verify that the delivered native package contains the current consumer bytes."""
from pathlib import Path
from zipfile import ZipFile
import hashlib
import json
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--assemblies", action="store_true", help="also require bytes from this local build")
args = parser.parse_args()

ROOT = Path(__file__).resolve().parents[1]
PACK = ROOT / "dist/cinderwatch-0.1.0.zip"
with ZipFile(PACK) as archive:
    names = archive.namelist()
    assert len(names) == len(set(names))
    assert len([n for n in names if n.endswith(".dll")]) == 2
    assert {Path(n).name for n in names if n.endswith(".dll")} == {"Cinder.Core.dll", "Cinder.Native.dll"}
    for name in names:
        relative = Path(name).relative_to("cinderwatch")
        assert not relative.is_absolute() and ".." not in relative.parts
        data = archive.read(name)
        if ".godot" not in relative.parts or args.assemblies:
            assert data == (ROOT / relative).read_bytes(), f"Stale delivered file: {relative}"
        if name.endswith(".dll"):
            assert data.startswith(b"MZ") and len(data) > 512
    config = json.loads(archive.read("cinderwatch/Native/.godot/mono/temp/bin/Debug/Cinder.Native.runtimeconfig.json"))
    assert config["runtimeOptions"]["tfm"] == "net10.0"
print(json.dumps({"files": len(names), "bytes": PACK.stat().st_size, "sha256": hashlib.sha256(PACK.read_bytes()).hexdigest()}))
