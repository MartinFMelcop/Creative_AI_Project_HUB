# Avoidance is not the same observation as a counter opportunity

**Question/context:** Can P06's parry, directional dodge and a single seal be treated
as equivalent defensive options when designing a bounded character comparison?
The [combat-response instrument](../labs/combat-response/README.md) drives unchanged
Veilbreak 0.6.0 at 60 Hz, one stationary phase-one sweep, 28 cases repeated twice.
See its [inputs](../labs/combat-response/scenarios.json),
[outcomes](../evidence/combat-response/results.json) and
[execution record](../evidence/combat-response/RUN.json) before applying the finding.

**Observed positive result:** a near parry 5/8 ticks before contact prevents sweep
damage and permits the fixed early blade counter for 24 damage. Outward dodges at
all five tested leads also prevent damage but end outside blade range. Early dodge
commitment rejects the common blade request. At 110px a parry succeeds while the
103px blade misses: successful defense does not imply a reachable reward.

**Observed negative controls:** no-resolve defenses are rejected; 111px guard fails;
a single seal does not interrupt this sweep; an imposed overlapping echo still hurts
after a successful parry. These refute general protection or equivalence of all
responses within these cases. They do not prove that one option dominates all play.

**Interpretation/practical consequence:** an instrument for recognizable action needs
to expose accepted/rejected commands, commitment, position, resource cost and reachable
consequence alongside survival. A damage-only summary would hide the positional and
temporal trade-off. Future character experiments should measure whether intended
rewards remain accessible after a valid response, rather than changing class labels
or adding attributes to indistinguishable actions.

**Validity limit:** this is a fixed early-counter probe, not the best policy for each
response or a full timing sweep. It excludes player perception, delayed counter choice,
other attacks/phases, networking, physical input, readability and listening. Repeated
traces are not independent participants. Class identity/fun/learning remain untested;
Virgo Diamond has no destination consumer. CRE-001/012/084 motivates the question,
not its empirical proof; ENG-004/015 and SCI-005/017/051 bound the inference.

**Revisit when:** a real character consumer, other threat, timing rate, movement policy
or external observation changes the envelope. Preserve the current trace as a scoped
reference, not a universal combat rule or automatically approved creative decision.
