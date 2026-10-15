---
name: work-on-issue
description: >-
  Implements a GitHub issue on its own branch, commits there, and opens a
  pull request. Always fetch and branch from the latest origin/main before
  creating that branch. Before every commit, run the full CI check set and
  do not commit or push while anything fails. Use when the user asks to work
  on, implement, fix, or build a GitHub issue. Do not use for only reading
  or triaging an issue.
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

1. Fetch the latest `origin/main`, then create the new branch from that ref — not from a local `main` or another feature branch:

   ```
   git fetch origin main
   git switch -c issue/<number>-<short-slug> origin/main
   ```

   If that branch or an open pull request for the issue already exists, continue it instead of creating a new one.
2. Commit only on that branch, and only after **Checks before every commit** passes. Reference the issue the way **github-backlog** requires (`(#N)` or `Refs #N`, and the repository close policy). Several commits on one branch are fine; run that full check set again before each one.
3. Push the branch and open one pull request. After the push, wait until the push/pull-request CI workflow on that branch is green. If it fails, fix the failure, re-run the full local check set, commit, and push again. The pull request body must contain this line on its own, which is what GitHub uses to link the issue (`closingIssuesReferences`):

   ```
   Closes #<number>
   ```

   `Closes #<number>` also closes the issue when the pull request merges. Commit messages stay as in step 2.

   After `gh pr create`, confirm `gh pr view <pr> --json closingIssuesReferences` includes that issue number. If it is missing, `gh pr edit` the body to add the line and check again.

4. If the change is visible in the UI, attach a screenshot of that screen in the pull request description. Skip this when there is nothing to show, a screenshot cannot be captured, or `gh` has no `--attach` flag (added in 2.99.0). Do not block the pull request on a screenshot, and do not commit the image.

   Put the image in the body before the `Closes #<number>` line, and upload it with the same `gh` command:

   ```
   gh pr create --body-file body.md --attach './screenshot.png#What changed on screen'
   ```

   In `body.md`, reference the same path so `gh` rewrites it to the uploaded URL: `![What changed on screen](./screenshot.png)`. If the pull request already exists, use `gh pr edit <pr> --attach './screenshot.png#What changed on screen'`. Keep `Closes #<number>` on its own line after the image.

## Checks before every commit

Before each commit, run every check that push and pull-request CI runs. Do not commit, push, or open a pull request while any of them fail.

1. Read `.github/workflows/ci.yml`. Ignore workflows that run only on `workflow_dispatch`.
2. From the repo root, run `make check`.
3. Also run every CI command that `make check` does not already cover, with the environment variables that workflow sets. That includes the frontend production build and Serverless config validation, plus any extra step the workflow lists (for example mobile lint).
4. If anything fails, fix it and run the full set again. A partial re-run is not enough.
5. Do not skip git hooks. If a hook fails, fix it and run the full set again before a new commit.

## Scope

Issue body, labels, and dependency wording stay with **github-backlog**. Planning and review pauses stay with **plan-and-incremental-build**. This skill adds the git steps, the checks before every commit, and the blocked-issue stop.
