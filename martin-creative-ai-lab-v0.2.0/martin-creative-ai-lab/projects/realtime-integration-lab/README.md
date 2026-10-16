# P11 — Project Rooms / Live exchange

**Version:** 0.8.0. A local project workspace with remembered participants,
separate conversations, saved notes/decisions, recoverable history, JSON export,
assigned actions, blockers/outcomes, change history, bidirectional discussion reading, complete-record search,
portable offline reading copies and consistent workspace recovery.
The original ephemeral exercise remains available with its unchanged protocol.

![Actual portable handover reader with explicitly fictional Chromium records](../../evidence/realtime-chat/portable-demo.png)

## Run Project Rooms

Use **Node 24+** (tested 24.19.0) for the persistent mode and complete test suite.
From this directory:

```bash
npm ci
npm run rooms
# Open http://127.0.0.1:3000/studio/ in two browsers or tabs.
npm test
# Room discussion/reconnection checks:
npm run test:rooms
```

1. Choose a display name, then create or open a project.
2. Share its browser address or Copy project link. Another participant chooses
   their own name; the address selects the same room.
3. Send a discussion note or record a decision. Both are saved before broadcast;
   decisions also appear in a separate project record. Use **Create action** to
   turn one into work, or open Actions to create an independent action.
4. Switch projects without losing drafts, reload, reconnect or restart the server.
   Your remembered local identity reopens the saved room and its latest entries.
5. Assign a participant who has joined the room. Move work through To do, In
   progress, Blocked and Done; blockers/completion require a recorded update.
6. Use **Search record** to find earlier text, decisions or historical action revisions. Open saved context to inspect nearby records, the source decision and current linked work.
7. Load earlier/newer entries, Return to latest, or Export record for all notes, decisions, actions and
   action history. `Assigned to me` and `Unassigned` filter the action board.
8. **Export reading copy** creates a self-contained HTML handover. Open it in a
   browser without running this workspace; it retains the full record at export.

`ROOMS_DB` selects the SQLite file; default `data/rooms.sqlite` is ignored by Git.
`HOST`/`PORT` default to `127.0.0.1:3000`. CLI assets/database paths work outside
this directory. Stop with Ctrl+C; restart against the same database to continue.
The separate `npm start` command runs the original ephemeral lab at `/`.
Project Rooms also serves that exercise at `/`; their Socket.IO namespaces do not
share events. The package's Node 22 minimum remains for that legacy exercise;
the rooms entry explicitly requires Node 24. No dependencies were added or upgraded.

## Persistence and delivery contract

SQLite schema 2 adds room participants, actions and action events to the original
sessions, unique project names and ordered entries with
foreign keys/indexes. Session tokens are random, stored as hashes in the database
and remembered by this browser. Display names are chosen, not verified accounts.
All participants in this trusted workspace can open every room; stream separation
is not private-room authorization. Changing participant creates a new identity
and leaves earlier authorship intact. Browser drafts are scoped to that identity.
Clearing browser storage loses its remembered identity/drafts, not saved entries.

A send has an immutable client attempt ID, scoped to its participant. Commit
precedes broadcast/acknowledgement. Retrying the same content/ID returns the saved
entry without another insert/broadcast; reusing an ID for different content is
rejected. Lost acknowledgement keeps an explicit Previous attempt, without
replacing newer typing. Rejoining history resolves a saved attempt; an unsaved
attempt can be retried explicitly. No offline send or automatic replay is queued.
An explicit rejection preserves the editable draft and releases the retry state.
This is single-server idempotency, not a distributed exactly-once guarantee.

History pages contain 50 chronological entries; the browser holds at most 300.
The decision panel shows the latest 100; JSON export includes the complete record
without credentials. Limits: 500 characters per entry, 40 per participant name,
60 per project name, 100 projects, 5,000 local identities and 10,000 entries per
project. Export is a consumable record, not a database restore/import tool.
Use the workspace recovery workflow below to preserve full continuation.
Do not copy a running WAL database as though its main file alone were complete.

## Read an earlier discussion without losing your place

**Load earlier entries** and **Load newer entries** traverse the entire saved
conversation in 50-entry pages. At most 300 rows stay loaded: loading earlier
removes rows from the newer end; loading newer removes rows from the older end.
The visible row and its position remain when retained. If that row leaves the
window, reading falls back to its earliest retained row. A removed focused control
returns focus to the conversation; earlier data stays on the server.
Boundary text identifies whether earlier/newer entries are available.

**Return to latest** fetches the latest saved page, rather than only scrolling
already loaded text. It keeps discussion/action drafts and search results.
The 0.7.0 UI intentionally stopped chronological browsing at 300 loaded entries
and suggested search; search still helps when you know words to find.

