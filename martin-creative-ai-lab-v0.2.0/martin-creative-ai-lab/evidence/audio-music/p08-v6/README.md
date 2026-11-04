# Finite P08 research intake and actual critical-cue preservation

[RUN.json](RUN.json) binds independently replayed research, candidate failures and
an accepted bounded improvement in the EXISTING C#/Chromium consumer. This is one
finite author-directed laboratory increment, not a new Workbench product or lab.

The actual supplied filename is `P08_V6_FINAL_REENVIO.zip`, 7,789,823 bytes, SHA256
`887a1a16a84d09b7fa68aa1c4ad47b2d8500d28debd0699f8d7de9e7cca51923`.
It contains the expected `P08_AUDIO_RESEARCH_V6` root. Original ZIP/extraction remain
outside Git in isolated scratch. No supplied media, source implementation or new
package is distributed here. The [inventory](research/archive-inventory.json) and
[read-only audit](research/archive-audit.json) bind all246files/245manifest entries.

The [derived lesson](../../../knowledge/audio-engineering.md) is the knowledge entry;
[the lab](../../../labs/audio-music/README.md) owns its method. Do not copy this study
into SEED, prompts or another knowledge hierarchy.

## Evidence map

- [Research replay](research/INTAKE_REPLAY.json):112actual Python tests in ten suites,
  13exact regenerated reports, all246source files stable. The archive's own runner
  also executes tests; those repeats are not additional tests or independent studies.
- [Scientific interpretation](research/scientific-review.md) and
  [rights review](research/creative-rights-review.md):12claim rows provide mechanical
  traceability, not independent truth. Five sample-pass/4x-interpolated-fail rows do
  not certify ITU true peak. All47WAV/1MIDI remain held; public gates exit2 as expected.
- [Candidate execution](candidate/results.json):five actual builds passed; Core142/
  Music36 passed; Adaptive/Timing failed. Exact logs are UTF-8 strings inside
  [candidate/logs.json](candidate/logs.json), with original names, byte counts and hashes.
  This representation preserves whitespace and diagnostic content. Source copies and
  all supplied media stay outside Git; no candidate repair was attempted.
- [Actual baseline](baseline/playback.json), [PCM](baseline/output.wav) and
  [producer](baseline/producer.mjs):an unchanged0.60s survey-outcome cue was cut after
  8.707ms by later accepted begin/walk. Baseline source preimages are under
  `baseline/preimages/`; these are evidence, not current instructions.
- [Current native](native.json), [exact comparison](native-comparison.json) and
  [final native gate](final-native-execution.json):85controls, original67controls/
  ten assets exact. Current31events contain the original22prefix plus nine actual
  new admission events. The initial whole-list comparator mistake is recorded.
- [Current priority execution](current/priority-browser.json):28actual Chromium
  controls with all11input identities stable. [Terminal PCM](current/terminal-overlap.wav)
  has a nonzero effects-only late tail; [the isolated FIFO mutant](current/critical-cut-mutant.wav)
  loses it. [Contact saturation](current/contact-saturation.wav) retains the explicit
  two-voice overload trade-off. These captures use only existing original Composer
  audio, and each is its own bounded capture, not a continuous combined performance.
- `superseded-26/` retains the earlier successful26-control execution and its exact
  hash-verified producer preimage. Recovery is not reexecution. The final producer
  adds explicit duck-end and decoded-budget controls, with a disclosed timing proxy.
- `legacy-browser/` retains the29unchanged audio controls and their actual capture.
  [Regression report](report.json) binds Presentation47native/20Chromium, P08 source
  14Godot/8Python controls and four strict whole-C#-tree assays. `prior-assays/` keeps
  the replaced RUN/results bytes. No identity dependency/comparison was pruned.
- [Final review](final-review.json), [engineering handover](engineering-review.md),
  [exact diagnostic container](execution-logs.json),
  [current identity recheck](current-input-recheck.json),
  [preservation](preservation.json) and [final repository gates](verification.json)
  separate source review, execution, preservation and publication.

## Reproduction boundary

Use the original attachment only in isolated scratch after inspecting the scripts,
dependencies and finite archive audit. `research/archive-check.py` is a read-only
original audit; `research/replay-intake.py` preserves the exact external replay driver
and its original task-local paths. Adjust paths in a COPY to repeat elsewhere. It
requires the supplied archive, NumPy/SciPy and the disclosed pinned SoundFile dependency;
no held media is fetched from this repository or made publicly available by a test.

From the extracted root, the requested commands actually ran:

```sh
python3 -B tools/run_v6_checks.py --out EXTERNAL_RUN_JSON
python3 -B tools/validate_v6.py
python3 -B experiments/intersample_peak_probe.py demonstrations/sfx --out EXTERNAL_PEAK_JSON
```

From the maintained workspace, with SDK10.0.401 and the existing locked Playwright/
Chromium setup, the destination commands are:

```sh
dotnet build north-star/csharp/AudioChecks/NorthStar.AudioChecks.csproj -c Release -m:1 --disable-build-servers
dotnet north-star/csharp/AudioChecks/bin/Release/net10.0/NorthStar.AudioChecks.dll EXTERNAL_JSON EXTERNAL_ASSETS
node labs/audio-music/browser.mjs dotnet EXTERNAL_LEGACY_DIRECTORY
node labs/audio-music/priority-browser.mjs dotnet EXTERNAL_PRIORITY_DIRECTORY
```

Raw timing/PCM varies across hosts. Reproduction enforces properties, while source
WAV/manifest identities and canonical source assays require exact equality. Research
output, native controls, actual browser captures, candidate checks and repeated
executions remain distinct categories. None represents human listeners, perceived
masking/recognition/quality, certified true peak, hardware latency, licensed Unity,
Windows Player, Steam, commercial rights or production acceptance.
