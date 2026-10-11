# Lab state

**Updated:** 2026-10-11 (environment UTC date). **Seed version:** 0.4.6, unchanged.
**Current increment:** shared GitHub regression checks.
P10 dialogue 0.1.1, P02 runner 0.2.0, P11 app 0.1.3 and starter contract 0.1.0
remain unchanged; their bounded M4 scopes are not promoted by CI.

The checkout began clean at published
`6f9891a3f5fc754140d84f3a42514517a1ca9094`; fetch/merge confirmed the same main.
The three working destinations have regressions but no GitHub workflow. Choose
shared QA rather than expand products or manufacture human/candidate evidence.

[Lab checks](https://github.com/MartinFMelcop/Creative_AI_Project_HUB/actions/workflows/lab-checks.yml)
now defines two Ubuntu 24.04 jobs for main pushes, pull requests to main and manual
dispatch. Integrity/dialogue runs the registry, link, archive, validator, scene
and manifest checks. Chat/evaluation installs locked dependencies and matching
Playwright Chromium, requires its executable, runs real protocol/browser checks,
runner regressions and controlled calibration. Actions are commit-pinned with
contents-read permissions, no persisted checkout credentials and job deadlines.
Full Git history preserves pinned evaluator/starter snapshots. ADR-019 records
the durable QA choice and its limits.

`tools/check_calibration.py` requires baseline rejection at 15/17 and pinned
reference acceptance at 17/17 with complete counts and the behavior gate. It
creates new JSON records without replacing prior runs; CI retains diagnostics
for 14 days, including failure records when available. This is calibration,
not an independently produced model submission or score.

[Initial local CI evidence](../evidence/continuous-integration/RUN.json) records commands,
environment, artifact identity and controlled probes. All 11 validator, 23 scene,
22 runner and 26 chat checks pass; actionlint 1.7.12 accepts the workflow. Live
calibration has the expected 15/17 and 17/17 results. Missing-browser and changed
baseline probes both fail; an existing output directory exits 2 without replacing
records. The workspace initially blocked localhost; permitted execution resolved
that environment restriction. Final links/archive and manifest checks run at
closure. Prior [dialogue evidence](../evidence/waystone-dialogue/TRUST_RUN.json),
all historical records, sources and project implementations stay unchanged.

The [first hosted run](https://github.com/MartinFMelcop/Creative_AI_Project_HUB/actions/runs/38106719666)
passed integrity/dialogue and all 26 chat checks, then exposed a cleanup-test race:
a killed child disappears between checking `/proc` and reading its state. Read
the state directly and tolerate only missing-file/missing-process errors; retain
the assertion rejecting a live child and propagate permission errors. A new
regression verifies those distinctions. [Follow-up evidence](../evidence/continuous-integration/FOLLOWUP_RUN.json)
reproduces the published error and corrected success with a real child and a
controlled stat-read race. All 23 current evaluator regressions pass. P02 runtime
and its 17-check task are unchanged; the initial evidence remains historical.

This record precedes follow-up publication. Local execution uses Linux, Python 3.12.14,
Node 24.19.0 and system Chromium 154; GitHub installs Playwright's browser.
The final report supplies the verified remote SHA and hosted-run result; local
checks alone do not establish remote success. Branch protection is not enabled
by this workflow. Human narrative/usability review, other platforms, engine
migration and an independent EVAL-001 candidate remain unverified.

Next: reader playthrough of P10 truthful/conflict/repair paths and wording/pacing
feedback; then one independent EVAL-001 submission with recorded provenance and
Martin's P11 usability review. Martin supplied direction; Codex implemented/tested.
