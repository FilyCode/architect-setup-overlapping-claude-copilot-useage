#!/usr/bin/env python3
"""UserPromptSubmit: tell the owner once an hour when the session runs a retired model.

Reads the last ~512 KB of the transcript, takes the last assistant entry's message.model, and when it is in
RETIRED warns (systemMessage plus additionalContext). Warned-at time is kept in
$TMPDIR/model_guard_<sid>.json. Any internal error stays silent.
"""
import json
import os
import re
import sys
import time
from pathlib import Path

RETIRED = {"claude-opus-5"}
TAIL = 512 * 1024
HOUR = 3600
MSG = ("This session still runs claude-opus-5; the workspace pins claude-opus-5-5 (same family, cheaper per "
       "token). Type /model claude-opus-5-5 to switch (one cache rebuild).")
CTX = "This session runs the retired model claude-opus-5; tell the owner once to type /model claude-opus-5-5."


def last_model(transcript: Path):
    with open(transcript, "rb") as f:
        f.seek(0, 2)
        f.seek(max(0, f.tell() - TAIL))
        lines = f.read().decode("utf-8", errors="replace").split("\n")
    for line in reversed(lines):
        try:
            e = json.loads(line)
        except json.JSONDecodeError:
            continue
        m = e.get("message") if isinstance(e, dict) else None
        if e.get("type") == "assistant" and isinstance(m, dict) and m.get("model"):
            return m["model"]
    return None


def main():
    try:
        d = json.load(sys.stdin)
        if last_model(Path(d["transcript_path"])) not in RETIRED:
            return 0
        sid = re.sub(r"[^\w-]", "", str(d.get("session_id") or "nosession"))
        path = Path(os.environ.get("TMPDIR") or "/tmp") / f"model_guard_{sid}.json"
        state = json.loads(path.read_text()) if path.exists() else {}
        now = time.time()
        if now - state.get("warned_at", 0) < HOUR:
            return 0
        path.write_text(json.dumps({"warned_at": now}))
        print(json.dumps({"systemMessage": MSG, "hookSpecificOutput": {
            "hookEventName": "UserPromptSubmit", "additionalContext": CTX}}))
    except Exception:
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
