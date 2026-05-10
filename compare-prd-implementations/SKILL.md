---
name: compare-prd-implementations
description: Independently review two git branches or PRs that implement the same PRD, then cross-compare them. Produces a verifiable, scored, file:line-cited markdown report for research comparison of coding-assistant outputs. Use when the user wants to compare two implementations against a PRD, evaluate two coding harnesses on the same task, audit PR quality vs spec, or mentions "compare PRs", "compare branches", "PRD compliance review", or "coding harness comparison".
---

# Compare PRD Implementations

Compares two implementations (branches or PRs) of the same PRD. Produces a research-grade markdown report saved to the current working directory.

## Inputs

Three arguments:

1. PRD path — local markdown file
2. Implementation A — git branch ref OR GitHub PR URL
3. Implementation B — git branch ref OR GitHub PR URL

Auto-detect: if the argument starts with `https://github.com/` or matches `<owner>/<repo>#<num>`, treat as PR URL (use `gh`). Otherwise treat as git ref (use `git`).

## Setup

You need a working tree to verify line numbers and file contents — the diff alone is not enough.

- If the current working directory is the repo of both refs, work there.
- Otherwise, clone the repo into a sibling temp directory and `git fetch` both refs. Record the absolute path used for verification in the report header.
- Always check out each ref into a worktree (`git worktree add`) so file:line citations resolve against the head of each branch.
- **Remote detection**: run `git remote`. If exactly one remote, use it. If multiple, prefer `origin`; else use the first listed.
- **gh auth check**: if any input looks like a PR URL, run `gh auth status` first. If not authenticated, abort with: `gh not authenticated — run: gh auth login`. Do not attempt unauthenticated PR fetches.

## Workflow

Run independently for each implementation, **then** cross-compare. Do not let findings on A bleed into B's review.

### 1. Parse the PRD

- Read the PRD file in full.
- Extract an ordered list of requirements as `R1, R2, ...`. Each requirement = one testable obligation. Quote the source line(s).
- Capture explicit non-goals and constraints (e.g. "must not break X").
- Save the requirement table — every later finding must reference one of these IDs, or be tagged `OUT-OF-SCOPE`.

### 2. Resolve refs

- Branch ref: compute `git merge-base <ref> origin/main` (fallback `origin/master`); diff is `merge-base..ref`.
- PR URL: `gh pr view <url> --json headRefName,baseRefName,headRefOid,baseRefOid,number,title,url,headRepository,baseRepository` then use `gh pr diff <url>` plus a local checkout of `headRefOid` for line-accurate review. Diff base = `merge-base(headRefOid, baseRefOid)`.
- Record per implementation: PR/branch URL, head SHA (short + full), base SHA, file count, +/- lines. These go in the report header for traceability.

### 3. Independent review per implementation

For each implementation, in isolation, produce:

**a. Change inventory** — list every modified file with one-line purpose.

**b. PRD compliance matrix** — for each `Rn`: `Met | Partial | Missing | N/A` + file:line evidence + 1-sentence justification. Missing or Partial → finding.

**c. Findings** — bugs, race conditions, error-handling gaps, security issues, broken invariants, dead code, regressions, code quality issues. Each is tagged with one of two flat categories:

- `PRD-impact` — breaks, misses, or only partially meets a PRD requirement, or violates a stated non-goal.
- `Quality` — code health (readability, duplication, naming, test gaps, scope creep) with no PRD breach.

Format (IDs are `F-A-NNN` for Implementation A, `F-B-NNN` for B):

```
F-A-001  [PRD-impact]  <one-line title>
  Implementation: A
  Location: A: path/to/file.ts:42-58 @ <head-sha-short>
  Requirement: R3 (or OUT-OF-SCOPE for Quality findings)
  Observation: <what the code does>
  Why it's wrong: <reasoning, citing PRD line, invariant, or runtime behavior>
  Suggested fix: <concrete change>
```

