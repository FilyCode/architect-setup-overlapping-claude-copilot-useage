import json
import subprocess
import sys
from pathlib import Path

HOOK = Path(__file__).resolve().parents[1] / "workspace-config" / "hooks" / "model_guard.py"


def transcript(tmp_path, *models):
    p = tmp_path / "t.jsonl"
    lines = [json.dumps({"type": "user", "message": {"role": "user", "content": "hi"}})]
    for m in models:
        lines.append(json.dumps({"type": "assistant", "message": {"role": "assistant", "model": m, "content": []}}))
        lines.append(json.dumps({"type": "user", "message": {"role": "user", "content": "more"}}))
    p.write_text("\n".join(lines) + "\n")
    return p


def run(tmp_path, tp, sid="s1", raw=None):
    payload = {"session_id": sid, "hook_event_name": "UserPromptSubmit", "transcript_path": str(tp), "prompt": "x"}
    r = subprocess.run([sys.executable, str(HOOK)], input=raw if raw is not None else json.dumps(payload),
                       capture_output=True, text=True, env={"TMPDIR": str(tmp_path), "PATH": "/usr/bin"})
    return r.returncode, r.stdout


def test_retired_model_warns_once_per_hour(tmp_path):
    tp = transcript(tmp_path, "claude-opus-5")
    rc, out = run(tmp_path, tp)
    o = json.loads(out)
    assert rc == 0 and "/model claude-opus-5-5" in o["systemMessage"]
    assert o["hookSpecificOutput"]["hookEventName"] == "UserPromptSubmit"
    assert "retired model claude-opus-5" in o["hookSpecificOutput"]["additionalContext"]
    assert run(tmp_path, tp) == (0, "")  # second prompt inside 60 min


def test_warns_again_after_an_hour(tmp_path):
    tp = transcript(tmp_path, "claude-opus-5")
    run(tmp_path, tp)
    state = tmp_path / "model_guard_s1.json"
    state.write_text(json.dumps({"warned_at": 0}))
    assert "systemMessage" in json.loads(run(tmp_path, tp)[1])


def test_current_model_silent_and_last_entry_wins(tmp_path):
    assert run(tmp_path, transcript(tmp_path, "claude-opus-5-5")) == (0, "")
    assert run(tmp_path, transcript(tmp_path, "claude-opus-5", "claude-opus-5-5")) == (0, "")


def test_errors_silent(tmp_path):
    assert run(tmp_path, tmp_path / "missing.jsonl") == (0, "")
    assert run(tmp_path, None, raw="not json") == (0, "")
