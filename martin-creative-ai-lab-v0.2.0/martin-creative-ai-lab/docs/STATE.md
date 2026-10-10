# Lab state

**Updated:** 2026-10-10. **Seed version:** 0.3.0.
**Primary workstream:** P11 local text chat, increment 0.1.0 completed and
automatically validated. Working directory names retain their v0.2.0 package
origin; no historical source archive was rewritten.

## What changed

P11 moved from recovered source to an active working project in
[projects/realtime-integration-lab](../projects/realtime-integration-lab/README.md).
The preserved server received/logged messages but had no broadcast; its UI had
no receive/render path. The adaptation supplies both paths, input validation,
literal text rendering, visible connection/error state, draft preservation,
rejoin semantics, and a 200-item local retention bound. Pinned dependencies and
a lockfile replace the historical placeholder test workflow.

[Assessment](ASSESSMENT.md) and [improvement plan](IMPROVEMENT_PLAN.md) continue
the v0.2.0 recovery without activating the other ten seeds. The root README now
points to the nested lab and its working sample. ADR-008 records the selected
scope; [knowledge](../knowledge/realtime-delivery.md) records candidate learning.

## Verification

See [execution evidence and artifact hashes](../evidence/realtime-chat/RUN.json).

- Original P11 files: archive and three individual SHA-256 checks passed.
  The current browser delivery test reproduced the defect: 1 test executed,
  1 expected failure; server logged receipt but the sender's list stayed empty.
- Working P11: `npm test` completed 15 tests, all passed (6 protocol, 9 Chromium).
  Checks include two-way display, no sender duplication, literal markup,
  rejected payloads and length boundaries, offline drafts, new/rejoining clients,
  automatic transport reconnect, bounded history, and delayed/lost acknowledgements.
- Frozen reinstall: `npm ci` passed with the saved lockfile (97 packages).
- CLI startup: `PORT=3123 npm start` served health, the page, the Socket.IO script,
  and one accepted broadcast to two clients. The temporary servers were stopped.
- Lab validation also exposed upstream dependency-document traversal; the
  validator now prunes `node_modules`. All 3 regression tests passed, including
  maintained-link and archive-corruption failures.
- The documentary validator passed: 11 projects, 11 transfers, 0 assets,
  2 legacy sources, and 62 maintained local links. The manifest is regenerated
  from actual maintained files and checked at closure; its inherited two
  absent-file entries are removed. Runtime and documentary outcomes are in the
  execution record. Reusable installation/startup instructions were tested and
  saved as an environment draft; saving did not publish or restart the environment.

Environment: Linux cloud container, Node 24.19.0, npm 11.9.0, Python 3.12.14,
system Chromium 154.0.8037.57, Playwright Core 1.64.0. Starting Git HEAD:
`951c21ec8565d9ac64ab8207f569bb2fe4f01c27`; changes remain in the working tree.
The environment is not evidence of installation or review on Martin's machine.

## Limits and attribution

Martin provided direction, source context, and authorization. Codex performed
this assessment, implementation, and automated verification. Martin has not
been credited with reviewing or testing the sample.

P11 is an ephemeral, local, single-room prototype. There is no persistence,
identity, public deployment, reliability guarantee across outages, cross-browser
study, human usability review, or formal accessibility audit. A lost acknowledgement
can follow successful delivery; manual resend can duplicate it. No game runtime,
Unity/RMXP integration, model benchmark, audio master, or image asset was validated.
The v0.2.0 combat/dialogue PASS reports remain historical evidence, not new runs.

The source archive still contains 175 Rave Master texts and 3 WebSocket files.
It is not a complete backup. All eleven transfer records remain candidates;
none has a verified destination consumer. No shared component was promoted.

## Next concrete action

Have Martin try P11 in two tabs and review message readability, keyboard use,
connection feedback, and uncertain-delivery wording. Capture that feedback
before choosing a public portfolio case. After that, select whether to adapt
the reproduced defect into P02; define evaluation/reference isolation before
running any candidate. P01 still requires recovery of its own baseline.
