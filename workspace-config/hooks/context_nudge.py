#!/usr/bin/env python3
"""UserPromptSubmit hook: nudge when context is large; hint effort for heavy planning.

Bands (owner 2026-10-22, revised 2026-11-26; token cost is 61% cache reads, so context length is
the lever): compact belongs between tasks, /clear between phases and waves. From 200k the hook
suggests /compact only at a task boundary (a git commit since the last prompt, or 30+ min idle,
when the cache is cold anyway) and only if the next prompt starts a new task; from 500k it asks
for /compact before the next task; auto-compaction (CLAUDE_CODE_AUTO_COMPACT_WINDOW=650000) is
the backstop. Each nudge fires once per 100k band; CLAUDE_NUDGE_TOKENS overrides the 200k start. Also reminds once per session
when the retro log has open proposals and was last integrated over 7 days ago. Any error exits
0 silently.

Speed: reads a 256 KB transcript tail once (shared by both lookups), 2 MB only if that holds no usage entry
or previous prompt. At a wave/phase boundary (a retro-officer or aim-keeper dispatch, or a git add/commit of
PROJECT_STATE.md or a phases/ file, since the last prompt) with context >= CLAUDE_CLEAR_MIN (150k)
it tells the owner it is a good point to /clear and has Claude write a handoff (once per boundary
event; commit and idle boundaries never do); the
SessionStart hook session_handoff.py points the next session at it.
"""
import datetime as dt
import json
import os
import re
import sys
from pathlib import Path

DEFAULT_THRESHOLD = 200_000
FIRM = 500_000
AUTO_COMPACT = 650_000
IDLE = dt.timedelta(minutes=30)

TAIL_SMALL = 256 * 1024
TAIL = 2_000_000  # fallback when the small tail holds no usage entry / previous prompt
CLEAR_MIN = 150_000
HANDOFF_DIR = "/projectnb/liu-scc/philipp/software/claude-handoffs"
BAND = 100_000
RETRO_LOG = Path(os.environ.get("CLAUDE_RETRO_LOG", "/projectnb/liu-scc/philipp/"
                 "architect-setup-overlapping-claude-copilot-useage/docs/retros/retro-log.md"))
COMMIT = re.compile(r"(?:^|[;&|\n])\s*git\s+(?:-C\s+\S+\s+)?commit\b")
GIT_ADD = re.compile(r"(?:^|[;&|\n])\s*git\s+(?:-C\s+\S+\s+)?add\b")
PHASE_FILE = re.compile(r"PROJECT_STATE\.md|(?:^|[\s/'\"])phases/")
WAVE_AGENTS = ("retro-officer", "aim-keeper")  # the last steps of a wave close (skill wave-review)
HEREDOC = re.compile(r"<<-?\s*['\"]?(\w+)['\"]?[^\n]*\n.*?\n\1(?=\n|$)", re.S)  # body is data, not commands
HEAVY = re.compile(r"\b(brainstorm\w*|architect\w*|design doc|spec|implementation plan|writing-plans|plan the)\b", re.I)


_CACHE = {}


def _read_tail(transcript: Path, n: int):
    with open(transcript, "rb") as f:
        f.seek(0, 2)
        size = f.tell()
        f.seek(max(0, size - n))
        return f.read().decode("utf-8", errors="replace").split("\n")[1:], size > n


def _tail(transcript: Path, n: int):
    """(lines, truncated) of the last n bytes; one read per size and file state per process."""
    st = os.stat(transcript)
    key = (str(transcript), n, st.st_size, st.st_mtime_ns)
    if key not in _CACHE:
        _CACHE[key] = _read_tail(transcript, n)
    return _CACHE[key]


def last_context(transcript: Path):
    """Context size from the last usage entry: 256 KB tail first, the 2 MB tail only if none is there."""
    for n in (TAIL_SMALL, TAIL):
        lines, truncated = _tail(transcript, n)
        for line in reversed(lines):
            try:
                e = json.loads(line)
            except json.JSONDecodeError:
                continue
            u = (e.get("message") or {}).get("usage") if isinstance(e.get("message"), dict) else None
            if u:
                return u.get("input_tokens", 0) + u.get("cache_creation_input_tokens", 0) + u.get("cache_read_input_tokens", 0)
        if not truncated:
            break
    return None


def boundary_info(transcript: Path, now: dt.datetime):
    """(kind, key): kind 'wave' if since the last user prompt a retro-officer/aim-keeper was dispatched or a git
    add/commit touched PROJECT_STATE.md or a phases/ path; else 'commit' if a git commit ran (key: that tool_use's
    id, else its timestamp); else 'idle' if the last entry is 30+ min old (key: its timestamp); else (None, None).
    Wave beats commit beats idle: the scan runs back to the previous prompt before settling on a commit.
    Reads the 256 KB tail; retries at 2 MB only when the previous prompt is not in it."""
    for n in (TAIL_SMALL, TAIL):
        lines, truncated = _tail(transcript, n)
        last_ts, found_prompt, commit = None, False, None
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
                found_prompt = True
                break  # the previous prompt: anything older belongs to an earlier task
            for b in content if isinstance(content, list) else []:
                if e.get("type") != "assistant" or not isinstance(b, dict) or b.get("type") != "tool_use":
                    continue
                inp = b.get("input") if isinstance(b.get("input"), dict) else {}
                key = str(b.get("id") or e.get("timestamp") or "")
                cmd = HEREDOC.sub("", str(inp.get("command", "")))
                is_commit = bool(COMMIT.search(cmd))
                if (b.get("name") in ("Agent", "Task") and inp.get("subagent_type") in WAVE_AGENTS) or (
                        (is_commit or GIT_ADD.search(cmd)) and PHASE_FILE.search(cmd)):
                    return "wave", key
                if is_commit and commit is None:
                    commit = key  # keep scanning: a wave marker may sit behind it
        if found_prompt or not truncated:
            break
    if commit is not None:
        return "commit", commit
    if last_ts and now - dt.datetime.fromisoformat(last_ts.replace("Z", "+00:00")) >= IDLE:
        return "idle", last_ts
    return None, None


