import json
import os
import subprocess
import sys
import time
from pathlib import Path

HOOK = Path(__file__).resolve().parents[1] / "workspace-config" / "hooks" / "session_handoff.py"
CWD = "/projectnb/x/My Proj"
SAN = "-projectnb-x-My-Proj"


def run(tmp_path, payload, raw=None):
    env = {**os.environ, "CLAUDE_HANDOFF_DIR": str(tmp_path)}
    r = subprocess.run([sys.executable, str(HOOK)], input=raw if raw is not None else json.dumps(payload),
                       capture_output=True, text=True, env=env)
    return r.returncode, r.stdout


def make(tmp_path, age_s=60, body="SECRET BODY"):
    f = tmp_path / SAN / "latest.md"
    f.parent.mkdir(parents=True)
    f.write_text(body)
    t = time.time() - age_s
    os.utime(f, (t, t))
    return f


def test_pointer_for_clear_and_startup_never_the_body(tmp_path):
    f = make(tmp_path)
    for src in ("clear", "startup"):
        rc, out = run(tmp_path, {"source": src, "cwd": CWD})
        assert rc == 0
        h = json.loads(out)["hookSpecificOutput"]
        assert h["hookEventName"] == "SessionStart"
        assert h["additionalContext"].startswith(f"Handoff from the previous session: {f} (written ")
        assert h["additionalContext"].endswith("Read it before starting.")
        assert "SECRET BODY" not in out


def test_silent_for_resume_compact_stale_missing_or_bad_input(tmp_path):
    assert run(tmp_path, {"source": "clear", "cwd": CWD}) == (0, "")  # no file yet
    make(tmp_path, age_s=13 * 3600)
    assert run(tmp_path, {"source": "clear", "cwd": CWD}) == (0, "")  # older than 12 h
    make_fresh = tmp_path / SAN / "latest.md"
    t = time.time() - 11 * 3600
    os.utime(make_fresh, (t, t))
    assert "Handoff from" in run(tmp_path, {"source": "clear", "cwd": CWD})[1]  # 11 h: still fresh
    for src in ("resume", "compact"):
        assert run(tmp_path, {"source": src, "cwd": CWD}) == (0, "")
    assert run(tmp_path, None, raw="{{") == (0, "")
    assert run(tmp_path, {"source": "clear"})[0] == 0
