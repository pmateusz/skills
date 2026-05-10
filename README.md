# skills

Personal skills.

## Install

```bash
npx skills@latest add pmateusz/skills
```

Or globally: `npx skills@latest add pmateusz/skills -g`.

## Skills

| Name | Type | Purpose |
|---|---|---|
| `code-review` | user-invocable | Review a GitHub PR / GitLab MR locally; present findings in chat. |
| `gh-cli` | knowledge | `gh` CLI patterns for PRs, reviews, CI runs, issues. |
| `git-hygiene` | knowledge | Stage only files belonging to the change; no LLM/tool attribution; never push to main/master. |
| `glab-cli` | knowledge | `glab` CLI patterns for MRs, discussions, pipelines. |
| `bound-tool-output` | knowledge | Cap output from Bash, search, and file-read tools to preserve context. |
| `python-edit` | knowledge | AST-validate `.py` files after Edit/Write. |
| `careful-planning` | knowledge | Verified implementation plans to `./plans/<slug>.md`; deep symbol exploration; LSP probe; confirmation gate before coding. |
| `write-a-prd` | knowledge | Interview + codebase exploration to produce a PRD; saved to `./prds/<slug>.md` (no GitHub issue). |
| `prd-to-ferment` | user-invocable | Reframe a PRD into answers to four discovery questions (build, goal, success criteria, non-negotiables) without losing info. |
| `compare-prd-implementations` | user-invocable | Independently review two branches/PRs implementing the same PRD; produces a scored, file:line-cited markdown report. |
| `pi-mono-bug-repro` | knowledge | Turn pi-mono jsonl session(s) into a failing kimchi terminal-bench task that reproduces a coding-harness bug for red-green TDD. |

Knowledge skills load automatically when their description matches the task. `code-review` is invoked explicitly.
