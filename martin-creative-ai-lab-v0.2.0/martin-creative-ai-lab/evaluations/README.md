# AI evaluation and QA

[P02 — EVAL-001: chat send buffering](chat-send-buffering/README.md) is the first
working task. It exports a candidate starter and checks submitted client artifacts
with evaluator-owned protocol/browser gates. [Calibration evidence](../evidence/evaluation-task/CALIBRATION.json)
records a defective baseline, known correction, and unavailable-browser probe.

This is a calibrated practice-task harness, not a model benchmark. No independent
candidate, score, or model comparison has been recorded. Use the [task template](../templates/EVALUATION_TASK.md)
and [seed protocol](../SEED.md) for later tasks, without mandatory expansion.
Copy only the exported workspace into a separate candidate context. Public
repository folders are not confidential; packaging does not establish secrecy.

Runner 0.1.1 preserves timeout/launch attempts and partial output, and terminates
inherited POSIX process groups with bounded capture. Starter contract 0.1.0 is
unchanged. [Current correction evidence](../evidence/evaluation-task/TIMEOUT_RUN.json)
records executed cleanup limits; no sandbox or independent model score is claimed.
