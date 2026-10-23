# Status/formula source assay

This extends the Combat & Responsiveness destination through the preserved Rave
Master combat sources and a separately authored portable C# consumer. It does not
replace the existing Veilbreak/P06 method or transfer historical fiction.

## Reproduce

Build `north-star/combat-study/Checks/NorthStar.CombatChecks.csproj` in Release configuration using the
repository-pinned SDK (from `north-star/csharp` so its global.json applies), then:

```sh
python3 labs/combat-response/status/test_instrument.py
python3 labs/combat-response/status/run.py --output /absolute/evidence/directory --dotnet /absolute/path/to/dotnet
```

The caller owns an evidence directory strictly outside the maintained workspace.
`--configuration Release` is the default; `--configuration Debug` or `--consumer
/absolute/consumer.dll` selects another prebuilt artifact explicitly. `--dotnet`
accepts an absolute executable or a name resolved through PATH. Both child
processes have a 60-second timeout. The instrument verifies all fifteen locked
source payloads before staging and after execution. Copied vectors and the runner
are hash-checked against the lock before execution and again afterwards. Both
result streams must preserve the complete ordered (component, TestID) identity
and numeric expected value of every source row; passing totals alone are insufficient.
Actual/Got values are independently compared against finite source expectations:
probabilities within 1e-6, RAW within 1e-5, and integer components exactly. It copies nine complete CSVs
and the reviewed historical Python runner into that directory, executes that
surrogate there, checks all 49 results, and sends the same rows to the actual C#
`Checks --vectors INPUT OUTPUT` consumer. It rejects missing/changed sources rather
than inheriting the runner's permissive behavior of skipping absent CSVs. Reports,
logs, staged inputs and JSON remain outside protected source. No Ruby or RMXP
execution is claimed. Reproduction requires an already built C# consumer.

## Observed result and retained limits

2026-10-23: nine components, 49/49 historical Python surrogate vectors and 49/49
actual C# vectors passed. Seventeen instrument regressions passed: exact intake,
missing vector, changed vector, changed runner, DEV/DIST identity, false invalid
ratio equivalence, surrogate rounding/discrepancy, workspace output rejection, external output acceptance,
configuration selection, executable resolution, staged-byte tampering, 49 duplicated
passing identities, altered reported expectations, fabricated actual values in both
formats, nonfinite values, and component-specific numeric tolerances. Initial lock construction
used an incorrect guessed DIST path and failed before creating the lock; file
inventory resolved the actual `RM_DIST/RMXP_BASE/ScriptsCustom/` variant. Initial
regressions exposed unclosed intake handles; context managers corrected them.
These are instrument corrections, not changed protected source or repaired vectors.

The Python runner says it is aligned with Ruby, but its `safe_ratio(n,d)` returns
zero only when d==0. Ruby instead replaces every d<=0 with 0.000001. Static
transcription for ACC=10/EVA=-10 therefore yields .95 versus the executed Python
surrogate's .05. Destination valid-domain policy rejects negative EVA. This
negative is preserved separately from the 49 valid vectors: passing them does not
prove universal runtime equivalence. Ruby half-away-from-zero rounding is another
explicit binding, rather than C# default banker's rounding. The Python runner's
FINAL_DAMAGE first rounds mitigation and then rounds Defender; it does not
implement the full damage-ID/resistance/critical pipeline described by the rules.

## Intake disposition

- **INTEGRATED, bounded:** the nine QA formula components (HIT, CRIT, RAW, MIT,
  APPLY, DUR, DOT, REAPPLY, FINAL_DAMAGE) as explicit typed C# functions with the
  above valid-domain and rounding boundaries. The CSV is an oracle input, not
  dynamically executed formula text.
- **REJECTED, direct equivalence claim:** complete interchangeability of the
  Python surrogate and Ruby helper on invalid ratios. The retained discrepancy is
  evidence, not an unexplained failing destination vector.
- **UNRESOLVED:** full Ruby/RMXP battle integration, historical runtime execution,
  initiative/formation/downstate/reaction systems, complete catalog effects and
  human experience. The Ruby helper has no status container or complete battle
  loop. A new C# owner implements selected global-round behavior; it is authored
  destination code, not recovered historical runtime.

DEV and DIST Ruby helper bytes are identical (see source-lock.json). The helper
mentions `Data/RM_CSV/COMBAT_FORMULAS.csv` but does not read it; embedded DEFAULTS
actually determine formulas. STATUS_EFFECTS and REGRAS_DE_COMBATE provide status
requirements beyond those helpers: DOT at global round end, duration addition
without magnitude stacking, bleed's healing reduction, burn's attack reduction,
disarm, and Defender applying only to direct damage. Integration claims for these
requirements must be backed by the new C# owner and consumer checks, not by this
formula vector run alone.

Cinderwatch remains a preserved incompatible authored consumer: its scorch ticks
at an individual turn start with fixed two damage and a shield interaction. Neither
that policy nor Crossing's beat timing is silently relabeled as global-round
legacy behavior. This assay is not a new human, device, Unity, Windows or Steam
assessment, and does not establish balance or enjoyment.
