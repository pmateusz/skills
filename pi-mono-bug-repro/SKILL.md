---
name: pi-mono-bug-repro
description: Build a failing terminal-bench task that reproduces a coding-harness bug observed in pi-mono jsonl session(s). Analyzes whole sessions (parent + subagents via parentSession) for anomalies, then emits a kimchi-style task under ./tasks/<slug>/ for red-green TDD harness fixes. Use when user wants to reproduce harness bugs from pi-mono transcripts, turn jsonl sessions into terminal-bench tasks, or build red-green tests for kimchi-code/coding-agent regressions.
---

# pi-mono-bug-repro

Turn pi-mono session jsonl(s) into a failing kimchi terminal-bench task that reproduces an observed harness bug. Output: `./tasks/<slug>/` (override on request).

Reference task layout: `castai/kimchi-dev` PR #140 (`benchmark/terminal-bench-smoke/tasks/*`).

## Workflow

### 1. Locate input jsonl(s)

- Default location: `~/.pi/agent/sessions/--<cwd>--/<ts>_<uuid>.jsonl`.
- If the user didn't pass a path, scan there. Found candidates → list and ask user to confirm. None found → ask for path.
- A session header may contain `parentSession`: follow it (and recursively) to gather subagent files. Confirm the full set with user before parsing.

### 2. Parse with bundled script

Run `scripts/parse_session.py <path> [<path> ...]` to load v3 jsonl, reconstruct the active branch (leaf→root via parentId), and emit anomaly signals: tool-call counts, repeated identical tool calls, `isError` rate, bash exit-code failures, token usage, compaction events. Treat the output as candidates, not ground truth.

### 3. Identify the bug

If the user already described the bug, verify it against signals. If unclear, **grill the user** (delegate to `grill-me` skill if available). Do not assume. Walk every branch of the decision tree until the anomaly is precisely defined: which entries, which pattern, which bad behavior.

### 4. Pick repro style (per-bug)

- **End-state coding task**: bug corrupts output (wrong files, wrong content, missed steps). Test asserts files / exit-codes the buggy harness misses. Mirror PR 140's `go-rate-limiter` style.
- **Transcript inspection**: bug is purely behavioral (loops, repeated failed tool calls, runaway tokens, ignored instructions). Test runs harness, then parses produced jsonl for the anomalous pattern.

If neither yields a deterministic failing test in the terminal-bench format, **stop and explain why** to the user, and propose alternatives (e.g. unit test in pi-mono, scripted replay harness, manual repro steps). Do not fabricate a test.

### 5. Pick env image

Read `cwd` from session header and inspect transcript signals (language, tools used). Suggest a base image to user (e.g. `golang:1.22`, `python:3.12-slim`, `node:20`) — confirm before generating Dockerfile.

### 6. Pick slug

Propose 2-3 slug candidates derived from the anomaly (e.g. `bash-loop-on-exit-1`, `repeated-edit-same-file`, `subagent-context-leak`). User picks one.

### 7. Generate task

Create under `./tasks/<slug>/`:

```
tasks/<slug>/
├── environment/Dockerfile
├── instruction.md          # abstract — coding/research task only, no transcript leak
├── task.toml               # kimchi shape (PR 140), adapt per bug
└── tests/
    ├── test.sh
    ├── test_<slug>.py      # end-state asserts and/or transcript-jsonl inspection
    └── EVIDENCE.md         # transcript ids, snippets, source jsonl paths — for fixer, not task-runner
```

Use the templates in [REFERENCE.md](REFERENCE.md) — copy `task.toml`, `Dockerfile`, `test.sh` from there and adapt to the bug (slug, timeouts, base image, deps, asserts).

Rules:
- `instruction.md` is what the harness sees — keep it abstract, no anomaly hints.
- `EVIDENCE.md` carries traceability (session id, entry ids, parent chain, key snippets, signal output).
- Test must **fail under the buggy harness**. State this expectation in `EVIDENCE.md` along with observed-vs-expected behavior.

### 8. Verify red (automated)

`run-local.sh` only runs tasks under `benchmark/terminal-bench-smoke/tasks/`. If the task lives elsewhere, symlink it in (lossless, reversible) — see [REFERENCE.md](REFERENCE.md) for the exact commands. With `KIMCHI_API_KEY` set:

```bash
( cd $KIMCHI_DEV && bash benchmark/terminal-bench-smoke/scripts/run-local.sh -i <slug> )
reward=$(cat $KIMCHI_DEV/benchmark/terminal-bench-smoke/jobs/*/<slug>__*/verifier/reward.txt | tail -n1)
test "$reward" = "0"   # exit 0 = RED confirmed; non-zero = repro wrong, iterate
```

If reward is `1`, the buggy harness solved the task — repro is wrong, do not ship. Iterate on the test or task design, do not loosen the assertion to make red appear.

## Notes

- pi-mono v3 schema: header `{type:"session",version:3,id,cwd,parentSession?}`; entries carry `id`+`parentId`; message roles `user|assistant|toolResult`; also `bashExecution`, `compaction`, `branch_summary`, `model_change`. Active branch = leaf→root walk.
- Sub-agent sessions are separate files linked by `parentSession` in their header.
- Analyze the **whole** session, not just the last message.
