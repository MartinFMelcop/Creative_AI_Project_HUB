# Two stores, separate accounts

An original finite C# consumer of selected historical reputation arithmetic.
Quay and Orchard keep independent accounts. Borrowing a tool creates actual custody;
only returning that store's held tool spends the return cost and changes its standing.
A service requires its own accepted payment and receipt. Visiting, promises, elapsed
wall time and another store's history cannot supply it.

This is **one corrective legacy/laboratory unit**, not another production reputation
system or an additional product/portfolio unit. The stores, initial values, costs and
service policy are original experimental setup under Martin's direction, not approved
North Star canon or imported Rave Master fiction. The existing downloadable authored
scene, RequestExpedition, Crossing, old Recovery format and other consumers remain
separate and unchanged.

## Execute the actual consumer

Use the existing pinned SDK10.0.401. From the maintained workspace:

```sh
cd north-star/csharp
dotnet build ../reputation-study/Host/NorthStar.ReputationStudy.csproj -c Release -m:1 --disable-build-servers
dotnet ../reputation-study/Host/bin/Release/net10.0/NorthStar.ReputationStudy.dll --serve 8767 ../reputation-study/web --seconds 300
```

Open the printed loopback URL. Ports are bounded to1024..65535 and host lifetime to
1..600 seconds. Ctrl+C stops the process. A graphical browser is required for the
visible consumer. This entry builds from source; it is not another downloadable release.

The session starts with four time periods, three coins and separate standing−1 at
each store. Those values describe the assay, not the player's worth or a final economy.
Choose the store before acting:

| Action | Accepted consequence |
|---|---|
| Visit Quay or Orchard | Select that account; no time, coin or standing change. |
| Borrow | Take that store's one available measuring tool into custody. No standing gain. |
| Return | Requires that actual custody and two time. Return the tool and apply+2 here. |
| Help | Spend one time and apply+1 here. At−1, the source arithmetic leaves standing−1. |
| Service | Requires standing≥+1, one time and two coins. Supplies that store's service once. |

Borrow → return → service is feasible at one store and leaves the other account
unchanged. Small help is a retained counterexample: repeated+1 tasks from−1 spend
time without crossing the boundary. It is not a secret better route or evidence that
the source rule is fair. Insufficient time can leave a real loan outstanding. A tool
returned to one store does not return the other store's tool. Each store allows one
loan and one service in this attempt; repeat requests cannot farm another return.

All choices remain inspectable, including refusals. The browser renders actual owner
facts and receipts; it owns no standing, costs or completion. Focus loss or an uncertain
reply leaves the view stale until an explicit read, without automatic retry. Accepted
restart creates a fresh ephemeral trial, discards its prior state and invalidates
already queued intentions for that prior trial. Browser refresh only reads the current
process; stopping or expiry loses this study. No save or shared-world claim follows.

## What was consumed, and what was not

[Standing.cs](Rules/Standing.cs) is a separate **C#8/netstandard2.1** library. Its typed
domain has six legal levels:−3,−2,−1,+1,+2,+3. It preserves the inspected source's
Set zero-to+1 normalization, clamp, saturation and Add crossing/zero threshold. Set and
Add are intentionally not interchangeable: Set(0) produces+1, while Add(−1,+1) stays−1.
The actual [Room](Host/Room.cs) uses this library for accepted return/help transitions.
That original finite service policy does not come from the historical effects table.

The source is the preserved Rave Master snapshot
`36af1651271422ae33856e8b5d7b45702215f165`, particularly the DEV/DIST
`RM_REPUTATION_RUNTIME.rb`, CORE/DIST `REPUTATION_RULES.csv` and their associated
source/QA records. [The laboratory method](../../labs/narrative-continuity/reputation/run.py)
binds the exact inspected paths and variant identities. Historical comments and
“CANON” labels are source data, not current North Star instructions or approval.

The source runtime's `effects_for` hook actually returns an empty array. The420 typed
effect rows are **source-only observations**, not executed shop prices, hostility,
spawns, dialogue or quest-access behavior. Header-only QA is not successful execution.
Unknown-zone/string coercions, region defaults, background seeding and automatic
hostility are not adopted by the typed library or the original stores. In particular,
no source background determines a North Star character's moral value or opportunities.
Full reputation/factions, content catalogs and historical Ruby/RMXP execution remain
unresolved beyond the narrow arithmetic contract and explicitly recorded decisions.

## Reproduce the method and actual execution

From the maintained workspace, with fresh outputs outside maintained sources:

```sh
python3 -m unittest discover -s labs/narrative-continuity/reputation -p 'test_*.py'
python3 labs/narrative-continuity/reputation/run.py --dotnet dotnet --output /tmp/reputation-source-method
python3 north-star/reputation-study/tools/verify.py --dotnet dotnet --output /tmp/reputation-consumer-execution
```

The complete verifier binds source and instrument identities before and after actual
execution. It runs the source interpretation, compiled rules, real C# consumer and
Chromium/HTTP observation, including a fabricated-service renderer negative. The
[current execution record](../../evidence/reputation-study/RUN.json) owns artifacts,
retained negatives and exact results:127 SAME Python/C# source cases,420 typed
source-only rows,25 native rule controls,29 native consumer controls,22 Chromium,
7 HTTP and5 instrument regressions. These groups overlap outcomes; they are not
independent participants, population observations, candidate attempts or effort metrics.
Python interpretation and C# agreement do not establish Ruby/RMXP game execution.

## Selection, dissent and limits

Independent Engineering, Scientific and Creative analyses compared this obligation
against licensed Unity/Windows execution, appropriate author/player/device assessment
and item/tool/unlock identity. CRE-005(A) informs observable costs and alternatives;
CRE-031/038/061(H) caution against moral ranking, involuntary public reputation and
unearned recognition. Those hypotheses neither approve the source policy nor establish
participant experience. The visible source threshold counterexample remains exposed.

Creative review preferred the item/tool frontier: actual recipes resolve their literal
item IDs, while the old crafting contract lacks nonconsumed tool requirements; the
source's multiple unlock references also retain unresolved AND/OR meaning. This remains
a strong alternative, not a rejected collection. The primary selected reputation as
a coherent corrective laboratory unit with a new pure library and separate consumer,
preserving old owners and the downloadable scene. This was a resolved disagreement,
not unanimous specialist preference or independent human approval.

The host and browser consumer execute with .NET10 on Linux. Their APIs are not claimed
Unity-compatible merely because the pure library targets netstandard2.1. Licensed
Unity Editor, activation/modules, Windows player and Steam execution remain separate
unexecuted acceptances. No agent or software assertion establishes comprehension,
accessibility, enjoyment, balance, real social trust, commercial clearance or production
ownership. Build/Operations remains incomplete. No protected source, variant, old save,
consumer, media or notice is retired by this study.
