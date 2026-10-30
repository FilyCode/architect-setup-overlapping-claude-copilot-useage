import json
import subprocess
import sys
from pathlib import Path

HOOK = Path(__file__).resolve().parents[1] / "workspace-config" / "hooks" / "dispatch_guard.py"


def run(payload, raw=None):
    stdin = raw if raw is not None else json.dumps(payload)
    r = subprocess.run([sys.executable, str(HOOK)], input=stdin, capture_output=True, text=True)
    return r.returncode, r.stdout


def ev(prompt="Implement X", model="opus", sub="implementer", tool="Agent"):
    ti = {"subagent_type": sub, "prompt": prompt}
    if model:
        ti["model"] = model
    return {"tool_name": tool, "tool_input": ti}


def test_opus_without_reason_warns():
    rc, out = run(ev("\n\nImplement the parser\nthis is a contract change"))
    assert rc == 0
    o = json.loads(out)["hookSpecificOutput"]
    assert o["hookEventName"] == "PreToolUse" and "DECISION-028/029" in o["additionalContext"]
    assert "permissionDecision" not in o


def test_task_alias_and_claude_opus_id_warn():
    assert run(ev(tool="Task"))[1]
    assert run(ev(model="claude-opus-5-5"))[1]


def test_reason_in_first_line_silent():
    for first in ("Cross-module change: rename API", "cross module rename", "Contract change", "RETRY of task 3"):
        assert run(ev(first + "\nbody")) == (0, "")


def test_sonnet_other_seat_other_tool_silent():
    assert run(ev(model="sonnet")) == (0, "")
    assert run(ev(model=None)) == (0, "")
    assert run(ev(sub="reviewer")) == (0, "")
    assert run(ev(tool="Bash")) == (0, "")


def test_malformed_stdin():
    assert run(None, raw="{{") == (0, "")
    assert run({"tool_name": "Agent", "tool_input": "str"}) == (0, "")
    assert run(ev(prompt=None)) [0] == 0
