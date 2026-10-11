# Lab state

**Updated:** 2026-10-10 (client date). **Seed version:** 0.4.3.
**Current iteration:** registry reference validation.
P11 remains 0.1.2; P02 runner remains 0.1.2 and EVAL-001 contract remains 0.1.0.
The enclosing directory retains its original v0.2.0 package name.

## Change and assessment

The checkout began clean on `work` at `786678549e586dc35ce82985bf6014b4d24e64d3`.
GitHub inspection exposed newer remote work. The initial sandboxed fetch failed
to connect to proxy port 8080; approved execution fetched and fast-forwarded to
`b5c0cedef03a3d569931fb99c95b5232ff8371e9`, preserving the P11 reading fix,
P02 recalibration and publication records before this iteration's commit.

The lab's validator checked the type of project evidence lists but never checked
their targets. Missing evidence, invalid working directories and unknown source
IDs could pass. [The new gate](REGISTRY_VALIDATION.md) rejects invalid local
references across projects/transfers and optional asset evidence. It keeps empty
seed/candidate evidence valid, resolves containment including symlinks, and
requires evidence files and working directories of the correct kind. No new
dependency, schema version or shared framework was introduced.

## Verification

[Raw execution record](../evidence/registry-validation/RUN.json) identifies the
synchronized base, validator/registry/runtime hashes and captured command output.
The recorded validator fails all eight new regression methods; the current
validator passes all 11 methods, including the original dependency-document,
broken-Markdown and archive-integrity checks. P02's 15 runner tests and P11's
22 current checks pass with no skips. The initial sandboxed chat attempt failed
to bind localhost (`listen EPERM`); approved execution runs the real test servers
and Chromium. The pre-sync 17-test run passed separately; the evidence record
contains the post-sync current suite, including all five reading tests.

Environment: Linux cloud container, Python 3.12.14, Node 24.19.0, retained locked
dependencies, system Chromium. See raw suite output for counts. Documentary and
final manifest checks are completed at closure. Earlier calibration, transport,
reading, source and timeout records are preserved without relabeling them as new
runs. Project maturity and registry content are unchanged.

## Limits and next action

File existence is documentary integrity, not proof of evidence quality or project
behavior. Referenced report contents, Markdown anchors, human usability, other
browsers, game/media engines and independent model performance are outside this
increment. Martin supplied direction; Codex implemented and tested the change.

Next: Martin's two-tab reading/keyboard review and one independent EVAL-001 client
with recorded identity/context/tools/attempts. Do not grow task inventory before
that evidence gate. The seed's new version records this QA contract, not new
project maturity.

## Publication

The current request explicitly authorizes a normal push to `origin/main`.
This pre-publication record makes no claim about the pending commit. At closure,
fetch/merge/status/diff/push/remote lookup must run in order; compare remote main
with local HEAD before reporting success. The final task report provides the
verified SHA and GitHub URL. Prior published increments remain in Git history.
