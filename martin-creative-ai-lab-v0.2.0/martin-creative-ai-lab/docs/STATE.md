# Lab state

**Updated:** 2026-10-11 (environment UTC date). **Seed version:** 0.4.6, unchanged.
**Current increment:** complete maintained-lab manifest coverage in shared CI.
P11 chat 0.1.5, P10 dialogue 0.1.1, P02 runner 0.2.0 and starter 0.1.0 stay unchanged.

The checkout began clean at published
`a57a7f75615babde69352a27d9a57a5cde809721`; fetch/merge confirmed the same main.
[The previous hosted run](https://github.com/MartinFMelcop/Creative_AI_Project_HUB/actions/runs/38108640021)
passed both jobs. A real manifest probe omitting `scene.py` still passes the old
CI hash command. This is a coverage defect in shared QA: listed hashes can match
while a maintained file receives no integrity check.

The new standard-library `tools/check_manifest.py` requires exactly the files
Git tracks plus nonignored untracked files under the nested lab, excluding the
manifest itself. It rejects omissions, stale entries, duplicate/malformed paths,
missing/linked files and byte mismatches. Tracked ignored files remain required;
normal ignored installation outputs stay outside the inventory. CI now runs this
gate and its 11 regressions. ADR-022 and the
[integrity contract](REGISTRY_VALIDATION.md) define scope and deletion handling.
The root workflow remains outside the nested manifest's coverage.

[Manifest evidence](../evidence/continuous-integration/MANIFEST_RUN.json) records
actual commands, input/source hashes and environment. The same omission probe
passes the old command, fails the new one, and its complete counterpart passes.
All 11 new real-Git fixture checks and 11 existing registry regressions pass.
Workflow lint passes. Documentary validation passes with 142 local file links.
Complete-manifest/hash verification runs after final continuity updates. Alternative probes preserve the
maintained manifest and source files. Historical execution records, source
archive, registries and all product implementations remain unchanged.

This is a shared QA correction, not a new product or maturity promotion. Git is
a required inventory source; missing inventory fails. Matching hashes establish
consistency with the maintained list, not authenticity or runtime behavior.
Escaped/newline filenames are unsupported. No dependency is added. Martin
supplied direction and authorization; Codex implemented/tested. Product runtime
regressions and fixed 15/17 baseline rejection / 17/17 reference acceptance run in
hosted CI; those unchanged suites were not rerun locally in this iteration.

This record precedes publication. The final report supplies the matching remote
main SHA and actual hosted result. Next: human review of P11 resizing/keyboard
reading, P10 dialogue/consequences and an independent EVAL-001 submission remain
separate valuable gates. No human review or model score is inferred from CI.
