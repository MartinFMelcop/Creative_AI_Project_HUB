#!/usr/bin/env python3
"""Compare the delivered native project's source/configuration with maintained files."""
import json
from pathlib import Path
from zipfile import ZipFile
import pack_board

ROOT = Path(__file__).resolve().parents[1]


def main():
    with ZipFile(pack_board.OUT) as archive:
        names = archive.namelist()
        assert len(names) == len(set(names)), "Duplicate package entries"
        for name in names:
            relative = Path(name).relative_to("eclipse-board")
            assert ".." not in relative.parts and not relative.is_absolute(), "Unsafe package path"
            if ".godot" in relative.parts:
                assert relative.parent.as_posix() == "Native/.godot/mono/temp/bin/Debug", "Unwanted cache"
                assert relative.name in {"Eclipse.Board.dll", "Eclipse.Core.dll", "Eclipse.Board.deps.json", "Eclipse.Board.runtimeconfig.json"}, "Unwanted assembly"
                if relative.suffix == ".dll":
                    assert archive.read(name).startswith(b"MZ"), "Missing compiled managed assembly"
            else:
                assert archive.read(name) == (ROOT / relative).read_bytes(), f"Stale packaged source: {relative}"
        required = {"Native/project.godot", "Native/Main.tscn", "Native/Eclipse.Board.csproj", "Native/Main.cs", "Native/MapView.cs", "Native/BoardSession.cs", "Native/BoardChecks.cs", "Native/README.md",
                    "Core/Game.cs", "Core/Agents.cs", "Core/Eclipse.Core.csproj", "Cli/Journal.cs", "Directory.Build.props", "global.json"}
        required |= {"Native/.godot/mono/temp/bin/Debug/" + f for f in ["Eclipse.Board.dll", "Eclipse.Core.dll", "Eclipse.Board.deps.json", "Eclipse.Board.runtimeconfig.json"]}
        required |= {p.relative_to(ROOT).as_posix() for p in (ROOT / "Native").glob("*.uid")}
        assert set(names) == {"eclipse-board/" + f for f in required}, "Missing/unintended package entries"
        runtime = json.loads(archive.read("eclipse-board/Native/.godot/mono/temp/bin/Debug/Eclipse.Board.runtimeconfig.json"))
        assert runtime["runtimeOptions"]["tfm"] == "net10.0", "Wrong runtime contract"
    print(f"PASS: {len(names)} native package entries; current source/configuration, owned compiled assemblies, no redistributed engine/API/runtime.")


if __name__ == "__main__":
    main()
