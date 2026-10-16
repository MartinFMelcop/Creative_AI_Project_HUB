#!/usr/bin/env python3
"""Build a self-contained Godot .NET player from a clean, verified staging project."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED

ROOT = Path(__file__).resolve().parents[1]
VERSION = "0.5.0"
ENGINE_VERSION = "4.6.3.stable.mono.official.7d41c59c4"
ARCHIVE_SHA = "6436f474ee085fb0a94d3d296b9821736bdd663b6e91b2228fdf77066f1d1400"
TEMPLATE_SHA = "dde8bd2f5b6b8666c3656a57900f8c4163b3fc9799cc723746ca88468333b320"
RUNTIME_VERSION = "10.0.12"
DATA = "data_Cinder.Native_linuxbsd_x86_64"


def digest(path):
    with path.open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()


def sources():
    files = [ROOT / name for name in ["Directory.Build.props", "global.json", "Checks/Probe.cs",
        "Core/Cinder.Core.csproj", "Native/Cinder.Native.csproj", "Native/Cinder.Native.sln",
        "Native/Main.tscn", "Native/project.godot", "Native/export_presets.cfg"]]
    files += sorted((ROOT / "Core").glob("*.cs"))
    files += sorted((ROOT / "Native").glob("*.cs")) + sorted((ROOT / "Native").glob("*.uid"))
    return sorted(files)


def run(command, env, cwd=None):
    result = subprocess.run(command, env=env, cwd=cwd, text=True,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=240)
    print(result.stdout, end="")
    # Godot can report a zero exit code after a .NET export failure.
    if result.returncode or "ERROR:" in result.stdout or "Build FAILED" in result.stdout:
        raise RuntimeError("Build/import/export failed; the distribution was not replaced.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--templates", type=Path, help="Official 4.6.3 Mono TPZ; full digest is checked.")
    group.add_argument("--template", type=Path, help="Verified extracted Mono linux_release.x86_64.")
    parser.add_argument("--godot", default="godot-dotnet")
    parser.add_argument("--dotnet", default="dotnet")
    parser.add_argument("--output", type=Path, default=ROOT / f"dist/cinderwatch-linux-{VERSION}.zip")
    args = parser.parse_args()
    engine, dotnet = shutil.which(args.godot), shutil.which(args.dotnet)
    if not engine or not dotnet:
        parser.error("Godot .NET and the .NET SDK must be available to build.")
    if subprocess.check_output([engine, "--version"], text=True).strip() != ENGINE_VERSION:
        parser.error("Use the official Godot .NET 4.6.3 editor.")
    if subprocess.check_output([dotnet, "--version"], cwd=ROOT, text=True).strip() != "10.0.401":
        parser.error("Use SDK 10.0.401, pinned by global.json.")
    with tempfile.TemporaryDirectory(prefix="cinderwatch-export-") as scratch:
        work = Path(scratch)
        if args.templates:
            if digest(args.templates) != ARCHIVE_SHA:
                parser.error("Official Mono template archive digest mismatch.")
            with ZipFile(args.templates) as z:
                template = work / "linux_release.x86_64"
                template.write_bytes(z.read("templates/linux_release.x86_64"))
        else:
            template = args.template.resolve()
        if digest(template) != TEMPLATE_SHA:
            parser.error("Official Mono Linux release template digest mismatch.")

        stage = work / "project"
        inputs = sources()
        for source in inputs:
            destination = stage / source.relative_to(ROOT)
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, destination)
        # Raw media lives beside the player. Godot's texture/audio importer omits
        # the PNG/WAV sources consumed by Image/AudioStreamWav.LoadFromFile.
        preset = (stage / "Native/export_presets.cfg").read_text()
        preset += "\ncustom_template/release=" + json.dumps(str(template)) + "\n"
        (stage / "Native/export_presets.cfg").write_text(preset)
        env = os.environ.copy()
        env["PATH"] = str(Path(dotnet).parent) + os.pathsep + env.get("PATH", "")
        for key, name in [("XDG_DATA_HOME", "data"), ("XDG_CONFIG_HOME", "config"),
            ("XDG_CACHE_HOME", "cache"), ("DOTNET_CLI_HOME", "dotnet-home")]:
            env[key] = str(work / name)
        env.setdefault("NUGET_PACKAGES", str(work / "nuget"))
        env.update(DOTNET_CLI_TELEMETRY_OPTOUT="1", DOTNET_NOLOGO="1",
            DOTNET_GENERATE_ASPNET_CERTIFICATE="false")
        bundle = work / "Cinderwatch"
        bundle.mkdir()
        run([dotnet, "build", str(stage / "Native/Cinder.Native.csproj"), "-c", "Debug"], env)
        run([engine, "--headless", "--path", str(stage / "Native"), "--editor", "--import", "--quit"], env)
        run([engine, "--headless", "--path", str(stage / "Native"), "--export-release", "Linux",
            str(bundle / "cinderwatch.x86_64")], env)
        if digest(bundle / "cinderwatch.x86_64") != TEMPLATE_SHA or not (bundle / "cinderwatch.pck").is_file():
            parser.error("The export did not produce the pinned engine and actual resource pack.")
        data = bundle / DATA
        config = json.loads((data / "Cinder.Native.runtimeconfig.json").read_text())["runtimeOptions"]
        if config.get("includedFrameworks") != [{"name": "Microsoft.NETCore.App", "version": RUNTIME_VERSION}]:
            parser.error("The .NET runtime was not included at the pinned version.")
        for name in ["libhostfxr.so", "libcoreclr.so", "System.Private.CoreLib.dll", "GodotSharp.dll",
            "Cinder.Native.dll", "Cinder.Core.dll"]:
            if not (data / name).is_file():
                parser.error("Missing required runtime/game file: " + name)

        shutil.copytree(ROOT / "Native/media", bundle / "media", ignore=shutil.ignore_patterns("*.import"))
        for name in ["GODOT-LICENSE.txt", "GODOT-COPYRIGHT.txt"]:
            shutil.copyfile(ROOT / "third-party" / name, bundle / name)
        package_location = subprocess.check_output([dotnet, "nuget", "locals", "global-packages", "--list"], env=env, text=True).strip()
        cache = Path(package_location.split(": ", 1)[1])
        runtime = cache / "microsoft.netcore.app.runtime.linux-x64" / RUNTIME_VERSION
        shutil.copyfile(runtime / "LICENSE.TXT", bundle / "DOTNET-LICENSE.txt")
        shutil.copyfile(runtime / "THIRD-PARTY-NOTICES.TXT", bundle / "DOTNET-THIRD-PARTY-NOTICES.txt")
        (bundle / "README.txt").write_text("""Cinderwatch 0.5.0 — Linux x86_64 tactical rescue prototype

