# P11 — Live exchange

**Project:** Real-time Integration Lab / WebSocket. **Version:** 0.1.7.
**Scope:** one local, ephemeral text conversation. This is a working adaptation
of the historical Socket.IO exercise, not a raw WebSocket implementation.

## Purpose and acceptance

Let two participants exchange text visibly through the browser. An accepted
message is broadcast to every currently connected client, including its sender.
The UI renders only the broadcast, avoiding a second optimistic sender copy.

| Contract | Check |
|---|---|
| Two clients display one item each, in both directions | Real-browser delivery test, also used to reproduce the historical defect |
| A connected form submission waits behind an in-flight polling write | Real polling transport congestion check; both pages show each message once |
| String payload, 1–500 UTF-16 code units before trimming; whitespace-only and wrong types rejected | Protocol boundary and rejection tests; browser error/draft check |
| Accepted text is trimmed and never parsed as HTML | Protocol normalization and browser markup test |
| Connection failure/disconnection is visible; sending is disabled offline | Browser leave/rejoin check; `connect_error` handler inspected |
| No offline buffering, missed-message replay, or automatic retry after acknowledgement timeout | Offline submission, rejoin, new client, and lost-acknowledgement browser tests |
| A stale connected state does not retain a packet for reconnect replay | Controlled heartbeat-expiry check followed by an actual transport reconnect |
| New typing is preserved when an earlier send is acknowledged | Controlled delayed-acknowledgement browser test |
| A timed-out earlier attempt stays available when current typing differs | Real acknowledgement timeout with controlled broadcast/drop outcomes; literal text and narrow-width checks |
| Only latest 200 messages retained per page | Browser retention test |
| Follow incoming messages only within 24 CSS pixels of the bottom | Real-browser geometry check |
| Browsing earlier text keeps the visible message and its pixel offset | Broadcast and variable-height retention checks |
| An evicted reading anchor shows the earliest retained text | Retained-history boundary check |
| Browsing readers see new arrivals and can return to live text by keyboard | Unread count, manual reset, Enter/Space and focus checks |
| Inactive pages retain unread arrivals and show a bounded count in the tab title | Native Chromium tab focus, controlled visibility, retained-window and return-to-live checks |
| Viewport resizing keeps live text at the bottom or preserves earlier reading | Height changes, desktop/narrow text reflow, subsequent eviction and inactive-tab checks |
| Text size/spacing changes inside an unchanged panel preserve reading | Controlled user-style enlargement/reset, retention eviction and native inactive-tab checks |

The event remains `chat message`. Client → server payload is a string; server →
client payload is its trimmed string. Acknowledgement is `{ "ok": true }` or
`{ "ok": false, "error": "…" }`. Receipt of an acknowledgement confirms server
acceptance, not delivery to every peer. UTF-16 counting follows JavaScript
`string.length`; an emoji may occupy two units.

Version 0.1.0 used volatile emission, which drops messages when the live
transport is temporarily busy, even while connected. Version 0.1.1 uses ordinary
acknowledged emission so Engine.IO can drain a pending polling write. Immediately
after emission it clears Socket.IO's distinct reconnect `sendBuffer`: a heartbeat
can expire before `socket.connected` becomes false. Clearing that reconnect queue
does not clear the live Engine.IO write queue. The policy remains no automatic
replay after a failed connection; it is not durable message delivery.

Version 0.1.2 keeps the reading position when new text arrives. Within 24 CSS
pixels of the bottom, the list follows live messages. Farther away, it preserves
the first visible message and its pixel offset, including when earlier messages
leave the 200-item window. If that visible message is evicted, the list stays at
the earliest retained text. Scroll to the bottom to resume following.

Version 0.1.3 shows a Jump to latest button when new messages arrive while you
read earlier text. Its count is bounded to the 200 retained arrivals. Activate
it with Enter or Space to return to live text; focus moves into the conversation
before the button disappears. Manual scrolling within 24 pixels of the bottom
also clears the count. The conversation is keyboard-focusable. No extra history
store or recovery of evicted text is introduced.

Version 0.1.4 also counts arrivals while the page is hidden or lacks focus,
including when the conversation is at the bottom. The tab title shows the same
bounded count as Jump to latest. Returning to a visible, focused page clears the
count only within 24 pixels of the bottom; returning to earlier text preserves
the count and reading anchor. Scrolling to live text or activating Jump to latest
restores the original title. Hidden scroll events do not mark messages read.
This is a page-local indicator; it does not request notifications or save history.

Version 0.1.5 restores reading position when the conversation's width or height
changes. Live readers stay at the bottom; earlier readers retain the same visible
message and CSS-pixel offset where the available scroll range permits. Record
that position before reflow, then restore it through ResizeObserver. Reflow's own
scroll events must not overwrite the saved anchor. Broadcasts also reconcile a
pending resize before appending text. Resizing clears unread state only under
the existing visible, focused, near-bottom rule. This preserves message position,
not the same word or line after wrapping.

