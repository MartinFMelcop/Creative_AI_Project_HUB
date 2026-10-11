# Lab state

**Updated:** 2026-10-10 (client date). **Seed version:** 0.4.5.
**Current iteration:** P11 unread navigation, app 0.1.3.
P02 runner 0.1.3 retains syntax attribution; its runtime pin must be recalibrated
against the new P11 commit before combined publication. Starter contract 0.1.0.
The enclosing folder retains its original v0.2.0 package name.

## Change and starting state

The checkout began clean on `work` at published
`e322e3527d8516bdbb1e08bc47d5e945be74cd37`. Fetch and merge confirmed the remote
main was current. Prior syntax attribution, reading anchors, source archive,
registry-reference validation and recovery stash remain preserved.

The inspected chat preserves earlier reading position but gives no arrival count
or direct return to live messages. P11 0.1.3 adds one native button outside the
list. New arrivals while browsing increment a count capped at 200; normal live
following keeps it hidden. Manual scrolling within 24 pixels of the bottom
clears the count. Enter/Space activation scrolls to live text and transfers focus
to the keyboard-focusable conversation before hiding the button. Existing
anchoring, fractional correction, payload, send and outage rules remain intact.
No identity, persistence, extra live region, new dependency or shared framework.

## Executed verification

[Unread execution record](../evidence/realtime-chat/UNREAD_RUN.json) identifies
source commit, baseline/client/runtime hashes, environment and captured commands.
All 26 `npm test` checks pass without skips: 6 protocol and 20 Chromium checks.
The nine reading checks include four new count/reset/keyboard/retention methods.
Enter and Space run at 390x844; other reading geometry runs at 1280x800.
One targeted check on the recorded 0.1.2 client fails as expected: no new-arrival
control becomes visible. This is a controlled old-client route with current
markup, not an independent candidate or complete old-app execution.

The app's trusted markup/style/package bytes change. P02 correctly requires a
fresh suite pin and controlled 15/17 baseline, 17/17 reference calibration after
the P11 commit. That integration remains pending in this first development
commit and must be completed before either commit is pushed.

Environment: Linux cloud container, Python 3.12.14, Node 24.19.0, retained locked
dependencies and system Chromium. Real localhost servers and headless browser
execution use approved permissions. Documentary and manifest checks run after
final content; they do not validate behavior.

## Limits and next action

Counts cover arrivals available in the retained local window, not per-user read
receipts. Removed history is not recoverable. Human/assistive-technology review,
other browsers, hosted service and independent model evaluation remain pending.
Martin supplied direction; Codex implemented and tested this increment.

Next in this iteration: commit tested P11, recalibrate P02, commit its new pin and
publish both verified commits. Next product gate: Martin's two-tab reading and
keyboard review; one independently produced EVAL-001 client with context/tool/
attempt provenance. Project maturity remains M4 for the existing bounded slices.

## Publication

This task explicitly authorizes a normal push to `origin/main`. Publication is
pending here; the final report must compare the local and remote SHAs and report
both actual descriptive commit messages. Never publish the incompatible interim
state or rewrite existing history. Prior publication at `e322e35` is verified.
