#!/usr/bin/env python3
"""Package owned C# assemblies and editable sources; engine/runtime stay external."""
from pathlib import Path
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED

ROOT = Path(__file__).resolve().parents[1]
BIN = ROOT / "Native/.godot/mono/temp/bin/Debug"
OUT = ROOT / "dist/cinderwatch-0.4.0.zip"


def main():
    files = [ROOT / name for name in ("global.json", "Directory.Build.props", "Native/project.godot",
             "Native/Main.tscn", "Native/Cinder.Native.csproj", "Native/Cinder.Native.sln", "Native/export_presets.cfg", "Native/README.md", "Checks/Probe.cs")]
    files += sorted((ROOT / "Core").glob("*.cs")) + [ROOT / "Core/Cinder.Core.csproj"]
    files += sorted((ROOT / "Native").glob("*.cs")) + sorted((ROOT / "Native").glob("*.uid"))
    files += sorted(p for p in (ROOT / "Native/media").rglob("*") if p.is_file() and p.suffix in {".png", ".wav", ".json"})
    files += [ROOT / "tools/render_feedback.py", ROOT / "tools/check_media.py"]
    files += [BIN / name for name in ("Cinder.Native.dll", "Cinder.Core.dll", "Cinder.Native.deps.json", "Cinder.Native.runtimeconfig.json")]
    OUT.parent.mkdir(exist_ok=True)
    with ZipFile(OUT, "w") as archive:
        for path in sorted(files):
            if not path.is_file():
                raise SystemExit(f"Missing source/build file: {path}")
            entry = ZipInfo("cinderwatch/" + path.relative_to(ROOT).as_posix(), (1980, 1, 1, 0, 0, 0))
            entry.compress_type = ZIP_DEFLATED
            entry.external_attr = 0o644 << 16
            archive.writestr(entry, path.read_bytes())
    print(f"Packaged {len(files)} files, {OUT.stat().st_size} bytes: {OUT.name}")


if __name__ == "__main__":
    main()
