#!/usr/bin/env python3
"""Replay every Bash command in the transcript corpus through bash_guard.decide (Task 7 Step 4)."""
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "workspace-config" / "hooks"))
from bash_guard import decide  # noqa: E402

tx = Path(sys.argv[1] if len(sys.argv) > 1 else Path.home() / ".claude/projects/-projectnb-liu-scc-philipp")
verdicts, hits, n = Counter(), [], 0
for p in sorted(tx.glob("*.jsonl")) + sorted(tx.glob("*/subagents/*.jsonl")):
    for line in open(p, errors="replace"):
        try:
            e = json.loads(line)
        except json.JSONDecodeError:
            continue
        m = e.get("message")
        if not isinstance(m, dict) or m.get("role") != "assistant" or not isinstance(m.get("content"), list):
            continue
        for b in m["content"]:
            if isinstance(b, dict) and b.get("type") == "tool_use" and b.get("name") == "Bash":
                cmd = b.get("input", {}).get("command", "")
                v, reason = decide(cmd, e.get("cwd") or "/projectnb/liu-scc/philipp", {"JOB_ID": "x"})
                verdicts[v] += 1
                n += 1
                if v != "allow":
                    hits.append((v, cmd.replace("\n", " ")[:160]))
print(f"bash commands replayed: {n}; verdicts: {dict(verdicts)}")
for v, c in hits[:60]:
    print(f"{v:5s} | {c}")
