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
            assert relative.parts[0] == "Cinderwatch" and len(relative.parts) > 1
            assert ".." not in relative.parts and "\\" not in entry.filename and not relative.is_absolute()
            assert stat.S_ISREG(entry.external_attr >> 16), "Unexpected directory/link/device entry"
            assert not relative.suffix == ".pdb", "Unwanted debug symbols"
        info = json.loads(z.read("Cinderwatch/BUILD-INFO.json"))
        assert (info["schema"], info["project"], info["version"], info["platform"]) == (1, "P05", "0.4.0", "linux-x86_64")
        assert info["engine"] == export_linux.ENGINE_VERSION and info["self_contained"] is True
        assert info["template_sha256"] == export_linux.TEMPLATE_SHA and info["template_archive_sha256"] == export_linux.ARCHIVE_SHA
        assert info["runtime"] == export_linux.RUNTIME_VERSION and info["sdk"] == "10.0.401"
        expected = {"Cinderwatch/" + name for name in info["files_sha256"]} | {"Cinderwatch/BUILD-INFO.json"}
        assert set(names) == expected, "Unlisted/missing files in the delivered player"
        for name, sha in info["files_sha256"].items():
            assert hashlib.sha256(z.read("Cinderwatch/" + name)).hexdigest() == sha, "Damaged payload: " + name
        expected_sources = {p.relative_to(ROOT).as_posix(): export_linux.digest(p) for p in export_linux.sources()}
        assert info["source_sha256"] == expected_sources, "Stale/unintended source identity"
        binary = z.read("Cinderwatch/cinderwatch.x86_64")
        assert binary[:4] == b"\x7fELF" and binary[4:6] == b"\x02\x01" and struct.unpack_from("<H", binary, 18)[0] == 62
        assert hashlib.sha256(binary).hexdigest() == export_linux.TEMPLATE_SHA, "Unexpected engine template"
        assert stat.S_IMODE(z.getinfo("Cinderwatch/cinderwatch.x86_64").external_attr >> 16) == 0o755
        assert z.read("Cinderwatch/cinderwatch.pck")[:4] == b"GDPC", "Missing Godot resource pack"
        data = "Cinderwatch/" + export_linux.DATA + "/"
        config = json.loads(z.read(data + "Cinder.Native.runtimeconfig.json"))["runtimeOptions"]
        assert config["tfm"] == "net10.0" and config["includedFrameworks"] == [{"name": "Microsoft.NETCore.App", "version": "10.0.12"}]
        for name in ["libhostfxr.so", "libcoreclr.so", "System.Private.CoreLib.dll", "GodotSharp.dll", "Cinder.Core.dll", "Cinder.Native.dll"]:
            assert data + name in names, "Missing runtime/game component: " + name
        assert not any("GodotSharpEditor" in name or "GodotTools" in name for name in names), "Unwanted editor assemblies"
        for source in (ROOT / "Native/media").rglob("*"):
            if source.is_file() and source.suffix in {".png", ".wav", ".json"}:
                target = "Cinderwatch/media/" + source.relative_to(ROOT / "Native/media").as_posix()
                assert z.read(target) == source.read_bytes(), "Changed/missing original media: " + target
        for name in ["GODOT-LICENSE.txt", "GODOT-COPYRIGHT.txt"]:
            assert z.read("Cinderwatch/" + name) == (ROOT / "third-party" / name).read_bytes(), "Missing official Godot notice"
        assert b"Permission is hereby granted" in z.read("Cinderwatch/DOTNET-LICENSE.txt")
        assert len(z.read("Cinderwatch/DOTNET-THIRD-PARTY-NOTICES.txt")) > 10_000
    return {"player": path.name, "files": len(names), "bytes": path.stat().st_size, "sha256": export_linux.digest(path),
        "source_and_resource_identity": True, "runtime_included": True, "boundary": "Static package check; actual execution is separate."}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("package", type=Path, nargs="?", default=ROOT / "dist/cinderwatch-linux-0.4.0.zip")
    args = parser.parse_args()
    print(json.dumps(check(args.package)))
