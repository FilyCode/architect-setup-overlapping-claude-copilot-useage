#!/usr/bin/env python3
"""UserPromptSubmit hook: nudge when context is large; hint effort for heavy planning.

Threshold is declared workspace-specific (2026-10-14 corpus: calls above 500k carry
~69% of main-session cost) and overridable with CLAUDE_NUDGE_TOKENS. Owner band
2026-10-14: nudge at 50 % of the 1M window, auto-compaction backstop at 80 %
(CLAUDE_CODE_AUTO_COMPACT_WINDOW=800000), so compaction lands at a task boundary. Fires once per 100k band. Also reminds once per session
when the retro log has open proposals and was last integrated over 7 days ago. Any error exits
0 silently.
"""
import datetime as dt
import json
import os
import re
import sys
from pathlib import Path

DEFAULT_THRESHOLD = 500_000

TAIL = 2_000_000
BAND = 100_000
RETRO_LOG = Path(os.environ.get("CLAUDE_RETRO_LOG", "/projectnb/liu-scc/philipp/"
                 "architect-setup-overlapping-claude-copilot-useage/docs/retros/retro-log.md"))
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


def retro_hint(log: Path, today: dt.date):
    """One line when proposals are open and the last integration is older than 7 days."""
    if not log.is_file():
        return None
    text = log.read_text()
    n = len(re.findall(r"^- \[ \] R-", text, re.M))
    m = re.search(r"^Last integrated: (\d{4}-\d{2}-\d{2})", text, re.M)
    if not n or (m and (today - dt.date.fromisoformat(m.group(1))).days <= 7):
        return None
    return (f"Retro log: {n} open proposals, last integrated {m.group(1) if m else 'never'}. Tell the user "
            f"once: a weekly integration session runs skill `workspace-audit` (retro step).")


def message(ctx, prompt, state, threshold, retro=None):
    parts, state = [], dict(state)
    if retro and not state.get("retro_hint"):
        state["retro_hint"] = True
        parts.append(retro)
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
        retro = None if state.get("retro_hint") else retro_hint(RETRO_LOG, dt.date.today())
        msg, state = message(ctx, d.get("prompt", ""), state, int(os.environ.get("CLAUDE_NUDGE_TOKENS", DEFAULT_THRESHOLD)),
                             retro)
        state_path.write_text(json.dumps(state))
        if msg:
            print(json.dumps({"hookSpecificOutput": {"hookEventName": "UserPromptSubmit", "additionalContext": msg}}))
    except Exception:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