Version 0.1.6 also restores reading after text reflows inside an unchanged panel.
The same ResizeObserver watches retained message items; eviction removes their
observations, keeping the set bounded to 200 items plus the panel. Remember
content height as well as panel dimensions so reflow scroll events and incoming
broadcasts cannot replace the earlier anchor. Controlled font-size, line-height
and letter-spacing changes keep live readers at the bottom and earlier readers
at their retained message/offset. Inactive unread counts keep the existing rule.
These are Chromium user-style checks, not native zoom or assistive-technology
validation; human readability and other browsers remain unverified.

Version 0.1.7 preserves the exact earlier attempt in the existing feedback area
if its acknowledgement times out after the input has changed. Current typing
stays untouched. Feedback distinguishes the two texts, keeps markup literal and
wraps long words without clipping. If the input is unchanged, the original
draft-kept feedback remains. No new control, persistent store, retry or protocol is added.

On transport interruption Socket.IO reconnects. Messages sent while away are
not recovered. Existing messages remain in that page's memory until reload or
retention eviction. Offline drafts require explicit submission after reconnect.
If an acknowledgement is lost, the UI reports uncertain delivery. Current typing
stays in the input; an earlier attempt displaced by edits remains in feedback
until another submission or reload. It is page-local recovery text, not saved
history or confirmation that a peer received the message. Check the conversation
before resending; manual retries can duplicate
an already delivered message. This prototype makes no distributed exactly-once
claim and has no persistence, identities, rooms, or production service contract.

## Run and test

From the actual Git root, `/workspace/Creative_AI_Project_HUB`:

```bash
cd martin-creative-ai-lab-v0.2.0/martin-creative-ai-lab/projects/realtime-integration-lab
npm ci --cache /workspace/.cache/creative-ai-npm --no-fund --no-audit
npm test
npm start
```

Node 22+ is required; `.node-version` records tested Node 24.19.0. Direct
dependencies are pinned and the lockfile captures transitive packages.
Express 4.22.3 and Socket.IO 4.8.4 preserve the original API family and satisfy
the source's historical semver ranges. Playwright Core 1.64.0 drives existing
system Chromium; it does not download a browser. The tests use headless Chromium
with `--no-sandbox` for this container. Outside this machine, set `CHROMIUM_PATH`
to a compatible browser executable. Missing Chromium is a failed prerequisite,
not a skipped browser suite. Protocol-only tests use `npm run test:protocol`; `npm run test:reading` runs
the nineteen reading/activity/reflow checks, and `npm run test:browser` includes both browser suites.

The server binds to `127.0.0.1:3000` by default; `HOST` and `PORT` can override
the bind address. Open that address in two local browser tabs. A remote cloud
browser preview is not provided. Stop with Ctrl+C. Startup is independent of
the current directory; static files resolve relative to the server module.
Tests start isolated servers on available ephemeral ports and close them.

For a basic startup check, `curl --fail http://127.0.0.1:3000/health` should
return `{"status":"ok"}`. Health alone does not validate the chat; the browser
suite exercises form submission, Socket.IO transport, and rendered results.

To reproduce the two 0.1.0 transport defects without replacing working files,
from this project directory:

```bash
git show 66041e7fdd7687ee21099f95129dff41933c74dd:martin-creative-ai-lab-v0.2.0/martin-creative-ai-lab/projects/realtime-integration-lab/public/client.js > /tmp/creative-ai-p11-0.1.0-client.js
CHAT_TEST_CLIENT_PATH=/tmp/creative-ai-p11-0.1.0-client.js node --test --test-name-pattern='in-flight polling write|stale connected state' tests/browser.test.cjs
```

That baseline check executes two tests and fails both as expected. The harness
serves only the recorded client revision through a browser route; the server and
all other assets are unchanged. With `CHAT_TEST_CLIENT_PATH` unset, the same
tests exercise the working client and pass. The heartbeat check explicitly
injects expiry at the pinned Socket.IO boundary; it is not a real packet-loss
or elapsed-time study. The polling check uses actual HTTP transport writes.

## Origin and differences

Source: `MartinFMelcop/WebSocket`, commit
`df651a9ddef39c7b05a48f25f1b7fdaff6760185`, inventory `LEGACY-002` in
[legacy_sources.json](../../registry/legacy_sources.json). Only its three files
were extracted to a temporary directory, after archive and file SHA-256 checks.
The historical ZIP and inventory are unchanged.

