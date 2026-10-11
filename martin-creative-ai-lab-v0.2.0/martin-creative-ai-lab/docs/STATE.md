# Lab state

**Updated:** 2026-10-11. **Seed version:** 0.4.2.
**Primary workstream:** P11 0.1.2, preserve reading position during live updates.
**Auxiliary:** P02 runner 0.1.2 runtime recalibration; EVAL-001 contract stays 0.1.0.
The enclosing directory keeps its original v0.2.0 package name.

## What changed

The checkout began clean on `work` at published commit
`786678549e586dc35ce82985bf6014b4d24e64d3`; remote main matched. Previous chat,
evaluation, root instructions and publication commits remain preserved.

P11 always scrolled to the end of each broadcast, interrupting earlier-text
reading. Five real Chromium/Socket.IO checks reproduce three disruptions on the
recorded 0.1.1 client. [P11 0.1.2](../projects/realtime-integration-lab/README.md)
follows within 24 CSS pixels of the bottom; otherwise it preserves the visible
message and pixel offset. Scrolling back down resumes following. A surviving
anchor stays stable during variable-height eviction; an evicted anchor falls
back to the earliest retained text. The 200-message cap is unchanged.

An initial correction accumulated 4.0625 pixels of drift after ten evictions.
Carrying fractional scroll correction resolved that failure without relaxing
the one-pixel criterion. Server, markup/style, original 17 tests, send policy,
dependency resolutions and historical material are unchanged.

P11 is committed at `2aed760251bb8d1544e906606cd954ed80f1df2f` and included
in the verified published increment [f35e2e7](https://github.com/MartinFMelcop/Creative_AI_Project_HUB/commit/f35e2e767f215040e9e300eb0ee480fa2fc082d5).
Package metadata changed to 0.1.2, so P02's old pin correctly returned inconclusive.
Runner 0.1.2 now pins that tested revision. Its 17 send-policy checks exclude the
five new reading checks; starter contract, brief and all nine exports stay
byte-identical. See [the evaluator](../evaluations/chat-send-buffering/README.md).
The current task explicitly authorized normal publication to origin/main.
The push succeeded and remote main matched the full development SHA above;
prior development records retain their original point-in-time status.

## Verification and evidence

[Current record](../evidence/realtime-chat/READING_RUN.json) contains source
identities, raw before/after output, the intermediate drift failure, full chat
results, frozen installation and P02 compatibility checks.

- Recorded 0.1.1 client: 5 reading checks, 2 pass and 3 expected failures.
- Corrected client: 5 reading checks pass; full suite passes 22 tests (6 protocol,
  16 Chromium), with no failures, skips or uncaught browser errors.
- Frozen installation passes; all dependency resolutions/integrity entries match
  the prior lockfile. Only root package version metadata differs in the lockfile.
- P02's 15 runner regressions pass. Original-contract baseline rejects at 15/17
  with exactly the two send-policy failures; new P11 reference accepts at 17/17.
  These are controlled calibration artifacts, not independent model candidates.
- Documentary validation passes: 11 projects, 11 transfers, 0 assets, 2 legacy
  sources and 99 local links. All three validator regressions, preserved source
  bytes/commits and whitespace checks pass. Final integrity is recorded at closure.

Environment: Python 3.12.14, Node 24.19.0, npm 11.9.0, Chromium 154.0.8037.57,
Playwright Core 1.64.0 and Socket.IO 4.8.4 in the Linux cloud container. New reading
checks use a 1280×800 viewport and variable-height text. Tests start/close their
own servers; standalone CLI startup was not rerun. Existing setup suffices.

## Limits, learning and next action

Automated geometry is not Martin's usability review or other-browser/zoom/resize
coverage. Evicted text cannot be recovered. The heartbeat check is predicate
injection; polling uses actual HTTP. P02's public reference is discoverable;
process cleanup is not a sandbox and non-POSIX cleanup remains untested. No
independent candidate, model score, game runtime or creative/media master is claimed.

Pixel anchoring and rounding are candidate lessons for other interfaces; no
destination adaptation, shared component or new transfer promotion occurred.
TR-009 remains validated only for P02 task adaptation/calibration. Martin supplied
direction; Codex implemented, tested and documented this increment.

Next: Martin's two-tab review of reading, resuming live following, keyboard use
and uncertain-delivery wording; separately produce one independent EVAL-001
client with explicit identity/context/tools/attempts and raw evaluator evidence.
Do not grow task inventory before completing that evidence gate.

## Publication verification — 2026-10-11
+
+The verified increment contains P11 commit `2aed760` and P02/continuity commit
+`f35e2e7`. After implementation, tests, documentation and commit creation, the
+required fetch → merge → status → diff check → normal push → remote lookup
+sequence completed in order. Fetch observed the prior published base; merge
+reported "Already up to date." No conflicts, history rewriting or discarded files.
+Remote main and local HEAD both confirmed the full development SHA above.
+
+A documentation follow-up records that confirmation and refreshes integrity
+hashes. Implementation and raw execution records remain unchanged. Current
+publication can be rechecked with `git ls-remote origin refs/heads/main`; a later
+documentation tip still contains both verified development commits.
+