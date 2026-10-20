#!/usr/bin/env python3
"""Validate archive shape, pinned runtime, permissions, source metadata and checksum.

Static integrity is not execution or authentication of an untrusted publisher.
"""
import argparse
import hashlib
import json
from pathlib import Path
import stat
import struct
import zipfile
from export_linux import BUNDLE, DEFAULT, ROOT, TEMPLATE_SHA, digest, identity

NAMES = {"crossing-drill.x86_64", "crossing-drill.pck", "README.txt", "GODOT-LICENSE.txt",
         "GODOT-COPYRIGHT.txt", "PROVENANCE.json", "SOURCE-IDENTITY.json"}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def check_pack(pack, expected):
    # Godot 4.6.3 exports PCK v3 with relative paths and an unencrypted directory.
    # Inspect actual payloads, not only the producer's sidecar claims.
    require(112 <= len(pack) < 2_000_000, "Unexpected PCK size")
    magic, version, major, minor, patch, flags, base, directory = struct.unpack_from("<6I2Q", pack)
    require((magic, version, major, minor, patch, flags) == (0x43504447, 3, 4, 6, 3, 2), "Unsupported PCK format")
    require(112 <= base <= directory < len(pack) - 4, "Invalid PCK directory offset")
    count = struct.unpack_from("<I", pack, directory)[0]
    require(0 < count <= 256, "Unexpected PCK entry count")
    cursor = directory + 4
    files = {}
    for _ in range(count):
        require(cursor + 4 <= len(pack), "Truncated PCK entry")
        length = struct.unpack_from("<I", pack, cursor)[0]
        cursor += 4
        require(0 < length <= 512 and cursor + length + 36 <= len(pack), "Invalid PCK path length")
        name = pack[cursor:cursor + length].rstrip(b"\0").decode("utf-8")
        cursor += length
        offset, size = struct.unpack_from("<QQ", pack, cursor)
        checksum = pack[cursor + 16:cursor + 32]
        file_flags = struct.unpack_from("<I", pack, cursor + 32)[0]
        cursor += 36
        require(name not in files and not Path(name).is_absolute() and ".." not in Path(name).parts,
                "Unsafe or duplicate PCK path")
        require(file_flags == 0 and base + offset + size <= directory, "Invalid PCK payload bounds or flags")
        payload = pack[base + offset:base + offset + size]
        require(hashlib.md5(payload, usedforsecurity=False).digest() == checksum, "PCK payload checksum mismatch")
        files[name] = payload
    for name, sha in expected["sources"].items():
        require(name in files and hashlib.sha256(files[name]).hexdigest() == sha, "Embedded source differs: " + name)
    require(json.loads(files["runtime_identity.json"]) == expected, "Embedded runtime identity differs")
    return count


def check(path=DEFAULT):
    path = Path(path)
    require(path.stat().st_size < 40_000_000, "Unexpected archive size")
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        require(len(names) == len(NAMES) and set(names) == {BUNDLE + "/" + n for n in NAMES},
                "Unexpected, missing or duplicate archive entries")
        for info in archive.infolist():
            require(stat.S_ISREG(info.external_attr >> 16) and info.file_size < 80_000_000,
                    "Non-regular or oversized archive entry")
        require(archive.testzip() is None, "Corrupt ZIP entry")
        executable = archive.read(BUNDLE + "/crossing-drill.x86_64")
        require(len(executable) >= 20 and executable[:6] == b"\x7fELF\x02\x01" and struct.unpack_from("<H", executable, 18)[0] == 62,
                "Not a Linux x86_64 ELF")
        require(hashlib.sha256(executable).hexdigest() == TEMPLATE_SHA, "Release runtime digest mismatch")
        require((archive.getinfo(BUNDLE + "/crossing-drill.x86_64").external_attr >> 16) & 0o111,
                "Executable permission absent")
        pack = archive.read(BUNDLE + "/crossing-drill.pck")
        require(pack[:4] == b"GDPC", "Missing Godot resource pack")
        metadata = json.loads(archive.read(BUNDLE + "/SOURCE-IDENTITY.json"))
        require(metadata == identity(), "Source identity metadata differs from maintained consumer")
        resource_count = check_pack(pack, metadata)
        require(archive.read(BUNDLE + "/README.txt") == (ROOT / "PLAYER_README.txt").read_bytes(), "Player guide differs")
        require(archive.read(BUNDLE + "/PROVENANCE.json") == (ROOT / "provenance.json").read_bytes(), "Provenance differs")
        for name in ("GODOT-LICENSE.txt", "GODOT-COPYRIGHT.txt"):
            require(archive.read(BUNDLE + "/" + name) == (ROOT / "third-party" / name).read_bytes(), "Engine notice differs")
    require(path.with_suffix(".zip.sha256").read_text() == digest(path) + "  " + path.name + "\n", "Download checksum mismatch")
    return {"entries": len(NAMES), "bytes": path.stat().st_size, "sha256": digest(path),
            "pck_sha256": hashlib.sha256(pack).hexdigest(), "sources": len(metadata["sources"]), "resources": resource_count,
            "boundary": "Static archive/identity checks; execute the real player separately."}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", nargs="?", type=Path, default=DEFAULT)
    try:
        print("LINUX_PACKAGE", json.dumps(check(parser.parse_args().archive), sort_keys=True))
    except (OSError, ValueError, KeyError, zipfile.BadZipFile) as error:
        parser.exit(1, "FAIL: " + str(error) + "\n")
