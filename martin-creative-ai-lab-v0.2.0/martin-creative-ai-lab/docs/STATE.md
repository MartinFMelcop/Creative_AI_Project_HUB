# Lab state

**Updated:** 2026-10-10 (client date). **Seed version:** 0.4.5, unchanged.
**Current increment:** P02 runner 0.2.0, committed evaluator snapshots.
P11 stays 0.1.3; EVAL-001 starter stays 0.1.0; bounded maturity remains M4.

The checkout began clean at published `de1fd1a6c0729d8b1f2b3a7ba6a87ab2aeaaf49d`.
Fetch/merge confirmed remote main matched. Previous commits, sources, evidence and
recovery stash remain preserved. The former checker compared and executed P11's
working files, requiring another runtime pin after ordinary app updates.

The checker now materializes its existing evaluator allowlist from commit
`911bf789e31dc2b1df9586a894e37312375771f3` in each temporary runtime. Installed
evaluator-owned modules are linked only if dependency locks match; only app
version metadata is ignored. Missing modules, malformed locks or dependency
changes are inconclusive. No automatic installation, new dependency, candidate
contract change or P11 app edit is introduced. Syntax attribution and timeout
cleanup remain intact. ADR-016 records the decision and boundaries.

[Snapshot evidence](../evidence/evaluation-task/SNAPSHOT_RUN.json) captures source,
artifact/export hashes, commands, environment and results. All 22 runner tests
pass. Three new methods produce three expected failures on the old runner.
Controlled working-project copies change server, page, browser tests and package
version; the old runner refuses execution, while the new runner executes pinned
sources and retains baseline rejection at 15/17 and reference acceptance at
17/17. All nine exported files remain byte-identical. These are controlled
artifacts, not independent candidate/model attempts. Documentary validation
passes 112 local links; the final manifest verifies 61 entries.

The Linux cloud environment executes actual Node/Chromium checks with approved
localhost permissions. Lock compatibility is checked; installed module bytes
are not independently verified. POSIX symlinks are tested; Windows privileges
and other platforms remain unverified. Process cleanup is not a sandbox. The
unchanged P11 reading suite was not rerun; prior evidence remains historical.

Next: one independent EVAL-001 client with context/tool/attempt provenance and
Martin's two-tab reading/keyboard review. Martin supplied direction; Codex
implemented and tested. No new project maturity or human review is claimed.

Workflow 2.0 authorizes a normal push to main and requires a real message with a
72-character title and 1,200-character body maximum. At closure, verify the actual
stored message, synchronize, push and compare remote main with local HEAD. The
final report supplies the verified SHA/URL; this record precedes publication.
