# Reference: scoring, report skeleton

## Scoring rubric

Each criterion scored 0–5 per implementation, with a one-line justification citing findings.

| Criterion | 0 | 5 |
|---|---|---|
| **PRD compliance** | Most requirements missing or wrong | Every `Rn` Met with evidence; non-goals respected |
| **Correctness** | Multiple BLOCKERs | No BLOCKER, no MAJOR with runtime impact |
| **Robustness** | Error paths absent or panic-prone | Error paths handled, invariants documented or enforced |
| **Code quality** | Pervasive duplication, dead code, unclear naming | Tight, well-named, idiomatic for the codebase |
| **Test coverage of changes** | No tests for new behavior | New behavior tested at appropriate level (unit/integration) |
| **Scope discipline** | Large unrelated changes; refactors beyond PRD | Changes confined to what the PRD requires |
| **Diff hygiene** | Mixed concerns per commit, no useful messages | Logical commits, messages explain why |

Report per-criterion only. Do not sum or average.

## Report skeleton

````markdown
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

# <PRD title> — implementation comparison

> Citations are prefixed `A:` or `B:` with short SHA so the reader can resolve them at the URLs in the frontmatter.

## Overall summary

<≤ 6 sentences. Headline differences in PRD compliance, correctness, code quality. Cite finding IDs (F-A-NNN / F-B-NNN) and PRD requirement IDs (Rn).>

## Verdict

**<Implementation A is closer to merge-ready | Implementation B is closer to merge-ready | Tie / both require comparable additional work>**

<2–4 sentences justifying the verdict by referring to the score table, defect delta, and specific finding IDs. The verdict follows from the rubric and finding counts; no new claims are introduced here.>

### Outstanding work to be merge-ready

**Implementation A**:
- <item> — see `F-A-001`
- <item> — see `F-A-003`

**Implementation B**:
- <item> — see `F-B-002`

---

## PRD requirements

| ID | Requirement | Source line(s) |
|---|---|---|
| R1 | <text> | `prd.md:12-14` |
| R2 | <text> | `prd.md:18` |

**Non-goals / constraints**:
- N1: <text> (`prd.md:30`)

---

## Review — Implementation A

URL: <link to branch/PR>
Head SHA: `<short>`

### Change inventory
- `A: path/to/file.ts` — <one-line purpose>

### PRD compliance matrix
| Req | Status | Evidence | Notes |
|---|---|---|---|
| R1 | Met | `A: path:42-58 @ <sha-A>` | <1 sentence> |
| R2 | Missing | — | <1 sentence> |

### Findings

```
F-A-001  [PRD-impact]  <title>
  Implementation: A
  Location: A: path:42-58 @ <sha-A>
  Requirement: R3
  Observation: ...
  Why it's wrong: ...
  Suggested fix: ...
```

```
F-A-004  [Quality]  <title>
  Implementation: A
  Location: A: path:80-95 @ <sha-A>
  Requirement: OUT-OF-SCOPE
  Observation: ...
  Why it's wrong: ...
  Suggested fix: ...
```

### Score (Implementation A)
| Criterion | Score | Justification |
|---|---|---|
| PRD compliance | 3 | R2, R5 Missing (F-A-002, F-A-005) |
| Correctness | 2 | F-A-001 breaks R3 |
| Robustness | ... | ... |
| Code quality | ... | ... |
| Test coverage | ... | ... |
| Scope discipline | ... | ... |
| Diff hygiene | ... | ... |

---

## Review — Implementation B

URL: <link to branch/PR>
Head SHA: `<short>`

(same structure as A, with `F-B-NNN` finding IDs and citations prefixed `B:`)

---

## Cross-comparison

### Shared approach
- Both <observation>. See `A: path:line @ <sha-A>` and `B: path:line @ <sha-B>`.

### Divergences
- **<topic>**: A does X (`A: path:line @ <sha-A>`), B does Y (`B: path:line @ <sha-B>`). Trade-off: <neutral statement>.

### PRD coverage delta
| Req | A | B |
|---|---|---|
| R1 | Met | Met |
| R2 | Missing | Partial |

### Defect delta
| Category | A only | B only | Shared |
|---|---|---|---|
| PRD-impact | F-A-001 (R3), F-A-002 (R5) | F-B-002 (R2) | — |
| Quality | F-A-004, F-A-005 | F-B-001, F-B-003 | — |
| **Total** | <n> | <n> | <n> |

### Side-by-side scores
| Criterion | A | B |
|---|---|---|
| PRD compliance | 3 | 4 |
| Correctness | 2 | 4 |
| Robustness | ... | ... |
| Code quality | ... | ... |
| Test coverage | ... | ... |
| Scope discipline | ... | ... |
| Diff hygiene | ... | ... |

---

## Appendix: verification

**Working tree**: `<absolute path used for verification>`

```
git -C <path> log -1 --oneline <head-sha-A>
git -C <path> log -1 --oneline <head-sha-B>
git -C <path> diff <base-sha-A>..<head-sha-A> -- <files>
git -C <path> diff <base-sha-B>..<head-sha-B> -- <files>
```
````

## Slug rules

- Lowercase, ASCII, hyphens only, max 40 chars.
- Source: PRD's first H1 (or filename stem if no H1) for `<prd-slug>`; PR title or branch name for ref slugs.
- Strip leading ticket prefixes (`LLM-1234-`, `nojira-`) only if both refs share the same prefix; otherwise keep them.
- If two slugs collide, append `-a` / `-b`.
