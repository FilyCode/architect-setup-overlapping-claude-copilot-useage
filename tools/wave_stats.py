#!/usr/bin/env python3
"""Cost summary of one session for the retro-officer seat: main-session calls and summed
per-call context, the share of it from calls at or above 500k, compactions, subagents by type with their summed context, and the subagents
that hit their turn limit. Reads transcripts only; never the conversation text beyond the
turn-limit notices.

Usage: wave_stats.py <main transcript .jsonl> [--since ISO-8601]
"""
import argparse
import json
import re
from pathlib import Path

from measure_context import _entries, agent_type

TURN_LIMIT = re.compile(r"<task-id>(\w+)</task-id>.*?stopped at its \d+-turn limit", re.S)


def _calls(path: Path, since: str | None):
    seen = set()
    for e in _entries(path):
        m = e.get("message")
        if not isinstance(m, dict) or not m.get("usage") or m.get("id") in seen:
            continue
        seen.add(m.get("id"))
        if since and e.get("timestamp", "") < since:
            continue
        u = m["usage"]
        yield u.get("input_tokens", 0) + u.get("cache_creation_input_tokens", 0) + u.get("cache_read_input_tokens", 0)


def summarize(main: Path, since: str | None = None) -> dict:
    ctx = list(_calls(main, since))
    compactions, limited = 0, []
    for e in _entries(main):
        if since and e.get("timestamp", "") < since:
            continue
        if e.get("subtype") == "compact_boundary":
            compactions += 1
        m = e.get("message")
        text = m.get("content") if isinstance(m, dict) else None
        if isinstance(text, str):
            limited += [t for t in TURN_LIMIT.findall(text) if t not in limited]
    subs: dict[str, dict] = {}
    for p in sorted((main.parent / main.stem / "subagents").glob("agent-*.jsonl")):
        c = list(_calls(p, since))
        if not c:
            continue
        s = subs.setdefault(agent_type(p), {"n": 0, "context_tokens": 0})
        s["n"] += 1
        s["context_tokens"] += sum(c)
    return {"main": {"calls": len(ctx), "context_tokens": sum(ctx), "max_context": max(ctx, default=0),
                     "compactions": compactions,
                     # summed context of calls at or above 500k over all summed context: the
                     # share the 500k nudge targets. Raw context, not cost: the 2026-10-14
                     # cost-weighted share (cache write/read and output priced) was ≈ 0.67, n = 15;
                     # compare this number only with itself across waves.
                     "share_above_500k": round(sum(c for c in ctx if c >= 500_000) / sum(ctx), 3) if ctx else 0.0},
            "subagents": subs, "turn_limit_hits": limited}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("transcript")
    ap.add_argument("--since")
    a = ap.parse_args(argv)
    print(json.dumps(summarize(Path(a.transcript), a.since), indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
