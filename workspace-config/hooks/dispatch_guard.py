#!/usr/bin/env python3
"""PreToolUse(Agent): warn on an opus implementer whose brief's first line names no reason (DECISION-028/029).

Warns only; never denies. Any internal error stays silent.
"""
import json
import re
import sys

REASON = re.compile(r"cross[- ]module|contract|retry", re.I)
MSG = ("Opus implementer without a reason in the brief's first line (DECISION-028/029): name the "
       "cross-module/contract change or retry there, or drop model: opus.")


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
            print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "additionalContext": MSG}}))
    except Exception:
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
