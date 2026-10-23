# P02 — Chat send-buffering practice task

**Task:** EVAL-001. **Runner version:** 0.2.1. **Starter contract:** 0.1.0. **Runtime:** Python orchestration and
Node/Socket.IO/Chromium behavior checks. This is P02's first working task, adapted
from P11; its earlier Unity proposal remains an origin, not a runtime requirement.

Repair one client send policy, covering polling congestion and stale-state
reconnect buffering. These are observed defects from P11 0.1.0, not invented
benchmark cases. [The candidate brief](BRIEF.md) states behavior without supplying
the correction. [P11](../../projects/realtime-integration-lab/README.md) retains
the application, locked dependencies, reference client, and evaluator-owned tests.

## Prepare and check

Requires Python 3.9+, Git with commits `66041e7` and `911bf78` retained, Node 22+,
P11's locked dependencies installed, and compatible system Chromium. Use P11's
documented `npm ci` command if needed. No Unity, model API, token, or new npm
dependency is required. Run from the lab directory:

```bash
python3 evaluations/chat-send-buffering/test_runner.py
python3 evaluations/chat-send-buffering/run.py prepare /tmp/p02-candidate
```

The destination must not exist. Move only that exported directory to a separate
candidate machine/context. It contains seven starter app files from commit
`66041e7fdd7687ee21099f95129dff41933c74dd`, the brief, and a hash manifest. It has
no `.git`, tests, working reference, knowledge, evidence, or project README.
The candidate may install dependencies there; change only `public/client.js`.

Return the workspace to the evaluator, then run outside the candidate context:

```bash
python3 evaluations/chat-send-buffering/run.py check /tmp/p02-candidate --result /tmp/p02-result.json
```

The result must be a new file outside the submission. Existing workspaces and
result records are never overwritten. Exit codes: `0` accepted artifact,
`1` rejected artifact, `2` inconclusive execution or command/input error. Command
errors before execution print the error without manufacturing a run result.

The checker verifies submitted support files against Git, materializes its server,
page, styles, package metadata and tests from pinned commit `911bf78` into a
temporary runtime, and copies only the submitted client bytes. It checks syntax,
probes real browser startup/dependencies and runs the pinned 17 P11 checks
(6 protocol, 11 browser). Ordinary working-project source changes cannot replace
those committed evaluator files.
Submitted `node_modules` is ignored, never imported by the evaluator. It removes
external URL/client override variables from the test environment. The submitted
client reaches both real browser pages through the existing test route; the
working application files are never replaced. Skipped, cancelled, missing,
incomplete, contradictory, or zero-test outcomes cannot be accepted. Changing
the evaluator commit still requires explicit recalibration.

The temporary runtime links to the evaluator-owned P11 `node_modules`. Its
working dependency lock must match the pinned graph; only top-level and root
package version metadata may differ. Preflight reports all direct runtime/dev
dependency versions and compares them with that committed lock. A mismatch,
missing version report, missing modules or invalid/changed lock is inconclusive
at the environment gate, before behavior tests. Records retain expected versions
and the actual report. No installation or network operation is automatic.
This verifies lock compatibility and direct version metadata, not installed
module bytes or transitive versions. POSIX symlink
execution is tested; a Windows symlink policy has not been verified.

Records contain the client hash, runner and evaluator hashes, source commits,
`evaluator_source: git_snapshot`,
tool/browser versions, attempted commands, captured output, test counts and failed
check names. Each command adds elapsed time, deadline, timeout/launch status,
real exit code and capture completeness. Timeout at syntax/startup/behavior gates
is inconclusive even if a late output contains a passing summary. Launch failure
keeps the attempt in the record; it does not reject the client as invalid syntax.
Only exit 1 with a complete SyntaxError diagnostic naming the temporary client
rejects at the syntax gate. Runtime option/preload failures, signals and unknown
nonzero outcomes are inconclusive; diagnostic changes fail conservatively.
See [syntax-gate evidence](../../evidence/evaluation-task/SYNTAX_RUN.json).

On POSIX, each command owns a new process group. Timeout sends SIGTERM, waits up
to one second, then SIGKILL if needed, with up to one further second for output
draining. An escaped pipe holder marks capture incomplete; closing pipes and a
bounded final reap avoid indefinite waiting. The non-POSIX fallback targets only
the direct process and has not been executed here. This is cleanup, not a sandbox:
children creating another session/group are outside the group policy.

Runner 0.2.1 leaves the starter contract at 0.1.0, preserving existing exports byte
for byte. `runner_version` identifies the correction separately from `task_version`.
No model identity or score is inferred from an artifact.

## Calibration and limits

The lab's `tools/check_calibration.py` uses two controlled artifacts: the exported
0.1.0 client and the committed 0.1.3 reference from `SUITE_COMMIT`. To check the
working P11 client separately, export a **second**
fresh directory, copy only P11's working `public/client.js` into it, and check it.
The baseline must reject with the polling and stale-state checks failing; the
reference must accept with all 17 passing. See [snapshot calibration](../../evidence/evaluation-task/SNAPSHOT_RUN.json), [prior unread runtime calibration](../../evidence/evaluation-task/UNREAD_CALIBRATION.json), [prior runtime recalibration](../../evidence/realtime-chat/READING_RUN.json), [prior timeout evidence](../../evidence/evaluation-task/TIMEOUT_RUN.json) and [original calibration](../../evidence/evaluation-task/CALIBRATION.json).

These probes validate the harness and TR-009's bounded P11 → P02 adaptation.
They are not independent candidate attempts, a model comparison, a score, or
evidence of AI performance. A separate [destination study](../../labs/ai-evaluation/README.md)
now records one independent-context artifact, its tools/attribution and available
timing/cost limits; calibration remains distinct from that candidate.

The same Codex session designed the harness and applied existing reference/tests.
Export separation reduces accidental context inclusion; it is not filesystem
isolation, a security sandbox, or secrecy. Public source/history exposes the
answer to anyone who seeks it. An independent study needs controlled execution
and context provenance; this public practice task cannot supply confidentiality.
Heartbeat expiry is injected at a pinned predicate; polling uses real HTTP writes.
Neither proves production outage reliability, human usability, or Unity behavior.

The [destination laboratory](../../labs/ai-evaluation/README.md) now owns the
independent-context artifact decision and its next objective. Keep raw artifact
acceptance separate from any claim about its author.

Runner 0.2.1 retains P11 commit `911bf789e31dc2b1df9586a894e37312375771f3`
without importing current app sources. Controlled changed-working-project checks
retain the 15/17 and 17/17 outcomes; all nine exports remain unchanged. The
original 17 task checks are byte-identical; P11's reading suites remain
outside EVAL-001. No current app or candidate contract change is required.

[Version-gate evidence](../../evidence/evaluation-task/DEPENDENCY_RUN.json)
records an isolated Socket.IO package-version declaration changed to
`0.0.0-controlled`, with code and lock unchanged. Runner 0.2.0 still accepted
the reference at 17/17; 0.2.1 stops before behavior with an inconclusive environment
result. All 25 runner regressions pass and normal calibration remains 15/17 and
17/17. This controlled metadata fault does not test another package release or
authenticate dependency code; it demonstrates the missing prerequisite guard.
