#!/usr/bin/env python3
"""PreToolUse guard for Bash: SGE submissions request only the cores they use.

Why: 2026-10-31, 14 days of this user's jobs reserved 9143 core-h and used 3242 (35%); the
EC523 arrays held 4 or 8 slots and used ~1.1-1.25 (memory feedback_sge_least_cpu.md).

For qsub / qrsh / qlogin / qalter requesting `-pe <pe> K` with K > 1 (inline, in the script's
`#$` lines, or in a heredoc fed to qsub):
  - no `# cores: <reason>` note in the command or script -> deny: say which command uses the
    K threads ($NSLOTS), or request 1;
  - the job name's measured history (tools/sge_efficiency.py cache) shows < 50% of K used over
    >= 2 runs -> deny once with the numbers and a suggested K; resubmitting the identical command
    passes (state in $TMPDIR/qsub_guard_<sid>.json), for runs that really differ.
A qsub from a subagent is denied: the caller owns every qsub (core rule 5).
Any internal error allows the command; a broken guard must not block work.
"""
import hashlib
import json
import os
import shlex
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from bash_guard import _expand, _is_assign, _lines, _segments, _strip  # noqa: E402

REPO = HERE.parents[1]
CACHE = Path(os.environ.get("SGE_EFF_CACHE", "/projectnb/liu-scc/philipp/software/claude-sge")) / "efficiency.json"
STALE = 6 * 3600
SUBMIT = {"qsub", "qrsh", "qlogin", "qalter"}
NOARG = {"-cwd", "-V", "-terse", "-notify", "-clear", "-h", "-help", "-verify"}
MARK = "# cores:"
PROBE_MIN_TASKS = 10  # an unmeasured multi-slot array this large gets a probe first
# Node-local dirs: the execution host cannot read a job script kept there (R-20261102-3).
# QSUB_GUARD_NODE_LOCAL (":"-separated prefixes) overrides it; the tests use that, since pytest's tmp is node-local.
NODE_LOCAL = tuple(x for x in os.environ.get("QSUB_GUARD_NODE_LOCAL", "").split(":") if x) or tuple(
    sorted({"/scratch/", "/tmp/", os.path.join(os.environ.get("TMPDIR") or "/tmp", "")}))


def _options(tokens):
    """(opts, script): qsub-style options as {flag: [values]} and the first positional argument."""
    opts, i = {}, 0
    while i < len(tokens):
        t = tokens[i]
        if not t.startswith("-"):
            return opts, t
        n = 0 if t in NOARG else 2 if t == "-pe" else 1
        opts.setdefault(t, []).append(tokens[i + 1:i + 1 + n])
        i += 1 + n
    return opts, None


def _directives(text):
    """Options from `#$` lines of a job script."""
    toks = []
    for ln in text.splitlines():
        if ln.startswith("#$"):
            try:
                toks += shlex.split(ln[2:], comments=True)
            except ValueError:
                continue
    return _options(toks)[0]


def _heredoc_bodies(command):
    """Bodies of heredocs started on a line that runs a submit command."""
    out, body, end = [], [], None
    for ln in command.split("\n"):
        if end is not None:
            if ln.strip() == end:
                out.append("\n".join(body))
                end = None
            else:
                body.append(ln)
            continue
        if "<<" in ln and any(w in ln.split() for w in SUBMIT):
            tag = ln.split("<<", 1)[1].lstrip("-").strip().split()[0] if ln.split("<<", 1)[1].strip() else ""
            end, body = tag.strip("'\""), []
    return out


def _slots(opts):
    for vals in reversed(opts.get("-pe", [])):
        if len(vals) == 2:
            rng = vals[1].split("-")[-1]
            return int(rng) if rng.isdigit() else None
    return 1 if "-pe" not in opts else None


