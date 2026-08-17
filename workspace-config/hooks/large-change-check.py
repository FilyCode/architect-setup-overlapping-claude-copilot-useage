#!/usr/bin/env python3
"""Stop hook: flag large, seemingly-unverified changes. Deterministic, no API calls.

Replaces the DECISION-013 prompt-based Stop hook, which had a 100% API-error rate
against the hook evaluator's haiku access (see DECISION-016). This version can't
fail that way because it never calls a model -- it's a keyword/size heuristic, not
a judge. It will occasionally be wrong in both directions; that's the tradeoff for
being immune to the failure mode that made the previous one pure noise.

Fires on every Stop event (Stop supports no matcher/if-gating), but is a near-zero-cost
no-op for small turns -- the size check runs before anything else.

Any exception anywhere in this script exits 0 silently. A broken check must never
become a new source of spurious blocking.
"""
import json
import re
import sys

LARGE_FILES_THRESHOLD = 4       # distinct files touched this turn
LARGE_CHARS_THRESHOLD = 4000    # approx changed characters this turn (~100-150 lines)
TAIL_BYTES = 2_000_000          # only look at the last ~2MB of the transcript

COMPLETION_RE = re.compile(
    r"\b(done|complete|completed|fixed|resolved|passes|passing|verified|"
    r"all set|working now|ready to (?:commit|push|merge))\b",
    re.IGNORECASE,
)
NEGATION_RE = re.compile(r"\b(not|isn'?t|doesn'?t|didn'?t|n't|no longer|without)\b", re.IGNORECASE)
EVIDENCE_RE = re.compile(
    r"(\d+\s*/\s*\d+)|(\bexit\s*0\b)|(\bexit_status\s*0\b)|(\bPASSED\b)|(\bFAILED\b)|"
    r"(\bqacct\b)|(\bqstat\b)|(```)|(\.py:\d+)|(\.md:\d+)|(job\s+\d+)",
    re.IGNORECASE,
)


def read_tail_lines(path, max_bytes):
    with open(path, "rb") as f:
        f.seek(0, 2)
        size = f.tell()
        f.seek(max(0, size - max_bytes))
        data = f.read()
    text = data.decode("utf-8", errors="replace")
    lines = text.split("\n")
    if len(lines) > 1:
        lines = lines[1:]  # drop possibly-partial first line
    return lines


def is_real_user_prompt(entry):
    if entry.get("type") != "user":
        return False
    content = (entry.get("message") or {}).get("content")
    if isinstance(content, str):
        return True
    if isinstance(content, list):
        return any(isinstance(b, dict) and b.get("type") != "tool_result" for b in content)
    return False


def measure_current_turn(lines):
    """Walk backward from the end; stop at the most recent real user prompt."""
    files = set()
    chars = 0
    for raw in reversed(lines):
        raw = raw.strip()
        if not raw:
            continue
        try:
            entry = json.loads(raw)
        except (json.JSONDecodeError, ValueError):
            continue
        if is_real_user_prompt(entry):
            break
        if entry.get("type") != "assistant":
            continue
        for block in (entry.get("message") or {}).get("content", []) or []:
            if not (isinstance(block, dict) and block.get("type") == "tool_use"):
                continue
            name = block.get("name")
            inp = block.get("input") or {}
            if name == "Edit":
                fp = inp.get("file_path")
                if fp:
                    files.add(fp)
                chars += len(str(inp.get("old_string", ""))) + len(str(inp.get("new_string", "")))
            elif name == "Write":
                fp = inp.get("file_path")
                if fp:
                    files.add(fp)
                chars += len(str(inp.get("content", "")))
            elif name == "MultiEdit":
                fp = inp.get("file_path")
                if fp:
                    files.add(fp)
                for e in inp.get("edits", []) or []:
                    chars += len(str(e.get("old_string", ""))) + len(str(e.get("new_string", "")))
    return len(files), chars


def looks_like_bare_completion_claim(text):
    if not text:
        return False
    if EVIDENCE_RE.search(text):
        return False  # already cites test output, an artifact, or a command result
    for m in COMPLETION_RE.finditer(text):
        window = text[max(0, m.start() - 25):m.start()]
        if not NEGATION_RE.search(window):
            return True
    return False


def main():
    try:
        data = json.load(sys.stdin)
        transcript_path = data.get("transcript_path")
        last_msg = data.get("last_assistant_message") or ""
        if not transcript_path:
            sys.exit(0)

        lines = read_tail_lines(transcript_path, TAIL_BYTES)
        n_files, n_chars = measure_current_turn(lines)
        is_large = n_files >= LARGE_FILES_THRESHOLD or n_chars >= LARGE_CHARS_THRESHOLD
        if not is_large:
            sys.exit(0)

        if looks_like_bare_completion_claim(last_msg):
            sys.stderr.write(
                f"Large change this turn ({n_files} files, ~{n_chars} chars) and the "
                "closing message reads as a completion claim with no visible evidence "
                "(no test output, exit status, qacct/qstat result, or file:line reference "
                "in the same message). Before ending: point to the specific command output, "
                "artifact, or diff that backs this up -- or say plainly if it wasn't checked.\n"
                "(Heuristic, keyword-based check -- .claude/hooks/large-change-check.py. "
                "If this misfired, just state your evidence or note none exists; it will "
                "not re-block for the same reason.)\n"
            )
            sys.exit(2)

        sys.exit(0)
    except Exception:
        sys.exit(0)  # fail open, always -- a broken check must never block


if __name__ == "__main__":
    main()
