import json
import subprocess
import sys
from pathlib import Path

HOOK = Path(__file__).resolve().parents[1] / "workspace-config" / "hooks" / "ask_guard.py"
GOOD = "Pro: simple. Con: slower."


def run(tmp_path, questions, sid="s1", raw=None):
    payload = {"session_id": sid, "tool_name": "AskUserQuestion", "tool_input": {"questions": questions}}
    r = subprocess.run([sys.executable, str(HOOK)], input=raw if raw is not None else json.dumps(payload),
                       capture_output=True, text=True, env={"TMPDIR": str(tmp_path), "PATH": "/usr/bin"})
    return r.returncode, r.stdout


def q(desc=GOOD, label="Option A", question="Which way?"):
    return [{"question": question, "header": "Way", "multiSelect": False,
             "options": [{"label": label, "description": desc}]}]


def reason(out):
    o = json.loads(out)["hookSpecificOutput"]
    assert o["hookEventName"] == "PreToolUse" and o["permissionDecision"] == "deny"
    return o["permissionDecisionReason"]


def test_missing_con_denied_then_identical_resubmit_passes(tmp_path):
    qs = q(desc="Pro: simple.")
    rc, out = run(tmp_path, qs)
    msg = reason(out)
    assert rc == 0 and "Way" in msg and "Option A" in msg and "Con:" in msg
    assert "resubmit the identical call" in msg
    assert run(tmp_path, qs) == (0, "")


def test_changed_call_with_problem_is_denied_again(tmp_path):
    run(tmp_path, q(desc="Pro: simple."))
    assert "Con:" in reason(run(tmp_path, q(desc="Pro: simpler."))[1])


def test_missing_pro_denied(tmp_path):
    assert "Pro:" in reason(run(tmp_path, q(desc="Con: slow."))[1])


def test_explained_code_not_flagged(tmp_path):
    assert run(tmp_path, q(question="Follow DECISION-145 (the Bile tier ruling)?")) == (0, "")
    assert run(tmp_path, q(question="Follow (DECISION-145) as ruled?")) == (0, "")


def test_unexplained_codes_flagged(tmp_path):
    for text in ("DECISION-145a", "MA-172", "D018", "R-20261029-2", "PR #107", "#107", "3f9a1c2d7e"):
        msg = reason(run(tmp_path, q(question=f"Do we keep {text} as is?"), sid=text.replace("#", "h").replace(" ", ""))[1])
        assert text.lstrip("#").split()[-1].lstrip("#") in msg, text


def test_plain_words_and_pure_digit_or_letter_tokens_silent(tmp_path):
    assert run(tmp_path, q(question="Use deadbeef or 1234567 or the decision record?")) == (0, "")


def test_clean_question_silent_and_errors_silent(tmp_path):
    assert run(tmp_path, q()) == (0, "")
    assert run(tmp_path, None, raw="not json") == (0, "")
    assert run(tmp_path, None, raw=json.dumps({"tool_input": None})) == (0, "")
