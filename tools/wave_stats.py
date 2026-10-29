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
from datetime import datetime, timezone
from pathlib import Path

from measure_context import _entries, agent_type

TURN_LIMIT = re.compile(r"<task-id>(\w+)</task-id>(?:(?!</task-notification>).)*?stopped at its \d+-turn limit", re.S)


def _parse_since(since: str | None) -> datetime | None:
    """--since as an aware UTC datetime.

    This used to be a naive STRING comparison against the transcript's UTC timestamps, so a
    local-time bound silently measured the wrong window -- 4 hours too wide from US/Eastern,
    which is how every retro in this workspace that passed a local --since has been measured.
    A bare timestamp is now read as LOCAL time, because that is what a human typing one
    means, and converted to UTC before any comparison; an explicit offset or trailing Z is
    honoured as given.
    """
    if not since:
        return None
    s = since.strip().replace("Z", "+00:00")
    dt = datetime.fromisoformat(s)
    if dt.tzinfo is None:
        dt = dt.astimezone()  # naive -> local
    return dt.astimezone(timezone.utc)


def _after(entry: dict, since: datetime | None) -> bool:
    """Is this entry at or after the bound? Unparseable or missing timestamps are KEPT.

    Dropping an entry whose timestamp cannot be read would silently shrink the window, which
    is the same class of error as the timezone bug: a measurement quietly answering about a
    different population than the one asked for.
    """
    if since is None:
        return True
    raw = entry.get("timestamp")
    if not isinstance(raw, str) or not raw:
        return True
    try:
        dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return True
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)  # transcripts are UTC
    return dt >= since


def _text_of(message) -> str:
    """All text in a message, whether content is a string or a list of blocks.

    Turn-limit notices arrive as list-of-blocks far more often than as a bare string, so the
    string-only version reported turn_limit_hits: [] for waves that demonstrably had them --
    including the 2026-10-29 MeMES wave, where two seats hit their limits.
    """
    if not isinstance(message, dict):
        return ""
    content = message.get("content")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "\n".join(
            b.get("text", "") for b in content if isinstance(b, dict) and "text" in b
        )
    return ""


def _calls(path: Path, since: datetime | None):
    seen = set()
    for e in _entries(path):
        m = e.get("message")
        if not isinstance(m, dict) or not m.get("usage") or m.get("id") in seen:
            continue
        seen.add(m.get("id"))
        if not _after(e, since):
            continue
        u = m["usage"]
        yield u.get("input_tokens", 0) + u.get("cache_creation_input_tokens", 0) + u.get("cache_read_input_tokens", 0)


def summarize(main: Path, since: str | None = None) -> dict:
    bound = _parse_since(since)
    ctx = list(_calls(main, bound))
    compactions, limited = 0, []
    for e in _entries(main):
        if not _after(e, bound):
            continue
        if e.get("subtype") == "compact_boundary":
            compactions += 1
        text = _text_of(e.get("message"))
        if text:
            limited += [t for t in TURN_LIMIT.findall(text) if t not in limited]
    subs: dict[str, dict] = {}
    for p in sorted((main.parent / main.stem / "subagents").glob("agent-*.jsonl")):
        c = list(_calls(p, bound))
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
