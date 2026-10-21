#!/usr/bin/env python3
"""Fresh-stage the current consumer with the pinned official Linux release runtime."""
import argparse
import ast
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
VERSION = "4.6.3.stable.official.7d41c59c4"
TEMPLATE_SHA = "2c78919325d7f29fa7607287c7c1eeac367ea4c94e7b8b6f5f4c6b20492f73d0"
ARCHIVE_SHA = "3fbe2c0e2dec9d537ab9ec97bcf8da91dcf23357fc51f67092dd068d839290a8"
DEFAULT = ROOT / "dist/crossing-drill-linux-0.2.0.zip"
BUNDLE = "CrossingDrill"


def digest(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def source_paths():
    # Consume the existing explicit PCK inventory instead of maintaining a second list.
    text = (ROOT / "tools/pack.gd").read_text()
    match = re.search(r"for name in (\[[^\n]+\]):", text)
    if not match:
        raise ValueError("PCK inventory is unavailable")
    names = ast.literal_eval(match[1])
    if len(names) != len(set(names)) or any(Path(n).is_absolute() or ".." in Path(n).parts for n in names):
        raise ValueError("Unsafe or duplicate PCK source inventory")
    return names


def identity():
    return {"schema_version": 1, "engine_version": VERSION, "template_sha256": TEMPLATE_SHA,
            "sources": {n: digest(ROOT / n) for n in sorted(source_paths()) if n.endswith(".gd")}}


def run_engine(command, env):
    result = subprocess.run(command, env=env, capture_output=True, text=True, timeout=90)
    log = result.stdout + result.stderr
    if result.returncode or any(s in log for s in ("SCRIPT ERROR:", "Parse Error:", "ERROR:")):
        raise ValueError("Godot import/export failed: " + log[-2500:])


def export(output=DEFAULT, godot="godot", template=None, templates=None):
    output = Path(output)
    engine = shutil.which(godot)
    if not engine:
        raise ValueError("Godot executable unavailable")
    if (template is None) == (templates is None):
        raise ValueError("Provide exactly one official template or TPZ")
    with tempfile.TemporaryDirectory(prefix="crossing-export-") as folder:
        work = Path(folder)
        env = os.environ.copy()
        for key in ("XDG_DATA_HOME", "XDG_CONFIG_HOME", "XDG_CACHE_HOME"):
            env[key] = str(work / key)
            Path(env[key]).mkdir()
        version = subprocess.run([engine, "--version"], env=env, capture_output=True, text=True, timeout=10)
        if version.returncode or version.stdout.strip() != VERSION or "ERROR:" in version.stderr:
            raise ValueError("Use the pinned standard Godot 4.6.3 editor")
        if templates:
            if digest(templates) != ARCHIVE_SHA:
                raise ValueError("Official TPZ digest mismatch")
            with zipfile.ZipFile(templates) as archive:
                template = work / "linux_release.x86_64"
                template.write_bytes(archive.read("templates/linux_release.x86_64"))
        template = Path(template).resolve()
        if digest(template) != TEMPLATE_SHA:
            raise ValueError("Official Linux release-template digest mismatch")
        stage = work / "project"
        stage.mkdir()
        for name in source_paths():
            target = stage / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / name, target)
            uid = ROOT / (name + ".uid")
            if uid.exists():
                shutil.copyfile(uid, stage / (name + ".uid"))
        record = identity()
        encoded = json.dumps(record, sort_keys=True, indent=2) + "\n"
        (stage / "runtime_identity.json").write_text(encoded)
        preset = (ROOT / "export_presets.cfg").read_text()
        preset += "\ncustom_template/release=" + json.dumps(str(template)) + "\ndebug/export_console_wrapper=0\n"
        (stage / "export_presets.cfg").write_text(preset)
        bundle = work / BUNDLE
        bundle.mkdir()
        run_engine([engine, "--headless", "--path", str(stage), "--editor", "--import", "--quit"], env)
        run_engine([engine, "--headless", "--path", str(stage), "--export-release", "Linux",
                    str(bundle / "crossing-drill.x86_64")], env)
        if digest(bundle / "crossing-drill.x86_64") != TEMPLATE_SHA:
            raise ValueError("Export changed the pinned runtime")
        (bundle / "SOURCE-IDENTITY.json").write_text(encoded)
        for name in ("GODOT-LICENSE.txt", "GODOT-COPYRIGHT.txt"):
            shutil.copyfile(ROOT / "third-party" / name, bundle / name)
        shutil.copyfile(ROOT / "provenance.json", bundle / "PROVENANCE.json")
        shutil.copyfile(ROOT / "PLAYER_README.txt", bundle / "README.txt")
        output.parent.mkdir(parents=True, exist_ok=True)
        # Build fully before replacing the ZIP; its checksum is a separate sidecar.
        with tempfile.NamedTemporaryFile(dir=output.parent, suffix=".zip.tmp", delete=False) as temp:
            temporary = Path(temp.name)
        try:
            with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
                for path in sorted(bundle.iterdir()):
                    info = zipfile.ZipInfo(BUNDLE + "/" + path.name, (1980, 1, 1, 0, 0, 0))
                    info.create_system = 3
                    info.external_attr = (0o100755 if path.suffix == ".x86_64" else 0o100644) << 16
                    info.compress_type = zipfile.ZIP_DEFLATED
                    archive.writestr(info, path.read_bytes(), compresslevel=9)
            temporary.replace(output)
        finally:
            temporary.unlink(missing_ok=True)
        output.with_suffix(".zip.sha256").write_text(digest(output) + "  " + output.name + "\n")
    print("EXPORTED", output.name, output.stat().st_size, "bytes; runtime verification is separate")
    return output


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--template", type=Path)
    group.add_argument("--templates", type=Path)
    parser.add_argument("--godot", default="godot")
    parser.add_argument("--output", type=Path, default=DEFAULT)
    args = parser.parse_args()
    try:
        export(args.output, args.godot, args.template, args.templates)
    except (OSError, ValueError, subprocess.SubprocessError, zipfile.BadZipFile) as error:
        parser.exit(1, "FAIL: " + str(error) + "\n")
