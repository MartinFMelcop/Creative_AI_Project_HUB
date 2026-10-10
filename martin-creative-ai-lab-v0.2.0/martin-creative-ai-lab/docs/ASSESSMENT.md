# Portfolio assessment

Updated: 2026-10-10. Scope: maintained lab documents, registries, legacy inventory,
the published P11 0.1.1 app/tests, and P02 EVAL-001 at published base `e1850d0`. No legacy source
was extracted and no complete game, manuscript, image, or audio corpus was audited
in this session. This assessment continues the v0.2.0 recovery and v0.3.0 increment
described in [the seed](../SEED.md) and [legacy guide](LEGACY_REPOSITORIES.md).

## Evidence and opportunities

| Projects / resources | Available evidence | Strength / issue | Current evidence boundary |
|---|---|---|---|
| P11 — Real-time Integration Lab / WebSocket | Three preserved historical files; working 0.1.0 committed at `66041e7` | Bidirectional chat already exists. New tests expose connected-send loss during polling and a stale-state reconnect queue; 0.1.1 corrects both | 17 current tests passed; [transport evidence](../evidence/realtime-chat/POLLING_SEND_RUN.json) distinguishes real polling writes from injected heartbeat expiry |
| P10 — Adventures Unleashed / Rave Master | 175 preserved texts; source inventory and previous runner reports | Useful dialogue, combat, and QA specifications. Ten pairs of same-named Ruby scripts have different hashes; source selection matters | Historical recovery reports show 49 combat checks and 19 dialogue steps; not rerun here. No RMXP runtime, equivalent engine implementation, or game balance claim |
| P01, P03, P05, P06 | Seed descriptions and references to historical packages | Economy, timing, and combat could produce useful slices | Baselines absent from this checkout; no execution. Unity and RMXP are not prerequisites for P11 |
| P04 — O Lich mais velho da tumba mais antiga | Narrative and editorial summary in the seed | Concrete character/world direction and potential for interactive adaptation | Full manuscript absent; dramatic quality of a new scene requires selected source and reader review |
| P07 / P08 | P10 art specifications and asset/cue inventory summaries | Visual consistency and cue-driven integration have useful contracts | 293 indexed images are metadata, not inspected images; 25 cues are planned, not audio. No actual masters validated here |
| P02 / P09 | P02 EVAL-001 export/checker plus prior case templates | Actual P11 defects now support a bounded practice task with calibrated gates | P02 runner 0.1.1: 15 runner tests, preserved diagnostics/cleanup, compatible old exports, 15/17 baseline and 17/17 reference. Original missing-browser probe remains prior evidence. No independent model, external client or professional outcome |
| Shared lab structure | Registries, templates, validator, source archive | Clear project IDs and origin records; documented local checks | The 0.1.0 manifest/validator defects were corrected previously. Retain those checks; refresh integrity hashes after this increment is final |

The previous P11 correction checkout began clean at
`66041e7fdd7687ee21099f95129dff41933c74dd`, containing the committed 0.1.0
increment. Its recorded artifact hashes matched before editing; documentary
validation passed with 62 maintained links. Node 24.19.0, npm 11.9.0,
Python 3.12.14, Chromium 154.0.8037.57 and retained dependencies are available.
Use `/workspace/.cache/creative-ai-npm` for the writable package cache.

The original 0.1.0 assessment started at `951c21e`, with 29 local links and an
unimplemented receive/render path in the historical source. That finding was
resolved by the working adaptation; it is not the current defect.

## Previous selected direction — P11 0.1.1

Correct P11's connected-send semantics before extending the sample. A form
submission behind an actual polling write is discarded by volatile emission.
A second test pins heartbeat expiry while `connected` is still true and finds a
packet retained for reconnect replay. Both checks fail on the recorded 0.1.0
client and pass on 0.1.1. The correction allows the live transport write queue
while clearing the separate reconnect queue; it adds no persistence or retry.

This bounded defect correction is executable here and independent of Martin's
pending human UI review. P10 extraction, P02 evaluation, missing game packages,
and media masters remain separate candidates/dependencies. See
[the updated plan](IMPROVEMENT_PLAN.md).

Technical acceptance does not establish visual appeal, accessibility audit,
human usability, production reliability, or portfolio approval by Martin.
Portfolio claims should link the executed evidence and state those limits.

## Historical execution — P11 0.1.0

P11's original delivery defect was reproduced in a real Chromium run. That working
adaptation passed 15 targeted tests and a separate CLI startup smoke. It is a
verified local technical sample, awaiting human usability review and portfolio
selection. No claim has been upgraded for other projects or missing media.

Installing dependencies exposed the validator's accidental traversal of upstream
Markdown: 30 errors originated only under `node_modules`. Pruning that subtree
restores the lab check; 3 regression tests preserve meaningful failures for
maintained links and corrupted source archives. The source archive and its
inventory remain byte-identical to the starting checkout.

## Current execution — P11 0.1.1

Seventeen current tests pass (6 protocol, 11 Chromium), including existing text,
validation, draft, retention, reconnection, and acknowledgement behavior. Frozen
installation passed with unchanged dependency resolutions. A test-harness route
can serve the recorded client revision for a two-failure baseline comparison.
The historical source archive, inventory, and original execution record remain
unchanged. The working server is unchanged; its earlier CLI smoke remains prior
evidence, not a newly performed startup check.

The heartbeat case is controlled fault injection at the pinned library boundary;
it does not prove every real-world outage or packet-loss scenario. Technical
validation remains distinct from Martin's usability review and public presentation.

## Previous task setup — P02 EVAL-001 0.1.0

This iteration began clean at published merge `df1bd59`, with no divergence or
uncommitted user files. Earlier paragraphs retain the P11 assessment/history.
P11 is functionally verified; human review is pending. P02 lacked executable
task delivery, while Unity/game/media baselines remain unavailable or conditional.

Choose a real send-buffering repair task using the existing app and suite. An
explicit export excludes solution/evaluator material. The checker rejects support
mutations and classifies missing execution separately. Known artifacts calibrate
the checker: baseline fails exactly the two recorded transport checks; reference
passes all 17. Eight runner regressions and exported starter install/CLI smoke pass.
No new runtime dependency is needed. [Calibration](../evidence/evaluation-task/CALIBRATION.json)
records identity, inputs and results. TR-009 has a verified consumer in P02; this
does not transfer model ability or justify another shared component.

Export separation is practical packaging, not confidential or independent context
proof. No model/author comparison was run. The next evidence gap is one independent
artifact with an explicit source-exposure/tool policy. UI appeal, human usability,
game execution and missing masters remain outside current acceptance.

## Current correction — P02 runner 0.1.1

This iteration began clean at `e1850d0`, also observed on remote main. Before an
independent artifact attempt, real command probes revealed lost timeout evidence
and a surviving inherited child. The old invocation returned promptly on this
Python version; over-deadline pipe waiting was an unconfirmed hypothesis.

Prioritize reliable incomplete-run records and cleanup within this existing
consumer. The correction preserves partial output and attempted commands, enforces
inconclusive deadlines, terminates inherited groups, and bounds escaped-pipe capture.
Fifteen runner tests pass; known artifacts retain their calibrated results with
byte-identical old exports. [Current evidence](../evidence/evaluation-task/TIMEOUT_RUN.json)
separates real processes, injected gate boundaries, and browser checks. No model
performance or sandbox property is inferred. Independent context and human review
remain the next evidence gaps; no missing creative master was reconstructed.
