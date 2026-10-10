# Improvement plan

Updated: 2026-10-10. One primary workstream; no mandatory backlog expansion.

## Current iteration — P02 chat send-buffering task

**Priority:** 1 — completed and locally calibrated. P11 0.1.1 is published;
P02 began this iteration with only templates.
Use its reproduced 0.1.0 transport defects as one bounded repair task. This adds
an executable evaluation workflow without a new application, engine, or model
dependency. P11's working implementation remains unchanged.

**Scope:** `evaluations/chat-send-buffering/`: candidate brief, allowlisted export
from commit `66041e7`, evaluator-owned artifact runner, and runner regressions.
Use existing P11 locked dependencies, server, and 17 protocol/Chromium checks.
Update maintained continuity, P02/TR-009 records, provenance, and final hashes.

**Acceptance:** export a fresh workspace without Git history, reference client,
tests, knowledge, or prior evidence; preserve starter/support files; distinguish
rejected artifacts from unavailable or incomplete execution; record artifact,
test-suite and environment identity. Calibrate the baseline at two known failures
and the corrected artifact at 17 passes. Verify scope violations and incomplete
result handling. Public-source separation is not secrecy or a security sandbox.

**Dependencies:** Python 3.9+, retained Git objects, Node 22+, installed P11
dependencies and system Chromium. No credentials, model calls, Unity, or media
masters are required. No candidate model is evaluated or scored in this iteration.

**Next gate:** an independently produced client with known context/tool identity,
separate candidate execution, and recorded attempts; Martin's P11 UI review remains
independent. Existing P11 completion notes below are historical, not active work.

## Prior completed work and constrained alternatives

| Priority | Problem / evidence | Value | Scope, dependencies, acceptance |
|---|---|---|---|
| 1 — completed | P11 0.1.0 drops a connected form submission while a polling write is busy; a stale connected state can also retain a reconnect packet. Both fail current targeted browser checks | Correct the existing sample's send semantics without expanding product scope | Existing Node/Socket.IO/Chromium stack. The form submission must reach both browsers once after a real polling write drains; a simulated expired heartbeat must leave no reconnect packet, preserve the draft, and never replay the failed attempt |
| 2 — deferred | P10 has combat vectors and dialogue scenarios but no working destination project | Executable rules or a coherent interactive scene | Select a source subset and formalize edge cases; compare expected transitions or combat outcomes. Independent workstream; do not start during P11 |
| 3 — blocked by missing source | P01/P03/P04/P05/P06 have historical direction without full baseline packages here; P07/P08 lack inspected masters | Higher creative value once a real source is chosen | Recover a bounded baseline or master, define adaptation criteria, then verify in its destination. Do not reconstruct missing content from inventory labels |

## Completed P11 objective and boundaries

Continue the already implemented chat in `projects/realtime-integration-lab/`.
The prior correction was 0.1.1: correct connected-send buffering in `public/client.js`
and extend `tests/browser.test.cjs`. Update version metadata, provenance/usage,
assessment, state, significant decisions, P11's registry entry, candidate lessons,
seed summaries, execution evidence, and the integrity manifest. The historical
ZIP, its inventory, and the original 0.1.0 execution record remain unchanged.

Use one broadcast path including the sender; do not append optimistically.
Accept trimmed string payloads with 1–500 UTF-16 code units. Reject wrong types,
whitespace-only strings, and oversized strings with explicit acknowledgement.
Render using text nodes. Show connection and rejection status. Disable sending
while disconnected; do not queue or replay offline messages. Preserve a draft
on explicit rejection. Messages are ephemeral, and a joining/rejoining client
receives only future events. Bound each browser's retained list to 200 messages.

Exclude identity, authentication, rooms, persistence, public deployment, and
guaranteed delivery across outages. Do not claim exactly-once distributed
delivery: the gate is one visible item per accepted broadcast while connected.

## Verification and completion

1. Reproduce both defects on the committed 0.1.0 client at `66041e7`; execute
   the same tests on 0.1.1. The polling case uses actual HTTP writes; the
   heartbeat boundary is an explicit controlled fault, not a packet-loss study.
2. Preserve the existing payload, literal-text, sender, retention, reconnect,
   acknowledgement, and draft checks. No skipped browser tests count as readiness.
3. Make the baseline reproducible by serving its recorded client through the
   browser test harness, without replacing repository or historical source files.
4. Run the documented full suite and the lab's documentary check. Check frozen
   installation after version metadata changes; no dependency upgrade is needed.
5. Record current artifact hashes and refresh the manifest after maintained
   content is final. Human review remains a separate outstanding action.

TR-009 is now adapted and calibrated in P02. TR-010 (P11 → P01) remains
a candidate until adapted and verified in that destination. No shared
component is justified by a single chat consumer.

## Previous completed increment — 0.1.0

P11 0.1.0 is implemented and locally validated: the original browser delivery
check failed as expected, and 15 adaptation tests passed (6 protocol, 9 Chromium).
The documented CLI startup served a page and broadcast to two clients. Frozen
reinstallation passed. See [the execution record](../evidence/realtime-chat/RUN.json).

The first dependency installation exposed an auxiliary defect in the lab
validator: it traversed upstream `node_modules` Markdown and reported 30 unrelated
errors. It now prunes dependency/Git folders; 3 regression tests confirm that
working-project broken links and archive corruption still fail. This directly
supports developing P11 without weakening the maintained-document check.
The manifest's two absent-file references are replaced from actual maintained
files at closure. No second primary workstream was started.

The previous planned next step was Martin's local UI review. That remains
pending; it does not block the newly reproduced transport correction. Evaluation
reuse stays deferred until candidate/reference isolation is defined. No second
primary workstream is activated.

## Completed correction — 0.1.1

Two targeted tests fail on the committed 0.1.0 client and pass on 0.1.1.
The full working suite completes 17 tests with no failures or skips; dependencies
are unchanged and frozen installation passes. [Current evidence](../evidence/realtime-chat/POLLING_SEND_RUN.json)
records the baseline client hash, regression inputs, injected boundary, and
working artifact hashes. No new engine, feature workstream, or shared component
was introduced. Human UI review is still pending; the P02 export/checker is now implemented
and calibrated. Its bounded TR-009 adaptation is verified, without model evaluation.

## Completed P02 increment — 0.1.0

Nine files exported from the recorded starter/brief/manifest, eight runner checks
passed, baseline rejected at 15/17 and corrected artifact accepted at 17/17.
Missing-browser probe returned inconclusive; starter frozen installation and CLI
server smoke passed. [Calibration](../evidence/evaluation-task/CALIBRATION.json)
records exact sources and complete evaluator output. No new shared abstraction,
model candidate, score or app was introduced. Next priority is one independently
produced client with explicit context and tools, rather than more task inventory.
