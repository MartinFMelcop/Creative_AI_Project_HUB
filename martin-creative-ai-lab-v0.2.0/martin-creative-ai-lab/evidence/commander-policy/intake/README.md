# One-time CommanderSIM attachment verification

`archive-audit.json` is OBSERVED_SOURCE: ZIP CRCs, bounded paths/types, duplicate
refusal, every member identity, actual declared manifest/checksum matches and four
100-card lists with five fixed commander identities. The Abzan comparative list is
unchanged. Both exact supplied archives are retained in `../inputs/`; their embedded
research notices and limitations are preserved. No explicit general-purpose license
was found in the archives. User-directed research intake does not establish commercial
reuse rights for Magic names, card text, artwork or fiction. None enters North Star.

`execution.json` is RECORDED_EXECUTION: all inspected commands, exits and log identities.
Python3.12.14 and g++14.2.0 were actually used. Only a separate scratch copy was compiled
or executed. No network script, report builder, PowerShell installer or next-run prompt
was executed. The six-scenario producer writes a report, so it ran solely in the copy;
all38original engine members remained byte-identical afterwards. Its produced JSON is
retained and exactly equals the supplied six-scenario JSON.

Actual suite discovery passed64tests without skips. Its C++ smoke executed16surrogate
sessions twice and asserted byte-identical results (32episodes, not Commander games).
The original test deletes smoke raw JSON through TemporaryDirectory; this retention
limit is explicit. The standalone Palladia test FAILED with ModuleNotFoundError: its
bootstrap names a nonexistent `models/` directory. Suite discovery succeeds because
prior modules add `engine/` to the shared import path. Neither archive nor test was
silently repaired. This launch-order dependency is retained as a negative finding.

The transfer mechanical checker passed its32reference/10section/12concept checks and
missing-status mutant. It is not independent-reader G8 or research validation.
The new intake's11archive-boundary controls reject traversal, drive/backslash paths,
links, special files, duplicates, dot segments and malformed ZIPs. They never execute
archive members. Retain the post-command metadata collector's path error separately;
its already-written logs supported corrected metadata assembly without another suite run.

The supplied30,000surrogate episodes,15,000paired trials and six bounded fixtures were
checked against actual report structures/identities. They were not rerun at30,000scale.
No complete fully rules-verified Commander game is present or newly executed: zero.
Aggregate arithmetic and bounded fixture replay cannot validate full Magic mechanics,
causal card strength, balanced decks or human strategic diversity. The25%target remains
specific to that fixed-deck research, not a HUB gameplay requirement.

Reproduce static intake from the maintained workspace:

```bash
python labs/economy-simulation/commander-intake.py \
  --engine-archive evidence/commander-policy/inputs/CommanderSIM_v16_Motor_Refinado.zip \
  --transfer-archive evidence/commander-policy/inputs/Creative_HUB_CommanderSIM_Research_Transfer_v10.zip \
  --output /tmp/commander-intake.json
python -m unittest discover -s labs/economy-simulation -p test_commander_intake.py -v
```

For original-code reexecution, validate/extract into a fresh scratch tree, inspect it,
then use the exact commands in execution.json. Compiler output must remain scratch-only.
The raw `bounded-scenarios-reexecution.json` is source-case evidence, not original North
Star content or an additional experiment/participant.
