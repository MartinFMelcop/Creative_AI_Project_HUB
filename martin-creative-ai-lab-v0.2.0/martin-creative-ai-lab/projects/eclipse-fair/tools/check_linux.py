#!/usr/bin/env python3
"""Check the Linux player bytes, source identity and complete runtime/resource inventory."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import stat
import struct
from zipfile import ZipFile
import export_linux

ROOT = Path(__file__).resolve().parents[1]


def check(path):
    with ZipFile(path) as z:
        names = z.namelist()
        assert len(names) == len(set(names)), "Duplicate package entries"
        for entry in z.infolist():
            relative = PurePosixPath(entry.filename)
            assert relative.parts[0] == "EclipseFair" and len(relative.parts) > 1
            assert ".." not in relative.parts and "\\" not in entry.filename and not relative.is_absolute()
            assert stat.S_ISREG(entry.external_attr >> 16), "Unexpected directory/link/device entry"
            assert not relative.suffix == ".pdb", "Unwanted debug symbols"
        info = json.loads(z.read("EclipseFair/BUILD-INFO.json"))
        assert (info["schema"], info["project"], info["version"], info["platform"]) == (1, "P01", "0.5.0", "linux-x86_64")
        assert info["engine"] == export_linux.ENGINE_VERSION and info["self_contained"] is True
        assert info["template_sha256"] == export_linux.TEMPLATE_SHA and info["template_archive_sha256"] == export_linux.ARCHIVE_SHA
        assert info["runtime"] == export_linux.RUNTIME_VERSION and info["sdk"] == "10.0.401"
        expected = {"EclipseFair/" + name for name in info["files_sha256"]} | {"EclipseFair/BUILD-INFO.json"}
        assert set(names) == expected, "Unlisted/missing files in the delivered player"
        for name, sha in info["files_sha256"].items():
            assert hashlib.sha256(z.read("EclipseFair/" + name)).hexdigest() == sha, "Damaged payload: " + name
        expected_sources = {p.relative_to(ROOT).as_posix(): export_linux.digest(p) for p in export_linux.sources()}
        assert info["source_sha256"] == expected_sources, "Stale/unintended source identity"
        binary = z.read("EclipseFair/eclipse-fair.x86_64")
        assert binary[:4] == b"\x7fELF" and binary[4:6] == b"\x02\x01" and struct.unpack_from("<H", binary, 18)[0] == 62
        assert hashlib.sha256(binary).hexdigest() == export_linux.TEMPLATE_SHA, "Unexpected engine template"
        assert stat.S_IMODE(z.getinfo("EclipseFair/eclipse-fair.x86_64").external_attr >> 16) == 0o755
        assert z.read("EclipseFair/eclipse-fair.pck")[:4] == b"GDPC", "Missing Godot resource pack"
        data = "EclipseFair/" + export_linux.DATA + "/"
        config = json.loads(z.read(data + "Eclipse.Board.runtimeconfig.json"))["runtimeOptions"]
        assert config["tfm"] == "net10.0" and config["includedFrameworks"] == [{"name": "Microsoft.NETCore.App", "version": "10.0.12"}]
        for name in ["libhostfxr.so", "libcoreclr.so", "System.Private.CoreLib.dll", "GodotSharp.dll", "Eclipse.Core.dll", "Eclipse.Board.dll"]:
            assert data + name in names, "Missing runtime/game component: " + name
        assert not any("GodotSharpEditor" in name or "GodotTools" in name for name in names), "Unwanted editor assemblies"
        for name in ["GODOT-LICENSE.txt", "GODOT-COPYRIGHT.txt"]:
            assert z.read("EclipseFair/" + name) == (ROOT / "third-party" / name).read_bytes(), "Missing official Godot notice"
        assert b"Permission is hereby granted" in z.read("EclipseFair/DOTNET-LICENSE.txt")
        assert len(z.read("EclipseFair/DOTNET-THIRD-PARTY-NOTICES.txt")) > 10_000
    assert path.with_suffix(".zip.sha256").read_text() == export_linux.digest(path) + "  " + path.name + "\n", "Download checksum mismatch"
    return {"player": path.name, "files": len(names), "bytes": path.stat().st_size, "sha256": export_linux.digest(path),
        "source_and_resource_identity": True, "runtime_included": True, "boundary": "Static package check; actual execution is separate."}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("package", type=Path, nargs="?", default=ROOT / "dist/eclipse-fair-linux-0.5.0.zip")
    args = parser.parse_args()
    print(json.dumps(check(args.package)))
