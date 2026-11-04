# Independent Creative / rights review — P08 V6 intake

Read-only review of maintained consumer at HEAD `1cc982a525b63abbd8a1091ebd70e16df7844cb5`. No maintained files edited. Archive sources are research evidence, not current operating authority. Root/workspace AGENTS, full Continuous Development v2 and STATE were read. Creative Brain chapters CRE-067, CRE-070 and CRE-072 were retrieved in full through the protected query tool; all are H (hypothesis), not author approval or canon.

## Decision

Use V6 as the finite research handoff and adapt one narrow, newly authored consequence-aware playback/mix rule in the actual existing Crossing consumer. Preserve the existing C# `Plan.Observe` meaning, Domain state, composer, original WAV identity, aligned transports and silence semantics. Do not import candidate source, MIDI or WAV wholesale. Do not create a replacement Workbench, new soundtrack, new audio owner or another research-only version.

The present browser `cue()` function owns two voices but removes the oldest voice regardless of semantic value. It also resets the music-duck recovery whenever a cue starts, using only the newest cue's duration. Both are concrete consumer questions. A policy that controls gain/voice count while losing a critical cue can satisfy a signal bound and still fail its purpose. Choose an improvement with actual captured PCM and independently observable content preservation, not a quieter ledger alone.

## Creative acceptance and ownership

C# accepted observations remain the sole source of event meaning. Playback never invents damage, paid protection, next threat, success, world changes or a turn. Duplicate/stale/refused observations remain silent; consumed identity advances while muted/suspended; resume never replays backlog. Terminal won/lost supersedes stale combat feedback. New policy should distinguish current actionable next-threat information from previous decorative/tail content. A newly accepted next-threat cue supersedes obsolete warning content; permanently preserving every stale cue would itself misrepresent the current state.

Suggested bounded hierarchy for evaluation: terminal result first; current actionable warning and material player consequence next; descriptive contact/tails below; music/ambience below those. Exact ordering of damage versus next-warning is a product choice and should be explicit rather than inferred from volume. The existing paired feedback/next-threat plan need not be recast as the archive oracle's at-most-one cue. Test contention with the actual accepted sequence and record which audio was completed, attenuated, interrupted or suppressed. Do not silently call every consumed observation an audible success. Preserve visual/text alternatives and independent Music/Effects controls.

CRE-072 materially requires coherent adaptation, deliberate silence and avoiding music that conceals telegraphs; it explicitly leaves motif notes/instruments/BPM open. CRE-067 requires recognizable action signatures rather than color/loudness alone. CRE-070 argues for region/material identity and restraint instead of one industrial palette for all settings. These constrain evaluation without approving candidate class/world fiction.

## Composition, harmony, timing and Foley assessment

- `research/09_MUSIC_GRAMMAR_AND_IDENTITY.md` usefully separates motif intent (interval contour, rhythm, rests, narrative role), actual section behavior and performance articulation. Its three named motif specifications remain briefs, not approved themes. General methods are reusable; no artist/game note sequences, lyrics, samples, riffs or branding should be adopted.
- Fixed envelopes, extra notes, randomized chords and novel meter are not reliable substitutes for authorial structure. The supplied arrangement audit counts density, exact bar repetition and low-register onset overlap; those are audition prompts, not tests of harmonic quality, originality or masking. It cannot approve a composition.
- `ScoreCoherence.cs` defaults pitched snapping off and exempts some sustained layers, but still repairs duplicates/overlaps. Such changes may alter intentional unison/rearticulation, articulation or groove. Keep repair opt-in with authored timing provenance and a retained original. No present Crossing need justifies porting this subsystem.
- `BarTransitionScheduler.cs` illustrates integer tick-to-frame boundary scheduling in fixed BPM with odd-meter support. It does not establish variable-tempo maps, expressive feel or sample-accurate future Unity playback. Existing actual aligned stems already solve a narrower real consumer need.
- `research/10_SOUND_REALISM_AND_MIX.md` models motion/contact/resonance/secondary motion/decay and material context. Reusable causal event design is stronger than relabeling an oscillator. The 12 supplied synthetic SFX are not verified animal/material recordings. No claim of naturalness or realism follows from format, spectra or procedural generation.
- Variant similarity is only triage. Different SHA values do not prove variety; high global spectral similarity does not prove perceptual sameness. The portal/fire/creature flags invite blinded tests; unflagged electric/steel/stone pairs are not validated recognition successes.

## Three independent evidence boundaries

