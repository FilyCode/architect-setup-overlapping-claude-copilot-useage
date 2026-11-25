# REPO/tests/test_precompact_state.py
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

HOOK = Path(__file__).resolve().parents[1] / "workspace-config" / "hooks" / "precompact_state.py"
QSTAT_OUT = ("job-ID  prior   name       user  state submit/start at     queue  slots ja-task-ID\n"
             "-----------------------------------------------------------------------------------\n"
             "  111 0.5 a me r 11/25/2026 10:00:00 x@y 1\n"
             "  333 0.5 c me qw 11/25/2026 10:00:00  1\n")


def stub(bindir, name, body):
    bindir.mkdir(exist_ok=True)
    p = bindir / name
    p.write_text("#!/bin/sh\n" + body + "\n")
    p.chmod(0o755)


def run(tmp_path, cwd, session="s1", qstat="printf '%s' \"$QOUT\"", extra=None):
    bindir = tmp_path / "bin"
    if qstat is not None:
        stub(bindir, "qstat", qstat)
    real_git = subprocess.run(["which", "git"], capture_output=True, text=True).stdout.strip()
    (bindir).mkdir(exist_ok=True)
    if not (bindir / "git").exists():
        (bindir / "git").symlink_to(real_git)
    env = {"PATH": f"{bindir}:/usr/bin:/bin", "USER": "me", "QOUT": QSTAT_OUT,
           "CLAUDE_SESSION_JOBS_DIR": str(tmp_path / "led"), "CLAUDE_HANDOFF_DIR": str(tmp_path / "ho"),
           "HOME": str(tmp_path)}
    env.update(extra or {})
    payload = {"session_id": session, "cwd": str(cwd), "trigger": "auto", "transcript_path": "/x", "custom_instructions": ""}
    r = subprocess.run([sys.executable, str(HOOK)], input=json.dumps(payload), capture_output=True, text=True,
                       env=env, timeout=20)
    assert r.returncode == 0, r.stderr
    return r.stdout


def ledger(tmp_path, ids, session="s1"):
    d = tmp_path / "led"
    d.mkdir(exist_ok=True)
    (d / f"{session}.txt").write_text("".join(i + "\n" for i in ids))


def make_repo(path, n_dirty=1):
    path.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init", "-q", str(path)], check=True)
    for i in range(n_dirty):
        (path / f"f{i:03d}.txt").write_text("x")


def test_nothing_to_report_prints_nothing(tmp_path):
    cwd = tmp_path / "plain"
    cwd.mkdir()
    assert run(tmp_path, cwd) == ""


def test_running_jobs_only_those_in_qstat(tmp_path):
    cwd = tmp_path / "plain"
    cwd.mkdir()
    ledger(tmp_path, ["111", "222", "333"])
    out = run(tmp_path, cwd)
    assert out.splitlines()[0].startswith("Preserve verbatim in the summary")
    assert "111" in out and "333" in out and "222" not in out


def test_job_filter_fail_proof_other_qstat(tmp_path):
    # same ledger, qstat now lists only 222: output must flip from 111/333 to 222
    cwd = tmp_path / "plain"
    cwd.mkdir()
    ledger(tmp_path, ["111", "222", "333"])
    out = run(tmp_path, cwd, extra={"QOUT": "job-ID\n----\n  222 0.5 b me r x\n"})
    assert "222" in out and "111" not in out and "333" not in out


def test_all_ledger_jobs_finished_prints_nothing(tmp_path):
    cwd = tmp_path / "plain"
    cwd.mkdir()
    ledger(tmp_path, ["999"])
    assert run(tmp_path, cwd) == ""


def test_qstat_failure_marks_unknown(tmp_path):
    cwd = tmp_path / "plain"
    cwd.mkdir()
    ledger(tmp_path, ["111", "222"])
    out = run(tmp_path, cwd, qstat="exit 1")
    assert "state unknown" in out and "111" in out and "222" in out


def test_unsafe_session_skips_jobs(tmp_path):
    cwd = tmp_path / "plain"
    cwd.mkdir()
    (tmp_path / "led").mkdir()
    (tmp_path / "led" / "...txt").write_text("111\n")
    assert run(tmp_path, cwd, session="..") == ""


def test_git_dirty_listed_and_clean_silent(tmp_path):
    repo = tmp_path / "repo"
    make_repo(repo, 2)
    out = run(tmp_path, repo)
    assert "f000.txt" in out and "f001.txt" in out
    (repo / "f000.txt").unlink()
    (repo / "f001.txt").unlink()
    assert run(tmp_path, repo) == ""


def test_git_over_30_lines_counts_rest(tmp_path):
    repo = tmp_path / "repo"
    make_repo(repo, 35)
    out = run(tmp_path, repo)
    assert len(re.findall(r"f\d{3}\.txt", out)) == 30
    assert "5 more" in out


def test_handoff_pointer_fresh_old_and_missing(tmp_path):
    cwd = tmp_path / "plain"
    cwd.mkdir()
    d = tmp_path / "ho" / re.sub(r"[^A-Za-z0-9]", "-", str(cwd))
    d.mkdir(parents=True)
    f = d / "latest.md"
    f.write_text("SECRET BODY")
    out = run(tmp_path, cwd)
    assert str(f) in out and "SECRET BODY" not in out
    old = time.time() - 13 * 3600
    os.utime(f, (old, old))
    assert run(tmp_path, cwd) == ""


def test_cap_4000_with_marker(tmp_path):
    repo = tmp_path / ("r" * 100)
    make_repo(repo, 0)
    for i in range(40):
        (repo / (("n" * 200) + f"{i:03d}.txt")).write_text("x")
    out = run(tmp_path, repo)
    assert len(out) <= 4000
    assert "truncated" in out
    small = tmp_path / "small"
    make_repo(small, 1)
    assert "truncated" not in run(tmp_path, small)


def test_garbage_stdin_exits_zero_silent(tmp_path):
    r = subprocess.run([sys.executable, str(HOOK)], input="not json", capture_output=True, text=True, timeout=10)
    assert r.returncode == 0 and r.stdout == ""
