---
name: work-on-issue
description: >-
  Implements a GitHub issue on its own branch, commits there, and opens a
  pull request. Use when the user asks to work on, implement, fix, or build
  a GitHub issue. Do not use for only reading or triaging an issue.
---

# Work on an issue

When the user asks to work on, implement, fix, or build a GitHub issue, follow this skill in the repository that owns the issue.

## Blocked issues

Never work on a blocked issue unless specifically instructed.

An issue is blocked when either of these is true:

- GitHub **blocked by** lists an issue that is still open
- The body contains `Depends on #N` and `#N` is still open

That is the same meaning as the personal **github-backlog** skill. Check it before creating a branch or editing code.

If the issue is blocked and the user did not explicitly say to proceed anyway, stop and name the blocking issue. Do not create a branch, commit, or open a pull request.

"Specifically instructed" means the user names that issue and says to work on it despite the block.

## Delivery

Asking to work on an issue authorizes a branch, commits on that branch, a push, and a pull request. Do not commit on the default branch.

1. Branch from the default branch: `issue/<number>-<short-slug>`. If that branch or an open pull request for the issue already exists, continue it.
2. Commit only on that branch. Reference the issue the way **github-backlog** requires (`(#N)` or `Refs #N`, and the repository close policy). Several commits on one branch are fine.
3. Push the branch and open one pull request linked to the issue.

## Scope

Issue body, labels, and dependency wording stay with **github-backlog**. Planning and review pauses stay with **plan-and-incremental-build**. This skill only adds the git steps and the blocked-issue stop.
