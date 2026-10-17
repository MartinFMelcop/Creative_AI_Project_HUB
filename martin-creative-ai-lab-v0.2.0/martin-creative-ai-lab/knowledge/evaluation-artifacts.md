# Calibrate the checker before evaluating an author

## Context and use

**Question:** Can a checker distinguish a known artifact defect from missing or
failed execution? **Origins:** P02 EVAL-001 and P11's reproduced send-buffering
defects. The records below pin the task, runner, inputs and environment for each
claim; these are instrument findings, not measurements of an AI model.

| Observation / outcome | Interpretation and practical consequence | Validity boundary |
|---|---|---|
| Positive calibration: the known defective client scores 15/17 and the recorded correction 17/17; missing-browser execution is inconclusive. | Calibrate against known inputs before using acceptance to judge a submitted artifact. | Seventeen original send-policy checks and their pinned inputs; no independent candidate attempt or model score. |
| Negative: the earlier runner lost timeout evidence. Positive: the correction retains attempted commands, partial streams and deadline classification. | Keep failed and incomplete runs auditable; a late summary must not hide expiry. | Recorded Python 3.12 POSIX process-group policy; escaped sessions and untested platforms are outside it. |
| Inconclusive causal hypothesis: the original delayed-return hypothesis was not reproduced. | Retain the non-reproduction rather than presenting the proposed mechanism as established. | Declared timeout probe and environment only. |
| Negative: runtime options or a missing preload can fail before parsing the candidate. Positive: parser attribution probes distinguish those failures from candidate syntax. | Require diagnostics identifying the candidate; preserve unknown or signal exits as inconclusive. | Recorded Node probes and runner formats; not protection against a malicious runtime. |

**Consumers:** TR-009 validates the task/checker adaptation in P02. Broader
laboratory, P09 and Virgo Diamond uses need their own consumers and execution
evidence. The following sections retain the original reasoning and source links.

## Acceptance is not model evaluation

P02 consumes P11's two reproduced send-buffering regressions through
[EVAL-001](../evaluations/chat-send-buffering/README.md). Its exported starter
contains only the original app files, brief, and hashes; the evaluator retains
the browser/protocol suite and loads only submitted client bytes. This is a
verified adaptation into a second project, not a shared application framework.

[Calibration](../evidence/evaluation-task/CALIBRATION.json) rejects the recorded
defective client at 15/17 and accepts the existing correction at 17/17. A missing
browser returns inconclusive, not a rejected author or a successful zero-test run.
Support-file changes are rejected before behavior execution. Pinning source and
suite hashes makes later evaluator changes visible and requires recalibration.

Acceptance describes one artifact against these gates. Calibration establishes
the checker can distinguish known inputs. Neither alone measures a model's
ability, records an independent attempt, or justifies a numeric performance score.
Record candidate identity, available tools, context, source exposure, attempts and
cost separately; absent information stays absent.

Allowlisting an export prevents accidental inclusion of reference/tests/evidence
in that bundle. It does not restrict the recipient's access to public source or
create isolation on the same machine. Copy only the export into a controlled
candidate environment for a future independent run. This public practice task
cannot establish private-test confidentiality or absence of training exposure.

TR-009 is validated only for task adaptation/calibration. Any broader protocol
reuse in P09 or another project remains a candidate until that destination uses
and verifies it. No model training, new transfer record, or shared component is
implied by storing these files together.

## Keep failed execution evidence

P02 runner 0.1.1 [corrects actual timeout-record loss](../evidence/evaluation-task/TIMEOUT_RUN.json).
Capture the attempted command and partial streams before classifying incomplete
execution. Keep the deadline, elapsed time, real exit/launch state and capture
completeness; a late passing summary cannot override expiry. Process-group cleanup
controls inherited children, not escaped sessions or untrusted execution. The
detached-pipe test deliberately demonstrates that boundary and stops its own child.
The original delayed-return hypothesis was not reproduced on Python 3.12 POSIX.

Separate runner version from unchanged task contract so a repair does not reject
old exports. Candidate reuse of this command-recording lesson in P09 or another
consumer remains unverified; no new shared component or transfer is promoted.

## Attribute parser failures before rejecting artifacts

[Real Node probes](../evidence/evaluation-task/SYNTAX_RUN.json) show that runtime
options and missing preloads can fail a syntax command without parsing the client.
P02 runner 0.1.3 requires complete parser diagnostics identifying its temporary
client, rather than treating any nonzero exit as invalid candidate syntax. A
preload SyntaxError identifies a different file; signal exits and unknown formats
remain inconclusive. This is a candidate lesson for other consumers, not a new
validated transfer or defense against a malicious runtime.
