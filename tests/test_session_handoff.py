import json
import os
import subprocess
import sys
import time
from pathlib import Path

HOOK = Path(__file__).resolve().parents[1] / "workspace-config" / "hooks" / "session_handoff.py"
CWD = "/projectnb/x/My Proj"
SAN = "-projectnb-x-My-Proj"


def run(tmp_path, payload, raw=None, job="1001"):
    env = {k: v for k, v in os.environ.items() if k != "JOB_ID"}
    env["CLAUDE_HANDOFF_DIR"] = str(tmp_path)
    if job:
        env["JOB_ID"] = job
    r = subprocess.run([sys.executable, str(HOOK)], input=raw if raw is not None else json.dumps(payload),
                       capture_output=True, text=True, env=env)
    return r.returncode, r.stdout


def make(tmp_path, age_s=60, body="SECRET BODY", name="1001.md"):
    f = tmp_path / SAN / name
    f.parent.mkdir(parents=True, exist_ok=True)
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
    make_fresh = tmp_path / SAN / "1001.md"
    t = time.time() - 11 * 3600
    os.utime(make_fresh, (t, t))
    assert "Handoff from" in run(tmp_path, {"source": "clear", "cwd": CWD})[1]  # 11 h: still fresh
    for src in ("resume", "compact"):
        assert run(tmp_path, {"source": src, "cwd": CWD}) == (0, "")
    assert run(tmp_path, None, raw="{{") == (0, "")
    assert run(tmp_path, {"source": "clear"})[0] == 0


sys.path.insert(0, str(HOOK.parent))
import session_handoff as sh  # noqa: E402


def test_key_from_job_id_else_ppid_sanitised():
    assert sh.handoff_key({"JOB_ID": "8963259"}) == "8963259"
    assert sh.handoff_key({"JOB_ID": "12.3/../x y"}) == "12.3_.._x_y"
    assert sh.handoff_key({}) == f"pid{os.getppid()}"
    assert sh.handoff_key({"JOB_ID": ""}) == f"pid{os.getppid()}"
    assert sh.handoff_path(CWD, {"JOB_ID": "7"}, "/h").as_posix() == f"/h/{SAN}/7.md"
    assert sh.handoff_path(CWD, {"CLAUDE_HANDOFF_DIR": "/e", "JOB_ID": "7"}).as_posix() == f"/e/{SAN}/7.md"


def test_fallback_key_is_hook_parent_pid(tmp_path):
    f = make(tmp_path, name=f"pid{os.getpid()}.md")  # the hook subprocess's parent is this pytest process
    out = run(tmp_path, {"source": "clear", "cwd": CWD}, job=None)[1]
    assert str(f) in out


def test_two_sessions_do_not_collide_and_clear_points_only_at_own(tmp_path):
    a = make(tmp_path, name="1001.md", body="A")
    b = make(tmp_path, name="2002.md", body="B")
    out = json.loads(run(tmp_path, {"source": "clear", "cwd": CWD}, job="2002")[1])["hookSpecificOutput"]["additionalContext"]
    assert str(b) in out and str(a) not in out  # clear: own file only, no listing
    assert a.read_text() == "A" and b.read_text() == "B"


def test_startup_lists_others_not_as_yours(tmp_path):
    other = make(tmp_path, name="2002.md", body="x\n# Handoff: the other thing " + "z" * 200 + "\n", age_s=600)
    legacy = make(tmp_path, name="latest.md", body="# legacy one\n", age_s=1200)
    make(tmp_path, name="3003.md", body="# stale\n", age_s=13 * 3600)
    out = json.loads(run(tmp_path, {"source": "startup", "cwd": CWD}, job="1001")[1])["hookSpecificOutput"]["additionalContext"]
    assert "Handoff from the previous session" not in out  # no own file
    assert "other sessions, not yours" in out and "only if the user says it is theirs" in out
    assert out.index(str(other)) < out.index(str(legacy))  # newest first
    assert "# legacy one" in out and "3003.md" not in out
    line = [ln for ln in out.splitlines() if str(other) in ln][0]
    assert "10 min ago" in line and "# Handoff: the other thing" in line
    assert len(line.split("): ", 1)[1]) <= 100


def test_startup_lists_at_most_three_others(tmp_path):
    for i in range(5):
        make(tmp_path, name=f"{2000 + i}.md", age_s=60 * (i + 1), body="# h\n")
    out = json.loads(run(tmp_path, {"source": "startup", "cwd": CWD}, job="1001")[1])["hookSpecificOutput"]["additionalContext"]
    assert out.count(".md") == 3 and "2000.md" in out and "2004.md" not in out


def test_own_file_and_others_together_on_startup(tmp_path):
    own = make(tmp_path, name="1001.md")
    make(tmp_path, name="2002.md", body="# o\n")
    out = json.loads(run(tmp_path, {"source": "startup", "cwd": CWD}, job="1001")[1])["hookSpecificOutput"]["additionalContext"]
    assert out.startswith(f"Handoff from the previous session: {own} (written ") and "2002.md" in out


def test_prune_deletes_only_old_matching_files(tmp_path):
    day = 86400
    old_key = make(tmp_path, name="4004.md", age_s=15 * day)
    old_latest = make(tmp_path, name="latest.md", age_s=15 * day)
    young = make(tmp_path, name="5005.md", age_s=13 * day)
    other_ext = make(tmp_path, name="notes.txt", age_s=30 * day)
    odd = make(tmp_path, name="has space.md", age_s=30 * day)
    tmpf = make(tmp_path, name="6006.md.tmp", age_s=30 * day)
    sibling = tmp_path / "-other-cwd" / "7007.md"
    sibling.parent.mkdir()
    sibling.write_text("s")
    os.utime(sibling, (time.time() - 30 * day,) * 2)
    assert run(tmp_path, {"source": "startup", "cwd": CWD})[0] == 0
    assert not old_key.exists() and not old_latest.exists()
    assert young.exists() and other_ext.exists() and odd.exists() and tmpf.exists() and sibling.exists()
    assert run(tmp_path, {"source": "resume", "cwd": CWD}) == (0, "")  # resume never prunes