def boundary(transcript: Path, now: dt.datetime):
    """'wave', 'commit' or 'idle' (see boundary_info), else None."""
    return boundary_info(transcript, now)[0]


def handoff_path(cwd: str, base=None) -> Path:
    base = base or os.environ.get("CLAUDE_HANDOFF_DIR") or HANDOFF_DIR
    return Path(base) / re.sub(r"[^A-Za-z0-9]", "-", cwd) / "latest.md"


def clear_signal(ctx, kind, key, state, clear_min, cwd):
    """(systemMessage, additionalContext, state) once per wave boundary event at ctx >= clear_min."""
    state = dict(state)
    if ctx is None or kind != "wave" or ctx < clear_min or state.get("clear_key") == f"{kind}:{key}":
        return None, None, state
    state["clear_key"] = f"{kind}:{key}"
    path = handoff_path(cwd)
    sysmsg = f"Good point to /clear: wave/phase boundary at {ctx // 1000}k context. Claude is writing a handoff first."
    extra = (f"Wave/phase boundary at {ctx // 1000}k context. Before anything else, write a handoff (overwrite it) to {path} "
             f"(mkdir -p its directory) with these sections: done this session; files modified and uncommitted; running "
             f"SGE job ids and the artifact each should produce; findings and ledger paths; open owner approvals; "
             f"UNVERIFIED figures; the skill in use; Next step. Then tell the owner in one line it is safe to /clear "
             f"and that the next session is pointed at the handoff.")
    return sysmsg, extra, state


def retro_hint(log: Path, today: dt.date):
    """One line when proposals are open and the last integration is older than 7 days."""
    if not log.is_file():
        return None
    text = log.read_text()
    n = len(re.findall(r"^\s*- \[ \] R-", text, re.M))  # entries may indent their proposal bullets
    m = re.search(r"^Last integrated: (\d{4}-\d{2}-\d{2})", text, re.M)
    if not n or (m and (today - dt.date.fromisoformat(m.group(1))).days <= 7):
        return None
    return (f"Retro log: {n} open proposals, last integrated {m.group(1) if m else 'never'}. Tell the user "
            f"once: a weekly integration session runs skill `workspace-audit` (retro step).")


def message(ctx, prompt, state, threshold, retro=None, boundary=None, compact=True):
    parts, state = [], dict(state)
    if retro and not state.get("retro_hint"):
        state["retro_hint"] = True
        parts.append(retro)
    if ctx is not None and ctx < threshold:
        state.pop("band", None)  # compaction dropped context: re-arm for the next climb
    if ctx is not None and ctx >= threshold:
        band = ctx // BAND
        if compact and band > state.get("band", -1) and (ctx >= FIRM or boundary):
            state["band"] = band
            if ctx >= FIRM:
                parts.append(f"Context is {ctx // 1000}k tokens; auto-compaction fires at {AUTO_COMPACT // 1000}k. "
                             f"Make the first line of your reply a request that the user run `/compact <what to "
                             f"keep>` (name what to keep) before starting the next task; finish only the step in "
                             f"progress until they do.")
            else:
                why = "the session was idle, so the cache is cold" if boundary == "idle" else "work was just committed"
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
        _CACHE.clear()
        ctx = last_context(tx) if tx.is_file() else None
        retro = None if state.get("retro_hint") else retro_hint(RETRO_LOG, dt.date.today())
        threshold = int(os.environ.get("CLAUDE_NUDGE_TOKENS", DEFAULT_THRESHOLD))
        clear_min = int(os.environ.get("CLAUDE_CLEAR_MIN", CLEAR_MIN))
        kind = key = None
        if ctx and ctx >= min(threshold, clear_min) and tx.is_file():
            kind, key = boundary_info(tx, dt.datetime.now(dt.timezone.utc))
        edge = kind if ctx and ctx >= threshold else None
        sysmsg, extra, state = clear_signal(ctx, kind, key, state, clear_min, str(d.get("cwd") or os.getcwd()))
        msg, state = message(ctx, d.get("prompt", ""), state, threshold, retro, edge, compact=not sysmsg)  # one message, not two
        state_path.write_text(json.dumps(state))
        msg = " ".join(x for x in (msg, extra) if x) or None
        if msg:
            out = {"hookSpecificOutput": {"hookEventName": "UserPromptSubmit", "additionalContext": msg}}
            if sysmsg:
                out["systemMessage"] = sysmsg
            print(json.dumps(out))
    except Exception:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