While reading earlier rows, paging or using Actions/Search, new notes and decisions
stay saved and update their record panels without displacing the conversation.
A newer-entry signal offers explicit navigation. It is an availability signal,
not an exact unread count. Your own confirmed send resolves its pending attempt
even when that row belongs beyond the current window. Fetching a saved page also
confirms a matching uncertain own attempt, without another send. Later typing
stays intact.
At the visible current end, arrivals continue to follow normally.

Failed requests retain the window and allow retry. Room, identity and reconnect
boundaries invalidate delayed responses. Navigation does not reclaim focus from
an editor used while waiting. Reconnect/reload still opens the latest page;
reading position is not persisted. This is a trusted single-server workspace,
not synchronized read receipts or private-room authorization.

Run `npm run test:history` for SQLite/API and real Chromium regression journeys.
[Execution evidence](../../evidence/realtime-chat/HISTORY_RUN.json) compares the
same 650-entry fixture against 0.7.0 and 0.8.0. The records/participants shown in
[the captured view](../../evidence/realtime-chat/history-reading.png) are fictional.
Independent handover, screen-reader and other-browser use remain unverified.

## Search the complete project record

Search record covers every saved note/decision and every action revision, including
records outside the loaded timeline and recent decision/history panels. Enter
1–8 literal words (at most 160 characters) and optionally choose a record type.
Every word must occur in the entry body or the revision's title/update; order
and case/accents do not matter. Punctuation, quotes, `%` and `_` are literal.
There are no query operators, wildcard expansion, ranking or semantic answers.

Twenty newest matches appear per page with author/time and exact revision/status.
Several revisions of one action can match. Pagination pins both immutable record
streams, so later writes cannot reorder Previous/Next. New records trigger
**Refresh results**; pages also detect newer server records when no socket arrival
was observed. Refresh explicitly starts a new snapshot. A new search, room change,
reconnect or identity change resets the search view; queries are not persisted.

**Open saved context** shows two nearby records/revisions on either side of the
match, the original linked decision and current linked actions. The matched item
is labelled. Current work is a separate snapshot taken when context opens; it is
not the historical revision's status or a live-updating view. **Open current
action** returns to the board and retains its highest known revision. Search and
navigation preserve conversation/action drafts and spend no action attempt.
**Back to matched result** restores keyboard focus without reloading that page.

Search reads SQLite directly under the existing room/capacity bounds; no durable
index, schema migration, new dependency or external service is added. It does not
search other projects, participant names, attachments or deleted/off-site records.
All trusted identities can already open all projects: scoping is not private-room
access control. [Execution](../../evidence/realtime-chat/SEARCH_RUN.json) records
old/new retrieval, actual Chromium journeys and a bounded 20,000-record sample;
this is not independent team usability or production-load validation.

## Carry the record outside the workspace

Download **Export reading copy** and open the `.html` in a browser with JavaScript
enabled. The recipient needs no server, Node installation, account or connection.
Try the delivered [fictional handover](examples/cistern-handover.html) first;
[its JSON source](examples/cistern-handover.json) explicitly describes invented
participants and outcomes. Download the HTML before opening it; GitHub's source
page is not the reader. This demo is not a record of real team activity.

**Work at export** filters current actions by status and chosen owner label.
**Complete saved record** searches all notes, decisions and every action revision,
including records omitted from the live recent panels. Search uses the same
literal word/case/accent semantics as the workspace; empty search browses all
records. Twenty-item pages bound displayed work, results, linked actions and
revision histories. Duplicate display names share a label filter, not an account.

Open a match to see nearby discussion, its immutable source decision, and the
selected revision alongside **Current at export**. The complete revision history
starts on the selected revision's page; keyboard Back restores the original
button. This snapshot never receives later writes or changes live drafts. It
neither imports nor restores a workspace. Done is still a participant's recorded
outcome, not independently verified delivery.

Choose **Prepare complete print report** to review every saved entry, current
action and historical revision in one report, then **Print / Save as PDF**.
Browser Print (Ctrl/Cmd+P) produces the same complete snapshot automatically.
Filters, search terms and selected pages do not restrict the report; it may be
long and includes earlier text and chosen names. Review it before sharing.
**Back to reading copy** restores the selected pages, filters and keyboard focus.
Cancelling browser printing leaves the reading state intact.

Current work includes owner labels, creation/update times, action IDs and source
decision references. Discussion retains saved entry order; revision histories are
grouped by action in recorded revision order, with Historical/Current at export
labels. Earlier exports without actions explicitly disclose missing data. The
source SHA-256 identifies embedded JSON bytes, not authorship or authenticity.
The report is built locally on demand, uses inert text and makes no network
requests. Existing exported HTML files keep their old renderer: reconvert their
original JSON with the current converter to obtain complete printing.

