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
VERSION = "0.6.0"
ENGINE_VERSION = "4.6.3.stable.mono.official.7d41c59c4"
ARCHIVE_SHA = "6436f474ee085fb0a94d3d296b9821736bdd663b6e91b2228fdf77066f1d1400"
TEMPLATE_SHA = "dde8bd2f5b6b8666c3656a57900f8c4163b3fc9799cc723746ca88468333b320"
RUNTIME_VERSION = "10.0.12"
DATA = "data_Eclipse.Board_linuxbsd_x86_64"


def digest(path):
    with path.open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()


def sources():
    files = [ROOT / name for name in ["Directory.Build.props", "global.json", "Cli/Journal.cs",
        "Core/Eclipse.Core.csproj", "Native/Eclipse.Board.csproj", "Native/Eclipse.Board.sln",
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
    parser.add_argument("--output", type=Path, default=ROOT / f"dist/eclipse-fair-linux-{VERSION}.zip")
    args = parser.parse_args()
    engine, dotnet = shutil.which(args.godot), shutil.which(args.dotnet)
    if not engine or not dotnet:
        parser.error("Godot .NET and the .NET SDK must be available to build.")
    if subprocess.check_output([engine, "--version"], text=True).strip() != ENGINE_VERSION:
        parser.error("Use the official Godot .NET 4.6.3 editor.")
    if subprocess.check_output([dotnet, "--version"], cwd=ROOT, text=True).strip() != "10.0.401":
        parser.error("Use SDK 10.0.401, pinned by global.json.")
    with tempfile.TemporaryDirectory(prefix="eclipse-fair-export-") as scratch:
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
        bundle = work / "EclipseFair"
        bundle.mkdir()
        run([dotnet, "build", str(stage / "Native/Eclipse.Board.csproj"), "-c", "Debug"], env)
        run([engine, "--headless", "--path", str(stage / "Native"), "--editor", "--import", "--quit"], env)
        run([engine, "--headless", "--path", str(stage / "Native"), "--export-release", "Linux",
            str(bundle / "eclipse-fair.x86_64")], env)
        if digest(bundle / "eclipse-fair.x86_64") != TEMPLATE_SHA or not (bundle / "eclipse-fair.pck").is_file():
            parser.error("The export did not produce the pinned engine and actual resource pack.")
        data = bundle / DATA
        config = json.loads((data / "Eclipse.Board.runtimeconfig.json").read_text())["runtimeOptions"]
        if config.get("includedFrameworks") != [{"name": "Microsoft.NETCore.App", "version": RUNTIME_VERSION}]:
            parser.error("The .NET runtime was not included at the pinned version.")
        for name in ["libhostfxr.so", "libcoreclr.so", "System.Private.CoreLib.dll", "GodotSharp.dll",
            "Eclipse.Board.dll", "Eclipse.Core.dll"]:
            if not (data / name).is_file():
                parser.error("Missing required runtime/game file: " + name)

        for name in ["GODOT-LICENSE.txt", "GODOT-COPYRIGHT.txt"]:
            shutil.copyfile(ROOT / "third-party" / name, bundle / name)
        package_location = subprocess.check_output([dotnet, "nuget", "locals", "global-packages", "--list"], env=env, text=True).strip()
        cache = Path(package_location.split(": ", 1)[1])
        runtime = cache / "microsoft.netcore.app.runtime.linux-x64" / RUNTIME_VERSION
        shutil.copyfile(runtime / "LICENSE.TXT", bundle / "DOTNET-LICENSE.txt")
        shutil.copyfile(runtime / "THIRD-PARTY-NOTICES.TXT", bundle / "DOTNET-THIRD-PARTY-NOTICES.txt")
        (bundle / "README.txt").write_text("""Eclipse Fair 0.6.0 — Linux x86_64 native board

Extract the ENTIRE EclipseFair folder, then run ./eclipse-fair.x86_64.
Keep eclipse-fair.pck and data_Eclipse.Board_linuxbsd_x86_64 beside it.
No installed Godot, .NET runtime, SDK, Python or source checkout is needed.
If an extractor drops permissions: chmod +x eclipse-fair.x86_64
The OS still needs a desktop/display stack, ICU and OpenGL 3.3 support.

New fair chooses one to four LOCAL seats and Planning/Classic rivals.
For several local players, Begin the named player's turn before choosing plans.
Inspect a venue, select an action, compare budgets/Next turns, then Commit.
Collect three sigils, remove curse and Claim at the Gate; reaching it is not claiming.
Next turns stops before the next human decision and is a model, not a guarantee.
Tab/arrows and Enter/Space navigate controls. How to play explains the rules.
No audio, gamepad, LAN or account identity is added. Close the window to exit.

Accepted turns autosave to the current one of three independent local fair slots.
Saved fairs shows validated summaries and Continue replays the chosen fair. New fair
saves immediately; replacing an occupied slot needs confirmation. Slot one keeps
the original match.json path. Export replay writes a separate economy-only journal
beside each slot. A failed save blocks switching until progress can be saved.
Board schema 1/rules 0.1.0 remain unchanged; earlier plain journals load as Vaelis.
Keep private copies of important saves. No undo/cloud save or automatic backup.

Technical verification uses scripted input, never an independent playtest:
./eclipse-fair.x86_64 --headless -- --verify --save-path /tmp/eclipse-check/match.json
Always use an isolated path: verification replaces the specified test save.

BUILD-INFO.json identifies sources/runtime and complete payload hashes.
Godot/.NET licenses and third-party notices accompany their actual binaries.
Source/author: https://github.com/MartinFMelcop/Creative_AI_Project_HUB
Physical hardware/accessibility, independent enjoyment, other OS and commercial
readiness remain unverified. Existing economy and fictional identity are retained.
""")
        files = sorted(path for path in bundle.rglob("*") if path.is_file())
        info = {"schema": 1, "project": "P01", "version": VERSION, "platform": "linux-x86_64",
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
                    entry = ZipInfo("EclipseFair/" + path.relative_to(bundle).as_posix(), (1980, 1, 1, 0, 0, 0))
                    entry.create_system = 3
                    entry.external_attr = (0o100755 if path.name == "eclipse-fair.x86_64" else 0o100644) << 16
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
