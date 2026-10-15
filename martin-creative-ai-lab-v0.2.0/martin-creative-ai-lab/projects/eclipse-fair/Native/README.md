# Eclipse Fair — native board 0.5.0

Play one local participant in **any seat**, or two to four participants sharing
the native board. Unchecked seats use Planning or Classic rivals. Eight connected
venues, real budget/action previews, theft/wards, rites and Gate/deadline results
consume the same C# economy. All positions/resources are public.

## Play the Linux distribution

Download [eclipse-fair-linux-0.5.0.zip](../dist/eclipse-fair-linux-0.5.0.zip)
([SHA-256](../dist/eclipse-fair-linux-0.5.0.zip.sha256)). Extract the complete
`EclipseFair/` folder and run `./eclipse-fair.x86_64`. Keep `eclipse-fair.pck` and
`data_Eclipse.Board_linuxbsd_x86_64/` beside it. No installed Godot, .NET runtime,
SDK or checkout is needed. If extraction drops permissions, use
`chmod +x eclipse-fair.x86_64`. Linux x86_64 desktop/display libraries, ICU and
OpenGL 3.3 remain system requirements. No audio or physical controller is added.

The package includes the exact official Godot .NET 4.6.3 release runtime and
self-contained .NET 10.0.12 with their licenses/notices. `BUILD-INFO.json` identifies
source/configuration hashes and the complete payload. This is a standalone native
player, with the unchanged economy/local-play/save rules. All previous ZIPs remain
preserved. [Release execution](../../../evidence/eclipse-fair/RELEASE_RUN.json)
records the actual isolated runtime, compatibility and interaction checks.

## Play the delivered package

The optional [compiled project pack](../dist/eclipse-board-0.5.0.zip) remains for
engine users. Install **Godot .NET 4.6.3** and the **.NET 10 runtime**; standard
Godot cannot load C#. From the extracted `eclipse-board` folder:

```sh
/path/to/Godot_mono --path Native
```

Owned compiled assemblies and editable sources/configuration are included. No SDK
or NuGet restore is needed to play this project pack, but its engine/runtime are
external. Its new solution/export preset supports rebuilding the standalone player.
Use the Linux distribution above when you do not want to install development tools.

## Local play and decisions

**New fair** selects a seed, Planning/Classic mode and one to four LOCAL seats:
Vaelis, Madra, Nira or Morrak. At least one must remain selected. One participant
plays immediately on their turn. With several, **Begin <name>’s turn** acknowledges
handoff before plans or suggestions become available. Waiting/beginning spends no
turn. The previous plan is cleared; auto/manual rivals cannot spend a local turn.
The board, income, objective, preview and response use the actual local actor.
Four local seats disable Auto rivals. This is shared-device play, without LAN,
hidden information, account identity or a privacy curtain.

Inspect a venue, select an action, compare its actual consequences, then **Commit
this plan**. Travel crosses at most one edge for one obol; staying is free. Buy
three sigils at Market/Bazaar; each adds curse and raises the next price. Prices
rise again after round ten. Chapel rites remove two curse for two obols, or free
during a procession. Curse reduces wages. Reach the Gate with three sigils and
zero curse, then **Claim**. A raven ward blocks one co-located theft; successful
theft transfers obols and adds curse. At round twenty, rank by sigils, least curse,
then obols; exact ties share victory. Results name actual winners in every seat.

**Next turns** executes the selected action in a fork, then only configured rivals
until the next local player or an ending. It never predicts another human's
choice, even if that player has a suggestion profile. With consecutive local
turns, no rival reply is invented. Compare another plan without spending a turn.
The dialog names the next local decision and the initiating actor's actual budget.

