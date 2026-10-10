# Lab state

**Updated:** 2026-10-10. **Seed version:** 0.4.1.
**Primary workstream:** P02 evaluator runner 0.1.1, timeout diagnostics and cleanup.
EVAL-001's starter contract remains 0.1.0; P11 remains 0.1.1. The enclosing
directory retains its original v0.2.0 package name.

## What changed

The checkout began clean on `work` at published commit
`e1850d0f0a78211a02784bf5c7ff568fe2433b4e`; remote `main` matched. The earlier P02
increment is committed and published, superseding the prior uncommitted statement.
Both P11 development commits and the root `AGENTS.md` remain preserved.

Two actual probes found that P02 0.1.0 omits timed-command attempts/partial output
from records and leaves an inherited child running after parent timeout. The old
runner returned promptly on Python 3.12 POSIX; a delayed pipe-wait hypothesis was
not reproduced. [The runner](../evaluations/chat-send-buffering/README.md) now
records attempted command, real exit/launch state, elapsed time, deadline,
timeout, capture completeness, stdout and stderr. Timeouts at every gate are
inconclusive, including a late otherwise-passing summary.

Each command uses a private process group on POSIX. Timeout requests termination,
then forced shutdown if necessary, with bounded output draining. An escaped child
holding pipes marks capture incomplete instead of keeping the checker waiting.
This controls inherited groups, not all detached descendants or untrusted code.

Runner version and starter-contract version are separate. All nine exported
files remain byte-identical to 0.1.0, and old exports are accepted as submissions.
No app, dependency, chat test, candidate brief, model call, or shared framework
changed. P11 implementation, historical ZIP/inventory, and earlier evidence are
unchanged. This correction remains local and uncommitted; no publication occurred.

## Verification and evidence

[Current timeout record](../evidence/evaluation-task/TIMEOUT_RUN.json) identifies
the old source, current hashes, real command probes, injected boundaries and
full artifact-check output. [Original calibration](../evidence/evaluation-task/CALIBRATION.json)
remains historical evidence, unchanged.

- Current 15 runner tests pass, no skips. The recorded 0.1.0 runner fails all
  seven new test methods; the original eight methods continue to pass. Failure
  events include subtests and exceptions, separately recorded.
- Real command tests cover both streams, partial timeout diagnostics, nonzero
  exit, forced inherited-child termination, escaped-pipe capture, and launch failure.
- Gate injection substitutes real short-lived Python commands at syntax/startup/
  behavior boundaries; this is controlled fault injection, not three browser outages.
- Exact old exports remain compatible. Recalibration rejects the old client at
  15/17 and accepts P11's existing correction at 17/17 (6 protocol, 11 Chromium).
  These are controlled artifacts, not independent model candidates.
- Documentary validator passes: 11 projects, 11 transfers, 0 assets, 2 legacy
  sources and 90 local links. All three validator regressions pass; preserved
  sources/commits and `git diff --check` pass. Final manifest verification is
  recorded at closure after content is final.

Environment: Linux cloud container, Python 3.12.14, Node 24.19.0, npm 11.9.0,
Chromium 154.0.8037.57, Playwright Core 1.64.0, Socket.IO 4.8.4. POSIX/Linux
process-group behavior was executed; the non-POSIX direct-process fallback was not.
No new package or credential is required. Prior installation/CLI starter smoke
belongs to 0.1.0 evidence and was not repeated for this source-preserving correction.

## Limits, learning and next action

Process cleanup is not a sandbox. Children that create another group/session can
escape it; the detached fixture is stopped separately by its owning test. Public
source remains discoverable. There is no model identity, score, independent
candidate, human usability review, Unity/game runtime, or recovered media master.
The heartbeat check remains an injected pinned predicate; polling uses real HTTP.

TR-009 remains validated only for P02 task adaptation/calibration. Timeout-record
handling is a candidate lesson for other projects until a destination verifies it;
no new shared component or transfer record is promoted. Martin supplied direction;
Codex diagnosed, corrected and verified this increment.

Next: one independently produced EVAL-001 client with a separate context, explicit
source/tool policy, identity, attempts, timing and available cost. Preserve artifact
and raw evaluator result before performance claims. Martin's P11 UI review remains
pending. Review the current diff and commit text; publishing this correction needs
explicit authorization in its publication task.
