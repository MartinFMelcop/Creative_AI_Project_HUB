# Martin Creative AI Lab

An evolving laboratory of games, narrative, images, audio, data, and AI
evaluation by **Martin Melcop Neto**. Projects are adaptable seeds: build small
slices, verify behavior, record decisions, and test reuse in actual destinations.

**Current seed: v0.15.0.** The lab includes eleven project lines, 178 preserved
historical texts, a working local project-conversation workspace, a calibrated
practice-task harness, a complete rescue adventure with browser/terminal editions,
two original browser rhythm stages with rendered soundtracks and sustained notes, a native C# economy board with preserved terminal workbench, a complete Portuguese story with EPUB/PDF, and a native
Godot boss arena with painted art, adaptive audio and an executed PCK. Private
Sites demos support the browser games. No full RPG migration, model benchmark,
finished music catalogue or public-audience deployment is claimed.
The containing directory keeps its original v0.2.0 package name. Latest verified
project versions and execution boundaries are in the state and registry.

## Start here

- [P04 — A água sob Darsen](projects/lich-cistern/README.md): complete standalone story, EPUB and A5 PDF.
- [Reading edition execution](evidence/lich-cistern/RUN.json): conformance, text identity and implementer editorial review.

- [P01 — Eclipse Fair](projects/eclipse-fair/README.md): playable Godot .NET board, concrete previews, paced rivals and replayable resume; terminal workbench preserved.
- [Native board execution](evidence/eclipse-fair/BOARD_RUN.json): compiled source and runtime-only package, UI journeys and rendered review.
- [Economy execution](evidence/eclipse-fair/RUN.json): source/compiled package, synthetic play and tuning limits.

- [P06 — Veilbreak](projects/veil-arena/README.md): native painted Godot boss encounter, adaptive audio, source and playable resource pack.
- [Native media execution](evidence/veil-arena/PRESENTATION_RUN.json): actual mixer, OpenGL frames, preserved full fight and media-inclusive pack execution.

- [State](docs/STATE.md): completed increment, limits, and next action.
- [Assessment](docs/ASSESSMENT.md) and [improvement plan](docs/IMPROVEMENT_PLAN.md): evidence and selected priorities.
- [P03 — Tokyo 80s Night Shift](projects/tokyo80s/README.md): choose Midnight Signal or Rain Circuit, carry long notes, calibrate timing and finish/replay.
- [Rhythm/audio evidence](evidence/tokyo80s/RUN.json): real 69-second Web Audio run and registered master/export, with honest review limits.
- [P11 — Project Rooms](projects/realtime-integration-lab/README.md): persistent project notes/decisions, local identity, history recovery, drafts and export.
- [P02 — EVAL-001](evaluations/chat-send-buffering/README.md): export a starter, check a client, and inspect limits.
- [Current dependency-gate evidence](evidence/evaluation-task/DEPENDENCY_RUN.json): installed direct version checks, controlled mismatch and unchanged calibration.
- [P10 — Flood Crossing browser](projects/waystone-dialogue/browser/README.md): two connected days: rescue, relief priorities, clinical timing, food/seed, local resume and backward-compatible portable saves.
- [Browser milestone evidence](evidence/waystone-dialogue/BROWSER_RUN.json): Python parity, actual Chromium journeys and implementing-agent presentation review.
- [Rescue milestone evidence](evidence/waystone-dialogue/ADVENTURE_RUN.json): actual route playthroughs, cargo-order comparison, connected checks and same-agent review.
- [Prior dialogue evidence](evidence/waystone-dialogue/DUSK_RUN.json): 32 checks, deadline-aware closing responses, seven CLI comparisons and unchanged rules across all reachable states.
- [Previous dialogue evidence](evidence/waystone-dialogue/DIALOGUE_RUN.json): 29 checks, contextual responses and unchanged rules across all reachable states.
- [Persistent rooms evidence](evidence/realtime-chat/ROOMS_RUN.json): database/server reopening, collaborator workflow, idempotent retry and complete export.
- [Previous chat evidence](evidence/realtime-chat/DRAFT_RECOVERY_RUN.json): edited-draft timeout recovery, both controlled delivery outcomes, literal wrapping and all 38 chat checks.
- [Prior text-reflow evidence](evidence/realtime-chat/TEXT_REFLOW_RUN.json): fixed-panel user styles, reading anchors and pinned evaluator compatibility.
- [Prior activity evidence](evidence/realtime-chat/ACTIVITY_RUN.json): inactive-page arrivals, tab-title counts, focus/visibility reset and bounded history.
- [Prior unread-navigation evidence](evidence/realtime-chat/UNREAD_RUN.json): arrival counts and keyboard focus.
- [Prior reading/recalibration evidence](evidence/realtime-chat/READING_RUN.json): geometry, source comparison, full chat results and P02 compatibility.
- [Previous timeout/recalibration evidence](evidence/evaluation-task/TIMEOUT_RUN.json): actual command probes, source comparison, compatible artifacts, environment and hashes.
- [P11 transport evidence](evidence/realtime-chat/POLLING_SEND_RUN.json): prior correction and its bounded tests.
- [SEED.md](SEED.md), [agent instructions](AGENTS.md), and [decisions](docs/DECISIONS.md): direction and operating context.
- [Project registry](registry/projects.json) and [legacy inventory](registry/legacy_sources.json): IDs and evidence boundaries.
- [Recovered sources](docs/LEGACY_REPOSITORIES.md): historical snapshots and their limitations.

