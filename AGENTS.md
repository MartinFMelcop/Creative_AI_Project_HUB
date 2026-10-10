# Agent Instructions — Creative AI Project HUB

These instructions apply at the repository root. Read them before making changes.

## Project entry point

The current portfolio seed was imported inside a versioned wrapper. Its actual working directory is:
`martin-creative-ai-lab-v0.2.0/martin-creative-ai-lab/`

Read that directory's `AGENTS.md`, `SEED.md`, and `docs/STATE.md` before developing. Do not mistake the root-level README for the entire project. Keep existing user changes and historic source snapshots intact.

## Git baseline and safety

Before modifying files, inspect `git status --short --branch`, `git branch -vv`, `git remote -v`, and the current HEAD. Distinguish checked-out files, local uncommitted changes, local commits, and changes actually published on GitHub. Never claim a push or PR succeeded without verifying its remote reference.

Do not force-push, delete branches, rewrite remote history, discard uncommitted changes, or commit secrets. Do not change project content just to work around a Git transport failure.

## Publishing and authorization

A user request to inspect, implement, or prepare commit text alone does **not** authorize publishing. If the current task explicitly instructs you to publish or push the completed changes to `MartinFMelcop/Creative_AI_Project_HUB`, that instruction **does** authorize a normal non-force publication of those verified changes to the requested branch, subject to the environment's real permissions and safety checks. Prefer a feature branch and pull request if no destination branch is specified; do not automatically push to `main`.

Publish via a supported authenticated GitHub integration or the task's built-in Publish Changes / Create PR capability. Only use `git push` if the task checkout has a working, authorized Git transport. If the environment has no `origin`, credentials, network path, or publishing capability, do not repeatedly retry or claim success. Keep the changes and commit safe in the current task, report the exact error and the local commit SHA, and explain the supported recovery route. Never place personal access tokens in files, commands, or chat.

A plain commit title/description is an output artifact, not evidence that any remote operation occurred.

## Closeout

After an authorized publish, report the remote branch, commit SHA, GitHub URL, checks run, and outstanding limitations. When publishing is blocked, clearly report **not published**. Maintain the nested project's `docs/STATE.md` and other relevant continuity records for substantive changes.
