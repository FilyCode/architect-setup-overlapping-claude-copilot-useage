#!/usr/bin/env python3
"""PostToolUse(Bash): record the SGE job ids this session submits, so bash_guard may allow `qdel` of those only.

When a command segment starts with `qsub` and tool_response.stdout holds SGE's submit line
(`Your job 8762857 ("name") has been submitted` or `Your job-array 8762857.1-4:1 ("name") ...`),
the id is appended to <ledger dir>/<session_id>.txt. The ledger dir is $CLAUDE_SESSION_JOBS_DIR,
default /projectnb/liu-scc/philipp/software/claude-session-jobs (home has a 10 GB quota).
Any internal error stays silent.
"""
import json
import os
import re
import shlex
import sys

LEDGER_DIR = "/projectnb/liu-scc/philipp/software/claude-session-jobs"
SUBMITTED = re.compile(r"^Your job(?:-array)? (\d+)[ .]", re.M)
SESSION = re.compile(r"^[\w.-]+$")


def ledger_path(session_id, env):
    """Ledger file for a session, or None when the id is empty or not a safe file name."""
    if not session_id or not SESSION.match(session_id) or session_id.startswith("."):
        return None
    return os.path.join(env.get("CLAUDE_SESSION_JOBS_DIR") or LEDGER_DIR, session_id + ".txt")


def owned_ids(session_id, env):
    """Set of job ids recorded for this session; empty when there is no ledger."""
    path = ledger_path(session_id, env)
    try:
        with open(path) as f:
            return {ln.strip() for ln in f if ln.strip()}
    except (OSError, TypeError):
        return set()


def runs_qsub(command):
    """True when some segment's command word is qsub (after env assignments)."""
    lex = shlex.shlex(command, posix=True, punctuation_chars=";&|")
    lex.whitespace_split = True
    first = True
    for tok in lex:
        if set(tok) <= set(";&|"):
            first = True
        elif first and not ("=" in tok and tok.split("=")[0].isidentifier()):
            if os.path.basename(tok) == "qsub":
                return True
            first = False
    return False


def main():
    try:
        d = json.load(sys.stdin)
        if d.get("tool_name") != "Bash" or not runs_qsub(d["tool_input"].get("command") or ""):
            return 0
        ids = SUBMITTED.findall(d["tool_response"].get("stdout") or "")
        path = ledger_path(d.get("session_id"), dict(os.environ))
        if ids and path:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "a") as f:
                f.writelines(i + "\n" for i in ids)
    except Exception:
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
