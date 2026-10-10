# P11 — Live exchange

**Project:** Real-time Integration Lab / WebSocket. **Version:** 0.1.1.
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
| Only latest 200 messages retained per page | Browser retention test |

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

On transport interruption Socket.IO reconnects. Messages sent while away are
not recovered. Existing messages remain in that page's memory until reload or
retention eviction. Offline drafts require explicit submission after reconnect.
If an acknowledgement is lost, the UI keeps the draft and reports uncertain
delivery. Check the conversation before resending; manual retries can duplicate
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
not a skipped browser suite. Protocol-only tests use `npm run test:protocol`.

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
The working package is private and this session did not publish it.

## Evidence, contribution, and next step

See [current transport correction evidence](../../evidence/realtime-chat/POLLING_SEND_RUN.json),
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
use, and the uncertain-delivery wording before selecting this as a public case.
Keep P11 → P02 and P11 → P01 as candidate transfers until a destination task
actually uses and verifies the lesson. No shared library is needed yet.
