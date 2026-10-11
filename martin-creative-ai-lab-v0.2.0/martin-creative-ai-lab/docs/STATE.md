# Lab state

**Updated:** 2026-10-11 (environment UTC date).
**Seed version:** 0.4.6, unchanged. **Current increment:** P11 chat 0.1.6.

The checkout began clean on `work` at `3d2b271e7beb3fe43b7d0a0e2ce347e7cdfe35f7`.
GitHub inspection confirmed the same remote main before edits. Git fetch failed
because the configured proxy was unreachable; authorized publication uses the
connected GitHub integration with a non-force update and remote verification.
This record precedes publication; the final report gives the resulting SHA.

SEED.md remains byte-identical to the baseline at version 0.4.6. Automatic
approval review rejected its full-file upload because it contains existing
personal/professional material. This patch changes no seed direction or inventory;
its current-state summary still describes the prior increment. Use this state
and the project registry for the latest verified P11 version and next action.

[P11](../projects/realtime-integration-lab/README.md) now preserves live and
earlier reading after text-size/spacing changes inside an unchanged panel.
ResizeObserver watches retained items as well as the panel; eviction unobserves
removed items. Content-height tracking prevents reflow scroll events from
replacing the saved anchor. Existing restoration, fractional offsets, retention
fallback and inactive unread rules remain. No UI, protocol or dependency is added.

[Text-reflow evidence](../evidence/realtime-chat/TEXT_REFLOW_RUN.json) records
three new Chromium user-style regressions failing on committed 0.1.5 and passing
on 0.1.6. All 36 chat checks pass (6 protocol, 30 browser), including viewport
resizing, send behavior, retention, keyboard navigation and inactive unread state.
These controlled font-size/line/letter-spacing checks do not establish native
zoom, other browsers, assistive technology or human readability.

P02 runner 0.2.0 and starter 0.1.0 stay unchanged. All 23 runner regressions pass;
known calibration stays 15/17 rejected and 17/17 accepted. A separate controlled
working-client probe passes 17/17 against the same evaluator snapshot. Dependency
graph and starter hashes are unchanged. Corrected README wording distinguishes
the pinned 0.1.3 reference from the working client; no independent candidate or
model score is claimed. Eleven registry and eleven manifest regressions pass;
Final records/link/archive validation passes with 149 local links; the manifest
covers all 77 maintained files with matching hashes after these updates.

P10 dialogue 0.1.2, preserved sources and prior evidence remain unchanged. P10's
runtime suite was not rerun locally. Bounded M4 is unchanged; human usability,
creative/audience quality, adoption and commercial demand remain unverified.
Martin supplied direction and authorization; Codex implemented and tested.

Next: a human reads earlier/live text with enlarged/spaced styling and reviews
keyboard navigation, unread feedback and uncertain-delivery wording. P10 reader
comparison and independent EVAL-001 provenance remain separate pending gates;
no extra workstream or content expansion is scheduled by this correction.
