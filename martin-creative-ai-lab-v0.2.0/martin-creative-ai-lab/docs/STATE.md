# Lab state

**Updated:** 2026-10-10. **Seed version:** 0.3.1.
**Primary workstream:** P11 local text chat, correction 0.1.1 completed and
locally verified. The containing directory retains its v0.2.0 package name.

## What changed

The checkout began clean at `66041e7fdd7687ee21099f95129dff41933c74dd`, with
P11 0.1.0 committed. Inspection and two new browser checks found a connected form
submission discarded behind an in-flight polling write, plus a heartbeat race
that retained a packet for reconnect replay. [P11 0.1.1](../projects/realtime-integration-lab/README.md)
uses ordinary acknowledged emission for the live transport queue and immediately
clears Socket.IO's separate reconnect queue. The offline guard, draft handling,
timeout feedback, text-only rendering, validation, and retention bound remain.

Changes are limited to the client send path, browser regression harness, working
version metadata, and continuity/evidence. Dependency resolutions, event contract,
server, historical ZIP, legacy inventory, and original 0.1.0 run record are unchanged.
The new correction remains uncommitted in this working tree.

## Verification and evidence

[Current run](../evidence/realtime-chat/POLLING_SEND_RUN.json) records environment,
inputs, baseline source identity, injected boundaries, and working artifact hashes.

- Two regressions fail on the recorded 0.1.0 client: missing polling submission
  and an unexpected reconnect-buffer entry. The harness serves the old client
  through a browser route without overwriting working or historical files.
- The same two checks pass on 0.1.1. The full `npm test` suite passes 17 tests
  (6 protocol, 11 Chromium), with zero failures, skips, or uncaught page errors.
- Frozen `npm ci` passes (97 packages). Parsed lockfile comparison confirms only
  root project version metadata changed; resolved dependencies are identical.
- The documentary validator passed: 11 projects, 11 transfers, 0 assets,
  2 legacy sources, and 66 maintained local links. All 3 existing validator
  regression checks passed. The final manifest is refreshed and verified at
  closure; documentary outcomes are recorded in the execution evidence.

The polling regression uses actual HTTP writes. The heartbeat regression forces
expiry at the pinned Socket.IO predicate, restores it immediately, then verifies
no replay through a real reconnect. This is controlled fault injection, not a
real elapsed-time/network-loss study. CLI startup is unchanged and was not rerun;
its prior smoke and 15-test result remain [0.1.0 evidence](../evidence/realtime-chat/RUN.json).

Environment: Linux cloud container, Node 24.19.0, npm 11.9.0, Python 3.12.14,
Chromium 154.0.8037.57, Playwright Core 1.64.0, Socket.IO 4.8.4. Browser tests
start and close their own local servers. The recorded machine capabilities do
not establish installation on Martin's machine.

## Limits and learning

P11 stays M4 for its local slice. No persistence, automatic retry, identity,
public hosting, cross-browser study, model benchmark, game runtime, media master,
formal accessibility audit, or human usability review was added. Uncertain
delivery still requires judgement before manual resend; duplicates remain possible.

[The delivery lesson](../knowledge/realtime-delivery.md) now distinguishes live
congestion from reconnect buffering. P02/P01 applications remain candidate
transfers without a verified destination consumer; no shared component was promoted.
Other projects' evidence boundaries remain unchanged. The archive is still a
selected textual recovery, not a complete backup or proof of available art/audio.

Martin provided the portfolio request and project context. Codex selected,
implemented, tested, and documented this correction. Martin is not credited with
manual review or testing, and no remote publication was performed in this session.

## Next concrete action

Review the local P11 interaction with Martin: keyboard input, message readability,
connection feedback, and uncertain-delivery wording. The next possible technical
increment is a bounded P02 task using one reproduced defect, with explicit
candidate/reference isolation and acceptance criteria before any candidate run.
That independent preparation does not require inventing human feedback. P01
still needs its own baseline; P10 remains a source reservoir rather than an
active parallel project.
