#!/usr/bin/env python3
"""PostToolUse(Write|Edit): warn when a project MEMORY.md exceeds the context_budget ceilings.

Measures with tools/context_budget.py (CEIL and _memory_loaded), so the numbers live in one place.
Any internal error stays silent.
"""
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(os.path.realpath(__file__)).parents[2] / "tools"))
import context_budget as cb  # noqa: E402

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


def main():
    try:
        d = json.load(sys.stdin)
        fp = d["tool_input"]["file_path"]
        if not is_memory_index(fp):
            return 0
        nbytes, entries = measure(Path(fp))
        over = []
        if nbytes > cb.CEIL["memory"]:
            over.append(f"{nbytes} bytes > ceiling {cb.CEIL['memory']}")
        if entries > cb.CEIL["memory_entries"]:
            over.append(f"{entries} entries > ceiling {cb.CEIL['memory_entries']}")
        if over:
            print(json.dumps({"hookSpecificOutput": {"hookEventName": "PostToolUse",
                  "additionalContext": f"{'; '.join(over)}. {ADVICE}"}}))
    except Exception:
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
