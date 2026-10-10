# Improvement plan

Updated: 2026-10-10. One primary workstream; no mandatory backlog expansion.

| Priority | Problem / evidence | Value | Scope, dependencies, acceptance |
|---|---|---|---|
| 1 — completed | P11 0.1.0 drops a connected form submission while a polling write is busy; a stale connected state can also retain a reconnect packet. Both fail current targeted browser checks | Correct the existing sample's send semantics without expanding product scope | Existing Node/Socket.IO/Chromium stack. The form submission must reach both browsers once after a real polling write drains; a simulated expired heartbeat must leave no reconnect packet, preserve the draft, and never replay the failed attempt |
| 2 — deferred | P10 has combat vectors and dialogue scenarios but no working destination project | Executable rules or a coherent interactive scene | Select a source subset and formalize edge cases; compare expected transitions or combat outcomes. Independent workstream; do not start during P11 |
| 3 — blocked by missing source | P01/P03/P04/P05/P06 have historical direction without full baseline packages here; P07/P08 lack inspected masters | Higher creative value once a real source is chosen | Recover a bounded baseline or master, define adaptation criteria, then verify in its destination. Do not reconstruct missing content from inventory labels |

## P11 objective and boundaries

Continue the already implemented chat in `projects/realtime-integration-lab/`.
The current increment is 0.1.1: correct connected-send buffering in `public/client.js`
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

Learning may support TR-009 (P11 → P02) or TR-010 (P11 → P01), but both remain
candidates until adapted and verified in those destinations. No shared
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
was introduced. Human UI review is still pending; defining P02 candidate/reference
isolation is the next possible coding increment, not a completed transfer.
