# Lab state

**Updated:** 2026-10-14 (UTC). **Seed:** 0.29.0.
**Current milestone:** P03 original-pitch rehearsal 0.4.0 / P08 derivatives 0.5.0.

[Tokyo 80s](../projects/tokyo80s/README.md) now supplies four 75%/90% Vorbis
backings derived from its preserved PCM masters. FFmpeg/Rubber Band performs
offline stretching; Web Audio plays them at 1× with mapped offsets/durations.
100%/full-run OGG, charts, scoring, calibration and best keys stay unchanged.
Exports distinguish performance tempo from actual backing identity/node rate.
Missing/wrong-duration assets cannot silently detune; one decoded buffer is cached.

Actual tab departure during a delayed load exposed an existing startup gap.
Loading now cancels on focus/visibility loss; Start is required after return.
Late responses cannot replace a newly selected track. The controlled failing
case passes after the fix, alongside existing playing/pause/error regressions.

[Execution](../evidence/tokyo80s/PITCH_RUN.json) records 24 logic cases, 16 browser
cases across source/rehearsal/full-song workflows, final affected regressions,
four decoded artifacts, encoded 440Hz/transient probes and real old/current
playback/OfflineAudioContext samples. Both complete 69s/84.5s stages ran.
Sampled eight phrase boundaries per asset show envelope offsets −10…0ms;
this is not proof of every attack or hardware latency. Codex reviewed frames.
Physical listening, unassisted practice/accessibility, timbral quality, other
browsers and learning/commercial benefit remain unverified.

Started clean at `45ea179`, matching fetched main; normal main publication is
authorized and push permitted. Reassessed portfolio/history and actual P03,
P11 and P10 sources. Recent native deliveries do not dictate this selection.
Pitch-preserving practice removes a concrete musical limitation; selective room
import needs authorship/merge semantics, while complete literature needs readers.
Standard/Mono Godot 4.6.3 and SDK 10.0.401 exist; preserve the established browser
consumer rather than migrate engines for an offline audio-processing milestone.

Original media/producers/charts, other products and archived sources are preserved.
The environment restart retained artifacts/logs. Existing CI now checks rendered
derivatives and encoded probes plus real playback; publication/CI status is
confirmed at task closure. Compare physical listening/practice with native
installation/tactics, independent P04/P10 reading and real P11 use next.
