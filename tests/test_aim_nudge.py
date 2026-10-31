import json
import subprocess
import sys
from pathlib import Path

HOOK = Path(__file__).resolve().parents[1] / "workspace-config" / "hooks" / "aim_nudge.py"


def run_raw(tmp_path, tool, ti, sid="s1", raw=None):
    payload = {"session_id": sid, "hook_event_name": "PreToolUse", "tool_name": tool, "tool_input": ti}
    r = subprocess.run([sys.executable, str(HOOK)], input=raw if raw is not None else json.dumps(payload),
                       capture_output=True, text=True, env={"TMPDIR": str(tmp_path), "PATH": "/usr/bin"})
    assert r.returncode == 0
    if not r.stdout:
        return None
    o = json.loads(r.stdout)["hookSpecificOutput"]
    assert o["hookEventName"] == "PreToolUse"
    return o


def run(tmp_path, tool, ti, sid="s1", raw=None):
    """Message of a non-denying result, or None; fails if the hook denied."""
    o = run_raw(tmp_path, tool, ti, sid, raw)
    if o is None:
        return None
    assert "permissionDecision" not in o, "hook denied where only a nudge was expected"
    return o["additionalContext"]


def fix(tmp_path, desc="Fix X", sid="s1"):
    """Classify one fix dispatch as None, 'soft', 'strong' or 'deny' by its message."""
    o = run_raw(tmp_path, "Agent", impl(desc), sid)
    if o is None:
        return None
    if o.get("permissionDecision") == "deny":
        assert "AskUserQuestion" in o["permissionDecisionReason"]
        return "deny"
    return {"Fix round 2": "soft", "Fix round 3": "strong"}[o["additionalContext"][:11]]


def impl(desc="Fix round 2", prompt="do it"):
    return {"subagent_type": "implementer", "description": desc, "prompt": prompt}


def test_retro_officer_prompts_aim_check(tmp_path):
    msg = run(tmp_path, "Agent", {"subagent_type": "retro-officer", "prompt": "retro"})
    assert "aim-keeper" in msg and "AskUserQuestion" in msg


def test_rounds_1_to_4_give_none_soft_strong_deny(tmp_path):
    assert [fix(tmp_path) for _ in range(4)] == [None, "soft", "strong", "deny"]
    run(tmp_path, "Agent", impl("Fix A"), sid="m")
    assert "really needed now" in run(tmp_path, "Agent", impl("Fix B"), sid="m")
    strong = run(tmp_path, "Agent", impl("Fix C"), sid="m")
    assert "aim-keeper" in strong and "register" in strong and "optimisation" in strong


def test_ask_after_deny_lets_exactly_one_fix_through(tmp_path):
    assert [fix(tmp_path) for _ in range(4)] == [None, "soft", "strong", "deny"]
    assert run(tmp_path, "AskUserQuestion", {"questions": []}) is None
    assert fix(tmp_path) is None  # allowed through, no message
    assert fix(tmp_path) == "deny"  # the next round needs a fresh ask
    run(tmp_path, "AskUserQuestion", {"questions": []})
    assert fix(tmp_path) is None
    assert fix(tmp_path) == "deny"


def test_ask_before_any_deny_does_not_pre_authorise(tmp_path):
    run(tmp_path, "AskUserQuestion", {"questions": []})
    assert [fix(tmp_path) for _ in range(4)] == [None, "soft", "strong", "deny"]


def test_aim_keeper_resets_to_round_zero(tmp_path):
    assert [fix(tmp_path) for _ in range(4)] == [None, "soft", "strong", "deny"]
    run(tmp_path, "Agent", {"subagent_type": "aim-keeper", "prompt": "check"})
    assert [fix(tmp_path) for _ in range(4)] == [None, "soft", "strong", "deny"]


def test_corrupt_state_allows_dispatch(tmp_path):
    (tmp_path / "aim_nudge_s1.json").write_text("{not json")
    assert run_raw(tmp_path, "Agent", impl("Fix A")) is None


def test_fix_word_in_first_prompt_line_counts_and_other_work_does_not(tmp_path):
    assert run(tmp_path, "Agent", impl("Task 4", prompt="\n\nFix the parser\nmore")) is None
    assert "round 2" in run(tmp_path, "Agent", impl("Task 4", prompt="follow-up on parser"))
    for _ in range(5):  # non-fix implementer work never counts
        assert run(tmp_path, "Agent", impl("Task 6: build", prompt="build"), sid="nf") is None
    assert run(tmp_path, "Agent", impl("Task 5: build prefix", prompt="build"), sid="other") is None
    assert run(tmp_path, "Agent", {"subagent_type": "reviewer", "description": "fix"}, sid="third") is None


def test_new_plan_file_nudges_existing_does_not(tmp_path):
    plan = tmp_path / "docs" / "superpowers" / "plans" / "p.md"
    assert "**Goal:**" in run(tmp_path, "Write", {"file_path": str(plan), "content": "x"})
    plan.parent.mkdir(parents=True)
    plan.write_text("old")
    assert run(tmp_path, "Write", {"file_path": str(plan), "content": "x"}) is None
    phase = tmp_path / "phases" / "ph1.md"
    assert "**Goal:**" in run(tmp_path, "Write", {"file_path": str(phase), "content": "x"})
    assert run(tmp_path, "Write", {"file_path": str(tmp_path / "docs" / "plans" / "a" / "b.md")}) is None
    assert run(tmp_path, "Write", {"file_path": str(tmp_path / "notes.md")}) is None


def test_errors_silent(tmp_path):
    assert run(tmp_path, None, None, raw="not json") is None
    assert run(tmp_path, "Agent", None) is None
