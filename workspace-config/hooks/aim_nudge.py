#!/usr/bin/env python3
"""PreToolUse(Agent|Task|Write|AskUserQuestion): graduated nudges to run the aim check (aim-keeper).

(a) a retro-officer dispatch closes the wave: run the aim check before the next wave or fix round;
(b) fix-like implementer dispatches since the last aim-keeper dispatch (counter reset by aim-keeper):
    round 2 soft nudge, round 3 stronger nudge, round 4 and later DENIED until the owner has been asked
    (an AskUserQuestion call after the deny lets exactly one fix dispatch through);
(c) a Write creating a new docs/plans, docs/superpowers/plans or phases markdown file: needs a Goal line.
Only (b) round 4+ denies. Counter state lives in $TMPDIR/aim_nudge_<sid>.json. Any internal error stays
silent and allows the call.
"""
import json
import os
import re
import sys
from pathlib import Path

FIX = re.compile(r"\b(fix|fixes|round \d|re-?review|repair|follow-?up)\b", re.I)
PLAN = re.compile(r"(^|/)(docs/(superpowers/)?plans|phases)/[^/]+\.md$")
STRICT_ROUND = 4
RETRO = ("This closes the wave. When the retro is in, run the aim check before any new wave or fix round: "
         "dispatch `aim-keeper` with the project path, the finished wave's goal and commit range, and the "
         "proposed next step; put its options to the owner with AskUserQuestion.")
SOFT = ("Fix round 2 since the last aim check. Is this round really needed now, or could the work be "
        "documented as it stands and moved on?")
STRONG = ("Fix round 3 since the last aim check. Before dispatching, decide for each item: is it a fix for a "
          "wrong or broken result that is needed now, or an optimisation, cost or robustness item that can go "
          "to the project's register for a later wave or phase? Also run the aim check (aim-keeper, then ask "
          "the owner) before more rounds.")
DENY = ("Fix round {n} since the last aim check: blocked until the owner agrees. Ask the owner with "
        "AskUserQuestion first, in plain, concise words: what broke, why it must be fixed now and not "
        "later, what this round costs, and the alternative of registering the item for a later wave or "
        "phase. After that question, retry this dispatch once; each later round needs a fresh question.")
PLAN_MSG = ("New plan or phase file: give it a `**Goal:**` line and quote, with its source, the aim one level "
            "up that it serves (phase aim for a wave plan, project aim for a phase).")


def agent_message(ti, state):
    """Return (kind, text); kind is None, "ctx" (additionalContext) or "deny"."""
    kind = ti.get("subagent_type")
    if kind == "aim-keeper":
        state.clear()
    elif kind == "retro-officer":
        return "ctx", RETRO
    elif kind == "implementer":
        first = next((ln for ln in str(ti.get("prompt") or "").splitlines() if ln.strip()), "")
        if FIX.search(str(ti.get("description") or "")) or FIX.search(first):
            n = state.get("fix_rounds", 0) + 1
            if n >= STRICT_ROUND and not state.get("owner_asked"):
                state["denied"] = True
                return "deny", DENY.format(n=n)
            state["fix_rounds"] = n
            state["owner_asked"] = False
            state["denied"] = False
            return {2: ("ctx", SOFT), 3: ("ctx", STRONG)}.get(n, (None, None))
    return None, None


def state_path(d):
    sid = re.sub(r"[^\w-]", "", str(d.get("session_id") or "nosession"))
    return Path(os.environ.get("TMPDIR") or "/tmp") / f"aim_nudge_{sid}.json"


def main():
    try:
        d = json.load(sys.stdin)
        ti, tool = d["tool_input"], d.get("tool_name")
        if d.get("hook_event_name") != "PreToolUse":
            return 0
        out = None
        if tool == "Write":
            fp = str(ti.get("file_path") or "")
            if PLAN.search(fp) and not os.path.exists(fp):
                out = ("ctx", PLAN_MSG)
        elif tool in ("Agent", "Task"):
            path = state_path(d)
            state = json.loads(path.read_text()) if path.exists() else {}
            out = agent_message(ti, state)
            path.write_text(json.dumps(state))
        elif tool == "AskUserQuestion":
            path = state_path(d)
            state = json.loads(path.read_text()) if path.exists() else {}
            if state.get("denied"):
                state["owner_asked"] = True
                path.write_text(json.dumps(state))
        if out and out[0]:
            h = {"hookEventName": "PreToolUse"}
            if out[0] == "deny":
                h.update(permissionDecision="deny", permissionDecisionReason=out[1])
            else:
                h["additionalContext"] = out[1]
            print(json.dumps({"hookSpecificOutput": h}))
    except Exception:
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
