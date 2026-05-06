# Reference: kimchi terminal-bench task layout (PR #140)

Copy these as starting points. Adapt fields per bug — names, timeouts, resources, deps.

## task.toml — coding task (from go-rate-limiter)

```toml
version = "1.0"

[task]
name = "kimchi-smoke/<slug>"
description = "<one-line task description, abstract — no bug hints>"
keywords = ["<lang>", "<tag>", ...]
[[task.authors]]
name = "kimchi-dev"

[metadata]
difficulty = "easy"          # easy | medium | hard
category = "coding"          # coding | research
tags = ["<lang>", "smoke", "harness-bug-repro"]

[verifier]
timeout_sec = 600.0

[agent]
timeout_sec = 900.0

[environment]
build_timeout_sec = 900.0
cpus = 2
memory_mb = 2048
storage_mb = 4096
gpus = 0
allow_internet = true
mcp_servers = []

[verifier.env]

[solution.env]
```

## task.toml — research task (from go-router-research)

Same shape, smaller footprint:

```toml
[metadata]
difficulty = "easy"
category = "research"
tags = ["research", "smoke", "harness-bug-repro"]
note = "Bug repro task. Compare runs via session artifacts (tokens, subagent count, duration) when end-state is trivial."

[verifier]
timeout_sec = 120.0

[agent]
timeout_sec = 300.0

[environment]
build_timeout_sec = 600.0
cpus = 1
memory_mb = 1024
storage_mb = 2048
```

## environment/Dockerfile — Go base (from go-rate-limiter)

```dockerfile
FROM golang:1.23-bookworm

RUN apt-get update && \
    apt-get install -y --no-install-recommends curl ca-certificates procps && \
    rm -rf /var/lib/apt/lists/*

ENV GOFLAGS=-mod=mod \
    GOTOOLCHAIN=local

WORKDIR /app
```

Swap base image per language signal from transcript: `python:3.12-slim`, `node:20-bookworm`, `rust:1.80-bookworm`. Keep `WORKDIR /app`.

## tests/test.sh (from go-rate-limiter)

```bash
#!/usr/bin/env bash
set -uo pipefail

mkdir -p /logs/verifier

curl -LsSf https://astral.sh/uv/0.9.5/install.sh | sh >/dev/null 2>&1
source "$HOME/.local/bin/env"

uvx -p 3.13 -w pytest==8.4.1 -w pytest-json-ctrf==0.3.5 -w httpx==0.27.2 \
    pytest --ctrf /logs/verifier/ctrf.json /tests/test_<slug>.py -rA
status=$?

if [ $status -eq 0 ]; then
    echo 1 > /logs/verifier/reward.txt
else
    echo 0 > /logs/verifier/reward.txt
fi
exit $status
```

Add/remove `-w <pkg>==<ver>` as the test needs. Keep the reward.txt convention (1 = pass, 0 = fail).

## tests/test_<slug>.py — patterns

**End-state pattern**: import/exec the agent's artefact under `/app/...`, assert behavior.

**Transcript-inspection pattern**: kimchi-agent writes session jsonl to `/logs/agent/sessions/` inside the verifier container (`benchmark/terminal-bench-2/src/kimchi_agent/agent.py`: main session at `main.jsonl`, subagents as `<ts>_<uuid>.jsonl`). Parse with the same logic as `scripts/parse_session.py`. Skeleton:

```python
import json, pathlib

SESSIONS_DIR = pathlib.Path("/logs/agent/sessions")

def load(path):
    lines = [json.loads(l) for l in path.read_text().splitlines() if l.strip()]
    return lines[0], lines[1:]

def active_branch(entries):
    by_id = {e["id"]: e for e in entries if "id" in e}
    children = {}
    for e in entries:
        children.setdefault(e.get("parentId"), []).append(e)
    leaves = [e for e in entries if "id" in e and e["id"] not in children]
    cur, chain = max(leaves, key=lambda e: e.get("timestamp","")), []
    while cur:
        chain.append(cur)
        cur = by_id.get(cur.get("parentId"))
    return list(reversed(chain))

def test_no_repeated_identical_tool_calls():
    files = list(SESSIONS_DIR.glob("*.jsonl"))
    assert files, "no session jsonl produced"
    for f in files:
        _, entries = load(f)
        # walk active branch, count consecutive identical (name, arguments) tool calls
        # assert max_run_length < THRESHOLD
```

Field names (pi-mono v3, ground truth from `packages/ai/src/types.ts` and `packages/coding-agent/src/core/messages.ts`):
- assistant `content[].type == "toolCall"`, fields `name`, `arguments`
- tool result `role == "toolResult"`, fields `toolCallId`, `toolName`, `content`, `isError`
- bash exec is a **message role**: `message.role == "bashExecution"`, fields `command`, `output`, `exitCode`, `cancelled`, `truncated`
- usage on assistant: `usage.input`, `usage.output`, `usage.cacheRead`, `usage.cacheWrite`, `usage.totalTokens`

When inspection cannot be encoded deterministically, **stop and explain to the user, propose alternatives** (unit test in pi-mono, scripted replay, manual repro).

## Verify-red automation

`scripts/run-local.sh` hardcodes `BENCH_DIR=$(dirname $0)/..` and runs tasks from `$BENCH_DIR/tasks` — it has no `--path` override that escapes the smoke dir. To run a task that lives elsewhere, stage it into the smoke dir first.

Recommended (symlink, lossless, reversible):

```bash
KIMCHI_DEV=/home/pmateusz/dev/private/kimchi-dev   # adjust
SLUG=<slug>
ln -sfn "$PWD/tasks/$SLUG" "$KIMCHI_DEV/benchmark/terminal-bench-smoke/tasks/$SLUG"
( cd "$KIMCHI_DEV" && KIMCHI_API_KEY="$KIMCHI_API_KEY" \
    bash benchmark/terminal-bench-smoke/scripts/run-local.sh -i "$SLUG" )
```

Result lives under `$KIMCHI_DEV/benchmark/terminal-bench-smoke/jobs/<ts>/<task>__<trial>/`. Red check:

```bash
reward=$(cat "$KIMCHI_DEV"/benchmark/terminal-bench-smoke/jobs/*/${SLUG}__*/verifier/reward.txt | tail -n1)
test "$reward" = "0" && echo "RED confirmed" || { echo "task passed — repro is wrong"; exit 1; }
```

If the user is already inside `kimchi-dev` and writes the task directly under `benchmark/terminal-bench-smoke/tasks/<slug>/`, skip the symlink and run the script directly.

Alternative: invoke `harbor run` directly with `-d <abs-task-dir>` — see `benchmark/terminal-bench-2/README.md`.
