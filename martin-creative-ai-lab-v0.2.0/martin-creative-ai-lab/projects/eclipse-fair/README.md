# P01 — Eclipse Fair

**0.1.0**, a new C#/.NET economy workbench and playable terminal match from
Artemyra's Feira do Eclipse seed. One participant faces three agents on eight
connected venues. Earn obols, buy three sigils, cleanse curse and claim the Gate.
Compare rule variants across common seeds and all four policy/seat rotations.
This is new gameplay, not recovered RPG Maker code or a graphical engine build.

## Play the compiled package

Install the **.NET 10 runtime**, unzip `dist/eclipse-fair-0.1.0.zip`, then:

```bash
dotnet eclipse.dll play --seed 1
dotnet eclipse.dll play --load examples/partial-journal.json
dotnet eclipse.dll demo --seed 1 --out out/demo
dotnet eclipse.dll replay --load out/demo/journal.json
dotnet eclipse.dll compare --variant rules/expensive-seals.json --runs 100 --seed 0 --out out/compare
```

The pack contains compiled DLLs/configuration, rules and an actual accepted-action
example. No SDK, platform host, engine, art or audio binary is redistributed.
The runtime is required; this is not a self-contained executable. Linux x86_64
was executed. Other platforms remain unverified. Python/SDK are unnecessary for
playing the pack; rebuilding/checking source requires SDK **10.0.401** and Python.

In play mode you control Vaelis. Choose a numbered plan; each shows its destination
and actual projected obols/curse/sigils. Other participants take visible turns.
`hint` offers a heuristic suggestion; `auto` accepts it for one assisted turn.
`help` explains tactics. `save path.json` atomically replaces that requested file;
`quit` leaves without automatic saving. Loading rebuilds accepted actions in a
fresh match, including the forecast, rotating initiative and agent policies.
EOF leaves cleanly. No undo, trusted state snapshot or hidden offline progress.

## What decisions change

| System | Consequence |
|---|---|
| Travel | Stay or cross one edge, then take one action. Moving costs one obol; earning on arrival makes routing part of the budget. |
| Work | Venue wages differ; forecast rush/blight/procession/wharf conditions change returns. Curse reduces wages by up to two, with a floor of one. |
| Sigils | Markets 0/4 charge 6, 8, 10; from round 11 each price rises by one. A purchase adds one curse. Buying every available sigil has a recovery cost. |
| Rites | Chapel 2 removes up to two curse for two obols; a procession makes the rite free. Returning there costs route/time. |
| Protection/theft | A two-obol raven ward blocks one co-located theft. Theft transfers up to three existing obols and adds curse when successful. It never mints money. |
| Finish | Claim at Gate 7 with three sigils and zero curse. Otherwise the fair closes after 20 rounds; rank by sigils, least curse, then obols. Exact ties share the result. |

Map: `0—1—2—3—4—5—6—7—0`, with shortcuts `0↔4`, `2↔6`.
Market 0, Foundry 1, Chapel 2, Wharf 3, Bazaar 4, Orchard 5, Spire 6, Gate 7.
Initial positions and initiative shift with the seed; initiative rotates each
round. Current/next forecasts and all positions/resources are public information.

Collector prioritizes purchases, rites and the Gate; Keeper values protection
around rivals; Opportunist considers disrupting a co-located competitor. Worker
is an intentionally income-only control, not a balanced fourth playable class.
Policies use one-turn previews and next wages; they are not optimal solvers.

## Compare an actual scenario

`--runs` means distinct seeds. Each scenario executes four seat rotations for
every seed, so 100 seeds produce 400 matches and 1,600 participant rows per scenario.
`matches.csv` records each participant/result/economy; `summary.json` records rules,
completion, duration and fractional win credits for ties. Baseline and variant
share seeds/rotations. Relative policy order is retained; this is not all 24
permutations, independent agents, human play or a market forecast.

The included price variant changes the first price from six to eight. Actual
100-seed/four-rotation execution produced **258/400** baseline Gate claims versus
**223/400** under the price variant. Income-only Worker earned zero win credit;
Opportunist led the synthetic policies. These are observations of these rules and
agents, not proof of fair human balance. The initial 15-round/weak-route prototype
produced no Gate claims among the tested policies; production-aware planning and
20 rounds produced observed claims while retaining deadline outcomes. This does
not prove the earlier rules unwinnable for people. Further pacing needs people.

Rules validate bounded integer parameters (starting funds 0–30, goal 1–6, rounds
4–40, first price 1–30, price step 0–10, movement 0–5, rites 0–10, work bonus −1–5).
Unknown fields/options, unsupported journals and unavailable actions are rejected.
Seed range is 0–1,000,000; comparison accepts 1–1,000 seeds. This is in-match economy,
not real monetary modeling, financial advice or a live-service monetization model.

## Build and verify source

```bash
dotnet build Checks/Eclipse.Checks.csproj -c Release
dotnet run --project Checks -c Release --no-build
python3 tools/check_cli.py
dotnet publish Cli/Eclipse.Cli.csproj -c Release --no-self-contained -p:DebugType=None -o out/publish
python3 tools/pack.py
```

No NuGet package or test framework is required. Core owns transactions/agents;
CLI owns JSON/files/terminal/reporting. Ten C# checks cover actual public contracts,
including conservation across 100 complete matches. The Python workflow drives
the compiled process through input rejection, hint/save/resume, full assisted play,
replay and comparison/CSV. CI compiles source and executes the shipped package.

[Execution](../../evidence/eclipse-fair/RUN.json) distinguishes compilation,
terminal input, package consumption, synthetic comparisons and implementing-agent
design review. [Provenance](provenance.json) records the seed adaptation. No full
historical baseline, graphical/native-engine build, physical controller, human
enjoyment, commercial adoption or exclusive rights is claimed. A game engine is a
serious later presentation option; this net10.0 domain is not a drop-in Unity DLL.

Next compare unassisted decisions with these policies, then choose a native board
presentation and any minigame from actual product needs. Avoid expanding the old
48-tile roster/LAN plan before the smaller economy earns that scope.
