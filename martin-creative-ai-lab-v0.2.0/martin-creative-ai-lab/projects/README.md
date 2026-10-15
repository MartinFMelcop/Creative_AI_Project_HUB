# Working projects

Seven working directories contain the current games, reading editions and local
workspace. Each project README provides controls, setup, provenance and execution
evidence. The [project registry](../registry/projects.json) records all eleven
portfolio lines and their current scope; the [lab overview](../README.md) connects
them to references and shared capabilities.

## Games, literature and software

| Project and current version | Experience | Technology and delivery |
|---|---|---|
| [P01 — Eclipse Fair](eclipse-fair/README.md), native **0.4.0** | Eight-venue economy race, solo in any seat or 2–4 participants sharing one device; planning rivals and replay saves. | C#/.NET 10 and Godot .NET 4.6.3. The [compiled native project](eclipse-fair/dist/eclipse-board-0.4.0.zip) requires the matching engine and .NET runtime; [setup](eclipse-fair/Native/README.md#play-the-delivered-package). The terminal workbench **0.1.0** remains available. |
| [P03 — Tokyo 80s: Night Shift](tokyo80s/README.md), **0.4.0** | Two original rhythm stages, sustained notes, timing calibration and four-bar rehearsal at 75/90/100% with original-pitch backing. | HTML/JavaScript and Web Audio; [run locally](tokyo80s/README.md#play-locally) with Node 22+ or a static HTTP server. Gameplay needs no npm installation or remote service. |
| [P04 — A água sob Darsen / The Water Beneath Darsen](lich-cistern/README.md), **0.2.0** | Complete five-scene dark-fantasy story in Portuguese and English. | [Read Markdown, EPUB 3 or A5 PDF](lich-cistern/README.md#read) without a build environment. English **0.2.0** and preserved Portuguese **0.1.0** editions; production uses Python/ReportLab and Pandoc. |
| [P05 — Cinderwatch](cinderwatch/README.md), **0.3.0** | Three-encounter tactical rescue with announced enemy intentions, persistent supplies, salvage choices and replayable resume. | C#/.NET 10 and Godot .NET 4.6.3. [Standalone Linux x86_64 player](cinderwatch/dist/cinderwatch-linux-0.3.0.zip) includes engine/runtime; [system requirements and launch](cinderwatch/Native/README.md#play-the-linux-distribution). Editable source/project also available. |
| [P06 — Veilbreak: The Bell Warden](veil-arena/README.md), **0.6.0** | Native two-phase boss trial with painted art, animation, adaptive audio, blade/seal/dodge decisions and timed sweep counters and an optional real-speed sweep practice/review loop. | GDScript and Godot 4.6.3 standard. [Standalone Linux x86_64 player](veil-arena/dist/veilbreak-linux-0.6.0.zip) includes its runtime; [requirements and controls](veil-arena/README.md#play). Source and a separate engine-dependent PCK remain available. |
| [P10 — Flood Crossing](waystone-dialogue/browser/README.md), browser **0.5.0** | Two-day rescue campaign: cargo, routes, relief priorities and a noon handover with distinct local consequences; portable replay saves. | HTML/JavaScript browser game; [Node 22+ or static HTTP server](waystone-dialogue/browser/README.md#play-locally). The [Python reference](waystone-dialogue/README.md) retains adventure **0.2.0** and dialogue **0.1.3**. |
| [P11 — Project Rooms](realtime-integration-lab/README.md), **0.7.0** | Persistent conversations/decisions, assigned actions, revision history, complete-record search, workspace recovery and portable HTML reading copies with complete print reports. | Node 24+, SQLite and Socket.IO; [install/run](realtime-integration-lab/README.md#run-project-rooms) with `npm ci` and `npm run rooms`. The [offline handover example](realtime-integration-lab/examples/cistern-handover.html) is explicitly fictional. The original ephemeral chat exercise remains available. |

Download ZIPs, ebooks and the HTML handover before opening them. GitHub source
pages do not launch these products. P05/P06 include standalone Linux runtimes;
P01's native pack needs an installed Godot .NET engine and .NET runtime. Browser
games need HTTP rather than direct file navigation. The retained private Sites
demos are separate deployments and do not represent the latest Git versions.

## Evaluation and supporting lines

- [P02 — EVAL-001](../evaluations/chat-send-buffering/README.md), runner **0.2.1**,
  lives under `evaluations/`. Python/Git orchestration and Node/Socket.IO/Chromium
  checks package and evaluate a client-repair practice task. Controlled calibration
  verifies the harness; it is not an independent model benchmark.
- **P07 — Visual Generation & Asset Lab:** original portraits, paintings and motion
  atlases have actual consumers in [Cinderwatch](cinderwatch/Native/media/provenance.json)
  and [Veilbreak](veil-arena/media/provenance.json). This is a supporting production
  line, not a separate game directory; see [its seed](../SEED.md#p07--visual-generation--asset-lab).
- **P08 — Audio, Poetry & Music Lab:** [Tokyo 80s soundtracks](tokyo80s/media/provenance.json),
  [rehearsal derivatives](tokyo80s/media/rehearsal-provenance.json),
  [Veilbreak audio](veil-arena/media/provenance.json) and
  [Cinderwatch cues](cinderwatch/Native/media/audio/catalog.json) are integrated
  assets. A finished music/poetry catalogue is not established; see
  [its seed](../SEED.md#p08--audio-poetry--music-lab).
- **P09 — AI Delivery & Operations Cases:** a seed awaiting sourced professional
  cases, with no delivered case evidence in the current
  [registry](../registry/projects.json); see
  [its seed](../SEED.md#p09--ai-delivery--operations-cases).

## Evidence and source boundaries

Project records distinguish source, builds, actual bounded execution and
implementing-agent review. Human play/reading/listening, hardware accessibility,
other-platform support and commercial demand require their own evidence. Project
Rooms is a trusted local workspace, not a public service with verified accounts.

Current adaptations are separate from [historical references](../references/README.md).
Recovered literary PDFs do not ratify P04's story as canon; copied historical
code does not establish a restored RPG or a [North Star](../north-star/README.md)
runtime. Existing source snapshots and earlier delivered packages remain preserved.
