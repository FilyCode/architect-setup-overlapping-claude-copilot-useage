#!/usr/bin/env python3
"""SubagentStop hook: nudge the parent session to dispatch docs-sync after a clean
critic-reviewer pass. Deterministic, no API calls -- same keyword-heuristic philosophy
as large-change-check.py, not a judge.

Scoped via the settings.json matcher to agent_type == "critic-reviewer" only (not
alignment-officer too -- one docs-sync dispatch per wave is enough, and critic-reviewer
is the one that always runs per subagent-dispatch.md's wave-end review section).

Never blocks (always exits 0) -- this is a soft nudge via hookSpecificOutput.additionalContext,
not a gate. Blocking (exit 2) on SubagentStop would prevent the SUBAGENT itself from
stopping, not the parent session -- the wrong target, since critic-reviewer has no Agent
tool to dispatch docs-sync with anyway. The parent session decides whether to act on the
nudge, same as any other prose rule in this workspace.

Any exception anywhere in this script exits 0 silently. A broken check must never
become a new source of spurious noise.
"""
import json
import re
import sys

TAIL_BYTES = 500_000  # only look at the last ~500KB of the transcript

CLEAN_VERDICT_RE = re.compile(
    r"\b(no (?:blocking |correctness )?issues(?: found)?|approved|looks good|"
    r"lgtm|passes review|ready to (?:merge|commit|ship)|nothing (?:else )?to flag|"
    r"no findings)\b",
    re.IGNORECASE,
)
ISSUE_RE = re.compile(
    r"\b(blocking|must fix|critical|\bbug\b|incorrect|fails?\b|doesn'?t work|"
    r"needs? (?:a )?fix|should be fixed|\bproblem\b|confirmed\b.*\bfinding)\b",
    re.IGNORECASE,
)
NEGATION_RE = re.compile(r"\b(no|not|isn'?t|doesn'?t|didn'?t|n't|without)\b", re.IGNORECASE)


def read_tail_text(path, max_bytes):
    with open(path, "rb") as f:
        f.seek(0, 2)
        size = f.tell()
        f.seek(max(0, size - max_bytes))
        data = f.read()
    return data.decode("utf-8", errors="replace")


def last_assistant_text_from_transcript(path):
    text = read_tail_text(path, TAIL_BYTES)
    lines = text.split("\n")
    for raw in reversed(lines):
        raw = raw.strip()
        if not raw:
            continue
        try:
            entry = json.loads(raw)
        except (json.JSONDecodeError, ValueError):
            continue
        if entry.get("type") != "assistant":
            continue
        parts = []
        for block in (entry.get("message") or {}).get("content", []) or []:
            if isinstance(block, dict) and block.get("type") == "text":
                parts.append(block.get("text", ""))
        if parts:
            return "\n".join(parts)
    return ""


def has_real_issue_signal(text):
    """ISSUE_RE alone would also fire on "no blocking issues" -- an unnegated match
    within ~25 chars is required to count as an actual problem."""
    for m in ISSUE_RE.finditer(text):
        window = text[max(0, m.start() - 25):m.start()]
        if not NEGATION_RE.search(window):
            return True
    return False


def looks_like_clean_review(text):
    if not text:
        return False
    if has_real_issue_signal(text):
        return False  # reads as having found something -- don't nudge, let it get fixed first
    return bool(CLEAN_VERDICT_RE.search(text))


def main():
    try:
        data = json.load(sys.stdin)
        if data.get("agent_type") != "critic-reviewer":
            sys.exit(0)

        text = data.get("last_assistant_message") or ""
        if not text:
            transcript_path = data.get("transcript_path")
            if not transcript_path:
                sys.exit(0)
            text = last_assistant_text_from_transcript(transcript_path)

        if not looks_like_clean_review(text):
            sys.exit(0)

        print(json.dumps({
            "hookSpecificOutput": {
                "hookEventName": "SubagentStop",
                "additionalContext": (
                    "critic-reviewer just reported a clean review (no blocking issues "
                    "detected in its closing message). Per subagent-dispatch.md's "
                    "wave-end review section, consider dispatching docs-sync now to "
                    "check for governance-doc drift while the wave's changes are fresh. "
                    "(Heuristic nudge -- .claude/hooks/docs-sync-nudge.py -- skip it if "
                    "docs-sync already ran this wave or clearly doesn't apply.)"
                ),
            }
        }))
        sys.exit(0)
    except Exception:
        sys.exit(0)  # fail open, always -- a broken check must never block


if __name__ == "__main__":
    main()