def _tasks(opts):
    """Number of array tasks from `-t a-b[:s]` (1 when not an array or unparseable)."""
    try:
        spec = opts["-t"][-1][0]
        rng, _, step = spec.partition(":")
        a, _, b = rng.partition("-")
        return max(1, (int(b or a) - int(a)) // int(step or 1) + 1)
    except (KeyError, IndexError, ValueError):
        return 1


def _log(entry):
    """Append one verdict to guard.log next to the cache, so `# cores:` notes can be audited."""
    try:
        with open(CACHE.parent / "guard.log", "a") as fh:
            fh.write(json.dumps(entry) + "\n")
    except OSError:
        pass


def _summary():
    try:
        data = json.loads(CACHE.read_text())
    except (OSError, ValueError):
        data = {}
    if time.time() - data.get("updated", 0) > STALE:
        try:  # refresh in the background for the next call; this call uses what it has
            subprocess.Popen([sys.executable, str(REPO / "tools" / "sge_efficiency.py"), "refresh"],
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
        except OSError:
            pass
    return data.get("summary", {})


def submissions(command, cwd):
    """Yield (verb, K or None, job name or None, has_mark, array tasks) for each submit command."""
    bodies = iter(_heredoc_bodies(command))
    shvars = {k: v for k, v in os.environ.items() if k in ("HOME", "TMPDIR", "USER", "PWD")}
    for line in _lines(command):
        try:
            segs = list(_segments(line))
        except ValueError:
            continue
        for raw, _ in segs:
            for tok in raw[1:] if raw and raw[0] == "export" else raw:
                if not _is_assign(tok):
                    break
                name, _, value = tok.partition("=")
                shvars[name] = _expand(value, shvars) or ""
            seg = [(_expand(t, shvars) or t) for t in _strip(raw)]
            if seg and seg[0] == "cd" and len(seg) > 1 and "$" not in seg[1]:
                cwd = os.path.normpath(os.path.join(cwd or "/", os.path.expanduser(seg[1])))
                continue
            if not seg or os.path.basename(seg[0]) not in SUBMIT:
                continue
            verb = os.path.basename(seg[0])
            opts, script = _options(seg[1:])
            text = ""
            if verb == "qsub" and "<<" in line:
                text = next(bodies, "")
            elif verb == "qsub" and script and opts.get("-b", [["n"]])[-1][:1] != ["y"]:
                p = Path(script) if os.path.isabs(script) else Path(cwd or ".") / script
                if os.path.normpath(str(p)).startswith(NODE_LOCAL):
                    yield verb, ("node-local", str(p)), None, MARK in command, 1
                    continue
                try:
                    text = p.read_text(errors="replace")[:200_000]
                except OSError:
                    text = None
            if text is None:
                yield verb, ("unreadable", str(p)), None, MARK in command, 1
                continue
            merged = _directives(text)
            for k, v in opts.items():  # command-line options override script directives
                merged[k] = v
            name = (merged.get("-N") or [[None]])[-1][:1]
            name = name[0] if name else None
            if name is None and verb == "qsub" and script and "<<" not in line:
                name = os.path.basename(script)
            yield verb, _slots(merged), name, MARK in command or MARK in text, _tasks(merged)


def decide(command, cwd, summary, is_subagent=False):
    for verb, k, name, marked, tasks in submissions(command, cwd):
        if is_subagent and verb in ("qsub", "qrsh", "qlogin"):
            return "deny", ("The caller owns every qsub (core rule 5): write the job spec (script, resources, "
                            "expected artifact) into your report and stop.")
        if isinstance(k, tuple) and k[0] == "node-local":
            return "deny", (f"qsub: the job script {k[1]} is on a node-local path; the execution host "
                            "cannot read it (jobs 8393676, 8393908). Write the script under /projectnb "
                            "(e.g. the project's jobs/ or the findings dir) and submit that path.")
        if isinstance(k, tuple):
            return "warn", (f"qsub: could not read {k[1]} to check its `#$ -pe` slots. Make sure K matches "
                            "the threads the job really uses (skill running-sge-jobs).")
        if k is None:
            return "warn", (f"{verb}: could not read the requested slot count (variable or range in -pe). "
                            "Make sure K matches the threads the job really uses (skill running-sge-jobs).")
        if k <= 1 or (verb == "qalter" and marked):
            continue
        hist = summary.get(name or "", {})
        seen = f" Measured for '{name}': {hist['cores_used']} cores used of {hist['slots']:g} over " \
               f"{hist['n']} runs." if hist else ""
        if not marked:
            return "deny", (f"{verb} requests {k} slots without a `{MARK} <reason>` note.{seen} SGE charges "
                            "every reserved core. Request 1 unless the job runs K threads; then add e.g. "
                            f"`#$ -pe omp {k}  {MARK} bowtie2 -p $NSLOTS` to the script (or as a comment on "
                            "the command) and resubmit. Check with tools/sge_efficiency.py lookup <name>.")
        if not hist and tasks >= PROBE_MIN_TASKS and verb == "qsub":
            return "deny-once", (f"qsub: array of {tasks} tasks x {k} slots for '{name}', which has no measured "
                                 "run. Submit a probe first (-t 1-2), check `tools/sge_efficiency.py job <id>` "
                                 "when it ends, then submit the rest with the measured K. Resubmitting the "
                                 "identical command passes.")
        if hist and hist["n"] >= 2 and hist["eff"] < 0.5 and k >= 2 * hist["cores_used"]:
            sys.path.insert(0, str(REPO / "tools"))
            from sge_efficiency import suggest
            return "deny-once", (f"{verb} requests {k} slots, but '{name}' used {hist['cores_used']} cores "
                                 f"(median, {hist['n']} runs, {hist['eff']:.0%} of its slots). Request "
                                 f"-pe omp {suggest(hist['cores_used'])}; do not add slots for memory (SCC enforces "
                                 "memory loosely; a higher mem_per_core narrows the hosts). If this run really differs, resubmit the identical "
                                 "command and it will pass.")
    return "allow", ""


def main():
    try:
        d = json.load(sys.stdin)
        if d.get("tool_name") != "Bash":
            return 0
        cmd = d.get("tool_input", {}).get("command", "")
        if not any(w in cmd for w in SUBMIT):
            return 0
        if not any(True for _ in submissions(cmd, d.get("cwd"))):
            return 0
        verdict, reason = decide(cmd, d.get("cwd"), _summary(), bool(d.get("agent_id")))
        entry = {"ts": int(time.time()), "sid": d.get("session_id"), "agent": d.get("agent_type"),
                 "cwd": d.get("cwd"), "verdict": verdict, "reason": reason[:200], "command": cmd[:500]}
        if verdict == "deny-once":
            sid = d.get("session_id", "x")
            path = Path(os.environ.get("TMPDIR") or "/tmp") / f"qsub_guard_{sid}.json"
            state = json.loads(path.read_text()) if path.exists() else {"seen": []}
            digest = hashlib.sha256(cmd.encode()).hexdigest()
            if digest in state["seen"]:
                verdict = "allow-resubmit"
            else:
                path.write_text(json.dumps({"seen": state["seen"] + [digest]}))
                verdict = "deny"
        _log(dict(entry, final=verdict))
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
