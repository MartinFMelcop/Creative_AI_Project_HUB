# Lab state

**Updated:** 2026-10-11 (client date; America/Sao_Paulo). **Seed version:** 0.4.6, unchanged.
**Current increment:** P11 local chat 0.1.4, activity-aware unread feedback.
P10 dialogue 0.1.1, P02 runner 0.2.0 and starter contract 0.1.0 stay unchanged.

The checkout began clean at published
`d498f08e20e4c59140771ed0ab502e5a099f110c`; fetch/merge confirmed the same main.
[The previous CI run](https://github.com/MartinFMelcop/Creative_AI_Project_HUB/actions/runs/38106979790)
passed both hosted jobs. The working chat still clears incoming unread state at
its live edge when the page lacks focus. Select this user-visible correction
within the existing prototype, without inventing human or candidate review.

[P11](../projects/realtime-integration-lab/README.md) now counts an arrival when
its page is hidden, lacks focus or is reading earlier text. The tab title and
Jump to latest show the same count, capped at 200 retained arrivals. Returning
to a visible, focused page clears the count only within 24 pixels of the bottom;
returning to earlier text preserves the count and reading anchor. Hidden scroll
events cannot mark messages read. Jump to latest keeps its existing keyboard
focus destination and restores the title. Near-bottom following, transport,
no-replay behavior and retained-history limits remain in place. ADR-020 records
this page-local activity policy; the dependency graph is unchanged.

[Activity evidence](../evidence/realtime-chat/ACTIVITY_RUN.json) records the
published client identity, source/test hashes, environment and actual commands.
Four new checks fail on committed 0.1.3 and pass on 0.1.4; all 30 current chat
checks and 23 evaluator regressions pass. Three activity checks use real Chromium
tab focus after disabling Playwright's forced-focus override. Headless tabs stay
visible, so the fourth explicitly controls the Page Visibility API boundary.
The fixed P02 baseline/reference calibration remains 15/17 rejection and 17/17
acceptance. P02's evaluator snapshot, nine-file starter and 17-check task are
unchanged. Final registry/link/archive and manifest verification runs at closure.
P10 and validator regression suites were not rerun locally; hosted CI checks them.

P11 remains bounded local-chat M4. No notification permission, persistence,
identity, extra package, shared library or deployment is added. Earlier evidence,
archives and source inventory remain unchanged. Local execution uses Linux,
Node 24.19.0 and system Chromium 154; the visibility probe does not establish
real minimized-window behavior. Human/assistive-technology review, other browsers,
resize/zoom behavior, independent candidate provenance and engine migration
remain unverified. Martin supplied direction; Codex implemented/tested.

This record precedes publication. The final report supplies the matching remote
main SHA and actual hosted-run result; the previous CI record remains historical.
Next: Martin reviews inactive-page title/count feedback and keyboard reading;
reader feedback on P10 and one independent EVAL-001 submission remain separate
valuable gates.