[Print execution](../../evidence/realtime-chat/PRINT_RUN.json) distinguishes actual
Chromium PDF/text checks and implementing-agent visual review from independent
team, assistive-technology and other-browser evaluation. Browser Save as PDF is
not a validated PDF/UA or archival PDF/A production workflow.

Already have a schema-1 JSON export? Convert it locally to a **new** output file:

```sh
npm run rooms:record -- project-conversation.json handover.html
# The supplied fictional source can also be converted to a new destination:
npm run rooms:record -- examples/cistern-handover.json /tmp/cistern-review.html
npm run test:record
```

The dependency-free converter also runs as `node /path/to/rooms-record.cjs
INPUT.json NEW-OUTPUT.html` outside this directory. It accepts earlier exports
without `actions`, clearly disclosing unavailable action data. Unsupported fields,
inconsistent source/revision data and records exceeding workspace limits are
rejected rather than repaired. Input is limited to a regular file of 64 MiB;
existing outputs/symlinks are refused. SQLite backups are not JSON records.

**Save embedded JSON record** recovers the exact compact source represented by
the reader. Its SHA-256 identifies those JSON bytes, not their author or origin.
All record text is literal; inert JSON encoding, DOM text rendering and a hash
based content policy restrict executable content to the bundled reader. No
external scripts, fonts, network requests, storage or workspace tokens are needed.
Text may itself contain sensitive information: inspect the entire record before
sharing. Authentication for the live export uses the existing trusted-workspace
rules; this does not create private-room permissions.

[Execution](../../evidence/realtime-chat/PORTABLE_RUN.json) distinguishes local
HTTP/CLI/Chromium verification from direct file navigation. Managed Chromium here
blocks `file://`; `ROOMS_RECORD_READER_TRANSPORT=loopback npm run test:record`
loads identical bytes from a temporary static server, then closes it and disables
network before interactions. Tests default to direct `file://` navigation in CI.
No policy is overridden. Other browsers, real collaborator handovers, assistive
technology and commercial interest still require external evidence.

## Assigned work and concurrent changes

A decision source stays immutable; several actions can implement one decision.
Every action records title, optional owner, status, update/outcome and revision.
Ownership communicates responsibility; it is not an access-control role. All
trusted collaborators can update work. Done is the participant's stated outcome,
not automatic verification of an artifact. Reopening requires a new reason and moves
work to To do or In progress. The history shows who changed each revision.

A save checks its expected revision and commits the action plus its event in one
transaction. A stale draft keeps its fields and displays the current version;
**Use latest version** replaces it explicitly. **Reapply my draft for review**
keeps edits against the new revision, then requires another Save. Other people's
updates keep the current view and closed editor intact. Each room/participant
keeps one active action draft: close/resume it, or discard it explicitly before
starting another. Room switches and reloads preserve that draft.

Lost confirmation retains a locked, immutable attempt. On reconnect/reload, an
accepted-attempt receipt resolves it, even if others subsequently changed the
work. An uncommitted attempt requires **Retry same action attempt**; reconnecting
never sends offline changes automatically. A replay returns the original accepted
snapshot; the board retains the highest revision. Browser storage is separate
from the SQLite backup, including action drafts and pending attempts.

The UI shows the latest 50 events for an action; export includes its complete
history. Schema-1 JSON keeps its original project/entries fields and adds an
`actions` array with histories. Capacity: 500 actions and 10,000 action events per
project. Actions are retained for audit.

```sh
npm run test:actions
```

[Action workflow execution](../../evidence/realtime-chat/ACTIONS_RUN.json) records
real two-context Chromium cooperation, uncertain committed/uncommitted saves,
revision conflicts, narrow layout, restart/recovery, literal text and declared
fixtures. Codex inspection is not independent collaborator/accessibility approval.

## Back up, inspect and recover a workspace

The Node 24 operator CLI runs locally; there is no backup HTTP endpoint.
The backup format remains version 1; database schemas 1 and 2 are supported.
**Before opening a schema-1 workspace, retain a 0.3.0 savepoint.** Opening with
0.4.0 or later migrates schema 1 to 2 transactionally; failed migration rolls back.
Existing 0.4.0/schema-2 workspaces open in 0.6.0 without a schema migration. Older
schema-1 bundles remain inspectable/restorable and upgrade on application open.
The 0.3.0 application cannot open schema 2; downgrade by selecting a retained old
backup in a new file, not by rewriting the version header. The current CLI can
snapshot a **running** Project Rooms database using SQLite's online backup API,
including committed WAL pages. It produces a new private directory containing
`workspace.sqlite` and `manifest.json`: date, application/schema versions,
SHA-256/size and per-project inventory. The database also retains participant
token hashes, authorship, immutable attempt IDs and sequences, plus action
assignments, complete change history and accepted-action retry receipts. The report
does not print credentials or entry bodies. Keep the entire bundle private;
`data/` and `backups/` are ignored by Git, and **no sample live backup is shipped**.