1. Mathematical/digital: correct event identity, byte identity, rendered waveform, clocks, sample peaks and measured signal content. These can be directly instrumented.
2. Playback operation: actual C#/browser consequences, finite voices, ordered ownership, phase, real output capture, lifecycle and controlled mutant detection. Offline synthetic reports do not establish these.
3. Perception/art: recognizing hit/block/threat/result, understanding meaning, comfort, physical realism, motif recall, expressive timing and authorial quality. Neither lower peaks, larger margins, signal energy ratios nor agent review establishes these.

V5's noncausal whole-scene gain optimizer must not become a real-time controller. Two scenes exceed its ceiling from background alone. V6's generic 4x FIR counterexample shows the limitations of sample peaks, not certified true peak, clipping heard in the game or LUFS. Preserve these negatives without adopting their fixture-specific values as shipping presets.

## Listener protocol assessment

The planned material/action forced choice, variant ABX, delayed motif recognition and actual gameplay critical-cue detection are distinct tasks. Preregister the task, main outcome, per-person paired design, device metadata, rights-cleared stimuli, hidden label mapping, randomized/counterbalanced order, handling of missing data and uncertainty. Equalize presentation level with a documented method while retaining transients. Avoid collecting names/sensitive health data. Keep unknown and withdrawal options; do not count repeated trials as independent listeners.

No listeners exist in V6 and no participant study was run in this review. The 12–24 pilot range and >=70% example are proposals, not powered sample sizes or international acceptance standards. The package explicitly disclaims BS.1116/MUSHRA compliance. No realistic/iconic/recognized/professional/better-playing claims are supported. Author approval and actual Unity/Windows output remain separate from browser technical acceptance.

## Rights inventory and actual gate execution

After inspecting `governance/asset_release_gate.py`, executed both modes against `WHOLE_PACKAGE_MEDIA_INVENTORY.json` with output exclusively in scratch:

- Research: exit 0, PASS, actual 48 / declared 48, zero errors.
- Public: expected exit 2, FAIL, actual 48 / declared 48, zero errors, 48 blocked.
- Exact inventory: 35 candidate reference WAV + 12 demonstration WAV + 1 demonstration MIDI = 47 WAV and 1 MIDI. Every entry is UNVERIFIED + RESEARCH_REVIEW_ONLY.
- Results: `rights-research.json` and `rights-public-blocked.json` beside this review. A passing research declaration/identity gate is not legal clearance.

No original LICENSE, NOTICE, COPYING or COPYRIGHT grant file was found anywhere in the intake. Candidate C# Core and Music target netstandard2.1/C#8; Desktop references Avalonia.Desktop/Themes.Fluent 12.1.4. Those project references are dependency declarations, not license evidence. The absence of an external package in a Core csproj does not prove original code ownership or a redistribution grant. Compilation or a repaired GUI restore cannot clear copyright. Literal candidate source import should remain unresolved pending actual ownership/usage authorization and notices.

The archive explicitly says source code and WAV are retained for private evaluation and not to publish them without separate dependency/original-work clearance. None of the media should enter public Git history, a downloadable public evidence bundle or a deployed stimulus set on current evidence. MIDI is included in this restriction: no soundfont dependency does not by itself prove score ownership.

The claimed TimGM6mb soundfont source/license, modification, sample redistribution and output rights are unresolved; the sf2/MP3 renders are excluded, and possession of outputs would not cure this. Sonniss is cited only as a methodological/legal source and its exact license version is asset-specific; do not ingest/redistribute any referenced library recordings or treat a general license URL as file-specific permission. The intake describes its 2026-08-27 v2 restrictions, but this review did not independently fetch or authenticate those external terms. No such sample is needed for the selected consumer increment.

Positive clearance for any later copied source/media requires exact owner/creator, source URI and original grant/license text/version/date, hashes, third-party chain, output/synchronization/standalone/commercial/AI-development terms, attribution/NOTICE and a documented decision for the actual consumer. Do not create a pseudo-license or infer public domain from AI generation.

Safe current reuse: cite the private intake's source identities and general engineering/research principles in newly authored contextual documentation; independently implement the minimum necessary algorithm in existing owned runtime code; generate experiments from the maintained original `Composer` without importing archive note strings/samples; retain repository notices and existing provenance. This does not establish broad commercial clearance for North Star.

## Refutable runtime acceptance recommendation

Use the same accepted event schedule before/after; include clean and overlapping cues, terminal arrival, stale/refused observations, music disabled, effects disabled, mute/suspend/resume, decode invalidation and rapid commands. Capture actual post-mix PCM. Confirm meaningful target cue content/duration or an explicitly documented interruption rule, finite voices and gain bounds with the original composer. Include a controlled content-loss or prematurely released-duck mutant that the instrument rejects; restore actual code before final evidence. Keep Domain/contact/outcome state and source/composer/media identities unchanged. Report only the properties actually executed and measured.
