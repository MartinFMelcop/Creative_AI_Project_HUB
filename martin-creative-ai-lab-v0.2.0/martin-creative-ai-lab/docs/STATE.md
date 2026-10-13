# Lab state

**Updated:** 2026-10-13 (UTC). **Seed:** 0.19.0.
**Current milestone:** P11 Project Rooms 0.4.0.

[Run Project Rooms](../projects/realtime-integration-lab/README.md). The former
conversation/decision workspace now carries decisions into assigned actions,
progress, blockers, completion and reopening with a new reason. Sources remain
immutable; every change records its author/revision. Separate views, owner filters,
history and complete export make the handoff inspectable.

SQLite commits each revision and event atomically. Stale edits keep their draft
and require explicit comparison/reapplication. Immutable attempts and receipts
recover uncertain committed/uncommitted sends without duplication or reverting
newer work. Offline changes require explicit saves. Updates preserve the current
reading view; drafts are scoped to participant/room and protected from replacement.

Schema 2 upgrades schema 1 transactionally; failed upgrades roll back. Backup
format 1 inspects/restores both database versions, including audit/attempt state.
An actual 0.3.0 savepoint was restored and migrated with identity/records intact.
Keep an old savepoint before upgrade; older applications cannot open schema 2.

[Execution](../evidence/realtime-chat/ACTIONS_RUN.json): full P11 suite 73 passes;
final 13 workflow checks pass after reopening/late-script review. Two Chromium
contexts exercise the complete handoff; declared fixtures cover lost confirmation,
newer peer writes, restore, corruption and failed migration. Desktop/narrow frames
reviewed by Codex. These are synthetic tests, not independent collaborator approval.

Started clean at `3cac6b9`, matching fetched main. Compared actual P01 one-step
rivals, P04 prose/feedback and completed native/game/music work. P11's missing
execution handoff offered a concrete product workflow. Retain Node/SQLite/Socket.IO;
dependency graph, legacy protocol, P02 snapshot, other projects/media and archive
remain preserved. GitHub main is authorized; no service hosting deployment.

Trusted local prototype: all participants can open/edit rooms; chosen names and
ownership are not verified accounts/permissions. Outcomes are recorded text,
not artifact certification. Browser storage is separate from backups. Independent
team usability, large workspace performance, public accounts and market demand
remain unverified. Next compare real handoff needs with P01 rival strategy, P10
dramatic progression and unassisted native/music/reader feedback.
