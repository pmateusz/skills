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

Knowledge skills load automatically when their description matches the task. `code-review` is invoked explicitly.
