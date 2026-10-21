"""Reject broken delivery contracts even when a replacement ZIP has a new checksum."""
import json
import hashlib
import struct
from copy import copy
import shutil
from pathlib import Path
import stat
import tempfile
import unittest
import zipfile
from check_linux import check, check_pack
from export_linux import BUNDLE, DEFAULT, digest, identity


class PackageChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with zipfile.ZipFile(DEFAULT) as archive:
            cls.entries = [(i, archive.read(i)) for i in archive.infolist()]

    def altered(self, name, change, expected_message=None):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "altered.zip"
            with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=1) as archive:
                for info, value in self.entries:
                    info = copy(info)
                    if info.filename == BUNDLE + "/" + name:
                        result = change(info, value)
                        if result is None:
                            continue
                        info, value = result
                    archive.writestr(info, value)
            path.with_suffix(".zip.sha256").write_text(digest(path) + "  " + path.name + "\n")
            with self.assertRaises((ValueError, KeyError)) as failure:
                check(path)
            if expected_message:
                self.assertIn(expected_message, str(failure.exception))

    def test_valid_delivery(self):
        self.assertEqual(check(DEFAULT)["entries"], 7)

    def test_missing_companion_pack(self):
        self.altered("crossing-drill.pck", lambda i, b: None)

    def test_runtime_substitution(self):
        self.altered("crossing-drill.x86_64", lambda i, b: (i, b[:-1] + bytes([b[-1] ^ 1])))

    def test_lost_executable_permission(self):
        def change(info, value):
            info.external_attr = (stat.S_IFREG | 0o644) << 16
            return info, value
        self.altered("crossing-drill.x86_64", change)

    def test_notice_removal(self):
        self.altered("GODOT-COPYRIGHT.txt", lambda i, b: (i, b""))

    def test_forged_source_metadata(self):
        def change(info, value):
            data = json.loads(value)
            data["sources"]["combat.gd"] = "0" * 64
            return info, json.dumps(data).encode()
        self.altered("SOURCE-IDENTITY.json", change)

    def test_embedded_source_corruption(self):
        def change(info, value):
            self.assertIn(b"extends RefCounted", value)
            return info, value.replace(b"extends RefCounted", b"extends RefCountef", 1)
        self.altered("crossing-drill.pck", change)

    def test_catalog_edit_rejected_even_with_fresh_pack_and_zip_checksums(self):
        def change(info, value):
            pack = bytearray(value)
            base, directory = struct.unpack_from("<QQ", pack, 24)
            count = struct.unpack_from("<I", pack, directory)[0]
            cursor = directory + 4
            for _ in range(count):
                length = struct.unpack_from("<I", pack, cursor)[0]
                cursor += 4
                name = bytes(pack[cursor:cursor + length]).rstrip(b"\0").decode()
                cursor += length
                offset, size = struct.unpack_from("<QQ", pack, cursor)
                if name == "data/fittings.json":
                    payload = bytes(pack[base + offset:base + offset + size])
                    edited = payload.replace(b'"recovery": 26.0', b'"recovery": 25.0')
                    self.assertNotEqual(edited, payload)
                    pack[base + offset:base + offset + size] = edited
                    pack[cursor + 16:cursor + 32] = hashlib.md5(edited, usedforsecurity=False).digest()
                    return info, bytes(pack)
                cursor += 36
            self.fail("Delivered catalog payload is absent")
        self.altered("crossing-drill.pck", change, "Embedded source differs: data/fittings.json")

    def test_unsafe_archive_name(self):
        def change(info, value):
            info.filename = "../crossing-drill.pck"
            return info, value
        self.altered("crossing-drill.pck", change)

    def test_malformed_pack_directory(self):
        with self.assertRaises(ValueError):
            check_pack(b"GDPC" + b"\0" * 120, identity())

    def test_bad_download_checksum(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "bad-checksum.zip"
            shutil.copyfile(DEFAULT, path)
            path.with_suffix(".zip.sha256").write_text("0" * 64 + "  " + path.name + "\n")
            with self.assertRaisesRegex(ValueError, "Download checksum"):
                check(path)

    def test_short_elf(self):
        self.altered("crossing-drill.x86_64", lambda i, b: (i, b[:6]))


if __name__ == "__main__":
    unittest.main()