From this project directory (the destination parent must already exist):

```bash
mkdir -p backups
# While the server is running; use a NEW bundle path for each savepoint:
npm run rooms:backup -- --db data/rooms.sqlite --out backups/pre-review
npm run rooms:inspect -- --from backups/pre-review
# Check the reported date, project counts and SHA-256. Stop the server (Ctrl+C).
# Restore to a NEW database, leaving the original available for comparison:
npm run rooms:restore -- --from backups/pre-review --db data/recovered.sqlite
ROOMS_DB=data/recovered.sqlite npm run rooms
```

Restore also accepts `--expect-sha` followed by the SHA-256 printed by inspection
to pin the reviewed savepoint. Direct `node /path/to/rooms-backup.cjs` commands
work outside the project directory; `--help` shows the complete workflow. Paths
are resolved from the caller's current directory. Existing bundles, destination
files, links and SQLite journal/sidecar paths are refused; there is no force or
overwrite option. An interrupted backup with no completed manifest is refused.

Inspection checks checksum/size, exact schema, SQLite integrity, foreign keys,
data contracts, capacity, entry/action sequences and matching inventory. Schema 2
also verifies contiguous action revisions, canonical commands, snapshots and their
links/owners before publishing a restored file. Recovery checks
the staged bytes again before exclusive, atomic file publication. It never opens
the destination as a live workspace or replaces a running database. POSIX
bundles are created with directory mode 0700 and files 0600; files/directories
are flushed before completion. Linux was executed; other filesystems/platforms,
power-loss behavior and hostile concurrent filesystem changes are unverified.
Checksums detect accidental changes; the manifest is **not signed** and does not
authenticate a backup's origin. Use a trusted private copy.

Reopen the same browser origin with its existing storage: remembered identities,
project links and browser drafts can continue against the recovered server. Browser
storage itself is **not in the backup**. Losing it loses tokens/drafts; display
names cannot recover an account. A snapshot excludes writes committed after its
savepoint, including later acknowledged entries. Preserve the newer original
when comparing records. History resolves attempts saved in the snapshot; an
unsaved browser attempt stays available for an explicit retry, without replacing
newer typing. No automatic import/merge of JSON exports is performed.

[Recovery execution](../../evidence/realtime-chat/RECOVERY_RUN.json) exercises
live WAL backup in a separate operator process, simulated original-file loss,
inspection, restore, same-origin server restart, two remembered participants,
deduplication, explicit uncertain retry, pagination/download and new saved work.
Fictional fixtures and synthetic Chromium input are not independent usability
or human collaboration evidence. Run `npm run test:recovery` to repeat it.

This is a local prototype for trusted collaborators. Public service operation,
verified accounts/roles, TLS hosting, revocation/retention policies, multi-process
writers, scheduled/off-site disaster recovery, encryption at rest and assistive technology remain
outside the validated contract. No hosted service, customer adoption or paid
market claim. Local-storage denial permits current-session use but prevents
remembering identity/drafts; the UI explains this limitation.

## Verification and origin

[Rooms execution](../../evidence/realtime-chat/ROOMS_RUN.json) records actual
SQLite reopening, HTTP/Socket.IO isolation, Chromium collaboration, permalink,
reload/server restart, controlled lost acknowledgements, explicit rejection,
pagination/export and desktop/narrow rendering. Existing 38 chat checks are
retained. Source and visual review are by Codex, not independent user approval.
The screenshot contains fictional automated fixtures, not actual collaboration.

Node/Express/Socket.IO remain appropriate for this existing real-time service.
Native SQLite adds relational persistence without another service or dependency.
A C#/ASP.NET or Go rewrite would duplicate the verified transport; a game engine
does not serve this workflow. P02 keeps its pinned evaluator and unchanged
dependency graph. This new workspace is authored under Martin's portfolio mandate,
not recovered historical functionality; the three original files and ZIP remain
unchanged. Human usability and commercial validation are future evidence.

# Legacy exercise — Live exchange

The retained ephemeral mode preserves the 0.1.7 interaction and event contract.
It is a working adaptation of the historical Socket.IO exercise, not a raw
WebSocket implementation.

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
