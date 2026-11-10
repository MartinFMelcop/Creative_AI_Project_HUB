# Combat rules boundary

This is a bounded C#8/netstandard2.1 port of the preserved combat helper arithmetic, not execution of Ruby/RGSS, a historical battle loop, or validated balance. The consumer owns hit/application decisions; formulas do not secretly consume random numbers.

Formula inputs must be finite, nonnegative and at most 1,000,000; levels are integers 0..1000. Calculated integer outputs must fit Int32. Historical string/nil coercion, fractional-level coercion, negative ratings, invalid denominators and unbounded inputs are rejected. All ties round away from zero. Duration retains the minimum of one, including negative calculated multipliers. Reapply accepts nonnegative integers, checks addition overflow, and retains the historical zero-plus-zero result of one. Dot preserves case-insensitive source matching without trimming whitespace; unknown identifiers produce zero. HP maximum one can legitimately produce zero DOT. These adapters do not authorize unknown effects in the strict container.

EffectSet has only four recognized effects. Duration is 1..1000, additive on reapplication with an atomic cap of 1000; magnitudes do not stack. Round numbering starts at one and must advance exactly once in sequence. EndRound computes all source DOT independently against the same HP maximum, then decrements every active effect once and removes expired entries. It rejects invalid round or HP before mutation. Defender does not enter this API. Attack, healing and weapon modifiers remain active until expiration or explicit cleanse. Returned arrays are detached copies and their elements have read-only properties. Tick entry Remaining is the duration AFTER that round; zero entries document expiration.

The separate FINAL_DAMAGE vector adapter applies Defender's 0.5 multiplier after integer mitigation and rounds again, matching the inspected historical QA runner. This adapter invokes no source script; the separate source assay executes a reviewed staged Python surrogate. A zero-length vector input, unknown component, missing field, malformed invariant number or invalid flag fails the invocation; no rows are skipped or fabricated.

## Actual encounter ownership

The existing `Host/Trial.cs` source is linked once into this C#8/netstandard2.1
assembly. Its mutable encounter state, costs, global rounds, initiative, passive,
response and control consequences execute here; Host/Room remains the .NET10 JSON
adapter. No gameplay policy or numbers changed. The native architecture guard rejects
a Host-owned duplicate before gameplay checks. The status verifier reuses the existing
fail-closed build graph, including only the reviewed exact Compile removal.

This moves Trial's assembly identity. Recompile consumers; this is not a promise of
precompiled binary compatibility, Unity serialization/API/IL2CPP, engine execution,
Windows Player or save migration. [Execution](../../../evidence/portable-combat/RUN.json).

The earned-practice Room observes the live Trial's read-only Secured query; it owns
the optional session unlock outside this assembly's deterministic replay. Forecast
reconstruction therefore cannot award. No new passive arithmetic, class/level grant,
public replay/save format or world authority is added. Rebuild existing consumers
for the added query; this remains C#8/netstandard2.1 code, not Unity execution.
