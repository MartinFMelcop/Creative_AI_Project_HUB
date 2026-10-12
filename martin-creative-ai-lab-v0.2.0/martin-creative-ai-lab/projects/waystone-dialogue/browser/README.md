# Flood Crossing — two-day campaign 0.4.0

A complete playable two-day adaptation of [P10's terminal adventure](../README.md).
Pack two items, talk to the Keeper, choose a river route, rescue the mill party
and decide what reaches shelter. The illustrated crossing map, shared flood
clock, residents/cargo, current forecast and action risks stay connected to
actual game state. All five endings have their own consequences and replay.

[Owner-private demo](https://the-last-waystone.sturdyspice.chatgpt.site).
GitHub remains the maintained source. Site identity is retained in
`.openai/hosting.json`; deployment does not change its audience.

## The morning crew

After any night ending, choose **Meet the morning crew**. The six-shift morning
uses actual night results: a permanent causeway carries four grain crates per
shift; a retained ferry carries two, with Iven reducing trip time. The ridge
trail provides a slower fallback after failed transport. Recovering stranded
people also recovers Iven, while Senn's planting crew needs the full mill party.
One fresh timber bundle joins any unused night timber; road/ferry work consumes
it where shown. An unresolved council lie must be corrected on the public list
before the Keeper helps repair the road; the original night trace stays intact.

Dry medicine already delivered means morning care can begin. A dry chest left
behind can be retrieved; spoiled medicine requires the depot reserve. Delivery
completed by shift 3 is timely. Later delivery supplies afternoon care without
inventing casualty counts. The wagon leaves at shift 6. Food, seed, transport,
clinical timing and resident recovery remain separate outcomes. Sowing is not a
harvest. A prepared backup ferry and a consumed depot reserve appear in the
handover instead of disappearing into dialogue.

Actual work-order comparison: after the spoiled-cargo ferry night, `depot,
supply-clinic, grain, grain, seed` gives timely care; `grain, grain, depot,
supply-clinic, seed` gives late care with the same people, grain and saved seed.
After a full permanent-road rescue, `grain, seed, plant, ready-ferry` completes
both days with planted seed, food and two usable afternoon routes. These are
spoilers and executed examples, not human balance approval.

## Play locally

Node 22+ for the included static server, or any static HTTP server for `dist/`.
The game itself needs only a modern browser with ES modules and structuredClone;
there are no runtime packages, remote APIs, fonts or media requests.

```bash
cd projects/waystone-dialogue/browser
npm start
```

Open `http://127.0.0.1:4174`. `PORT` can change the local port. You can also run
`python3 -m http.server 4174 --directory dist`. Serve over HTTP rather than
opening the module page with `file://`.

Use buttons, keyboard Tab/Enter or touch. Reading takes no time. Choices show
beat cost, resource consumption and rescue deadlines; ferry strokes also show
their actual forecast, projected hull and certain cargo damage. These expose
the existing deterministic rules, without supplying a solved route or score.
The mobile map can be expanded independently of the compact situation panel.

The Keeper's original twelve dialogue turns remain separate from the nine-beat
flood window. Once the landing floods, the interface explains why continuing
the conversation cannot reopen the crossing. Stranded residents seek refuge;
the game does not declare unrescued people dead. Four residents and Iven are
separate outcomes.

## Keep or resume a crossing

Accepted decisions autosave in localStorage. Reload offers Continue crossing;
completed endings also resume. Save file exports an actual JSON decision
journal. Load file replays it into a fresh engine and checks every action before
replacing the active journey. Replacement is explicit and cancellable. Invalid,
incompatible or oversized files leave the current journey untouched.

Blocked/full browser storage does not prevent play or file export/import.
Night-only saves retain format `waystone-save`, schema 1 and engine version
`0.2.0`. Existing 0.3.0 saves, including endings, still load and can continue.
Once morning begins, schema 2 / engine version `0.4.0` saves the full action
sequence across both days. Replay reconstructs inherited facts rather than
trusting supplied morning snapshots.
Snapshots and additional file fields are never trusted as game state. Files are
limited to 64 KiB and 1,024 decisions; a normal operation is much shorter. An
unusually long free-action loop can continue playing, but save controls explain
the exceeded limit instead of writing an unrestorable journey. Saves contain
only decisions. Use one active tab per browser; there is no cross-device sync,
account, server persistence or undo. Unknown future versions are rejected; the
old night format is the explicit supported migration.

## Implementation and verification

`engine.js` and `scene.js` port the unchanged Python adventure 0.2.0 and scene
0.1.3. The static dialogue catalogue is generated directly from Python; dynamic
response rendering and transition rules are a deliberate bounded port. No DSL,
shared narrative framework or historical RPG execution is implied. Python remains
the adaptation reference: update the port and parity checks when its rules change.

The vector map, layout and interaction text are new Codex-authored code under
Martin's direction. No external image, sample, font or historical art is imported.
The map is a situational diagram, not a restored RPG map or generated painting.

With P11's existing locked Playwright dependency and Chromium installed:

```bash
python3 tools/export_dialogue.py --check
npm test
```

Set `CHROMIUM_PATH` when using a different installed Chromium. CI installs the
matching browser. Python 3.10+ is needed by the oracle, not by the browser game.
`tools/export_dialogue.py` refreshes the source-derived catalogue.

The retained four night-domain checks compare actual Python choices, all trace fields, resulting
state and epilogues across 8,583 unique river states from twelve specified entry
histories, plus seeded dialogue paths: 20,124 transitions in this run. This is
not every possible workshop history. The retained ten Chromium checks play both complete
routes, compare cargo order, cover all five endings, resume loaded cargo,
export/import, reject bad saves, handle blocked storage, use touch/keyboard and
close a late workshop. Seven campaign checks explore 525 morning states and
720 transitions from six specified night endings and verify carryover, medical
priority, crew, records and replay. Four additional Chromium checks execute both
days, priority comparisons, old-save continuation, morning reload/export/import
and touch fallback. Desktop/mobile screenshots received implementing-agent
review. [Execution](../../../evidence/waystone-dialogue/BROWSER_RUN.json) records
the actual run and limits.

Automated inputs and same-agent design review do not establish unassisted player
understanding, literary quality, accessibility or commercial demand. Screen-reader
behavior, physical touch hardware, Safari/Firefox and reader enjoyment remain
unverified. This is a two-chapter prototype, not a finished paid game.


[Campaign execution](../../../evidence/waystone-dialogue/CAMPAIGN_RUN.json)
records 0.4.0. The morning is new Codex-authored fiction/rules under Martin's
direction, implemented in JavaScript; Python parity applies to the preserved
night, not to an invented Python morning reference. Next: unassisted two-day
play, then revise order/deadline pacing and character scenes before a further
chapter or commercial pitch.
