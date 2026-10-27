# Selected passive contracts in actual play

This method investigates the real missing seam between one stored passive ID and an
applied behavior in [Treatment Line](../../../north-star/combat-study/README.md).
It does not infer a full effect engine from a catalogue or another eligibility screen.

```bash
python3 labs/combat-response/passives/assay.py --output /tmp/passive-source.json
python3 north-star/combat-study/tools/passive-verify.py --dotnet dotnet --output /tmp/passive-new-output
```

The source assay reads actual DEV/DIST passive tables (77rows/28columns), the single
PASSIVE_MAIN_1 rule and differing UI helpers. It retains exact selected prose and
source hashes. WARRIOR_PAS_005 describes10%physical reduction with heavy armor;
WARRIOR_PAS_007 describes fatal-hit→1HP once/combat. ROGUE_MALE_PAS_006 instead has a
20% chance; KNIGHT_PAS_001 instead requires no control effect. These alternatives stay
distinct and unresolved, not normalized into the selected mechanics.

Both UI helpers store one scalar selected ID. DEV displays the rule string; DIST
lacks that parser. The inspected assignment branch does not check context/eligibility
or execute/remove Efeito. Reject only treating that UI as a complete rule/effect
provider, not its one-ID representation or the whole source collection. No actual
Ruby/RGSS/RMXP scene was executed and no vulnerability of a full historical game is
claimed from this source reading.

The adapted portable library supplies one explicit slot, preparation-only configuration,
conditional Lining and once-per-encounter Last Thread. Source level/class/gender,
rarity/learning pools and armor catalogue are not implemented or granted. Mechanics
are openly available study presets. The native cutscene-context refusal does not claim
an actual cutscene consumer. DOT exclusion, direct-hit categories, Guard-before-passive
and integer rounding away from zero are declared destination policy because source
prose does not define those details.

Actual original practice holds two treatments, real pressure, attacks and DOT. Last
Thread can make a real chosen route survive at1HP; another route is rescued by direct
contact and then defeated by remaining DOT in the SAME round. Lining changes actual
20→18 contact and10→9 guarded contact only in the declared context. Damage reduced,
actual HP lost and counterfactual HP loss avoided remain distinct, including overkill.

The complete verifier reexecutes affected old43rules/46consumer/17Chromium/5HTTP and
SAME49source-vector checks because the assembly, owner and UI closure changed. These
are regressions, not new participants/studies/source credit. Original producer bytes
and existing historical evidence remain retained. The old source-vector method is
separate from the selected prose assay; do not claim the new effects ran in Ruby.

[Prospective acceptance](../../../evidence/passive-response/protocol.json) and
[execution](../../../evidence/passive-response/RUN.json) record actual controls, causal
None comparison, losing policies, source identities and renderer negatives. Software
and independent agent review do not establish recognition, balance, enjoyment, human
comprehension, final canon, commercial clearance or Unity/Windows/Steam delivery.
