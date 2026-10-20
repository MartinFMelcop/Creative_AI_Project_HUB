#!/usr/bin/env python3
"""Execute the shipped release without editor/path overrides or developer tools."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import tempfile
import zipfile
from check_linux import check, require
from export_linux import BUNDLE, DEFAULT, identity


def unpack(archive, folder):
    package = check(archive)
    with zipfile.ZipFile(archive) as source:
        for info in source.infolist():
            target = Path(folder) / info.filename
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(source.read(info))
            target.chmod((info.external_attr >> 16) & 0o777)
    return Path(folder) / BUNDLE / "crossing-drill.x86_64", package


def environment(folder):
    env = os.environ.copy()
    for name in ("CROSSING_PROFILE", "CROSSING_CONTROLS", "CROSSING_CAPTURE"):
        env.pop(name, None)
    for name in ("XDG_DATA_HOME", "XDG_CONFIG_HOME", "XDG_CACHE_HOME"):
        env[name] = str(Path(folder) / name)
        Path(env[name]).mkdir(parents=True)
    # The Python verifier is external instrumentation; the app receives no tool PATH.
    env["PATH"] = "/nonexistent"
    return env


def verify(archive, output, compare=None):
    with tempfile.TemporaryDirectory(prefix="crossing-release-") as folder:
        folder = Path(folder)
        executable, package = unpack(archive, folder / "download")
        env = environment(folder)
        env["CROSSING_PROFILE"] = str(folder / "profile.json")
        env["CROSSING_CONTROLS"] = str(folder / "keys.json")
        rows = []
        for read_only in (False, True):
            target = folder / ("read.json" if read_only else "journeys.json")
            operation = "--verify-player-read" if read_only else "--verify-player"
            command = [str(executable), "--headless", "--audio-driver", "Dummy", "--", operation, str(target)]
            # cwd intentionally contains neither project.godot nor game sources.
            process = subprocess.run(command, cwd=folder, env=env, capture_output=True, text=True, timeout=35)
            log = process.stdout + process.stderr
            require(process.returncode == 0 and not any(s in log for s in ("ERROR:", "SCRIPT ERROR:", "Parse Error:")),
                    "Release execution failed: " + log[-2500:])
            require(target.is_file(), "Release did not emit its own result")
            row = json.loads(target.read_text())
            count = len(identity()["sources"]) + (3 if read_only else 15)
            require(row["checks"] == {"passed": count, "failed": 0} and len(set(row["labels"])) == count,
                    "Incomplete release checks")
            require(row["sources"] == identity()["sources"], "Executed release source identities differ")
            require(row["mode"] == "title" and row["tick"] == 0, "Release restored a gameplay session")
            rows.append(row)
        # The release must not silently discover game resources in our checkout/cwd.
        missing = folder / "missing"
        missing.mkdir()
        orphan = missing / executable.name
        os.link(executable, orphan)
        failure = subprocess.run([str(orphan), "--headless", "--quit-after", "1"], cwd=folder,
                                 env=env, capture_output=True, text=True, timeout=15)
        require(failure.returncode != 0, "Player without its companion PCK unexpectedly started")
        result = {"schema_version": 1, "package": package,
                  "observations": rows, "missing_pack_exit": failure.returncode,
                  "scope": "Actual pinned release, neutral cwd, absent developer-tool PATH, two complete approach/return journeys and a second process. Fixed policies are not participant validation."}
        if compare:
            expected = json.loads(Path(compare).read_text())
            require(result["observations"] == expected["observations"] and result["missing_pack_exit"] == expected["missing_pack_exit"],
                    "Rebuilt release behavior differs from the delivered release")
        output = Path(output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
        print("PASS: delivered release journeys, actual restart, missing-PCK rejection and embedded source identities")
        return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, default=DEFAULT)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--compare", type=Path)
    args = parser.parse_args()
    try:
        verify(args.archive, args.output, args.compare)
    except (OSError, ValueError, KeyError, subprocess.SubprocessError, zipfile.BadZipFile) as error:
        parser.exit(1, "FAIL: " + str(error) + "\n")
