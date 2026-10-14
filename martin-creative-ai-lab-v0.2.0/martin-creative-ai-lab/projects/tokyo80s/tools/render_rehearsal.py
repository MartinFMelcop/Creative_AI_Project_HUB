#!/usr/bin/env python3
"""Prepare original-pitch rehearsal backing from the preserved PCM masters."""
import array
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import wave

ROOT = Path(__file__).resolve().parents[1]
RATES = (.75, .9)
FILTER = "rubberband=tempo={rate}:pitch=1:transients=crisp:channels=together"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def command(*args):
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", *map(str, args)], check=True)


def samples(path):
    values = array.array("f", path.read_bytes())
    if sys.byteorder != "little":
        values.byteswap()
    return values


def main():
    version = subprocess.check_output(["ffmpeg", "-version"], text=True).splitlines()[0]
    setlist = json.loads((ROOT / "dist/setlist.json").read_text())
    records = []
    with tempfile.TemporaryDirectory(prefix="tokyo-rehearsal-") as directory:
        stage = Path(directory)
        for item in setlist:
            score = json.loads((ROOT / "dist" / item["score"]).read_text())
            master = ROOT / "media" / (item["id"] + ".wav")
            origin = ROOT / "media" / ("provenance.json" if item["id"] == "midnight-signal" else "rain-provenance.json")
            expected = json.loads(origin.read_text())["files"][master.relative_to(ROOT).as_posix()]
            assert sha(master) == expected, "Original master identity changed"
            with wave.open(str(master)) as w:
                assert (w.getnchannels(), w.getsampwidth(), w.getframerate()) == (2, 2, 44100)
                original_frames = w.getnframes()
            item["rehearsalAudio"] = {}
            for rate in RATES:
                name = f"{item['id']}-{round(rate * 100)}.ogg"
                raw = stage / "render.f32"
                command("-i", master, "-af", FILTER.format(rate=rate), "-f", "f32le", raw)
                pcm = samples(raw)
                target = round(original_frames / rate)
                assert abs(len(pcm) // 2 - target) <= 441, "Processor duration drift exceeds 10ms"
                peak = max(abs(n) for n in pcm)
                assert 0 < peak < 2
                # Leave decoded Vorbis headroom rather than clipping stretched peaks.
                gain = min(1., .89 / peak)
                command("-f", "f32le", "-ar", "44100", "-ac", "2", "-i", raw,
                    "-af", f"apad,atrim=end_sample={target},volume={gain:.12f}",
                    "-c:a", "libvorbis", "-q:a", "5", stage / name)
                url = "assets/rehearsal/" + name
                item["rehearsalAudio"][str(rate)] = url
                records.append({"track": item["id"], "rate": rate, "source": master.relative_to(ROOT).as_posix(),
                    "source_sha256": expected, "audio": "dist/" + url, "sha256": sha(stage / name),
                    "source_frames": original_frames, "processed_frames": len(pcm) // 2,
                    "frames": target, "duration_seconds": target / 44100, "sample_rate": 44100,
                    "channels": 2, "processing_peak": peak, "gain": gain,
                    "filter": FILTER.format(rate=rate)})
                print(f"RENDERED {name}: {target / 44100:.6f}s, gain {gain:.6f}")
        for record in records:
            destination = ROOT / record["audio"]
            destination.parent.mkdir(parents=True, exist_ok=True)
            temporary = destination.with_suffix(".ogg.tmp")
            temporary.write_bytes((stage / destination.name).read_bytes())
            temporary.replace(destination)
    (ROOT / "dist/setlist.json").write_text(json.dumps(setlist, indent=2) + "\n")
    provenance = {"schema": 1, "project": "P08", "version": "0.5.0", "consumer": "P03", "consumer_version": "0.4.0",
        "origin": "Tempo derivatives of the preserved original algorithmic PCM masters; no new composition, samples or recording.",
        "processor": version, "filter": FILTER, "encoder": "libvorbis quality 5",
        "boundary": "Build tools are not distributed. Signal tests are not physical listening, musical approval or commercial clearance.",
        "producer_sha256": sha(Path(__file__)), "renders": records}
    (ROOT / "media/rehearsal-provenance.json").write_text(json.dumps(provenance, indent=2) + "\n")


if __name__ == "__main__":
    main()
