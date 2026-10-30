#!/usr/bin/env python3
"""PostToolUse(Write|Edit|Bash): warn when a project MEMORY.md exceeds the context_budget ceilings.

For Bash (heredoc/sed/echo writes, the usual route): when the command mentions MEMORY.md, every
<config dir>/projects/*/memory/MEMORY.md modified in the last 120 s is checked ($CLAUDE_CONFIG_DIR or ~/.claude).

Measures with tools/context_budget.py (CEIL and _memory_loaded), so the numbers live in one place.
Any internal error stays silent.
"""
import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(os.path.realpath(__file__)).parents[2] / "tools"))
import context_budget as cb  # noqa: E402

FRESH = 120  # seconds: a Bash write just happened if the index changed this recently
ADVICE = ("MEMORY.md is over budget. Trim the line you just wrote: an index line is a link plus a hook "
          "of at most ~10 words; live status (branches, SHAs, next steps) belongs inside the memory "
          "file, not the index.")


def is_memory_index(path: str) -> bool:
    p = Path(os.path.realpath(path))
    parts = p.parts
    return p.name == "MEMORY.md" and len(parts) >= 4 and parts[-2] == "memory" and parts[-4] == "projects" \
        and parts[-5] == ".claude"


def measure(path: Path):
    nbytes = len(cb._memory_loaded(path).encode())
    entries = sum(1 for ln in path.read_text().splitlines() if ln.startswith("- ["))
    return nbytes, entries


def over_budget(path: Path):
    nbytes, entries = measure(path)
    over = []
    if nbytes > cb.CEIL["memory"]:
        over.append(f"{nbytes} bytes > ceiling {cb.CEIL['memory']}")
    if entries > cb.CEIL["memory_entries"]:
        over.append(f"{entries} entries > ceiling {cb.CEIL['memory_entries']}")
    return over


def recent_indexes(now: float):
    cfg = Path(os.environ.get("CLAUDE_CONFIG_DIR") or Path.home() / ".claude")
    return [p for p in cfg.glob("projects/*/memory/MEMORY.md") if now - p.stat().st_mtime <= FRESH]


def main():
    try:
        d = json.load(sys.stdin)
        ti = d["tool_input"]
        if d.get("tool_name") == "Bash":
            if "MEMORY.md" not in str(ti.get("command") or ""):
                return 0
            over = [f"{p}: {o}" for p in recent_indexes(time.time()) for o in over_budget(p)]
        else:
            fp = ti["file_path"]
            if not is_memory_index(fp):
                return 0
            over = over_budget(Path(fp))
        if over:
            print(json.dumps({"hookSpecificOutput": {"hookEventName": "PostToolUse",
                  "additionalContext": f"{'; '.join(over)}. {ADVICE}"}}))
    except Exception:
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
