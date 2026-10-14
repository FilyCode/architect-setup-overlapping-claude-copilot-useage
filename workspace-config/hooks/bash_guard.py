#!/usr/bin/env python3
"""PreToolUse guard for Bash: blocks the shared-tree hazards and login-node pytest.

Tokenises with shlex; never regex-matches the raw command. Any internal error allows
the command (a broken guard must not become a source of spurious blocks).
Spec: docs/superpowers/specs/2026-10-14-setup-restructure-design.md §5.5.
"""
import json
import os
import re
import shlex
import sys

PROJECTS = "/projectnb/liu-scc/philipp/projects"
SEP = {";", "&&", "||", "|", "&", "\n"}
HEREDOC = re.compile(r"<<-?\s*(['\"]?)(\w+)\1")
VAR = re.compile(r"\$\{?(\w+)\}?")
CACHE = {"__pycache__", ".mypy_cache", ".pytest_cache", ".ruff_cache"}
BIG = 1_000_000  # bytes; rtk's measured savings came from cat on multi-GB files (DECISION-026)


def _lines(command: str):
    """Logical lines: backslash-newline joined, heredoc bodies dropped."""
    out, end = [], None
    for ln in command.replace("\\\n", " ").split("\n"):
        if end is not None:
            if ln.strip() == end:
                end = None
            continue
        out.append(ln)
        m = HEREDOC.search(ln)
        if m:
            end = m.group(2)
    return out


def _expand(arg: str, env: dict):
    """Substitute $NAME/${NAME} from assignments seen so far; None if anything stays unresolved."""
    val = VAR.sub(lambda m: env.get(m.group(1), m.group(0)), arg)
    return None if "$" in val or "`" in val else val


def _segments(command: str):
    """Yield (tokens, piped): piped is True when the segment's output feeds a `|`."""
    lex = shlex.shlex(command, posix=True, punctuation_chars=";&|")
    lex.whitespace_split = True
    seg = []
    for tok in lex:
        if tok in SEP or set(tok) <= set(";&|"):
            if seg:
                yield seg, tok == "|"
            seg = []
        else:
            seg.append(tok)
    if seg:
        yield seg, False


def _strip(seg):
    i = 0
    while i < len(seg) and "=" in seg[i] and not seg[i].startswith(("-", "=")) and seg[i].split("=")[0].isidentifier():
        i += 1
    seg = seg[i:]
    if seg and seg[0].startswith("\\"):
        seg = [seg[0][1:]] + seg[1:]
    if seg and seg[0] == "command":
        seg = seg[1:]
    return seg


def _git(seg):
    i, work_tree = 1, False
    while i < len(seg) and seg[i].startswith("-"):
        if seg[i] in ("-C", "-c", "--git-dir", "--work-tree"):
            work_tree |= seg[i] == "--work-tree"
            i += 2
            continue
        work_tree |= seg[i].startswith("--work-tree=")
        i += 1
    sub = seg[i] if i < len(seg) else ""
    rest = seg[i + 1:]
    if sub == "stash" and (not rest or rest[0] not in ("list", "show")):
        return "deny", "git stash mutates the shared index; copy the pre-fix file with `git show HEAD:<path>` instead."
    if sub == "checkout" and work_tree:
        return "deny", "git --work-tree checkout stages into the real index; read past commits with `git show <c>:<path>`."
    return "allow", ""


def _under_projects(arg, cwd):
    if not os.path.isabs(arg) and cwd is None:
        return False
    p = os.path.normpath(arg if os.path.isabs(arg) else os.path.join(cwd, arg))
    return p == PROJECTS or p.startswith(PROJECTS + os.sep)


def _scratch(path, cwd):
    """Caches and agent scratch areas: .superpowers/sdd/, .scratch/, scratch*/ components."""
    full = os.path.normpath(path if os.path.isabs(path) or cwd is None else os.path.join(cwd, path))
    parts = full.split(os.sep)
    return bool(CACHE & set(parts)) or "/.superpowers/sdd/" in full + "/" or \
        any(p == ".scratch" or p.startswith("scratch") for p in parts)


