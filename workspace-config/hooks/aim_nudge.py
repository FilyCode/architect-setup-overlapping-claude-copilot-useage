#!/usr/bin/env python3
"""PreToolUse(Agent|Task|Write): warn-only nudges to run the aim check (aim-keeper) at the right moments.

(a) a retro-officer dispatch closes the wave: run the aim check before the next wave or fix round;
(b) the third fix-like implementer dispatch since the last aim-keeper dispatch (counter reset by aim-keeper);
(c) a Write creating a new docs/plans, docs/superpowers/plans or phases markdown file: needs a Goal line.
Never denies. Counter state lives in $TMPDIR/aim_nudge_<sid>.json. Any internal error stays silent.
"""
import json
import os
import re
import sys
from pathlib import Path

FIX = re.compile(r"\b(fix|fixes|round \d|re-?review|repair|follow-?up)\b", re.I)
PLAN = re.compile(r"(^|/)(docs/(superpowers/)?plans|phases)/[^/]+\.md$")
LIMIT = 3
RETRO = ("This closes the wave. When the retro is in, run the aim check before any new wave or fix round: "
         "dispatch `aim-keeper` with the project path, the finished wave's goal and commit range, and the "
         "proposed next step; put its options to the owner with AskUserQuestion.")
DRIFT = ("Third fix round since the last aim check. Before dispatching more: does this still serve the "
         "wave's goal, or has the work drifted? Run the aim check (aim-keeper, then ask the owner).")
PLAN_MSG = ("New plan or phase file: give it a `**Goal:**` line and quote, with its source, the aim one level "
            "up that it serves (phase aim for a wave plan, project aim for a phase).")


def agent_message(ti, state):
    kind = ti.get("subagent_type")
    if kind == "aim-keeper":
        state["fix_rounds"] = 0
        state["nudged"] = False
    elif kind == "retro-officer":
        return RETRO
    elif kind == "implementer":
        first = next((ln for ln in str(ti.get("prompt") or "").splitlines() if ln.strip()), "")
        if FIX.search(str(ti.get("description") or "")) or FIX.search(first):
            state["fix_rounds"] = state.get("fix_rounds", 0) + 1
            if state["fix_rounds"] >= LIMIT and not state.get("nudged"):
                state["nudged"] = True
                return DRIFT
    return None


def main():
    try:
        d = json.load(sys.stdin)
        ti, tool = d["tool_input"], d.get("tool_name")
        if d.get("hook_event_name") != "PreToolUse":
            return 0
        msg = None
        if tool == "Write":
            fp = str(ti.get("file_path") or "")
            if PLAN.search(fp) and not os.path.exists(fp):
                msg = PLAN_MSG
        elif tool in ("Agent", "Task"):
            sid = re.sub(r"[^\w-]", "", str(d.get("session_id") or "nosession"))
            path = Path(os.environ.get("TMPDIR") or "/tmp") / f"aim_nudge_{sid}.json"
            state = json.loads(path.read_text()) if path.exists() else {}
            msg = agent_message(ti, state)
            path.write_text(json.dumps(state))
        if msg:
            print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "additionalContext": msg}}))
    except Exception:
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
