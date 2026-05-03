---
name: code-review
description: Review a github pull request / gitlab merge request. Use when user asks to review a PR or provides a PR link, or says "code review", "review this PR", "review this MR".
---

# Code Review

Review a pull request (github) or a merge request (gitlab) locally. Never post comments unless explicitly asked. Present findings in chat.

## Inputs

- URL (required). If missing, ask. Don't guess.
- Current working dir: if it's the same repo, use a git worktree (keeps your working tree untouched). Otherwise `git clone` into `mktemp -d`.

Record the workspace path (worktree or clone). Reuse it for every step. Cleanup at the end uses this path.

## Tooling

- GitHub: `gh` (`gh pr view`, `gh pr diff`, `gh pr checkout`)
- GitLab: `glab` (`glab mr view`, `glab mr diff`, `glab mr checkout`)
- Never use WebFetch for the PR — auth + token cost.

### Existing comments

Before reviewing, fetch existing comments to avoid duplicating prior feedback and to pick up unresolved threads.

- GitHub:
  - PR-level: `gh pr view <N> --comments`
  - Inline review comments: `gh api repos/:owner/:repo/pulls/<N>/comments`
  - Review summaries: `gh api repos/:owner/:repo/pulls/<N>/reviews`
- GitLab:
  - `glab mr view <N> --comments`
  - Threaded discussions: `glab api projects/:id/merge_requests/<N>/discussions`

Skim them. Note: open threads, prior reviewer concerns, points the author already pushed back on. Don't re-raise issues already settled. If a prior comment raised something still unaddressed, surface it (credit the original commenter).

## Workflow

### 1. Checkout

Goal: an isolated working copy of the PR branch that does not disturb the user's current branch.

- **Inside the target repo** — use a worktree. `gh pr checkout` / `glab mr checkout` switch the *current* branch and are not isolated; don't use them here.
  - GitHub: `git fetch origin pull/<N>/head:pr-<N> && git worktree add <tmpdir> pr-<N>`
  - GitLab: `git fetch origin merge-requests/<N>/head:mr-<N> && git worktree add <tmpdir> mr-<N>`
- **Outside the target repo** — `git clone <url> <tmpdir>` (use `mktemp -d` for `<tmpdir>`), then `git -C <tmpdir> checkout <pr-branch>`. For PRs from forks, prefer `gh pr checkout <N>` inside the clone — it handles fork remotes.
- cd into `<tmpdir>` for exploration. Save the path for cleanup (§Cleanup).

### 2. Describe the PR

Read the diff (`gh pr diff` / `glab mr diff`) and explore changed files. Then write a description for a developer who wasn't the author and didn't see the design:

- What problem does it solve?
- High-level approach - **not** a function-by-function tour.
- Focus on: data model, data structures, API changes, DB schema/migrations.
- Skip cosmetic detail.

Present description. Ask user to confirm before moving on.

### 3. Find issues

Explore code added/changed in the PR and its interactions with the existing codebase. Don't audit unrelated code unless a clear bug intersects the PR.

Look for: bugs, code smells, performance issues, bad design decisions, missing edge cases, broken invariants.

Categorize:

- **blocker** — bugs, correctness, security, data loss
- **should fix** — design issues, maintainability, perf risks
- **nit** — style, naming, minor cleanup

### 4. Present issues one at a time

First message: total count + breakdown.
> Found N issues: X blockers, Y should, Z nit. Going through by importance.

Then one issue per turn, ordered by your subjective importance (must → should → nit, ranked within each):

```
Issue K/N [blocker|should|nit]: <short title>

File: path/to/file.ext:LINE  (or LINE-LINE for ranges)

Problem: <what is wrong and why it matters>

Proposed fix: <concrete suggestion>
```

Then ask: *Move to next issue, or discuss this one?*

### 5. Line numbers

**Line numbers must be correct.** Re-read the file in the worktree to verify before quoting. Wrong line numbers waste reviewer time. Use the post-PR line numbers (the state in the worktree), not diff hunk offsets.

### 6. Solution sanity check

When proposing a fix, mentally implement it. If the fix is awkward or reveals the issue isn't real, drop or downgrade the issue before presenting.

### 7. Final summary (ask)

After all issues discussed, ask: *Want a markdown summary of the review?*

If yes, write the summary to `<tmpdir>/review-summary.md` (the workspace path from §1). Use the Write tool — don't just print it in chat, since §8 reads it from disk. Since the code has already been discussed, comments can be terser than the in-chat presentation — but:

- Include a code example when flagging a bug (snippet showing the problem).
- Include a concrete fix suggestion when available (diff, snippet, or precise instruction).
- Keep file:line references.
- Group by category (blocker → should → nit).
- Skip issues the user dismissed during discussion.

Format per comment:

```
### [blocker|should|nit] <title>
`path/to/file.ext:LINE`

<short problem statement>

<example or fix snippet, if applicable>
```

### 8. Submit (ask)

**Preconditions**: step 7 wrote `<tmpdir>/review-summary.md` AND the user explicitly approved it. If either is missing, do not offer to submit — go back and produce/revise the summary first.

Ask: *Submit the approved summary to the PR?*

If yes (run from `<tmpdir>`):

- GitHub: `gh pr review <N> --comment -F review-summary.md`. For inline per-line comments, use `gh api repos/:owner/:repo/pulls/<N>/comments`.
- GitLab: `glab mr note <N> -m "$(cat review-summary.md)"`. For inline, use `glab api projects/:id/merge_requests/<N>/discussions`.

Default to a single review/note unless user wants inline. Do not approve or request changes — comment only, unless user explicitly asks.

## Cleanup

When user signals done, ask before removing. Show the exact command first:

- Worktree: `git worktree remove <tmpdir>` (run from the original repo). Add `--force` only if the user agrees.
- Temp clone: `rm -rf <tmpdir>` — confirm the path looks like `/tmp/...` from `mktemp -d` before running.

If user declines, leave it; mention the path so they can clean up later.

## Don'ts

- Don't post comments to the PR/MR.
- Don't approve/merge.
- Don't audit the whole codebase — stay scoped to the PR.
- Don't dump all issues at once.
