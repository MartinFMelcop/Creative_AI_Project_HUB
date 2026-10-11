# Lab state

**Updated:** 2026-10-10 (client date). **Seed version:** 0.4.4.
**Current iteration:** P02 syntax attribution, runner 0.1.3.
P11 remains 0.1.2; EVAL-001 starter contract remains 0.1.0. The enclosing
folder retains its original v0.2.0 package name.

## Change and assessment

The clean checkout started on `work` at `786678549e586dc35ce82985bf6014b4d24e64d3`.
Remote inspection found four newer commits. The in-progress increment was saved
in a named Git stash before fast-forwarding to
`6405a557ffcae2cef78a6546be1f5d9b1b0dfe6d`. The P11 reading-position fix,
P02 runtime recalibration, registry-reference gate and all prior commits remain
preserved. Only the syntax correction and its tests were reapplied to code;
continuity was updated from the synchronized documents.

A real invalid NODE_OPTIONS value made Node exit 9 and the old runner reject an
unchanged valid starter as invalid JavaScript. Missing preloads also return
nonzero, including exit 1. Runner 0.1.3 rejects syntax only for a complete exit-1
SyntaxError diagnostic naming the temporary submitted client. Other failures,
signal exits, preload SyntaxErrors and incomplete parser capture are inconclusive.
Command output and actual exit state remain recorded. Runtime options are not
silently removed to conceal environment failures.

No app, dependency, test-suite pin, starter, brief, historical archive, model call,
shared component or transfer maturity changes. P02 remains M4 for the bounded
calibrated harness; the increment does not create an independent candidate.

## Verification

[Raw syntax record](../evidence/evaluation-task/SYNTAX_RUN.json) records the
pre-correction false rejection, synchronized source commit, runner/artifact/suite
hashes, real runtime-option/preload/parser probes and complete command output.
Signal exits and incomplete parser capture are controlled injected boundaries
in the regression suite, not observed process crashes.

After synchronization: 19 runner regressions and 11 validator regressions pass.
The unchanged baseline is rejected at 15/17 and the P11 0.1.2 reference is
accepted at 17/17. All 22 full-chat checks pass with no skips. Exact commands
and captured output are in the raw record. Three new test methods produce four
failure events on the synchronized old runner, with no errors. Earlier registry, reading, calibration and timeout records remain
unchanged historical evidence. The initial restricted Chromium launch failed
with `setsockopt: Operation not permitted`; approved execution supplies the
localhost/Chromium permissions required by the actual test servers.

Environment: Linux cloud container, Python 3.12.14, Node 24.19.0, retained locked
dependencies and system Chromium. Manifest and documentary checks run after final
content: 106 local links and 58 manifest entries pass. The manifest excludes
itself and records maintained file bytes.

## Limits and next action

Parser diagnostic formatting is Node-specific; an unknown format conservatively
returns inconclusive and requires investigation. Diagnostic attribution is not a
security boundary against malicious runtime injection. Process cleanup remains
limited to inherited POSIX groups; non-POSIX fallback is not newly verified.
Human UI review, independent candidate provenance, game engines and media
validation remain outside this increment. Martin supplied direction; Codex
implemented and tested the correction.

Next: one independently produced EVAL-001 client with identity/context/tools,
attempts, timing and available cost; Martin's two-tab reading/keyboard review.
Do not infer a candidate/model score from controlled calibration artifacts.

## Publication

The task explicitly authorizes a normal push to `origin/main`. The development
commit must contain its real English title and substantive multiline body.
At closure, run fetch/merge/status/diff/push/remote verification and compare local
HEAD with remote main. This pre-publication record does not claim the pending
commit is already published; the final report provides the verified SHA and URL.
The named pre-sync stash remains as a recovery snapshot of this iteration.
