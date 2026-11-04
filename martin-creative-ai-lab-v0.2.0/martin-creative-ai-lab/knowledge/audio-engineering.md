# Preserve consequence content before calling a mix improved

**Question:** Can P08 V6 research improve the existing Crossing audio without
importing unverified assets, replacing its owner or equating lower peaks with better
play? The [execution record](../evidence/audio-music/p08-v6/RUN.json) separates private
intake, offline research, candidate C# execution and destination verification. The
existing [audio consumer](../north-star/csharp/Audio/README.md) owns its narrower
accepted-event, original-composition and aligned-transport contracts.

## Provenance and evidence classes

`P08_V6_FINAL_REENVIO.zip`, SHA-256
`887a1a16a84d09b7fa68aa1c4ad47b2d8500d28debd0699f8d7de9e7cca51923`, contains 246 files.
The [archive inventory](../evidence/audio-music/p08-v6/research/archive-inventory.json)
records original paths and hashes; this lesson is an original interpretation, not a
source/code/media import. Relevant intake sources are
`research/09_MUSIC_GRAMMAR_AND_IDENTITY.md`, `10_SOUND_REALISM_AND_MIX.md`,
`13_VARIANT_DIVERSITY_AND_PSYCHOACOUSTIC_LIMITS.md`, `23_COMBAT_MIX_POLICY_V4.md`,
`28_V5_SIGNAL_PRESERVATION_AND_INFEASIBILITY.md`, `30_V6_CANONICAL_FINDINGS_AND_STOP_CRITERIA.md`
and `31_V6_INTERSAMPLE_PEAK_ASSAY.md`; listener protocols are research files 11/17/20/25.

- **Research findings:** fixed synthetic scenes distinguish music ducking, SFX gain
  and voice culling. They do not describe actual gameplay or human listeners.
- **Executed intake/candidate observations:** identity checks, offline replay and the
  separate C# results below apply only to their recorded inputs and environment.
- **Accepted existing runtime:** game-owned C# observations already project contact,
  next threat and outcome; the browser consumes identity across silence and lifecycle
  changes. This is distinct from an offline event-policy oracle.
- **New admission policy:** [28 actual browser controls](../evidence/audio-music/p08-v6/current/priority-browser.json)
  support bounded destination acceptance: terminal/contact/threat priority, explicit
  suppression, two voices, longest-voice ducking and lifecycle. They do not establish
  full sample continuity or production/subjective approval.
- **Unverified perception:** recognition, masking, realism, timing feel, motif recall,
  comfort, artistic approval and physical-device experience have no listener result.

## Reusable methods and their limits

**Composition/harmony:** specify an original interval/rhythm cell, rests, phrase
function and actual section transformations before procedural expansion. Density,
exact repetition and low-register overlap are useful audition prompts; none proves
harmonic quality, originality or an effective theme. Artist/game references support
study of broad production methods, not copying melodies, samples, lyrics or branding.

**Timing:** retain rational score positions and explicit expressive offsets. A fixed
BPM tick/frame conversion is not a variable-tempo performance model. Do not silently
repair intentional overlaps or quantize deliberate anticipations. An unchanged
source and a reversible, explicit repair remain necessary comparison controls.

**Foley/variants:** design preparation, contact, material resonance and decay around
the actual causal event. Synthetic creature/impact sounds remain synthetic. Distinct
hashes do not prove audible variety; envelope/spectral similarity only prioritizes
listening. Unflagged pairs are not verified material-recognition successes.

**Mixing:** reserve headroom for the permitted concurrent voices and both adaptive
stems. Track completed, suppressed and interrupted audio separately from consumed
observations. Music ducking cannot guarantee SFX-on-SFX headroom. V5's whole-scene
gain search sees future samples and is a diagnostic, not a realtime controller; two
fixtures exceed its sample ceiling from background alone. V6's generic 4x FIR assay
finds five scene-policy rows passing that sample ceiling but exceeding its interpolated
estimate. This is neither certified true peak/LUFS nor evidence that a listener heard
clipping. Energy contribution and retained waveform content do not establish audibility.

**Adaptive/lifecycle:** authoritative accepted events supply meaning; playback must
not create damage, payment, a turn or victory. Repeated/stale/refused observations
remain silent. Mute/suspension consume identity; enable/resume cannot replay backlog.
Terminal results supersede obsolete combat content. Aligned stems share one start;
volume changes must preserve that transport. A finite voice budget needs an explicit
semantic trade-off, not an undocumented oldest-voice eviction or a claim that every
consumed event was heard. Preserve the independent Music/Effects controls and existing
visual/text alternatives.

