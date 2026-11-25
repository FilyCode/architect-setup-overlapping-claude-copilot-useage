#!/usr/bin/env python3
"""SessionStart hook: point a fresh session at the handoff the previous one wrote (context_nudge.py writes the request).

On source "clear" or "startup", when <handoff dir>/<sanitized cwd>/latest.md exists and is under 12 h old, adds one
line naming the file and its age. A pointer only, never the body. CLAUDE_HANDOFF_DIR overrides the directory.
Any error exits 0 silently.
"""
import json
import os
import re
import sys
import time
from pathlib import Path

HANDOFF_DIR = "/projectnb/liu-scc/philipp/software/claude-handoffs"
MAX_AGE = 12 * 3600


def main():
    try:
        d = json.load(sys.stdin)
        if d.get("source") not in ("clear", "startup"):
            return 0
        cwd = str(d.get("cwd") or os.getcwd())
        f = Path(os.environ.get("CLAUDE_HANDOFF_DIR") or HANDOFF_DIR) / re.sub(r"[^A-Za-z0-9]", "-", cwd) / "latest.md"
        age = time.time() - f.stat().st_mtime
        if age >= MAX_AGE:
            return 0
        shown = f"{int(age // 60)} min ago" if age < 3600 else f"{age / 3600:.1f} h ago"
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext":
              f"Handoff from the previous session: {f} (written {shown}). Read it before starting."}}))
    except Exception:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
