# Lab state

**Updated:** 2026-10-11 (environment UTC date). **Seed version:** 0.4.6, unchanged.
**Current increment:** P11 local chat 0.1.5, viewport reading-position correction.
P10 dialogue 0.1.1, P02 runner 0.2.0 and starter contract 0.1.0 stay unchanged.

The checkout began clean at published
`615fd7bef60d497a7b4d574b0ef391870fc3c945`; fetch/merge confirmed the same main.
[The previous hosted run](https://github.com/MartinFMelcop/Creative_AI_Project_HUB/actions/runs/38107882219)
passed both jobs. Current tests covered arrivals and activity but left resizing
unverified. Real viewport changes reproduce live-edge loss and earlier-message
reflow displacement, making this the selected user-visible correction.

[P11](../projects/realtime-integration-lab/README.md) remembers live-following
intent or the first visible message and pixel offset before layout changes.
ResizeObserver restores it when the conversation's width or height changes;
reflow-generated scroll events cannot overwrite that saved anchor. Broadcasts
reconcile a pending resize before appending, and reuse the same restoration
logic for retention eviction. Live readers stay at the bottom; earlier readers
keep their message and offset where the scroll range permits. Inactive unread
counts survive resizing; clearing still requires an active page near the bottom.
ADR-021 records this choice. The dependency graph is unchanged.

[Resize evidence](../evidence/realtime-chat/RESIZE_RUN.json) records actual
commands, environment, committed-baseline identity and artifact hashes. Three
new checks fail on committed 0.1.4 and pass on 0.1.5. All 33 current chat checks
(6 protocol, 27 Chromium) and 23 evaluator regressions pass locally. Real height
changes and desktop/narrow wrapping include subsequent retention eviction and
native tab focus. Historical execution JSON and the source archive are unchanged.
Registry/link/archive validation passes with 138 local file links. The manifest
is regenerated and verified at closure.

P02 still materializes its committed evaluator snapshot; no task repinning or
extra task requirement follows from working-client UI changes. Its controlled
15/17 baseline rejection and 17/17 reference acceptance, plus unchanged dialogue
and validator regressions, run in shared hosted CI after publication. They were
not rerun locally in this iteration. P11 remains bounded local-chat M4.

This preserves a message and CSS-pixel offset, not the same word after wrapping.
Browser zoom, font-only reflow, other browsers, real minimized-window behavior,
human/assistive-technology review and independent candidate provenance remain
unverified. No deployment or shared component is introduced. Martin supplied
direction; Codex implemented/tested.

This record precedes publication. The final report supplies the matching remote
main SHA and actual hosted result. Next: Martin reviews resizing, unread feedback
and keyboard reading; P10 reader feedback and an independent EVAL-001 submission
remain separate valuable gates.
