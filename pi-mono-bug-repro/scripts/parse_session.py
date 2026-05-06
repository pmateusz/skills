#!/usr/bin/env python3
"""Parse pi-mono v3 session jsonl(s), reconstruct active branch, surface anomaly signals.

Usage:
    parse_session.py <path.jsonl> [<path.jsonl> ...] [--include-parents] [--json]

Outputs a human-readable signal summary by default; pass --json for machine output.
Signals are candidates — interpret with the user, don't treat as ground truth.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path


def load_jsonl(path: Path) -> tuple[dict, list[dict]]:
    lines = [json.loads(l) for l in path.read_text().splitlines() if l.strip()]
    if not lines:
        raise ValueError(f"empty file: {path}")
    header, entries = lines[0], lines[1:]
    if header.get("type") != "session":
        raise ValueError(f"first line is not a session header: {path}")
    return header, entries


def active_branch(entries: list[dict]) -> list[dict]:
    """Walk leaf→root via parentId, return entries in chronological order."""
    by_id = {e["id"]: e for e in entries if "id" in e}
    children = defaultdict(list)
    for e in entries:
        pid = e.get("parentId")
        if pid:
            children[pid].append(e["id"])
    # leaf = entry whose id has no children, pick the latest by timestamp
    leaves = [e for e in entries if "id" in e and not children.get(e["id"])]
    if not leaves:
        return entries
    leaf = max(leaves, key=lambda e: e.get("timestamp", ""))
    chain = []
    cur = leaf
    while cur:
        chain.append(cur)
        pid = cur.get("parentId")
        cur = by_id.get(pid) if pid else None
    return list(reversed(chain))


def collect_signals(header: dict, branch: list[dict]) -> dict:
    tool_calls: Counter[str] = Counter()
    tool_errors: Counter[str] = Counter()
    bash_exits: Counter[int] = Counter()
    repeated_pairs: Counter[tuple[str, str]] = Counter()
    last_call_sig: str | None = None
    consecutive_repeats: list[tuple[str, int]] = []
    cur_repeat = 0
    total_in = total_out = 0
    compactions = 0
    user_msgs = assistant_msgs = tool_results = 0
    thinking_chars = 0

    for e in branch:
        t = e.get("type")
        if t == "compaction":
            compactions += 1
            continue
        if t != "message":
            continue
        msg = e.get("message", {})
        role = msg.get("role")
        if role == "user":
            user_msgs += 1
        elif role == "assistant":
            assistant_msgs += 1
            usage = msg.get("usage") or {}
            total_in += int(usage.get("input", 0) or 0)
            total_out += int(usage.get("output", 0) or 0)
            for c in msg.get("content", []) or []:
                ct = c.get("type")
                if ct == "toolCall":
                    name = c.get("name", "?")
                    args = json.dumps(c.get("arguments") or {}, sort_keys=True)
                    sig = f"{name}::{args}"
                    tool_calls[name] += 1
                    if sig == last_call_sig:
                        cur_repeat += 1
                    else:
                        if cur_repeat >= 2 and last_call_sig:
                            consecutive_repeats.append((last_call_sig, cur_repeat + 1))
                        cur_repeat = 0
                    last_call_sig = sig
                elif ct == "thinking":
                    thinking_chars += len(c.get("thinking") or c.get("text") or "")
        elif role == "toolResult":
            tool_results += 1
            if msg.get("isError"):
                tool_errors[msg.get("toolName", "?")] += 1
        elif role == "bashExecution":
            ec = msg.get("exitCode")
            if ec is not None:
                bash_exits[ec] += 1
    if cur_repeat >= 2 and last_call_sig:
        consecutive_repeats.append((last_call_sig, cur_repeat + 1))

    return {
        "session_id": header.get("id"),
        "cwd": header.get("cwd"),
        "parent_session": header.get("parentSession"),
        "version": header.get("version"),
        "branch_len": len(branch),
        "user_msgs": user_msgs,
        "assistant_msgs": assistant_msgs,
        "tool_results": tool_results,
        "tool_call_counts": dict(tool_calls.most_common()),
        "tool_error_counts": dict(tool_errors.most_common()),
        "bash_exit_codes": dict(bash_exits),
        "consecutive_identical_tool_calls": [
            {"signature": sig[:200], "run_length": n} for sig, n in consecutive_repeats
        ],
        "tokens_input": total_in,
        "tokens_output": total_out,
        "compactions": compactions,
        "thinking_chars": thinking_chars,
    }


def gather_with_parents(start: Path) -> list[Path]:
    seen, order = set(), []
    cur = start.resolve()
    while cur and cur not in seen:
        seen.add(cur)
        order.append(cur)
        try:
            header, _ = load_jsonl(cur)
        except Exception:
            break
        ps = header.get("parentSession")
        if not ps:
            break
        nxt = Path(ps)
        if not nxt.is_absolute():
            nxt = (cur.parent / nxt).resolve()
        cur = nxt if nxt.exists() else None
    return order


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("paths", nargs="+", type=Path)
    ap.add_argument("--include-parents", action="store_true",
                    help="follow parentSession chain in each file's header")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    files: list[Path] = []
    for p in args.paths:
        if args.include_parents:
            files.extend(gather_with_parents(p))
        else:
            files.append(p.resolve())
    seen = set()
    files = [f for f in files if not (f in seen or seen.add(f))]

    results = []
    for f in files:
        try:
            header, entries = load_jsonl(f)
        except Exception as exc:
            results.append({"path": str(f), "error": str(exc)})
            continue
        branch = active_branch(entries)
        sig = collect_signals(header, branch)
        sig["path"] = str(f)
        results.append(sig)

    if args.json:
        json.dump(results, sys.stdout, indent=2)
        sys.stdout.write("\n")
        return 0

    for r in results:
        print(f"=== {r.get('path')} ===")
        if "error" in r:
            print(f"  ERROR: {r['error']}")
            continue
        print(f"  session={r['session_id']} version={r['version']} cwd={r['cwd']}")
        if r["parent_session"]:
            print(f"  parentSession={r['parent_session']}")
        print(f"  branch_len={r['branch_len']} user={r['user_msgs']} "
              f"assistant={r['assistant_msgs']} toolResults={r['tool_results']}")
        print(f"  tokens in/out={r['tokens_input']}/{r['tokens_output']} "
              f"compactions={r['compactions']} thinking_chars={r['thinking_chars']}")
        if r["tool_call_counts"]:
            print(f"  tool_calls: {r['tool_call_counts']}")
        if r["tool_error_counts"]:
            print(f"  tool_errors: {r['tool_error_counts']}")
        if r["bash_exit_codes"]:
            print(f"  bash_exits: {r['bash_exit_codes']}")
        for run in r["consecutive_identical_tool_calls"]:
            print(f"  REPEAT x{run['run_length']}: {run['signature']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
