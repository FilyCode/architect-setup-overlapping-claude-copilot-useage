#!/usr/bin/env python3
"""First-call and per-call context metrics from Claude Code transcripts.

Gate of record for the 2026-10-14 restructure (spec §5.7). Reads usage and
attachment sizes only; never prints transcript content.
"""
import argparse
import json
import statistics
import sys
from collections import defaultdict
from pathlib import Path

BIG = 500_000  # declared, workspace-specific: calls above this carry ~69% of main cost (2026-10-14)


def _entries(path: Path):
    with open(path, errors="replace") as f:
        for line in f:
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                continue


def call_contexts(path: Path) -> list[int]:
    seen, out = set(), []
    for e in _entries(path):
        m = e.get("message")
        if not isinstance(m, dict) or not m.get("usage"):
            continue
        mid = m.get("id")
        if mid in seen:
            continue
        seen.add(mid)
        u = m["usage"]
        out.append(u.get("input_tokens", 0) + u.get("cache_creation_input_tokens", 0)
                   + u.get("cache_read_input_tokens", 0))
    return out


def first_attachments(path: Path) -> dict[str, int]:
    sizes: dict[str, int] = {"memory_in_instructions": 0}
    for e in _entries(path):
        a = e.get("attachment")
        if not isinstance(a, dict):
            continue
        t = a.get("type", "?")
        if t not in sizes:
            sizes[t] = len(json.dumps(a))
        if t == "instructions" and any(
                str(f.get("path", "")).endswith("MEMORY.md") for f in a.get("files", [])):
            sizes["memory_in_instructions"] = 1
        m = e.get("message")
        if isinstance(m, dict) and m.get("usage"):
            break  # attachments after the first model call are not startup context
    return sizes


def agent_type(path: Path) -> str:
    """'main' for a top-level session transcript; the sidecar agentType for a subagent; else 'unknown'."""
    if path.parent.name != "subagents" and not path.name.startswith("agent-"):
        return "main"
    meta = path.with_suffix(".meta.json")
    if meta.exists():
        try:
            return json.loads(meta.read_text()).get("agentType") or "unknown"
        except json.JSONDecodeError:
            return "unknown"
    return "unknown"


def summarize(paths) -> dict[str, dict]:
    groups = defaultdict(lambda: {"n": 0, "no_usage": 0, "first": [], "sum": 0, "big": 0, "calls": 0,
                                  "memory": 0})
    for p in paths:
        g = groups[agent_type(p)]
        g["n"] += 1
        calls = call_contexts(p)
        if not calls:
            g["no_usage"] += 1
            continue
        g["first"].append(calls[0])
        g["sum"] += sum(calls)
        g["calls"] += len(calls)
        g["big"] += sum(1 for c in calls if c > BIG)
        g["memory"] += first_attachments(p)["memory_in_instructions"]
    total = sum(g["sum"] for g in groups.values()) or 1
    for g in groups.values():
        f = g.pop("first")
        g["first_median"] = int(statistics.median(f)) if f else None
        g["first_max"] = max(f) if f else None
        g["share_of_ctx"] = round(g["sum"] / total, 4)
    return dict(groups)


def collect(tx: Path, since: str | None):
    paths = sorted(tx.glob("*.jsonl")) + sorted(tx.glob("*/subagents/*.jsonl"))
    if since:
        keep = []
        for p in paths:
            ts = next((e.get("timestamp") for e in _entries(p) if e.get("timestamp")), "")
            if ts[:10] >= since:
                keep.append(p)
        paths = keep
    return paths


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--tx", default=str(Path.home() / ".claude/projects/-projectnb-liu-scc-philipp"))
    ap.add_argument("--since")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    rows = summarize(collect(Path(a.tx), a.since))
    if a.json:
        print(json.dumps(rows, indent=1))
        return 0
    print(f"{'type':22s} {'n':>5s} {'noUse':>5s} {'1st med':>9s} {'1st max':>9s} {'>500k':>7s} {'ctx share':>9s} {'MEM':>5s}")
    for k, g in sorted(rows.items(), key=lambda kv: -kv[1]["sum"]):
        print(f"{k:22s} {g['n']:5d} {g['no_usage']:5d} {str(g['first_median']):>9s} {str(g['first_max']):>9s} "
              f"{g['big']:7d} {g['share_of_ctx']:9.1%} {g['memory']:5d}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
