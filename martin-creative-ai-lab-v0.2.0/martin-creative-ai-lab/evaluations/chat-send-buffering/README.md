# P02 — Chat send-buffering practice task

**Task:** EVAL-001. **Version:** 0.1.0. **Runtime:** Python orchestration and
Node/Socket.IO/Chromium behavior checks. This is P02's first working task, adapted
from P11; its earlier Unity proposal remains an origin, not a runtime requirement.

Repair one client send policy, covering polling congestion and stale-state
reconnect buffering. These are observed defects from P11 0.1.0, not invented
benchmark cases. [The candidate brief](BRIEF.md) states behavior without supplying
the correction. [P11](../../projects/realtime-integration-lab/README.md) retains
the application, locked dependencies, reference client, and evaluator-owned tests.

## Prepare and check

Requires Python 3.9+, Git with commits `66041e7` and `2d4e9a7` retained, Node 22+,
P11's locked dependencies installed, and compatible system Chromium. Use P11's
documented `npm ci` command if needed. No Unity, model API, token, or new npm
dependency is required. Run from the lab directory:

```bash
python3 evaluations/chat-send-buffering/test_runner.py
python3 evaluations/chat-send-buffering/run.py prepare /tmp/p02-candidate
```

The destination must not exist. Move only that exported directory to a separate
candidate machine/context. It contains seven starter app files from commit
`66041e7fdd7687ee21099f95129dff41933c74dd`, the brief, and a hash manifest. It has
no `.git`, tests, working reference, knowledge, evidence, or project README.
The candidate may install dependencies there; change only `public/client.js`.

Return the workspace to the evaluator, then run outside the candidate context:

```bash
python3 evaluations/chat-send-buffering/run.py check /tmp/p02-candidate --result /tmp/p02-result.json
```

The result must be a new file outside the submission. Existing workspaces and
result records are never overwritten. Exit codes: `0` accepted artifact,
`1` rejected artifact, `2` inconclusive execution or command/input error. Command
errors before execution print the error without manufacturing a run result.

The checker verifies immutable support files against Git, copies only the client
bytes to a temporary evaluator location, checks syntax, probes real browser
startup/dependencies, and runs the pinned 17 P11 checks (6 protocol, 11 browser).
Submitted `node_modules` is ignored, never imported by the evaluator. It removes
external URL/client override variables from the test environment. The submitted
client reaches both real browser pages through the existing test route; the
working application files are never replaced. Skipped, cancelled, missing,
incomplete, contradictory, or zero-test outcomes cannot be accepted. Changed
evaluator files require explicit recalibration.

Records contain the client hash, runner and evaluator hashes, source commits,
tool/browser versions, commands, complete captured output, test counts, and
failed check names. No model identity or score is inferred from an artifact.

## Calibration and limits

Calibration uses two controlled artifacts: the exported 0.1.0 client and P11's
already corrected 0.1.1 client. To prepare a reference probe, export a **second**
fresh directory, copy only P11's working `public/client.js` into it, and check it.
The baseline must reject with the polling and stale-state checks failing; the
reference must accept with all 17 passing. See [recorded calibration](../../evidence/evaluation-task/CALIBRATION.json).

These probes validate the harness and TR-009's bounded P11 → P02 adaptation.
They are not independent candidate attempts, a model comparison, a score, or
evidence of AI performance. Candidate identity, context, tools, attempts, timing,
and available cost must be recorded separately before a future candidate run.

The same Codex session designed the harness and applied existing reference/tests.
Export separation reduces accidental context inclusion; it is not filesystem
isolation, a security sandbox, or secrecy. Public source/history exposes the
answer to anyone who seeks it. An independent study needs controlled execution
and context provenance; this public practice task cannot supply confidentiality.
Heartbeat expiry is injected at a pinned predicate; polling uses real HTTP writes.
Neither proves production outage reliability, human usability, or Unity behavior.

Next: run one independently produced client with recorded context and permitted
tools. Keep raw artifact acceptance separate from any claim about its author.
