#!/usr/bin/env python3
"""PreToolUse(Agent): deny an opus implementer unless the brief's first line gives a reason (owner ruling 2026-11-25).

The first non-blank line of the prompt must start with "Opus because:" (case-insensitive) followed by at least
10 non-space characters. Non-opus models and other seats pass. Any internal error stays silent (allows).
"""
import json
import re
import sys

REASON = re.compile(r"^\s*opus because:\s*(\S(?:\s*\S){9})", re.I)
MSG = ('Opus implementer without a stated reason (owner ruling 2026-11-25). Make the first non-blank line of the '
       'prompt "Opus because: <reason>" with at least 10 non-space characters of reason, or drop model: opus '
       "so the implementer runs on the default model.")


def main():
    try:
        d = json.load(sys.stdin)
        ti = d["tool_input"]
        if d.get("tool_name") not in ("Agent", "Task") or ti.get("subagent_type") != "implementer":
            return 0
        model = str(ti.get("model") or "")
        if model != "opus" and not model.startswith("claude-opus"):
            return 0
        first = next((ln for ln in str(ti.get("prompt") or "").splitlines() if ln.strip()), "")
        if not REASON.search(first):
            print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny",
                              "permissionDecisionReason": MSG}}))
    except Exception:
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
