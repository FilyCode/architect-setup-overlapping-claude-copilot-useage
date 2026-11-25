#!/usr/bin/env python3
"""PreCompact hook: print LIVE state on stdout so the compaction summary keeps it (Claude Code feeds stdout to the summary).

Sections, each only when non-empty: (1) SGE jobs this session submitted (job_ledger.py ledger) still in `qstat -u $USER`
(ledger ids marked `state unknown` when qstat fails); (2) uncommitted files of the git repo containing cwd, at most 30
lines; (3) the handoff file path (session_handoff.py convention) when under 12 h old, never its body.
Output is capped at 4000 chars. Never blocks: any error exits 0 silently.
"""
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

CAP = 4000
MAX_FILES = 30
MAX_AGE = 12 * 3600
HEADER = "Preserve verbatim in the summary (live state at compaction):"
MARKER = "\n[truncated at 4000 chars]"


def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True, timeout=5)


def jobs_section(session_id, env):
    from job_ledger import owned_ids
    ids = sorted(owned_ids(session_id, env), key=lambda s: (len(s), s))
    if not ids:
        return None
    try:
        r = run(["qstat", "-u", env["USER"]])
        if r.returncode != 0:
            raise OSError("qstat failed")
        live = {m.group(1) for m in re.finditer(r"^\s*(\d+)\s", r.stdout, re.M)}
    except Exception:
        return "SGE jobs submitted this session (qstat failed, state unknown): " + ", ".join(ids)
    mine = [i for i in ids if i.split(".")[0] in live]
    return "SGE jobs this session submitted, still queued/running: " + ", ".join(mine) if mine else None


def git_section(cwd):
    r = run(["git", "-C", cwd, "status", "--porcelain"])
    lines = r.stdout.splitlines() if r.returncode == 0 else []
    if not lines:
        return None
    out = ["Uncommitted files in the git repo containing cwd:"] + ["  " + ln for ln in lines[:MAX_FILES]]
    if len(lines) > MAX_FILES:
        out.append(f"  ... and {len(lines) - MAX_FILES} more")
    return "\n".join(out)


def handoff_section(cwd, env):
    f = Path(env.get("CLAUDE_HANDOFF_DIR") or _handoff_dir()) / re.sub(r"[^A-Za-z0-9]", "-", cwd) / "latest.md"
    age = time.time() - f.stat().st_mtime
    return f"Handoff file (read it after compaction): {f}" if age < MAX_AGE else None


def _handoff_dir():
    from session_handoff import HANDOFF_DIR
    return HANDOFF_DIR


def section(fn, *args):
    try:
        return fn(*args)
    except Exception:
        return None


def main():
    try:
        d = json.load(sys.stdin)
        env = dict(os.environ)
        cwd = str(d.get("cwd") or os.getcwd())
        parts = [section(jobs_section, d.get("session_id"), env), section(git_section, cwd),
                 section(handoff_section, cwd, env)]
        parts = [p for p in parts if p]
        if not parts:
            return 0
        text = HEADER + "\n" + "\n".join(parts)
        if len(text) > CAP:
            text = text[:CAP - len(MARKER)] + MARKER
        sys.stdout.write(text + "\n" if len(text) < CAP else text)
    except Exception:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
