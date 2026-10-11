# Lab state

**Updated:** 2026-10-11 (environment UTC date). **Seed version:** 0.4.6, unchanged.
**Current increment:** P10 Waystone dialogue 0.1.1, trust consequences.
P02 runner 0.2.0, P11 app 0.1.3 and starter contract 0.1.0 remain unchanged.

The checkout began clean at published
`73bf8ee235d1f2ba235a17e99dc12d1b810c71eb`; fetch/merge confirmed the same main.
Actual 0.1.0 execution grants passage after lie/help/agreement with apology still
unresolved. Three lie/apology cycles raise trust from 45 to 63. Choose this
bounded correction before expanding the existing scene or inventing human review.

[The Last Waystone](../projects/waystone-dialogue/README.md) now remembers trust
when the first unresolved lie opens. Additional lies keep that ceiling, including
after an outburst. Apology recovers up to +6 without exceeding it, then clears the
obligation/ceiling. Cooperation requires no unresolved lie. A new scene response
asks the player to correct the false order; refusal takes a turn and can reach
dusk. Traces distinguish scene responses from the nine retained legacy records.
ADR-018 records the new rules, retained catalog deltas and effective recovery.

[Trust evidence](../evidence/waystone-dialogue/TRUST_RUN.json) records source/test
hashes, environment, actual commands and old/new CLI decisions. Four regression
methods fail on committed 0.1.0, with five failures including two trust subtests;
all 23 current behavior/CLI/source checks pass. The truthful cooperation path,
other endings, cooldown, restart, invalid-input and source checks remain covered.
Registry/link/archive validation and 11 validator regressions pass; the final
manifest is refreshed. [Initial 0.1.0 evidence](../evidence/waystone-dialogue/RUN.json)
stays historical. P02/P11 and the old scenario runner were not rerun.

P10 remains active at bounded CLI M4. The nine retained catalog records, archive
and source inventory are unchanged; the new refusal and trust ceiling are explicit
scene rules. No dependency, engine, other project or shared consumer is added.
Human narrative quality, usability and balance remain unreviewed; only Linux
Python 3.12.14 is executed. Martin supplied direction; Codex implemented/tested.

Next: reader playthrough of truthful cooperation, lying and repaired dialogue,
then feedback on wording/pacing. Independent EVAL-001 provenance and Martin's
P11 review remain separate gates. Publish the verified correction via the
Workflow 2.0 fetch/merge/push sequence; this record precedes publication and the
final report supplies the matching remote SHA/URL.
