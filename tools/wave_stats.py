#!/usr/bin/env python3
"""Cost summary of one session for the retro-officer seat: main-session calls and summed
per-call context, the share of it from calls at or above 500k, compactions, subagents by type with their summed context, and the subagents
that hit their turn limit. Reads transcripts only; never the conversation text beyond the
turn-limit notices.

Usage: wave_stats.py <main transcript .jsonl> [--since ISO-8601]
                     [--repo <path> --range <a..b> --register <relpath>]

`review_seats` is the share of summed subagent context spent in review seats (REVIEW_SEATS) over
the --since window. With --repo/--range/--register the output also carries `register`: markdown
table rows of that file added between a and b, and rows closed (Status column CLOSED at b, not
CLOSED at a) when the table has a Status column.
"""
import argparse
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from measure_context import _entries, agent_type

TURN_LIMIT = re.compile(r"<task-id>(\w+)</task-id>(?:(?!</task-notification>).)*?stopped at its \d+-turn limit", re.S)

REVIEW_SEATS = frozenset({
    "critic-reviewer", "domain-reviewer", "alignment-officer", "anomaly-hunter", "docs-sync",
    "inventory-auditor", "lean-critic", "pragmatism-officer", "retro-officer", "figure-auditor",
    "security-specialist"})


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
    total = sum(v["context_tokens"] for v in subs.values())
    review = sum(v["context_tokens"] for k, v in subs.items() if k in REVIEW_SEATS)
    return {"main": {"calls": len(ctx), "context_tokens": sum(ctx), "max_context": max(ctx, default=0),
                     "compactions": compactions,
                     # summed context of calls at or above 500k over all summed context: the
                     # share the 500k nudge targets. Raw context, not cost: the 2026-10-14
                     # cost-weighted share (cache write/read and output priced) was ≈ 0.67, n = 15;
                     # compare this number only with itself across waves.
                     "share_above_500k": round(sum(c for c in ctx if c >= 500_000) / sum(ctx), 3) if ctx else 0.0},
            "subagents": subs, "turn_limit_hits": limited,
            "review_seats": {"context_tokens": review, "subagent_tokens": total,
                             "share": round(review / total, 3) if total else 0.0}}


def _cells(line: str) -> list[str]:
    return [c.strip() for c in line.strip().strip("|").split("|")]


def _register_rows(text: str) -> tuple[dict[str, str | None], bool]:
    """(first cell -> status or None, whether any table has a Status column) over all markdown tables."""
    rows: dict[str, str | None] = {}
    has_status = False
    table: list[str] = []
    for line in text.splitlines() + [""]:
        if line.lstrip().startswith("|"):
            table.append(line)
            continue
        if len(table) >= 2:
            head = [c.lower() for c in _cells(table[0])]
            col = head.index("status") if "status" in head else None
            has_status = has_status or col is not None
            for ln in table[2:]:  # table[1] is the |---| separator
                c = _cells(ln)
                rows[c[0]] = c[col].replace("*", "").replace("`", "").strip().upper() if col is not None and col < len(c) else None
        table = []
    return rows, has_status


def _show(repo: Path, rev: str, rel: str) -> str | None:
    r = subprocess.run(["git", "-C", str(repo), "show", f"{rev}:{rel}"], capture_output=True, text=True)
    return r.stdout if r.returncode == 0 else None


def register_delta(repo: Path, rng: str, rel: str) -> dict:
    """Rows added and (with a Status column) rows closed in markdown tables of `rel` between a and b of `a..b`.

    A file absent at a counts as an empty register; absent at b is an error, not zero rows.
    """
    a, sep, b = rng.partition("..")
    if not sep or not a or not b:
        raise SystemExit(f"register delta needs --range a..b with both ends, got {rng!r}")
    after = _show(repo, b, rel)
    if after is None:
        raise SystemExit(f"register delta: cannot read {rel} at {b} in {repo} (git show failed)")
    before_rows, before_status = _register_rows(_show(repo, a, rel) or "")
    after_rows, after_status = _register_rows(after)
    out = {"status_column": "present" if after_status else "absent", "rows_before": len(before_rows),
           "rows_after": len(after_rows), "rows_added": len(after_rows.keys() - before_rows.keys())}
    if after_status:
        out["rows_closed"] = sum(1 for k, v in after_rows.items()
                                 if v and v.startswith("CLOSED") and not (before_rows.get(k) or "").startswith("CLOSED"))
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("transcript")
    ap.add_argument("--since")
    ap.add_argument("--repo")
    ap.add_argument("--range", dest="rng")
    ap.add_argument("--register")
    a = ap.parse_args(argv)
    if bool(a.repo) != bool(a.rng) or (a.register and not a.repo):
        ap.error("--repo and --range go together, and --register needs both")
    out = summarize(Path(a.transcript), a.since)
    if a.register:
        out["register"] = register_delta(Path(a.repo), a.rng, a.register)
    print(json.dumps(out, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
