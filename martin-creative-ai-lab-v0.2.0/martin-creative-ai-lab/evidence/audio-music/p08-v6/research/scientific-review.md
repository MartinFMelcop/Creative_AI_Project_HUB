# Independent P08 V6 scientific intake review

The extracted archive is an offline research packet, not repository authority or a
verified Unity audio product. Root/workspace instructions, the complete continuous
development process and STATE were read before inspection. SCI-013/014/017/064/070
were retrieved in full: rival explanations, operational measures, controls and the
separation of file identity, signal output and perception materially shaped this review.

## Execution and preservation

`replay_intake.py` was written outside the maintained tree. It fingerprints every
source file before/after, logs complete stdout/stderr for every command, inventories
test methods independently using AST, executes all ten suites individually in addition
to the requested archive runner, and retains regenerated reports outside the archive.
The complete observation is `INTAKE_REPLAY.json`; `source-before.json` and
`source-after.json` are identical over all 246 files. The archive's own manifest covers
245 files plus the manifest itself. Both before/after `validate_v6.py` passes were
observed; they verify stored evidence, not fresh execution by themselves.

All 26 commands had their expected exit status. The ten actual individual suites ran
9+9+15+11+10+22+3+14+10+9 = 112 tests, exactly the independently inventoried test count.
These include meaningful MIDI malformed/tempo controls, scalar-gain/shifted duplicate
triage, mute/stale/cooldown/event identity, malformed/overrange signal rejection,
voice-budget tradeoffs, nonfinite input, infeasible-background and claim/path negatives.
They are software controls, not independent studies, listeners or participants.
Thirteen regenerated JSON reports matched their references exactly, including two
expected public-asset rejection reports whose actual exit was 2.

The requested standalone probe is `experiments/intersample_peak_probe.py`, not a
`tools/` path. Its regenerated SHA-256 is
`1bdc4da92ec3fa02d3346ce693525685a0fc83decd1b2fc74b97cbff1e4ec936`.

The existing host provided Python 3.12.14, NumPy 2.3.5 and SciPy 1.17.0. SoundFile
was absent; only pinned SoundFile 0.13.1 was installed with `--no-deps --target` into
this external `science/python-deps` directory. CFFI 2.1.1/pycparser 3.0 were already
present; the installed wheel reports libsndfile 1.2.2. The full installation log is
retained. The archive reference Python was 3.13.5; the deterministic reports also
matched on the actual 3.12.14 execution. No maintained source or intake file changed.

## Exact findings and interpretation

- `reports/R32_V6_INTERSAMPLE_ESTIMATE.json`: six fixed synthetic scenes, 18 policy
  comparisons, 16 evaluated and two background-infeasible rows. Five comparisons
  pass the sample ceiling but exceed the generic 4x interpolated estimate; 12 rows
  exceed under that estimate. The estimator trims 64 original samples at both ends
  and uses SciPy Kaiser FIR reconstruction. It is neither complete-program nor
  standards-conformant/calibrated true-peak measurement.
- `reports/R32_V5_HEADROOM_PRESERVATION.json`: baseline exceeds the -1 dBFS sample
  ceiling in five scenes; fixed gain .37 exceeds it in two; the offline optimizer
  finds four feasible scenes and two background-only failures. It uses future
  whole-scene information and cannot be installed as a causal runtime controller.
- `reports/R32_FACTORIAL_POLICY_ABLATION.json`: the strongest combined cap/duck/.37
  treatment still reaches sample peak 1.062535 in one scene and suppresses three
  events/truncates three. Lower peak does not establish preserved communication.
- `reports/R32_VARIANT_SIMILARITY_TRIAGE.json`: portal/fire/creature pairs trigger
  coarse texture review; their waveform NCC is .036938/.043508/.13075. This is not
  a perceptual variety failure or listener judgment.

The 12-claim ledger comprises five OFFLINE_REPRODUCED, one PUBLICATION_BLOCKED,
three EXTERNAL_REPO_SNAPSHOT and three PENDING_UNVERIFIED rows. The crosswalk checks
JSON selectors and values, not independent truth or legal/scientific validity. Its
general auditor permits at least eight rows; `validate_v6` separately enforces 12.
The three remote snapshot rows are historical pointers. The SDK-not-installed
string emitted by `run_v6_checks.py` is hardcoded; it is not an availability probe
of this execution host. No human listener, Unity or Windows execution occurred.

All 48 WAV/MIDI files remain held outside maintained sources; research gate PASS
only validates inventory/declarations. Both independently executed public gates
refuse publication. No sample, score or source fiction was imported.

## Implementation frontier and revised judgment

The existing `NorthStar.Audio` already implements aligned transport, semantic
consequence ownership, consume-while-muted and two-voice bounds. Initially I judged
that priority admission needed an actual failing case, because terminal arrival
already clears other voices and plans contain at most two cues. I proposed original
event variation as an alternative, with no perceptual-quality claim. Engineering
then demonstrated the real gap: the unchanged actual survey win's 0.60-second cue
was stopped after 8.707 ms by accepted second-begin followed by walk. That evidence
supports the narrower priority-preservation frontier without altering original WAVs.

The prospective `labs/audio-music/priority-protocol.json` requires unchanged source
and gameplay observations, causal two-voice admission, explicit equal-critical
suppression, actual final PCM during overlapping real commands, a critical-cut
policy mutation, lifecycle/stale controls, headroom and a real phase-path negative.
It does not claim zero drops, perceptual masking prevention, recognition or comfort.
