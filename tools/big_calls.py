#!/usr/bin/env python3
"""What do the >500k-context calls do? Phase 0 probe P6 (read-only, prints no transcript text)."""
import json
import statistics
import sys
from collections import Counter
from pathlib import Path

BIG, NUDGE = 500_000, 400_000
tx = Path(sys.argv[1] if len(sys.argv) > 1 else Path.home() / ".claude/projects/-projectnb-liu-scc-philipp")
tools, first_cross, sessions = Counter(), [], 0
for p in sorted(tx.glob("*.jsonl")):
    # One assistant message is written as several lines sharing message.id (one content block
    # each), so collect every line's blocks per id before attributing tools.
    order, ctx_of, names_of = [], {}, {}
    for line in open(p, errors="replace"):
        try:
            m = json.loads(line).get("message")
        except json.JSONDecodeError:
            continue
        if not isinstance(m, dict) or not m.get("usage"):
            continue
        mid = m.get("id")
        if mid not in ctx_of:
            order.append(mid)
            u = m["usage"]
            ctx_of[mid] = u.get("input_tokens", 0) + u.get("cache_creation_input_tokens", 0) + u.get("cache_read_input_tokens", 0)
            names_of[mid] = []
        names_of[mid] += [b.get("name") for b in m.get("content", []) if isinstance(b, dict) and b.get("type") == "tool_use"]
    crossed, big = None, 0
    for idx, mid in enumerate(order, 1):
        if ctx_of[mid] >= NUDGE and crossed is None:
            crossed = idx
        if ctx_of[mid] > BIG:
            big += 1
            tools.update(names_of[mid] or ["(text only)"])
    if big:
        sessions += 1
    if crossed:
        first_cross.append(crossed)
print(f"main sessions with >500k calls: {sessions}; calls >500k by tool used in that call (n={sum(tools.values())}):")
for name, n in tools.most_common(12):
    print(f"  {n:6d}  {name}")
if first_cross:
    print(f"call index at which a session first reaches 400k: median {statistics.median(first_cross)}, "
          f"min {min(first_cross)}, max {max(first_cross)} (n={len(first_cross)} sessions)")