Extract the ENTIRE Cinderwatch folder, then run ./cinderwatch.x86_64.
Keep cinderwatch.pck, data_Cinder.Native_linuxbsd_x86_64 and media beside it.
Godot, an installed .NET runtime, SDK, Python and source checkout are unnecessary.
If your extractor drops permissions: chmod +x cinderwatch.x86_64
The OS still needs desktop/audio libraries, ICU and OpenGL 3.3 or a compatible driver.
Consult the repository execution evidence for tested distributions and limits.

Read the brief. Enter the yard, inspect announced threats and choose an action.
Confirm spends one turn. Resolve advances the named enemy; inspection spends none.
Tab/Shift+Tab and Enter navigate/activate controls. Tactics explains rows, Cover,
Pin, scorch and supplies. Choose salvage between the three encounters; damage and
resources carry forward. Sound toggles above the brief. Close the window to exit.

Accepted actions autosave to Godot's per-user Cinderwatch directory, shared with
the previous native project. Run files saves a verified recovery copy or opens
a valid journal. Opening a copy leaves its source intact; future accepted turns
use the primary autosave. Failed writes keep live progress: New run, Resume, Open
and quit ask whether to keep it, retry, copy elsewhere or explicitly discard.
A successful retry/copy returns to the current run. Save paths/errors are in the
status tooltip. No undo/cloud save. Rules and save schema remain 0.1.0.

For technical verification only (all input is scripted, not a human playtest):
./cinderwatch.x86_64 --headless -- --verify --save-path /tmp/cinder-check/save.json
Always use an isolated path: verification replaces that specified test save.

BUILD-INFO.json identifies sources/runtime and hashes; media/provenance.json records
original generated portraits and synthesized cues. Godot/.NET notices are included.
Source/author context: https://github.com/MartinFMelcop/Creative_AI_Project_HUB
No independent play, hardware listening/accessibility or commercial approval is claimed.
""")
        files = sorted(path for path in bundle.rglob("*") if path.is_file())
        info = {"schema": 1, "project": "P05", "version": VERSION, "platform": "linux-x86_64",
            "engine": ENGINE_VERSION, "template_archive_sha256": ARCHIVE_SHA, "template_sha256": TEMPLATE_SHA,
            "sdk": "10.0.401", "runtime": RUNTIME_VERSION, "self_contained": True,
            "source_sha256": {path.relative_to(ROOT).as_posix(): digest(path) for path in inputs},
            "files_sha256": {path.relative_to(bundle).as_posix(): digest(path) for path in files}}
        (bundle / "BUILD-INFO.json").write_text(json.dumps(info, indent=2) + "\n")
        output = args.output.resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        temporary = output.with_suffix(".zip.tmp")
        try:
            with ZipFile(temporary, "w", ZIP_DEFLATED, compresslevel=9) as z:
                for path in sorted(p for p in bundle.rglob("*") if p.is_file()):
                    entry = ZipInfo("Cinderwatch/" + path.relative_to(bundle).as_posix(), (1980, 1, 1, 0, 0, 0))
                    entry.create_system = 3
                    entry.external_attr = (0o100755 if path.name == "cinderwatch.x86_64" else 0o100644) << 16
                    entry.compress_type = ZIP_DEFLATED
                    z.writestr(entry, path.read_bytes(), compresslevel=9)
            if temporary.stat().st_size >= 100_000_000:
                parser.error("Player exceeds the normal GitHub file limit; choose a supported release artifact route.")
            temporary.replace(output)
        finally:
            if temporary.exists():
                temporary.unlink()
        output.with_suffix(".zip.sha256").write_text(digest(output) + "  " + output.name + "\n")
        print(f"EXPORTED {output.name}: {output.stat().st_size} bytes; bundled Godot and .NET {RUNTIME_VERSION}.")


if __name__ == "__main__":
    main()
