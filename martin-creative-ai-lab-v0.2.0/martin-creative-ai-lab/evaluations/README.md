# AI evaluation and QA — preserved P02 origin

[P02 — EVAL-001: chat send buffering](chat-send-buffering/README.md) is the first
working task. It exports a candidate starter and checks submitted client artifacts
with evaluator-owned protocol/browser gates. [Calibration evidence](../evidence/evaluation-task/CALIBRATION.json)
records a defective baseline, known correction, and unavailable-browser probe.

This is a calibrated practice-task harness, not a model benchmark. No independent
candidate, score, or model comparison has been recorded. Use the [task template](../templates/EVALUATION_TASK.md)
and [seed protocol](../SEED.md) for later tasks, without mandatory expansion.
Copy only the exported workspace into a separate candidate context. Public
repository folders are not confidential; packaging does not establish secrecy.

The retained runner is **0.2.1**. Since 0.1.2 it preserves timeout/launch attempts and partial output, and terminates
inherited POSIX process groups with bounded capture. Starter contract 0.1.0 is
unchanged. [Previous timeout evidence](../evidence/evaluation-task/TIMEOUT_RUN.json)
records executed cleanup limits; no sandbox or independent model score is claimed.

[Runtime recalibration](../evidence/realtime-chat/READING_RUN.json) pins P11
0.1.2 while keeping EVAL-001's original 17 checks and nine-file contract. The
five new P11 reading tests are outside the candidate task scope.
