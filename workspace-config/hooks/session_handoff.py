#!/usr/bin/env python3
"""SessionStart hook: point a fresh session at the handoff it wrote itself (context_nudge.py writes the request).

Path convention (single home, imported by context_nudge.py and precompact_state.py): handoff_path(cwd, env) is
<handoff dir>/<sanitized cwd>/<key>.md, where handoff_key(env) is the SGE job id $JOB_ID when set, else pid<getppid>
(the Claude process; both survive /clear), sanitised to [A-Za-z0-9_.-]. Concurrent sessions in one cwd therefore never
share a file. CLAUDE_HANDOFF_DIR overrides the directory.

On source "clear" or "startup", when this session's own file is under 12 h old, adds one line naming it and its age
(a pointer only, never the body). On "startup" (new process, new key) it also lists up to 3 other handoff files of the
same cwd dir under 12 h old, newest first, with age and first heading (<= 100 chars), marked as other sessions' files
(a legacy latest.md is listed there too). On both it deletes *.md files of that dir older than 14 days whose name
is a key or latest.md; nothing else is touched. Any error exits 0 silently.
"""
import json
import os
import re
import sys
import time
from pathlib import Path

HANDOFF_DIR = "/projectnb/liu-scc/philipp/software/claude-handoffs"
MAX_AGE = 12 * 3600
PRUNE_AGE = 14 * 86400
MAX_OTHERS = 3
KEY_MD = re.compile(r"^[A-Za-z0-9_.-]+\.md$")


def handoff_key(env) -> str:
    raw = str(env.get("JOB_ID") or "").strip() or f"pid{os.getppid()}"
    return re.sub(r"[^A-Za-z0-9_.-]", "_", raw)


def handoff_dir(cwd: str, env, base=None) -> Path:
    base = base or env.get("CLAUDE_HANDOFF_DIR") or HANDOFF_DIR
    return Path(base) / re.sub(r"[^A-Za-z0-9]", "-", cwd)


def handoff_path(cwd: str, env, base=None) -> Path:
    return handoff_dir(cwd, env, base) / f"{handoff_key(env)}.md"


def ago(age):
    return f"{int(age // 60)} min ago" if age < 3600 else f"{age / 3600:.1f} h ago"


def prune(d: Path, now):
    for f in d.iterdir():
        try:
            if KEY_MD.match(f.name) and f.is_file() and now - f.stat().st_mtime > PRUNE_AGE:
                f.unlink()
        except Exception:
            pass


def heading(f: Path) -> str:
    try:
        with open(f, errors="replace") as fh:
            for line in fh:
                if line.lstrip().startswith("#"):
                    return line.strip()[:100]
    except Exception:
        pass
    return "(no heading)"


def others(d: Path, own: Path, now):
    found = []
    for f in d.iterdir():
        try:
            if f != own and KEY_MD.match(f.name) and f.is_file() and now - f.stat().st_mtime < MAX_AGE:
                found.append((f.stat().st_mtime, f))
        except Exception:
            pass
    return [(f, now - t) for t, f in sorted(found, key=lambda x: -x[0])[:MAX_OTHERS]]


def main():
    try:
        d = json.load(sys.stdin)
        src = d.get("source")
        if src not in ("clear", "startup"):
            return 0
        cwd = str(d.get("cwd") or os.getcwd())
        env = dict(os.environ)
        own = handoff_path(cwd, env)
        now = time.time()
        try:
            prune(own.parent, now)
        except Exception:
            pass
        parts = []
        try:
            age = now - own.stat().st_mtime
            if age < MAX_AGE:
                parts.append(f"Handoff from the previous session: {own} (written {ago(age)}). Read it before starting.")
        except Exception:
            pass
        if src == "startup":
            try:
                lst = others(own.parent, own, now)
            except Exception:
                lst = []
            if lst:
                lines = [f"  {f} ({ago(a)}): {heading(f)}" for f, a in lst]
                parts.append("Other handoff files in this directory belong to other sessions, not yours; read one only "
                             "if the user says it is theirs:\n" + "\n".join(lines))
        if parts:
            print(json.dumps({"hookSpecificOutput": {"hookEventName": "SessionStart",
                  "additionalContext": "\n".join(parts)}}))
    except Exception:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
