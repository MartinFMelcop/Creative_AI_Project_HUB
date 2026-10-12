# Lab state

**Updated:** 2026-10-12 (UTC). **Seed:** 0.10.0.
**Current milestone:** P11 Project Rooms 0.2.0.

[Run Project Rooms](../projects/realtime-integration-lab/README.md) with Node 24
and `npm run rooms`, then open `/studio/`. Choose a remembered local participant,
create/share a project, exchange saved notes, record decisions, switch rooms with
drafts intact and export the complete record. SQLite commits before broadcast;
rejoining recovers missed entries. A fixed attempt ID permits explicit retry of
uncertain sends without another insert. Earlier attempts and newer typing survive
reload separately. The original ephemeral exercise and its protocol remain at `/`.

[Execution](../evidence/realtime-chat/ROOMS_RUN.json) covers six SQLite/API/socket
and eight Chromium workflow checks, plus 38 retained legacy checks. Actual database
reopening and server restart, disconnect recovery, lost acknowledgement with/without
commit, rejection, shared URLs, pagination/download and narrow UI were exercised.
CLI startup outside the project serves both modes; the new startup creates a real
ignored SQLite file. Source and desktop/narrow review are by the implementer.

This trusted local workspace has chosen display names, not verified accounts.
All participants may open every project. Browser storage keeps bearer identity
and per-participant drafts; SQLite keeps hashed tokens and the record. No automatic
offline sending, public hosting, roles, cross-process delivery, full restore/import,
human usability, assistive technology or commercial demand is claimed. Export is
a complete consumable record; operational backup needs the stopped database.

Baseline `25d4588` was clean and matched main after fetch/merge. Portfolio review
compared native P06, P03 music, P01 economy and P11 service completeness. Persistent
collaboration removes a real limitation while P06 already has an executed trial
and the games need unassisted play/listening. No mandatory project rotation.
Node/Socket.IO preserve the useful transport; built-in SQLite adds relational
persistence without another dependency/service. No rewrite to another stack.

P02 retains its pinned snapshot and dependency graph; historical archives, P06,
P03/P08 and P10 remain unchanged. No Sites deployment. Martin supplied direction
and main publication authority; Codex implemented and reviewed. Final delivery
confirms the stored message, remote SHA and hosted checks.

Next compare P11 real collaborator workflow/account/backup needs, P06 human pacing
and integrated sound/art, P03 a distinct musical stage, and P01 a bounded economy
loop. Missing full P04 manuscript and independent P02 candidate context remain
separate constraints; do not substitute fabricated feedback or recovery.