Original creative titles include Artemyra / ArtemiZ4, Tokyo 80s,
O Lich mais velho da tumba mais antiga, The Dark Knight, and Véu Partido.
Their historical full runtime baselines are not present here. Tokyo 80s now
has a new original browser destination, distinct from its unavailable old ZIP. Rave Master supplies
selected narrative, combat, and production material; planned art/audio indices
do not establish available masters. [The assessment](docs/ASSESSMENT.md) states
what was actually inspected or executed.

## Verify the lab

From this lab directory, with Python 3.10+ (CI uses 3.12):

```bash
python3 tools/validate_repo.py
python3 tools/test_validate_repo.py
python3 tools/test_check_manifest.py
python3 projects/waystone-dialogue/test_scene.py
python3 projects/waystone-dialogue/test_adventure.py
python3 projects/waystone-dialogue/browser/tools/export_dialogue.py --check
python3 projects/tokyo80s/tools/check_audio.py
python3 evaluations/chat-send-buffering/test_runner.py
python3 tools/check_manifest.py
```

The first check validates registries, local Markdown file links, and preserved
source hashes, excluding dependency documentation under `node_modules`. The
regression suite checks that maintained broken links and archive corruption still
fail. The manifest checker requires every Git-tracked or nonignored untracked
file inside this lab exactly once, excluding the manifest itself. Ignored
installation outputs are excluded; a tracked file remains required even if an
ignore pattern matches it. Missing entries, stale entries and hash mismatches
fail. See [the integrity contract](docs/REGISTRY_VALIDATION.md). These lab checks do not run
the browser acceptance suite; P02's checker and P11's test commands do.
P10's scene requires Python 3.10+ and has no external dependencies. P11 has its
own installation and test commands; other projects do not need to be installed
to develop it. Current execution and historical records are distinguished in
the state record.

[Lab checks](https://github.com/MartinFMelcop/Creative_AI_Project_HUB/actions/workflows/lab-checks.yml)
runs these checks on main pushes, pull requests to main, and manual dispatch.
Four Ubuntu 24.04 jobs include pinned .NET 10 compiled economy and Godot native gameplay/package checks,
Python 3.12, P11's recorded Node version, locked npm
packages and Playwright's matching Chromium. Browser installation/startup must
succeed; unavailable execution cannot produce a passing calibration. Full Git
history retains the evaluator's pinned starter and suite commits. Actions have
read-only repository permissions; no product deployment or model API is involved.

With P11 dependencies and Chromium available, run the same controlled calibration
locally from this lab directory (set `CHROMIUM_PATH` for a non-default browser):

```bash
python3 tools/check_calibration.py /tmp/lab-calibration-run
```

The output directory must be new. The command requires the baseline to reject at
15/17 and the pinned reference to accept at 17/17, with no skips or cancellation.
Any changed counts, wrong gate or inconclusive execution exits nonzero. Two JSON
records preserve diagnostics; CI uploads them for 14 days, including on failure
when records exist. These are controlled artifacts, not independent candidates.
[Initial CI evidence](evidence/continuous-integration/RUN.json) records local execution.
[Follow-up evidence](evidence/continuous-integration/FOLLOWUP_RUN.json) records
the first hosted cleanup-test race and its correction; the current evaluator
suite has 23 regressions. [Manifest evidence](evidence/continuous-integration/MANIFEST_RUN.json)
records the former omission false pass and complete-coverage correction.
GitHub job logs establish remote runner results.

The original delivery test failed on the preserved source and passed on 0.1.0.
Two further send-path regressions fail on that committed client and pass on 0.1.1.
Thirty-eight retained legacy tests verify the ephemeral contract, including connected
polling congestion, stale-state reconnect buffering, preserved reading position,
activity-aware unread counts, viewport resizing and fixed-panel text reflow. New
documentation, UI, code comments, and evidence are in English; historical texts
remain in their original language. Martin supplied direction and authorization;
Codex performed this increment. Manual usability review by Martin is pending.

TR-009 now has a verified P02 task consumer: baseline rejects at 15/17 and
reference accepts at 17/17. Other transfers remain candidates. No independent
model was evaluated. P11 0.1.2 and P02 runtime recalibration are Git-published in
[f35e2e7](https://github.com/MartinFMelcop/Creative_AI_Project_HUB/commit/f35e2e767f215040e9e300eb0ee480fa2fc082d5), confirmed on remote main after a normal push.
The starter contract remains 0.1.0. [State](docs/STATE.md) records source commits,
verification and publication. This task explicitly authorized the publication.