**e. Score** — fill the rubric in `REFERENCE.md`. Each criterion 0–5 with a one-line justification. Report per-criterion only; no aggregate total.

### 4. Cross-comparison

After both reviews are complete:

- **Shared approach** — what both did the same way (data structures, control flow, file boundaries, dependencies). Cite both sides explicitly: `A: A/path:line @ <sha-A>` and `B: B/path:line @ <sha-B>`.
- **Divergences** — where they took different approaches; for each, state the trade-off with file:line refs prefixed `A:` and `B:`.
- **PRD coverage delta** — table of `Rn` × {A, B} with Met/Partial/Missing.
- **Defect delta** — count and list which findings are unique to A, unique to B, or shared.
- **Score table** — side-by-side rubric scores.

### 5. Overall summary and verdict

After the cross-comparison, write a top-level summary and an explicit verdict:

- **Summary** (≤ 6 sentences) — the headline differences in PRD compliance, correctness, and code quality. Reference finding IDs (`F-A-001`, `F-B-003`) and PRD requirement IDs (`R2`).
- **Verdict** — one of: `Implementation A is closer to merge-ready`, `Implementation B is closer to merge-ready`, or `Tie / both require comparable additional work`. Justify in 2–4 sentences citing finding IDs and the score table. The verdict is a recommendation, not a final judgment; the appendix gives the reader the SHAs and links to confirm.
- **Outstanding work** — bullet list, per implementation, of what must change for it to be merge-ready, each item linking to a finding ID.

### 6. Write the report

Filename: `<prd-slug>.md` in the current working directory. Slug is lowercase-hyphen, max 60 chars, derived from the PRD title (or PRD filename stem if no H1). Branch identifiers go in the YAML frontmatter, not the filename. If a file with that name already exists, append `-<YYYYMMDD>`.

**Do not artificially wrap lines in the markdown.** Let lines run naturally; the renderer wraps.

The report starts with a compact YAML frontmatter carrying the key references — PRD, both implementations with their authors, SHAs, and diff stats — so the reader can resolve the comparison at a glance:

```yaml
---
prd: <relative path>
prd_title: <first heading>
a:
  url: <branch or PR URL>
  by: <harness/author>
  head: <full sha>
  base: <full sha>
  diff: "<N files, +X / -Y>"
b:
  url: <branch or PR URL>
  by: <harness/author>
  head: <full sha>
  base: <full sha>
  diff: "<N files, +X / -Y>"
generated: <YYYY-MM-DD>
---
```

**Deriving `by`**:

- For a PR URL: `gh pr view <url> --json author --jq .author.login`.
- For a branch ref: `git log -1 --format='%an' <ref>`.
- If the user supplied harness names alongside the refs (e.g. `claude-sonnet=feature/foo`), use those instead.

Below the frontmatter, follow the body skeleton in `REFERENCE.md`. Working tree path goes in the appendix, not the frontmatter.

## Evidence rules (non-negotiable)

- Every claim cites `path:line` or `path:start-end`. No claim without a citation.
- Every citation is prefixed with the implementation it belongs to: `A:` or `B:`. Example: `A: src/server.ts:42-58 @ a1b2c3d`. The reader must never have to guess which branch a citation refers to.
- Every citation includes the head SHA (short) of that implementation so the reader can resolve the line on GitHub.
- Every PRD claim references an `Rn` ID.
- Quote at most 5 lines of source per citation.
- If a claim cannot be verified from the diff + working tree alone (e.g. depends on runtime data, external service), mark it `UNVERIFIED` and explain what would resolve it. Do not omit it.

## Process rules

- Review B without re-reading A's review notes. Open A's review only at step 4.
- In the per-implementation sections, do not compare to the other implementation. Comparisons live only in cross-compare and verdict.
- The verdict in step 5 must follow from the rubric scores and finding counts; do not introduce new claims there.

## See also

- [REFERENCE.md](REFERENCE.md) — severity rubric, scoring rubric, report skeleton