| Original file | SHA-256 |
|---|---|
| index.js | `4002c77a6dafa16bc975cc34bdd7db5ce3fb60136c4e96fc045fffcdd419b3c9` |
| index.html | `fcb1fdf978778615aadfa8de49877464dfa4d3043afe459ba3f2371439927f0c` |
| package.json | `26f23da67e4b5a5df9294cdc689cd0d4a785a80808bf068c18a9c8f56379f6ba` |

Preserved: Express/HTTP/Socket.IO, one page, one room, string event name and
form interaction. Changed: broadcast and receive/render paths, explicit input
and outage contract, English UI, labelled controls, visible focus, responsive
layout, dependency lock, testable startup, and meaningful tests. No historical
creative title, game content, art, or audio was rewritten. The source package
declares ISC; it does not establish licensing for unrelated portfolio material.
The working package remains private in npm metadata. Git publication is
recorded separately in the lab state; no npm package or hosted service is released.

## Evidence, contribution, and next step

See [draft-recovery evidence](../../evidence/realtime-chat/DRAFT_RECOVERY_RUN.json),
[prior text-reflow evidence](../../evidence/realtime-chat/TEXT_REFLOW_RUN.json),
[prior viewport resize evidence](../../evidence/realtime-chat/RESIZE_RUN.json),
[activity-aware unread evidence](../../evidence/realtime-chat/ACTIVITY_RUN.json),
[prior unread-navigation evidence](../../evidence/realtime-chat/UNREAD_RUN.json),
[prior reading-position evidence](../../evidence/realtime-chat/READING_RUN.json),
[previous transport correction evidence](../../evidence/realtime-chat/POLLING_SEND_RUN.json),
[original adaptation evidence](../../evidence/realtime-chat/RUN.json),
[the selected plan](../../docs/IMPROVEMENT_PLAN.md), and
[transfer learning](../../knowledge/realtime-delivery.md).

Martin supplied the portfolio direction, source context, and authorization for
this increment. Codex performed this session's assessment, adaptation, tests,
and documentation. No manual review, usability session, or playtest by Martin
is attributed. Automated checks verify the specified local interaction; they
do not establish cross-browser compatibility, human accessibility/usability,
public hosting readiness, or a model benchmark.

Next: have Martin try the two-tab interaction and review readability, keyboard
use with enlarged/spaced text, and the uncertain-delivery wording before selecting this as a public case.
P11 → P02 is now verified for [EVAL-001 task adaptation/calibration](../../evaluations/chat-send-buffering/README.md) only; no independent model was evaluated. P11 → P01 remains a candidate. No shared library is needed.

The five historical 0.1.2 reading checks run actual Socket.IO broadcasts through Chromium at a
1280×800 viewport with variable-height message fixtures. Three fail on the
recorded 0.1.1 client; all five pass on the correction. These checks establish
scroll geometry for that browser/viewport, not human usability or all layouts.
P02 keeps its 17 send-policy checks. The historical runner 0.1.4
[recalibrated the P11 0.1.3 runtime](../../evidence/evaluation-task/UNREAD_CALIBRATION.json)
without changing the nine-file starter contract. Current runner 0.2.1 executes
its own committed evaluator snapshot, so this working-client update does not
repin that task. The nineteen reading/activity/reflow checks remain P11-only.

The four new activity checks fail on committed 0.1.3. Three use real tab focus
transitions after disabling Playwright's forced-focus emulation. Headless Chromium
keeps tabs visible, so the hidden-page check explicitly controls the Page Visibility
API boundary. These checks do not establish real minimized-window behavior,
other-browser support, operating-system notifications or human accessibility.

The three resize checks fail on committed 0.1.4 and pass on 0.1.5. They change
actual Chromium viewport dimensions, including 1280-pixel desktop and 390-pixel
narrow widths, and verify retention and native tab focus after reflow. They do
not establish every layout, browser zoom, font-only reflow or human usability.

The three text-reflow checks failed on committed 0.1.5 and passed on 0.1.6;
that suite passed 36 checks (6 protocol, 30 Chromium). They explicitly apply
user styles while asserting unchanged panel dimensions. They cover enlargement
and reset, line/letter spacing, subsequent eviction, and native tab focus after
reflow. P02's unchanged pinned suite also accepts the corrected client at 17/17;
this is a controlled compatibility probe, not an independent candidate attempt.

The two new draft-recovery checks fail on 0.1.6 and pass on 0.1.7; all 38 checks
pass (6 protocol, 32 Chromium). Each submits through the real form and timer;
an evaluator-owned server handler controls whether the earlier message is
broadcast, while withholding its acknowledgement. Both outcomes preserve new
typing and earlier text, render markup literally at 320-pixel width, and make
one attempt. The working client still passes P02's pinned 17 checks. Controlled
faults do not establish real network-outage reliability, human copy/readability
or assistive-technology behavior. Human review remains the next gate.