**Suggest plan** uses the stored profile. Planning compares legal first actions
by projecting a complete race with public classic models, then replans. Later
moves and other local decisions are assumptions. Hover a LOCAL roster label to
see its suggestion profile. Rival response/route models do not establish optimal
human play. [Prior planning comparison](https://github.com/MartinFMelcop/Creative_AI_Project_HUB/blob/main/martin-creative-ai-lab-v0.2.0/martin-creative-ai-lab/evidence/eclipse-fair/PLANNING_RUN.json)
retains its original synthetic scope.

Watch rivals individually or enable Auto rivals, paced at one turn per second.
Window focus loss stops auto turns; resume explicitly. Tab/arrows navigate native
controls; Enter/Space activate the focused control. No audio/controller is added.

## Save and replay

Accepted turns autosave to `user://match.json`; **Save** retries a failed write.
**Resume save** and startup loading replay every action and validate local seats
before replacing play. Multi-participant loading requires handoff again. No wall
time passes; malformed saves preserve the current match. Failed writes leave
accepted progress in memory with a visible notice. New fair replaces the saved
match only on an accepted turn or explicit Save. No undo/automatic backup.

Native saves use a **boardSchema 1 envelope**, with `humanSeats` and the original
schema-1/rules-0.1.0 economy journal under `match`. Earlier plain journals load
with Vaelis as the sole local seat and their stored profiles. Older consumers
cannot load the new envelope. **Export replay** writes `match.replay.json` beside
the save: the original economy format without local controls. The current CLI or
0.3.0 board can replay Planning profiles; original terminal 0.1.0/board 0.2.0 accept
only Classic profiles. Replays are records, not recordings of hidden human plans.
Earlier shipped packages are preserved.

## Build and verification

From the parent project, with SDK **10.0.401** and Godot .NET **4.6.3**:

```sh
dotnet run --project Checks -c Release
dotnet build Native/Eclipse.Board.csproj -c Debug
Godot_mono --headless --path Native --editor --import --quit
Godot_mono --headless --path Native -- --verify --save-path /tmp/eclipse-check/match.json
python3 tools/pack_board.py
python3 tools/check_board_pack.py
```

Use an isolated save. With a display, add `--capture <scratch>/frames` to inspect
raw engine frames. Checks drive actual controls/keyboard, configuration geometry,
all fifteen local-seat sets, mixed forecasts, invalid-save preservation, legacy
journals/export and twenty-six complete Gate/deadline matches. A four-local
Work-only sequence exercises choices independent of suggestions. Compiled
old/current session comparison shows seat-zero-only versus any-seat acceptance.
The final pack is executed outside source with runtime-only .NET and no SDK.

[Local-play execution](https://github.com/MartinFMelcop/Creative_AI_Project_HUB/blob/main/martin-creative-ai-lab-v0.2.0/martin-creative-ai-lab/evidence/eclipse-fair/LOCAL_RUN.json)
separates technical results, scripted inputs and Codex visual/gameplay judgment.
These are not human playtests. Unassisted handoff/strategy, accessibility,
physical controllers, other platforms, commercial demand and other-OS exports
remain unverified. No historical RPG runtime restoration is claimed.

## Build the standalone player

With the same pinned SDK and Godot .NET editor:

```sh
python3 tools/export_linux.py --godot /path/to/Godot_mono --templates /path/to/mono-templates.tpz
python3 tools/check_linux.py
python3 tools/test_check_linux.py
```

Run these from the parent project directory. `--template` also accepts the exact
verified `linux_release.x86_64`; unrelated templates/editors/SDKs are rejected.
The producer copies maintained source to fresh staging, builds/imports/exports,
checks bundled runtime components, includes notices and atomically replaces the
ZIP after successful assembly. It adapts the verified P05 producer pattern; this
is a real second consumer, not a shared gameplay framework or North Star transfer.

For scripted verification of the extracted release, always use a separate save:

```sh
./eclipse-fair.x86_64 --headless -- --verify --save-path /tmp/eclipse-check/match.json
```

This replaces that explicit test slot. Existing user saves are not verification
inputs. Release/source verification is implementing-agent evidence, not a human
playtest or proof of hardware accessibility, enjoyment, other OS or market demand.
