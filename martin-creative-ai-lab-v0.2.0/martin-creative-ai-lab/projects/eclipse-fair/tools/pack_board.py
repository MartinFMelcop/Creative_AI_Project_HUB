#!/usr/bin/env python3
"""Package the compiled native consumer, without redistributing an engine/runtime."""
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

ROOT = Path(__file__).resolve().parents[1]
NATIVE = ROOT / "Native"
ASSEMBLIES = NATIVE / ".godot/mono/temp/bin/Debug"
OUT = ROOT / "dist/eclipse-board-0.5.0.zip"


def main():
    files = [ROOT / "Directory.Build.props", ROOT / "global.json", NATIVE / "project.godot",
             NATIVE / "Main.tscn", NATIVE / "Eclipse.Board.csproj", NATIVE / "Eclipse.Board.sln", NATIVE / "export_presets.cfg", NATIVE / "README.md",
             ROOT / "Cli/Journal.cs", ROOT / "Core/Eclipse.Core.csproj"]
    files += sorted((ROOT / "Core").glob("*.cs"))
    files += sorted(NATIVE.glob("*.cs")) + sorted(NATIVE.glob("*.uid"))
    files += [ASSEMBLIES / name for name in ("Eclipse.Board.dll", "Eclipse.Core.dll", "Eclipse.Board.deps.json", "Eclipse.Board.runtimeconfig.json")]
    for path in files:
        if not path.is_file():
            raise SystemExit(f"Missing build/source file: {path}")
    OUT.parent.mkdir(exist_ok=True)
    with ZipFile(OUT, "w", ZIP_DEFLATED) as archive:
        for path in files:
            archive.write(path, "eclipse-board/" + path.relative_to(ROOT).as_posix())
    print(f"Packaged {len(files)} files: {OUT.name}")


if __name__ == "__main__":
    main()
