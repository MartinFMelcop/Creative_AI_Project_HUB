#!/usr/bin/env python3
"""Check delivered tempo derivatives; --signal also decodes and probes the DSP."""
import argparse
import array
import hashlib
import json
import math
from pathlib import Path
import random
import struct
import subprocess
import sys
import tempfile
import wave
from render_rehearsal import ROOT, RATES, FILTER, sha, command, samples


def container(path):
    data = path.read_bytes()
    cursor, frames, packets, stream = 0, 0, bytearray(), None
    while cursor < len(data):
        assert data[cursor:cursor + 4] == b"OggS" and data[cursor + 4] == 0
        serial = struct.unpack_from("<I", data, cursor + 14)[0]
        if stream is None:
            stream = serial
        assert serial == stream, "Unexpected chained stream"
        granule = struct.unpack_from("<Q", data, cursor + 6)[0]
        if granule != 2**64 - 1:
            frames = max(frames, granule)
        count = data[cursor + 26]
        sizes = data[cursor + 27:cursor + 27 + count]
        start = cursor + 27 + count
        if not packets:
            packets += data[start:start + sum(sizes)]
        cursor = start + sum(sizes)
    assert cursor == len(data) and packets[:7] == b"\x01vorbis"
    assert packets[11] == 2 and struct.unpack_from("<I", packets, 12)[0] == 44100
    return frames


def decode(path):
    result = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-f", "f32le", "-"],
        stdout=subprocess.PIPE, check=True)
    values = array.array("f", result.stdout)
    if sys.byteorder != "little":
        values.byteswap()
    return values


def tone_frequency(values):
    # Interpolated positive zero crossings on an isolated test tone, independent
    # of the producer's metadata and tempo formula.
    crossings = []
    for i in range(1, len(values)):
        if values[i - 1] <= 0 < values[i]:
            crossings.append(i - 1 - values[i - 1] / (values[i] - values[i - 1]))
    assert len(crossings) > 50
    return 44100 * (len(crossings) - 1) / (crossings[-1] - crossings[0])


def signal_probe():
    sr, duration = 44100, 12
    points = [1, 3, 5, 7, 9]
    values = array.array("h", [0]) * (sr * duration * 2)
    rng = random.Random(803120)
    for at in points:
        for i in range(sr // 2):
            t = i / sr
            envelope = min(t / .005, 1) * min((.5 - t) / .005, 1)
            values[(at * sr + i) * 2] = round(7000 * math.sin(2 * math.pi * 440 * t) * envelope)
        for i in range(sr // 100):
            values[(at * sr + i) * 2 + 1] = round(rng.uniform(-6500, 6500) * (1 - i / (sr // 100)))
    with tempfile.TemporaryDirectory(prefix="tokyo-signal-") as folder:
        folder = Path(folder)
        source = folder / "probe.wav"
        with wave.open(str(source), "wb") as w:
            w.setparams((2, 2, sr, 0, "NONE", ""))
            if sys.byteorder != "little":
                values.byteswap()
            w.writeframes(values.tobytes())
        rows = []
        for rate in RATES:
            raw = folder / "probe.f32"
            command("-i", source, "-af", FILTER.format(rate=rate), "-f", "f32le", raw)
            encoded = folder / "probe.ogg"
            command("-f", "f32le", "-ar", str(sr), "-ac", "2", "-i", raw,
                "-c:a", "libvorbis", "-q:a", "5", encoded)
            pcm = decode(encoded)
            offsets, frequencies = [], []
            for at in points:
                expected = round(at / rate * sr)
                lo = expected - sr // 10
                pulse = pcm[lo * 2 + 1:(expected + sr // 10) * 2:2]
                index = max(range(len(pulse)), key=lambda i: abs(pulse[i]))
                offsets.append((lo + index - expected) / sr * 1000)
                tone = pcm[(expected + sr // 8) * 2:(expected + sr // 3) * 2:2]
                frequencies.append(tone_frequency(tone))
            assert abs(len(pcm) / 2 / sr - duration / rate) < .01
            assert max(abs(n - 440) for n in frequencies) < 2, "Pitch probe failed"
            assert max(abs(n) for n in offsets) < 20, "Attack timing probe failed"
            # Prior playback-rate behavior would shift this 440Hz tone.
            assert abs(440 * rate - frequencies[0]) > 40
            rows.append({"rate": rate, "tone_hz": frequencies, "pulse_peak_offset_ms": offsets})
        return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--signal", action="store_true")
    args = parser.parse_args()
    provenance = json.loads((ROOT / "media/rehearsal-provenance.json").read_text())
    assert provenance["producer_sha256"] == sha(ROOT / "tools/render_rehearsal.py")
    setlist = json.loads((ROOT / "dist/setlist.json").read_text())
    renders = provenance["renders"]
    assert {(r["track"], r["rate"]) for r in renders} == {(s["id"], rate) for s in setlist for rate in RATES}
    assert len(renders) == 4
    diagnostics = []
    for record in renders:
        source, audio = ROOT / record["source"], ROOT / record["audio"]
        assert sha(source) == record["source_sha256"] and sha(audio) == record["sha256"]
        with wave.open(str(source)) as w:
            assert w.getnframes() == record["source_frames"]
        frames = round(record["source_frames"] / record["rate"])
        assert record["frames"] == frames == container(audio)
        assert record["filter"] == FILTER.format(rate=record["rate"])
        item = next(s for s in setlist if s["id"] == record["track"])
        assert "dist/" + item["rehearsalAudio"][str(record["rate"])] == record["audio"]
        if args.signal:
            pcm = decode(audio)
            peak = max(abs(n) for n in pcm)
            rms = math.sqrt(sum(n * n for n in pcm) / len(pcm))
            assert abs(len(pcm) / 2 / 44100 - frames / 44100) < .01
            assert 0 < peak < 1, "Decoded clipping/headroom probe failed"
            assert .02 < rms < .3
            diagnostics.append({"audio": record["audio"], "decoded_frames": len(pcm) // 2,
                "peak": peak, "rms": rms})
    print(json.dumps({"assets": 4, "original_sources_and_duration_verified": True,
        "decoded": diagnostics, "synthetic_signal_probes": signal_probe() if args.signal else [],
        "boundary": "Signal/format checks, not human listening or artistic approval."}))


if __name__ == "__main__":
    main()