## Actual candidate compilation exposes two acceptance failures

The [candidate results](../evidence/audio-music/p08-v6/candidate/results.json) record
SDK 10.0.401 on Debian 13/Linux x64. Only 75 `.cs`/`.csproj`/`.props` files were copied
to private scratch; no media was copied. All four test projects and CLI built with
zero warnings/errors. Core/Music target netstandard2.1/C#8; Workflows/tests/CLI use
net10.0. Desktop's Avalonia 12.1.4 packages were not restored/built or substituted.

Audio.Checks passed 142 cases and MusicChecks passed 36. AdaptiveChecks passed one case
then failed its 7/8 transition assertion. TimingChecks printed 24 individual PASS lines
then failed an odd-meter fixture validation; its outer summary says 23 because the
throwing nested suite never returned its earlier passing count. Remaining cases were
not reached. These counts are separate from the Python research tests.

Observed stack traces plus source inspection explain the failures. For Adaptive,
7/8 at 120 quarter BPM/22050 Hz has 38587.5 frames per bar: separately rounding start
and ramp gives 77176, while rounding the entire two-bar duration gives 77175. These
internal values are independently calculated, not printed runtime measurements. For
Timing, a generated seven-bar 4/4 fixture is changed to 7/8 without rescaling/removing
notes: total ticks shrink 26880→23520, and `Validate` rejects out-of-bounds notes before
the scheduler assertions. No candidate repair or assertion weakening was performed.
All 246 original files remained byte-identical, as recorded by
[preservation](../evidence/audio-music/p08-v6/candidate/intake-preservation.json).
Compilation therefore does not establish full candidate acceptance or runtime adoption.

## Bounded runtime consequence

The independently authored admission table preserves a playing terminal over later
accepted begin/contact observations; saturated equal-priority contacts are explicitly
suppressed without backlog. Eleven current input hashes match the final 28-control
execution. Its effects-only late terminal window contains 6175 frames, RMS 0.0190623;
the full nominal capture peaks at 0.199152. The decoded conservative two-voice bound is
0.454013 below the experimental 0.9 ceiling, and duck recovery remains scheduled to the
greatest live end. The isolated actual FIFO mutation cuts the terminal after 20.317 ms
and produces zero late-window PCM under the same criterion.

This establishes retained ownership plus measured late terminal contribution, not
sample-by-sample preservation of the full 0.60-second cue. ScriptProcessor
`playbackTime` labels input blocks as a browser signal-clock proxy; block labels can
overlap/gap and are not hardware-latency calibration. The effects-only window starts
at least 75 ms after later admitted short effects end. Mutant silence supports that
specific attribution while leaving precise onset/duration and human hearing unmeasured.

## Distribution and subjective acceptance stay separate

All 48 supplied media remain **UNVERIFIED / RESEARCH_REVIEW_ONLY**: 35 reference WAV,
12 demonstration WAV and one MIDI. The research gate passed identities/declarations;
public mode correctly refused all 48 with exit 2 and zero inventory errors. No original
license/NOTICE grant was found in the intake. Original code ownership, dependencies,
soundfont/sample output rights and per-file distribution permission remain unresolved.
MIDI and procedural generation do not themselves clear authorship. Keep supplied
code/media out of public Git and public stimulus sets pending positive clearance.
General methods can inform a freshly authored narrow implementation with attribution.

No listeners were recruited. Planned variant ABX, material/action identification,
critical-cue detection and delayed motif recall answer different questions. Preregister
the task, paired participant analysis, randomized/counterbalanced hidden labels,
rights-cleared stimuli, documented level matching, device conditions and missing-data
handling. Repeated trials are not independent listeners. The suggested pilot size and
recognition threshold are proposals, not powered sample sizes or standards; the plans
do not establish BS.1116/MUSHRA compliance. Author review, suitable people/devices,
actual Unity/Windows output and commercial clearance remain separate obligations.

CRE-067/070/072(H), read in full, materially support functional signatures, contextual
material identity, deliberate silence and adaptation that leaves telegraphs readable.
They do not approve candidate lore, a final score or subjective quality. Revisit this
lesson when actual cue-loss controls, target platforms, author decisions or properly
collected listener evidence contradict its bounded conclusions.
