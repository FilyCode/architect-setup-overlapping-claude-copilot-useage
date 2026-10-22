#!/usr/bin/env python3
"""UserPromptSubmit hook: nudge when context is large; hint effort for heavy planning.

Bands (owner 2026-10-22; token cost is 61% cache reads, so context length is the lever):
from 300k the hook nudges only at a task boundary (a git commit since the last prompt, or 30+
min idle, when the cache is cold anyway); from 500k it asks for /compact before the next task;
auto-compaction (CLAUDE_CODE_AUTO_COMPACT_WINDOW=650000) is the backstop. Each nudge fires once
per 100k band; CLAUDE_NUDGE_TOKENS overrides the 300k start. Also reminds once per session
when the retro log has open proposals and was last integrated over 7 days ago. Any error exits
0 silently.
"""
import datetime as dt
import json
import os
import re
import sys
from pathlib import Path

DEFAULT_THRESHOLD = 300_000
FIRM = 500_000
AUTO_COMPACT = 650_000
IDLE = dt.timedelta(minutes=30)

TAIL = 2_000_000
BAND = 100_000
RETRO_LOG = Path(os.environ.get("CLAUDE_RETRO_LOG", "/projectnb/liu-scc/philipp/"
                 "architect-setup-overlapping-claude-copilot-useage/docs/retros/retro-log.md"))
COMMIT = re.compile(r"(?:^|[;&|\n])\s*git\s+(?:-C\s+\S+\s+)?commit\b")
HEREDOC = re.compile(r"<<-?\s*['\"]?(\w+)['\"]?[^\n]*\n.*?\n\1(?=\n|$)", re.S)  # body is data, not commands
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


def boundary(transcript: Path, now: dt.datetime):
    """'commit' if a git commit ran since the last user prompt, 'idle' if the last entry is 30+ min old."""
    with open(transcript, "rb") as f:
        f.seek(0, 2)
        f.seek(max(0, f.tell() - TAIL))
        lines = f.read().decode("utf-8", errors="replace").split("\n")[1:]
    last_ts = None
    for line in reversed(lines):
        try:
            e = json.loads(line)
        except json.JSONDecodeError:
            continue
        last_ts = last_ts or e.get("timestamp")
        m = e.get("message") if isinstance(e.get("message"), dict) else {}
        content = m.get("content")
        if e.get("type") == "user" and (isinstance(content, str) or not any(
                isinstance(b, dict) and b.get("type") == "tool_result" for b in content or [])):
            break  # the previous prompt: anything older belongs to an earlier task
        for b in content if isinstance(content, list) else []:
            if e.get("type") == "assistant" and isinstance(b, dict) and b.get("type") == "tool_use" and COMMIT.search(HEREDOC.sub("", str(b.get("input", {}).get("command", "")))):
                return "commit"
    if last_ts and now - dt.datetime.fromisoformat(last_ts.replace("Z", "+00:00")) >= IDLE:
        return "idle"
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


def message(ctx, prompt, state, threshold, retro=None, boundary=None):
    parts, state = [], dict(state)
    if retro and not state.get("retro_hint"):
        state["retro_hint"] = True
        parts.append(retro)
    if ctx is not None and ctx < threshold:
        state.pop("band", None)  # compaction dropped context: re-arm for the next climb
    if ctx is not None and ctx >= threshold:
        band = ctx // BAND
        if band > state.get("band", -1) and (ctx >= FIRM or boundary):
            state["band"] = band
            if ctx >= FIRM:
                parts.append(f"Context is {ctx // 1000}k tokens; auto-compaction fires at {AUTO_COMPACT // 1000}k. "
                             f"Make the first line of your reply a request that the user run `/compact <what to "
                             f"keep>` (name what to keep) before starting the next task; finish only the step in "
                             f"progress until they do.")
            else:
                why = "work was just committed" if boundary == "commit" else "the session was idle, so the cache is cold"
                parts.append(f"Context is {ctx // 1000}k tokens and {why}: a good point to compact. If this prompt "
                             f"starts a new task, tell the user in one line to run `/compact <what to keep>` first; "
                             f"if it continues the current task, say nothing.")
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
        threshold = int(os.environ.get("CLAUDE_NUDGE_TOKENS", DEFAULT_THRESHOLD))
        edge = boundary(tx, dt.datetime.now(dt.timezone.utc)) if ctx and ctx >= threshold and tx.is_file() else None
        msg, state = message(ctx, d.get("prompt", ""), state, threshold, retro, edge)
        state_path.write_text(json.dumps(state))
        if msg:
            print(json.dumps({"hookSpecificOutput": {"hookEventName": "UserPromptSubmit", "additionalContext": msg}}))
    except Exception:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
