# Private candidate C# verification

Only 75 `.cs`, `.csproj` and `.props` files were copied from the P08 V6 candidate into this scratch directory; no WAV/MIDI or other source assets were copied. All 246 original intake files remained byte-identical after execution. Candidate source was not patched and no source was imported into Git.

SDK 10.0.401 / runtime 10.0.12, Debian 13 Linux x64. All four existing test projects and CLI compiled with zero warnings/errors. Core and Music compile as netstandard2.1/C#8, Workflows and tests/CLI as net10.0. Desktop Avalonia 12.1.4 dependencies were deliberately not restored or built; no version was substituted.

Actual suite results:

| Suite | Actual result |
|---|---|
| Audio.Checks | 142 cases passed, exit 0 |
| Audio.MusicChecks | 36 cases passed, exit 0 |
| Audio.AdaptiveChecks | 1 case passed, then 7/8 scheduling assertion failed, exit 1; remainder not reached |
| Audio.TimingChecks | 24 individual PASS lines, then odd-meter fixture validation failed, exit 1; remainder not reached |
| Audio.Cli | Compiled; command behavior not exercised |

The Timing suite's outer failure says `after 23 checks` because the nested ArrangementChecks had already printed one passing case before throwing and never returned its count. Report 24 observed individual cases with this qualification, never a full timing-suite pass. The optional external-score Adaptive case was never reached; inspection shows that no-argument invocation would count it without assertions, which must not become an external-fixture acceptance claim.

Source inspection and independent exact arithmetic explain the observed Adaptive failure: 7/8 at 120 quarter BPM / 22050 Hz maps one bar to 38587.5 frames, rounded half-up to 38588; adding two rounded bars yields 77176 while rounding the whole two-bar duration yields 77175. The test compares the planner's added-duration end with total duration and rejects the one-frame difference. These internal numbers were calculated from source, not emitted by the failing executable.

The Timing failure occurs before the scheduler assertions. Its fixture generates seven bars of 4/4 notes, changes the meter to 7/8 without removing/rescaling notes, and calls Validate. Total ticks shrink from 26880 to 23520 while final notes remain outside the new bounds. `Invalid note event` is the observed result. This failure does not demonstrate that its scheduler assertions pass or fail.

Complete actual commands, exit codes, log identities and preservation are in `results.json`; unmodified source identities in `copied-source-identities.json`. Logs retain failures. No repair, assertion weakening, fallback SDK, desktop build, device playback, UI, Unity/Windows/Steam, rights clearance or artistic/listener approval is claimed. Candidate remains private research source and fails its whole C# suite acceptance. C# accounting is separate from the parent Python verification; do not sum them into one validation score.
