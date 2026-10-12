#!/usr/bin/env python3
"""Package published own DLLs/configuration and the exact maintained examples."""
from pathlib import Path
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
PUBLISH = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "out/publish"
OUTPUT = ROOT / "dist/eclipse-fair-0.1.0.zip"
required = ["eclipse.dll", "Eclipse.Core.dll", "eclipse.deps.json", "eclipse.runtimeconfig.json"]
files = {name: (PUBLISH / name).read_bytes() for name in required}
for directory in ["rules", "examples"]:
    for path in sorted((ROOT / directory).glob("*.json")):
        files[path.relative_to(ROOT).as_posix()] = path.read_bytes()
files["PLAY.txt"] = b"Eclipse Fair 0.1.0. Requires .NET 10 runtime.\nRun: dotnet eclipse.dll play --seed 1\nResume: dotnet eclipse.dll play --load examples/partial-journal.json\nCompare: dotnet eclipse.dll compare --variant rules/expensive-seals.json --runs 100 --seed 0 --out out/compare\nNo graphical engine or self-contained executable.\n"
OUTPUT.parent.mkdir(exist_ok=True)
with zipfile.ZipFile(OUTPUT, "w", compression=zipfile.ZIP_DEFLATED) as archive:
    for name, blob in sorted(files.items()):
        info = zipfile.ZipInfo(name, (2026, 10, 12, 0, 0, 0))
        info.compress_type = zipfile.ZIP_DEFLATED
        info.external_attr = 0o644 << 16
        archive.writestr(info, blob)
print(f"Packaged {len(files)} files; {OUTPUT.stat().st_size} bytes")
