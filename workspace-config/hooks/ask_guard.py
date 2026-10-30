#!/usr/bin/env python3
"""PreToolUse(AskUserQuestion): deny once when an owner question breaks the plain-words rule (core.md).

Flags an option whose description lacks `Pro:` or `Con:`, and unexplained codes (DECISION-145a, MA-172,
D018, R-20261029-2, PR #107, #107, git SHAs) in question, label or description text. A code is explained
when followed by `(` or preceded by `(`. The first call with problems is denied and its hash recorded in
$TMPDIR/ask_guard_<sid>.json; resubmitting the identical call passes. Any internal error stays silent.
"""
import hashlib
import json
import os
import re
import sys
from pathlib import Path

PRO = re.compile(r"\bpros?:", re.I)
CON = re.compile(r"\bcons?:", re.I)
CODE = re.compile(r"(?<![\w#-])(?:[A-Z][A-Z0-9]*(?:-\d[\w]*)+|D\d{2,}|(?:PR\s*)?#\d+|[0-9a-f]{7,40})(?![\w-])")
TAIL = ("Owner decisions need plain words, every code explained, and Pro: and Con: on each option, "
        "recommended option first (core.md). Fix and ask again; if an item is a false alarm, "
        "resubmit the identical call and it will pass.")


def codes(text: str):
    found = []
    for m in CODE.finditer(text):
        tok = m.group()
        if re.fullmatch(r"[0-9a-f]{7,40}", tok) and not (re.search(r"\d", tok) and re.search(r"[a-f]", tok)):
            continue
        before, after = text[:m.start()], text[m.end():]
        if after.startswith("(") or after.startswith(" (") or before.endswith("("):
            continue
        found.append(tok)
    return found


def problems(ti):
    out = []
    for q in ti.get("questions") or []:
        head = q.get("header") or q.get("question") or "?"
        bad = codes(str(q.get("question") or ""))
        if bad:
            out.append(f"[{head}] question text: unexplained code(s) {', '.join(bad)}")
        for o in q.get("options") or []:
            label, desc = str(o.get("label") or ""), str(o.get("description") or "")
            missing = [m for m, rx in (("Pro:", PRO), ("Con:", CON)) if not rx.search(desc)]
            if missing:
                out.append(f"[{head}] option '{label}': description lacks {' and '.join(missing)}")
            bad = codes(label) + codes(desc)
            if bad:
                out.append(f"[{head}] option '{label}': unexplained code(s) {', '.join(bad)}")
    return out


def main():
    try:
        d = json.load(sys.stdin)
        ti = d["tool_input"]
        if d.get("tool_name") != "AskUserQuestion":
            return 0
        found = problems(ti)
        if not found:
            return 0
        sid = re.sub(r"[^\w-]", "", str(d.get("session_id") or "nosession"))
        path = Path(os.environ.get("TMPDIR") or "/tmp") / f"ask_guard_{sid}.json"
        state = json.loads(path.read_text()) if path.exists() else {}
        digest = hashlib.sha256(json.dumps(ti, sort_keys=True).encode()).hexdigest()
        if digest in state.get("seen", []):
            return 0
        path.write_text(json.dumps({"seen": state.get("seen", []) + [digest]}))
        reason = "Question needs fixing:\n- " + "\n- ".join(found) + "\n" + TAIL
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny",
                                                  "permissionDecisionReason": reason}}))
    except Exception:
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
