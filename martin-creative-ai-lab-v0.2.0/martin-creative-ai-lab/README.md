# Martin Creative AI Lab

An evolving laboratory of games, narrative, images, audio, data, and AI
evaluation by **Martin Melcop Neto**. Projects are adaptable seeds: build small
slices, verify behavior, record decisions, and test reuse in actual destinations.

**Current seed: v0.4.6.** The lab includes eleven project lines, 178 preserved
historical texts, a working local text-chat adaptation, a calibrated
practice-task harness, and a playable terminal dialogue scene. No game migration,
model benchmark, finished music catalogue, or public deployment is claimed.
The containing directory keeps its original v0.2.0 package name.

## Start here

- [State](docs/STATE.md): completed increment, limits, and next action.
- [Assessment](docs/ASSESSMENT.md) and [improvement plan](docs/IMPROVEMENT_PLAN.md): evidence and selected priorities.
- [P11 — Live exchange](projects/realtime-integration-lab/README.md): install, run, test, provenance, and contribution.
- [P02 — EVAL-001](evaluations/chat-send-buffering/README.md): export a starter, check a client, and inspect limits.
- [P10 — The Last Waystone](projects/waystone-dialogue/README.md): play a stateful dialogue scene, restart, inspect traces and verify its origin.
- [Current dialogue evidence](evidence/waystone-dialogue/TRUST_RUN.json): 23 checks, old/new CLI comparisons, agreement refusal and capped apology recovery.
- [Current unread-navigation evidence](evidence/realtime-chat/UNREAD_RUN.json): arrival counts, keyboard focus and bounded history.
- [Prior reading/recalibration evidence](evidence/realtime-chat/READING_RUN.json): geometry, source comparison, full chat results and P02 compatibility.
- [Previous timeout/recalibration evidence](evidence/evaluation-task/TIMEOUT_RUN.json): actual command probes, source comparison, compatible artifacts, environment and hashes.
- [P11 transport evidence](evidence/realtime-chat/POLLING_SEND_RUN.json): prior correction and its bounded tests.
- [SEED.md](SEED.md), [agent instructions](AGENTS.md), and [decisions](docs/DECISIONS.md): direction and operating context.
- [Project registry](registry/projects.json) and [legacy inventory](registry/legacy_sources.json): IDs and evidence boundaries.
- [Recovered sources](docs/LEGACY_REPOSITORIES.md): historical snapshots and their limitations.

Original creative titles include Artemyra / ArtemiZ4, Tokyo 80s,
O Lich mais velho da tumba mais antiga, The Dark Knight, and Véu Partido.
Their complete runtime baselines are not present here. Rave Master supplies
selected narrative, combat, and production material; planned art/audio indices
do not establish available masters. [The assessment](docs/ASSESSMENT.md) states
what was actually inspected or executed.

## Verify the lab

From this lab directory, with Python 3.10+ (CI uses 3.12):

```bash
python3 tools/validate_repo.py
python3 tools/test_validate_repo.py
python3 projects/waystone-dialogue/test_scene.py
python3 evaluations/chat-send-buffering/test_runner.py
sha256sum -c MANIFEST.sha256
```

The first check validates registries, local Markdown file links, and preserved
source hashes, excluding dependency documentation under `node_modules`. The
regression suite checks that maintained broken links and archive corruption still
fail. The manifest covers maintained files inside this lab, excluding
itself, ignored dependencies, and generated outputs. These lab checks do not run
the browser acceptance suite; P02's checker and P11's test commands do.
P10's scene requires Python 3.10+ and has no external dependencies. P11 has its
own installation and test commands; other projects do not need to be installed
to develop it. Current execution and historical records are distinguished in
the state record.

[Lab checks](https://github.com/MartinFMelcop/Creative_AI_Project_HUB/actions/workflows/lab-checks.yml)
runs these checks on main pushes, pull requests to main, and manual dispatch.
Two Ubuntu 24.04 jobs use Python 3.12, P11's recorded Node version, locked npm
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
[CI evidence](evidence/continuous-integration/RUN.json) records local execution;
GitHub job logs establish remote runner results.

The original delivery test failed on the preserved source and passed on 0.1.0.
Two further send-path regressions fail on that committed client and pass on 0.1.1.
Twenty-six current automated tests verify the local contract, including connected
polling congestion, stale-state reconnect buffering and preserved reading position. New
documentation, UI, code comments, and evidence are in English; historical texts
remain in their original language. Martin supplied direction and authorization;
Codex performed this increment. Manual usability review by Martin is pending.

TR-009 now has a verified P02 task consumer: baseline rejects at 15/17 and
reference accepts at 17/17. Other transfers remain candidates. No independent
model was evaluated. P11 0.1.2 and P02 runtime recalibration are Git-published in
[f35e2e7](https://github.com/MartinFMelcop/Creative_AI_Project_HUB/commit/f35e2e767f215040e9e300eb0ee480fa2fc082d5), confirmed on remote main after a normal push.
The starter contract remains 0.1.0. [State](docs/STATE.md) records source commits,
verification and publication. This task explicitly authorized the publication.
