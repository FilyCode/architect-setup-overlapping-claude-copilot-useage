#!/usr/bin/env python3
"""PreToolUse(Agent/Task): two dispatch guards. Any internal error stays silent (allows).

1. Opus implementer (owner ruling 2026-11-25): the first non-blank line of the prompt must start with
   "Opus because:" (case-insensitive) followed by at least 10 non-space characters. Non-opus models and other
   seats pass.
2. Brief preflight (owner ruling 2026-11-26), for every named seat (any subagent_type not in UNNAMED):
   - backticked path tokens (contain "/" or end in a common extension, optional :N or :N-M) must exist,
     resolved as absolute/~, then against the hook cwd, then the git top-level of cwd; :N needs >= N lines.
     Skipped: globs, <placeholders>, $VARS, lines containing a CREATION_VERBS word, elided paths (contain "..."
     or the unicode ellipsis), a single segment plus trailing "/" (`reference/`: a directory relative to an
     unstated base), and absolute tokens whose first segment does not exist under "/" (`/provenance/x`).
   - "HEAD" followed within ~20 chars by a backticked 7-40 hex sha must prefix-match `git rev-parse HEAD`.
   On a mismatch the dispatch is denied ONCE per (session_id, prompt hash); resubmitting the identical prompt
   passes. State: $TMPDIR (or /tmp)/dispatch_guard_<session>.json. Subprocesses time out at 3 s; at most
   MAX_TOKENS tokens are checked.
"""
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path


REASON = re.compile(r"^\s*opus because:\s*(\S(?:\s*\S){9})", re.I)
MSG = ('Opus implementer without a stated reason (owner ruling 2026-11-25). Make the first non-blank line of the '
       'prompt "Opus because: <reason>" with at least 10 non-space characters of reason, or drop model: opus '
       "so the implementer runs on the default model.")

UNNAMED = {"", "general-purpose", "Explore", "Plan", "claude-code-guide", "fork"}
CREATION_VERBS = re.compile(r"\b(create|creating|write|writes|written|new|add|mkdir|output|produce|artifact|report to)", re.I)
EXTS = (".py", ".md", ".tsv", ".json", ".sh", ".qsub", ".yaml", ".yml", ".toml", ".txt")
MAX_TOKENS = 200
MAX_LISTED = 15
BACKTICK = re.compile(r"`([^`\n]+)`")
PATH_TOKEN = re.compile(r"^([\w./~+@%-]+?)(?::(\d+)(?:-(\d+))?)?$")
HEAD_CLAIM = re.compile(r"HEAD.{0,20}?`([0-9a-f]{7,40})`", re.I)
FIX = "Fix the brief, or resubmit the identical prompt to dispatch anyway."


def _git(cwd, *args):
    r = subprocess.run(["git", "-C", cwd, *args], capture_output=True, text=True, timeout=3)
    return r.stdout.strip() if r.returncode == 0 else ""


def check_brief(prompt, cwd):
    """Return a list of problem strings for path and HEAD claims in a brief (empty = fine)."""
    problems = []
    top = _git(cwd, "rev-parse", "--show-toplevel") if cwd else ""
    seen = 0
    for line in prompt.splitlines():
        if CREATION_VERBS.search(line):
            continue
        for tok in BACKTICK.findall(line):
            tok = tok.strip()
            if re.search(r"[*?\[\]{}<>$\s]|://", tok):
                continue
            m = PATH_TOKEN.match(tok)
            if not m or not ("/" in m.group(1) or m.group(1).endswith(EXTS)):
                continue
            path = m.group(1)
            if "..." in tok or "\u2026" in tok:
                continue
            if path.endswith("/") and path.count("/") == 1:
                continue
            if path.startswith("/") and not Path("/", path.split("/")[1]).exists():
                continue
            seen += 1
            if seen > MAX_TOKENS:
                break
            a, b = m.group(2), m.group(3)
            p = Path(path).expanduser()
            cands = [p] if p.is_absolute() else [Path(base) / p for base in (cwd, top) if base]
            found = next((c for c in cands if c.exists()), None)
            if found is None:
                problems.append(f"`{tok}`: missing")
            elif a and found.is_file():
                n = len(found.read_text(errors="replace").splitlines())
                need = max(int(a), int(b or 0))
                if n < need:
                    problems.append(f"`{tok}`: file has only {n} lines")
    if cwd:
        for sha in HEAD_CLAIM.findall(prompt):
            head = _git(cwd, "rev-parse", "HEAD")
            if head and not head.startswith(sha.lower()):
                problems.append(f"HEAD `{sha}`: HEAD is now {head[:7]}")
    return problems


def _deny(reason):
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny",
                      "permissionDecisionReason": reason}}))


def _first_time(d, prompt):
    """True (and record) unless this session already had the identical prompt denied."""
    sid = re.sub(r"[^\w-]", "", str(d.get("session_id") or "nosession"))
    state = Path(os.environ.get("TMPDIR") or "/tmp") / f"dispatch_guard_{sid}.json"
    h = hashlib.sha256(prompt.encode()).hexdigest()
    try:
        seen = json.loads(state.read_text())
    except Exception:
        seen = []
    if h in seen:
        return False
    state.write_text(json.dumps(seen + [h]))
    return True


def main():
    try:
        d = json.load(sys.stdin)
        ti = d["tool_input"]
        if d.get("tool_name") not in ("Agent", "Task"):
            return 0
        sub = ti.get("subagent_type")
        prompt = str(ti.get("prompt") or "")
        if sub == "implementer" and not _opus_ok(ti, prompt):
            _deny(MSG)
            return 0
        if str(sub or "") not in UNNAMED:
            problems = check_brief(prompt, d.get("cwd") or "")
            if problems and _first_time(d, prompt):
                more = f" (+{len(problems) - MAX_LISTED} more)" if len(problems) > MAX_LISTED else ""
                _deny("Brief preflight failed: " + "; ".join(problems[:MAX_LISTED]) + more + ". " + FIX)
    except Exception:
        return 0
    return 0


def _opus_ok(ti, prompt):
    model = str(ti.get("model") or "")
    if model != "opus" and not model.startswith("claude-opus"):
        return True
    first = next((ln for ln in prompt.splitlines() if ln.strip()), "")
    return bool(REASON.search(first))


if __name__ == "__main__":
    sys.exit(main())
