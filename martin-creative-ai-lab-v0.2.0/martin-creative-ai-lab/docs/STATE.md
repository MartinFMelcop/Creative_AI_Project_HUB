# Lab state

**Updated:** 2026-10-14 (UTC). **Seed:** 0.25.0.
**Current milestone:** P11 Project Rooms 0.5.0 — complete-record retrieval.

[Run Project Rooms](../projects/realtime-integration-lab/README.md) and open
Search record. Literal Unicode case/accent-insensitive words find every saved
note/decision and historical action title/update. Twenty-match snapshot pages
remain stable during new writes; refresh is explicit. Context distinguishes the
matched revision, nearby records, original decision and current linked work.
Return to the matching control or board without replacing either draft.

[Execution](../evidence/realtime-chat/SEARCH_RUN.json): actual 0.4.0 and 0.5.0
servers receive identical fictional records. The old search endpoint returns
404; the new one finds a revision-2 blocker, its decision and the revision-63
completed action, all beyond recent panels. The complete suite passes 81 tests;
real Chromium covers desktop/mobile, keyboard return, pages, drafts and delayed
responses. A bounded local 10,000-entry/10,000-event sample preserves export data.
SQLite schema 2, backup format 1, dependencies, legacy/P02 sources and other
products remain intact. No private live database is shipped.

Started clean on `work` at `d56c971`, matching fetched main; transport works and
main publication is explicitly authorized. Compared actual P11 limits with P04's
complete edition and completed P01/P03/P05/P06/P10 milestones. Retrieval closes a
measurable workflow gap; more nearby game/media or prose expansion needs stronger
external experience evidence. Node/SQLite fit the existing service and bounded
immutable records; no engine rewrite or search service is warranted.

Technical checks are verified; UI judgment is Codex's assessment. Fictional
fixtures are not team feedback. Public accounts/privacy, concurrent production
load, independent usability/retention and commercial demand remain unverified.
Next compare real handoff retrieval with independent P04/P10 reading, musical
practice and native strategy/combat use before selecting another workstream.
