import json
import subprocess
import sys
from pathlib import Path

HOOK = Path(__file__).resolve().parents[1] / "workspace-config" / "hooks" / "aim_nudge.py"


def run(tmp_path, tool, ti, sid="s1", raw=None):
    payload = {"session_id": sid, "hook_event_name": "PreToolUse", "tool_name": tool, "tool_input": ti}
    r = subprocess.run([sys.executable, str(HOOK)], input=raw if raw is not None else json.dumps(payload),
                       capture_output=True, text=True, env={"TMPDIR": str(tmp_path), "PATH": "/usr/bin"})
    assert r.returncode == 0
    if not r.stdout:
        return None
    o = json.loads(r.stdout)["hookSpecificOutput"]
    assert o["hookEventName"] == "PreToolUse" and "permissionDecision" not in o
    return o["additionalContext"]


def impl(desc="Fix round 2", prompt="do it"):
    return {"subagent_type": "implementer", "description": desc, "prompt": prompt}


def test_retro_officer_prompts_aim_check(tmp_path):
    msg = run(tmp_path, "Agent", {"subagent_type": "retro-officer", "prompt": "retro"})
    assert "aim-keeper" in msg and "AskUserQuestion" in msg


def test_third_fix_round_nudges_once_and_aim_keeper_resets(tmp_path):
    assert run(tmp_path, "Agent", impl("Fix A")) is None
    assert run(tmp_path, "Task", impl("re-review B")) is None
    assert "Third fix round" in run(tmp_path, "Agent", impl("round 3 repair"))
    assert run(tmp_path, "Agent", impl("Fix again")) is None  # once only
    run(tmp_path, "Agent", {"subagent_type": "aim-keeper", "prompt": "check"})
    assert run(tmp_path, "Agent", impl("Fix C")) is None
    assert run(tmp_path, "Agent", impl("Fix D")) is None
    assert "Third fix round" in run(tmp_path, "Agent", impl("Fix E"))


def test_fix_word_in_first_prompt_line_counts_and_other_work_does_not(tmp_path):
    for _ in range(2):
        assert run(tmp_path, "Agent", impl("Task 4", prompt="\n\nFix the parser\nmore")) is None
    assert "Third fix round" in run(tmp_path, "Agent", impl("Task 4", prompt="follow-up on parser"))
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
