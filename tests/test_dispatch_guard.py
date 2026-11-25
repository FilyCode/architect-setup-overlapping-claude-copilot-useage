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


def denied(out):
    o = json.loads(out)["hookSpecificOutput"]
    assert o["hookEventName"] == "PreToolUse" and o["permissionDecision"] == "deny"
    return o["permissionDecisionReason"]


def test_opus_without_marker_is_denied_with_fix():
    rc, out = run(ev("\n\nImplement the parser\nthis is a contract change"))
    assert rc == 0
    why = denied(out)
    assert "Opus because:" in why and "model" in why


def test_task_alias_and_claude_opus_id_denied():
    denied(run(ev(tool="Task"))[1])
    denied(run(ev(model="claude-opus-5-5"))[1])


def test_marker_with_reason_passes():
    for first in ("Opus because: cross-module rename of the API", "  opus BECAUSE: needs the whole contract in view",
                  "OPUS because:   ten chars++"):
        assert run(ev(first + "\nbody")) == (0, ""), first
    assert run(ev("\n\nOpus because: long enough reason\nbody")) == (0, "")  # leading blank lines skipped


def test_marker_needs_first_line_and_ten_nonspace_chars():
    denied(run(ev("Implement X\nOpus because: a perfectly good reason"))[1])  # not the first line
    denied(run(ev("Opus because: short"))[1])                                   # 5 chars
    denied(run(ev("Opus because:      a b c d e"))[1])                         # 5 non-space chars, many spaces
    denied(run(ev("Opus because:"))[1])
    denied(run(ev("The old words: cross-module contract retry"))[1])           # old vocabulary no longer passes
    assert run(ev("Opus because: 1234567890")) == (0, "")                       # exactly 10


def test_sonnet_other_seat_other_tool_silent():
    assert run(ev(model="sonnet")) == (0, "")
    assert run(ev(model=None)) == (0, "")
    assert run(ev(sub="reviewer")) == (0, "")
    assert run(ev(tool="Bash")) == (0, "")


def test_malformed_stdin_stays_silent():
    assert run(None, raw="{{") == (0, "")
    assert run({"tool_name": "Agent", "tool_input": "str"}) == (0, "")
    assert run(ev(prompt=None))[0] == 0
