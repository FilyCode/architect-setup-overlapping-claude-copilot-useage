#!/usr/bin/env python3
"""UserPromptSubmit hook: nudge when context is large; hint effort for heavy planning.

Threshold is declared workspace-specific (2026-10-14 corpus: calls above 500k carry
~69% of main-session cost) and overridable with CLAUDE_NUDGE_TOKENS. Owner band
2026-10-14: nudge at 50 % of the 1M window, auto-compaction backstop at 80 %
(CLAUDE_CODE_AUTO_COMPACT_WINDOW=800000), so compaction lands at a task boundary. Fires once per 100k band. Any error exits 0 silently.
"""
import json
import os
import re
import sys
from pathlib import Path

DEFAULT_THRESHOLD = 500_000

TAIL = 2_000_000
BAND = 100_000
HEAVY = re.compile(r"\b(brainstorm\w*|architect\w*|design doc|spec|implementation plan|writing-plans|plan the)\b", re.I)


def last_context(transcript: Path):
    with open(transcript, "rb") as f:
        f.seek(0, 2)
        size = f.tell()
        f.seek(max(0, size - TAIL))
        lines = f.read().decode("utf-8", errors="replace").split("\n")[1:]
    for line in reversed(lines):
        try:
            e = json.loads(line)
        except json.JSONDecodeError:
            continue
        u = (e.get("message") or {}).get("usage") if isinstance(e.get("message"), dict) else None
        if u:
            return u.get("input_tokens", 0) + u.get("cache_creation_input_tokens", 0) + u.get("cache_read_input_tokens", 0)
    return None


def message(ctx, prompt, state, threshold):
    parts, state = [], dict(state)
    if ctx is not None and ctx < threshold:
        state.pop("band", None)  # compaction dropped context: re-arm for the next climb
    if ctx is not None and ctx >= threshold:
        band = ctx // BAND
        if band > state.get("band", -1):
            state["band"] = band
            parts.append(f"Context is {ctx // 1000}k tokens; auto-compaction fires near 800k. Tell the user in one "
                         f"line: at the next task boundary, `/compact <what to keep>` (or `/clear` before an "
                         f"unrelated task); hand long investigations to a seat.")
    words = " ".join(t for t in (prompt or "").split() if "/" not in t)  # paths name things, not tasks
    if HEAVY.search(words) and not state.get("effort_hint"):
        state["effort_hint"] = True
        parts.append("This looks like heavy planning or brainstorming. The default effort is medium; tell the user "
                     "once that `/effort high` (or `ultrathink` in the prompt) gives deeper reasoning for it.")
    return (" ".join(parts) or None), state


def main():
    try:
        d = json.load(sys.stdin)
        tx = Path(d.get("transcript_path", ""))
        sid = re.sub(r"[^\w-]", "", str(d.get("session_id") or "nosession"))
        state_path = Path(os.environ.get("TMPDIR") or "/tmp") / f"context_nudge_{sid}.json"
        state = json.loads(state_path.read_text()) if state_path.exists() else {}
        ctx = last_context(tx) if tx.is_file() else None
        msg, state = message(ctx, d.get("prompt", ""), state, int(os.environ.get("CLAUDE_NUDGE_TOKENS", DEFAULT_THRESHOLD)))
        state_path.write_text(json.dumps(state))
        if msg:
            print(json.dumps({"hookSpecificOutput": {"hookEventName": "UserPromptSubmit", "additionalContext": msg}}))
    except Exception:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
