# Lab state

**Updated:** 2026-10-10. **Seed version:** 0.4.0.
**Primary workstream:** P02 EVAL-001 task harness 0.1.0, locally calibrated.
P11 remains 0.1.1. The containing directory retains its v0.2.0 package name.

## What changed

The checkout began clean on `work` at
`df1bd5937e6168dd0ba42ce2f614304d80ffb59d`; a fresh remote query confirmed `main`
at the same merge commit. Both P11 development commits (`66041e7`, `2d4e9a7`)
and remote root-instructions commit `e30f799` are preserved and published.
The earlier state statement that P11 0.1.1 was uncommitted is superseded.

[P02's working task](../evaluations/chat-send-buffering/README.md) exports a
fresh, allowlisted P11 0.1.0 starter plus a behavior brief, without Git history,
reference code, tests, knowledge, or prior evidence. Its evaluator checks only
the submitted client through the existing browser route; source and evaluator
hashes, tool versions, commands, complete output, counts, and failures are recorded.
Support files are immutable; partial or unavailable execution is inconclusive.

No duplicate app, engine migration, model call, dependency change, or shared
framework was introduced. P02's current name is AI Evaluation & QA Lab; Unity
remains its historical proposal. TR-009 is validated for task adaptation and
calibration only. TR-010 and the other nine transfers remain candidates.
P11 implementation/tests/dependencies, source ZIP/inventory, and prior run records
are unchanged; its README now links the destination task.
This new increment is local and uncommitted; it has not been published.

## Verification and evidence

[Calibration evidence](../evidence/evaluation-task/CALIBRATION.json) includes
complete evaluator records and the separation, installation, and execution scope.

- Eight runner regression tests passed: exact starter export, overwrite
  protection, immutable support files, extra/missing/linked artifacts, complete
  result classification, and incomplete/skipped result rejection.
- Exported 0.1.0 client: 17 checks executed, 15 passed, 2 failed as expected
  (polling congestion and stale-state reconnect buffering); rejected artifact.
- Corrected P11 0.1.1 client, submitted through a separate export: 17 checks
  passed (6 protocol, 11 Chromium), zero failed/skipped/cancelled; accepted artifact.
- Missing-browser negative probe: inconclusive, exit 2; no behavior-test pass claim.
- Exported starter frozen installation passed, 97 packages. Its actual CLI
  served health/page and broadcast trimmed text to two Socket.IO peers. The
  server was stopped. This does not turn the defective starter client into a
  working browser solution; its two failures above remain the baseline.
- Documentary validation passed: 11 projects, 11 transfers, 0 assets, 2 sources,
  84 local links. Three existing validator regressions passed. Diff whitespace,
  preserved source/evidence checks and final manifest closure (52 entries) are
  recorded after maintained content is final.

Environment: Linux cloud container, Python 3.12.14, Node 24.19.0, npm 11.9.0,
Chromium 154.0.8037.57, Playwright Core 1.64.0, Socket.IO 4.8.4. The evaluator
probes real browser startup; each suite owns its ephemeral server and browsers.
No additional setup dependency or credential is required.

## Limits and learning

P02 is M4 for a calibrated artifact-checking harness, not for candidate/model
performance. Both artifacts are controlled calibration inputs. No independent
candidate, model identity, cost, score, benchmark, or human review is invented.
The same Codex session designed this harness and reused the existing correction
and tests. Exported context separation is not secrecy, OS isolation, or a sandbox;
public history exposes the answer. Future independent runs need controlled
candidate execution and explicit context/tool/attempt records.

The heartbeat test injects expiry at the pinned library predicate; polling uses
real HTTP writes. These bounded checks do not establish real-world outage
reliability, cross-browser behavior, accessibility, or human usability.
P01 baselines and creative/game/media masters remain missing; P10 remains a
source reservoir. No maturity or availability is inferred from asset labels.

Martin supplied direction and authorization. Codex implemented and calibrated
the task; no independent candidate attempt or manual testing is attributed to Martin.
[Evaluation learning](../knowledge/evaluation-artifacts.md) separates artifact
acceptance, harness calibration, context boundaries, and claims about an author.

## Next concrete action

Run one independently produced EVAL-001 client with an explicit candidate brief,
separate workspace/context, permitted tools, source exposure policy, attempts,
timing and available cost. Preserve its artifact and evaluator result before
making any claim about a model. Martin's P11 two-tab usability review remains
pending and independent. Prepare a commit from the current diff; publishing this
increment requires explicit authorization in its publication task.