def _rm(seg, cwd, shvars):
    flags = [a for a in seg[1:] if a.startswith("-")]
    recursive = any(f in ("-r", "-R", "--recursive") or (not f.startswith("--") and ("r" in f or "R" in f)) for f in flags)
    if not recursive:
        return "allow", ""
    for raw in seg[1:]:
        if raw.startswith("-") or ">" in raw or "<" in raw:
            continue
        t = _expand(raw, shvars)
        if t is None or _scratch(t, cwd):
            continue
        if _under_projects(t, cwd):
            return "deny", "Recursive delete inside projects/: delete the specific files you created, by name."
    return "allow", ""


def _cat(seg, cwd, shvars, piped):
    """Warn on cat of a large file whose output reaches the context (not piped, not redirected)."""
    if piped or any(t.lstrip("1").startswith(">") for t in seg[1:]):
        return ("allow", "")
    for a in seg[1:]:
        path = _expand(a, shvars)
        if not path or path.startswith("-"):
            continue
        if not os.path.isabs(path):
            if cwd is None:
                continue
            path = os.path.join(cwd, path)
        try:
            if os.path.getsize(path) > BIG:
                return ("warn", f"cat of a {os.path.getsize(path) // 1_000_000} MB file: bound it "
                                "(head -n N, sed -n 'A,Bp', or Read with offset/limit).")
        except OSError:
            continue
    return ("allow", "")


def _find(seg, shvars):
    """Warn on find from / or home without -maxdepth."""
    if "-maxdepth" in seg:
        return ("allow", "")
    home = shvars["HOME"]
    for a in seg[1:]:
        if a.startswith("-") or a in ("(", "!"):
            break
        path = _expand(a, shvars)
        if a.rstrip("/") == "~" or path in ("/", home, home + "/"):
            return ("warn", "find from / or home without -maxdepth walks everything: add -maxdepth N "
                            "or start from a narrower directory.")
    return ("allow", "")


def _is_assign(tok):
    name, eq, _ = tok.partition("=")
    return bool(eq) and name.isidentifier()


def decide(command: str, cwd: str, env: dict):
    shvars = {"PWD": cwd, "HOME": os.path.expanduser("~")}
    warn = None
    for line in _lines(command):
        try:
            segs = list(_segments(line))
        except ValueError:
            continue
        for raw, piped in segs:
            if raw and raw[0] == "export":
                raw = raw[1:]
            for tok in raw:
                if not _is_assign(tok):
                    break
                name, _, value = tok.partition("=")
                exp = _expand(value, shvars)
                if exp is not None:
                    shvars[name] = exp
                else:
                    shvars.pop(name, None)
            seg = _strip(raw)
            if not seg:
                continue
            cmd = os.path.basename(seg[0])
            if cmd == "cd":
                target = _expand(seg[1], shvars) if len(seg) > 1 else shvars["HOME"]
                cwd = None if target is None or cwd is None and not os.path.isabs(target) else \
                    os.path.normpath(target if os.path.isabs(target) else os.path.join(cwd, target))
                if cwd:
                    shvars["PWD"] = cwd
                continue
            if cmd == "git":
                v = _git(seg)
            elif cmd == "rm":
                v = _rm(seg, cwd, shvars)
            elif cmd in ("pytest", "py.test") or (cmd.startswith("python") and seg[1:3] == ["-m", "pytest"]):
                v = ("deny", "pytest outside an SGE job ($JOB_ID unset): submit it with qsub.") if not env.get("JOB_ID") else ("allow", "")
            elif cmd == "find" and "-delete" in seg and cwd and any(_under_projects(a, cwd) for a in seg[1:2] or ["."]):
                v = ("warn", "find -delete under projects/: confirm the match list first with the same find and no -delete.")
            elif cmd == "find":
                v = _find(seg, shvars)
            elif cmd == "cat":
                v = _cat(seg, cwd, shvars, piped)
            else:
                v = ("allow", "")
            if v[0] == "deny":
                return v
            if v[0] == "warn":
                warn = v
    return warn or ("allow", "")


def main():
    try:
        d = json.load(sys.stdin)
        if d.get("tool_name") != "Bash":
            return 0
        verdict, reason = decide(d.get("tool_input", {}).get("command", ""), d.get("cwd", os.getcwd()), dict(os.environ))
        if verdict == "deny":
            print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse",
                  "permissionDecision": "deny", "permissionDecisionReason": reason}}))
        elif verdict == "warn":
            print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "additionalContext": reason}}))
    except Exception:
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
