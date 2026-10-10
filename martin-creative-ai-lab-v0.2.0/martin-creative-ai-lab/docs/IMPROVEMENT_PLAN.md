# Improvement plan

Updated: 2026-10-10. One primary workstream; no mandatory backlog expansion.

| Priority | Problem / evidence | Value | Scope, dependencies, acceptance |
|---|---|---|---|
| 1 — selected | P11 has no broadcast or receive/render implementation in its preserved three-file snapshot | Close a real interaction gap and produce a reproducible technical portfolio sample | Node + Express + Socket.IO; system Chromium for browser checks. One local room, text only. Two clients must receive each accepted message once, invalid input must not broadcast, text must remain literal, disconnection must be visible, and reconnection must not replay missed or offline submissions |
| 2 — deferred | P10 has combat vectors and dialogue scenarios but no working destination project | Executable rules or a coherent interactive scene | Select a source subset and formalize edge cases; compare expected transitions or combat outcomes. Independent workstream; do not start during P11 |
| 3 — blocked by missing source | P01/P03/P04/P05/P06 have historical direction without full baseline packages here; P07/P08 lack inspected masters | Higher creative value once a real source is chosen | Recover a bounded baseline or master, define adaptation criteria, then verify in its destination. Do not reconstruct missing content from inventory labels |

## P11 objective and boundaries

Adapt the preserved unidirectional exercise into a usable local chat. The
historical ZIP and its inventory stay unchanged. Implement in
`projects/realtime-integration-lab/`: server, browser UI, locked dependencies,
targeted protocol and browser tests, and a project README with provenance.
Update this assessment, state, significant decisions, P11's registry entry,
candidate transfer actions, seed summaries, evidence, and integrity manifest.

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

1. Reproduce the missing rendered message using the original source files in a
   temporary directory and the same browser delivery test used on the adaptation.
2. Verify protocol payload boundaries and rejection without broadcasts.
3. Exercise real browsers: both directions, no sender duplication, literal
   markup, errors, offline submission, reconnect, and bounded history.
4. Check a representative request against the documented `npm start` command.
5. Run the lab validator, record environment and artifact hashes, and refresh
   the manifest only after maintained content is final.

Learning may support TR-009 (P11 → P02) or TR-010 (P11 → P01), but both remain
candidates until adapted and verified in those destinations. No shared
component is justified by a single chat consumer.

## Completed increment

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

Next priority is Martin's local UI review, as recorded in [state](STATE.md).
Evaluation reuse stays deferred until candidate/reference isolation is defined.
