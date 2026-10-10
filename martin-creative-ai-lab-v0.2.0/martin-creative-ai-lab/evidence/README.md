# Execution evidence

- [P02 timeout correction](evaluation-task/TIMEOUT_RUN.json): recorded-runner
  failures, partial diagnostics, cleanup boundaries and compatible artifact checks.
- [P02 EVAL-001 original calibration](evaluation-task/CALIBRATION.json): exact starter,
  export boundaries, runner tests, baseline/reference checks with complete output,
  unavailable-browser probe, and exported CLI smoke. No independent model attempt.
- [P11 transport correction](realtime-chat/POLLING_SEND_RUN.json): prior two
  baseline regressions and 17 protocol/browser checks, preserved unchanged.
- [P11 original adaptation](realtime-chat/RUN.json): historical source identity,
  reproduced browser failure, corrected interaction, command outcomes and hashes.
- [v0.2.0 recovery runs](legacy-audit/RUNS.json): historical offline combat/dialogue
  checks and syntax inspection; not rerun in this iteration.

Evidence supports bounded claims. Accepted reference artifacts are calibration
inputs, not candidate/model scores. Automated browser checks are not human review.
