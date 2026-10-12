# Flood Crossing — browser edition 0.3.0

A complete playable adaptation of [P10's terminal adventure](../README.md).
Pack two items, talk to the Keeper, choose a river route, rescue the mill party
and decide what reaches shelter. The illustrated crossing map, shared flood
clock, residents/cargo, current forecast and action risks stay connected to
actual game state. All five endings have their own consequences and replay.

[Owner-private demo](https://the-last-waystone.sturdyspice.chatgpt.site).
GitHub remains the maintained source. Site identity is retained in
`.openai/hosting.json`; deployment does not change its audience.

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
Saves require format `waystone-save`, schema 1 and engine version `0.2.0`.
Snapshots and additional file fields are never trusted as game state. Files are
limited to 64 KiB and 1,024 decisions; a normal operation is much shorter. An
unusually long free-action loop can continue playing, but save controls explain
the exceeded limit instead of writing an unrestorable journey. Saves contain
only decisions. Use one active tab per browser; there is no cross-device sync,
account, server persistence, undo or future-version migration.

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
node --test tests/engine.test.mjs tests/browser.test.mjs
```

Set `CHROMIUM_PATH` when using a different installed Chromium. CI installs the
matching browser. Python 3.10+ is needed by the oracle, not by the browser game.
`tools/export_dialogue.py` refreshes the source-derived catalogue.

Four domain checks compare actual Python choices, all trace fields, resulting
state and epilogues across 8,583 unique river states from twelve specified entry
histories, plus seeded dialogue paths: 20,124 transitions in this run. This is
not every possible workshop history. Ten Chromium checks play both complete
routes, compare cargo order, cover all five endings, resume loaded cargo,
export/import, reject bad saves, handle blocked storage, use touch/keyboard and
close a late workshop. Desktop/mobile screenshots received implementing-agent
review. [Execution](../../../evidence/waystone-dialogue/BROWSER_RUN.json) records
the actual run and limits.

Automated inputs and same-agent design review do not establish unassisted player
understanding, literary quality, accessibility or commercial demand. Screen-reader
behavior, physical touch hardware, Safari/Firefox and reader enjoyment remain
unverified. This is a short prototype operation, not a finished paid game.
