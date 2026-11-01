import os
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import scc_ci_status as ci  # noqa: E402

STUB = """#!/bin/bash
echo "$(basename $0) $@" >> "$STUB_LOG"
%s
"""


def git(cwd, *a):
    return subprocess.run(["git", "-C", str(cwd), *a], check=True, capture_output=True, text=True).stdout.strip()


@pytest.fixture
def env(tmp_path, monkeypatch):
    """A repo with a pushed commit, a bare origin named like EF's, and qsub/gh stubs on PATH."""
    origin = tmp_path / "origin.git"
    subprocess.run(["git", "init", "-q", "--bare", str(origin)], check=True)
    repo = tmp_path / "proj"
    subprocess.run(["git", "init", "-q", "-b", "main", str(repo)], check=True)
    for k, v in (("user.email", "a@b"), ("user.name", "t")):
        git(repo, "config", k, v)
    (repo / "run.sh").write_text("#!/bin/bash\n")
    git(repo, "add", "run.sh")
    git(repo, "commit", "-qm", "one")
    git(repo, "remote", "add", "origin", str(origin))
    git(repo, "push", "-q", "origin", "main")
    git(repo, "remote", "set-url", "origin", "git@github.com:FilyCode/EnzymeFinder.git")
    git(repo, "config", "url.%s.insteadOf" % origin, "git@github.com:FilyCode/EnzymeFinder.git")
    bindir = tmp_path / "bin"
    bindir.mkdir()
    (bindir / "qsub").write_text(STUB % 'if [[ "$*" == *hold_jid* ]]; then echo 202; else echo 101; fi')
    (bindir / "gh").write_text(STUB % "")
    for f in bindir.iterdir():
        f.chmod(0o755)
    log = tmp_path / "stub.log"
    monkeypatch.setenv("STUB_LOG", str(log))
    monkeypatch.setenv("PATH", f"{bindir}:{os.environ['PATH']}")
    monkeypatch.setattr(ci, "WORKTREES", tmp_path / "wt")
    return repo, log


def calls(log, name):
    return [ln for ln in log.read_text().splitlines() if ln.startswith(name + " ")] if log.exists() else []


def test_submit_posts_pending_then_qsubs_test_and_held_followup(env, capsys):
    repo, log = env
    (repo / ".venv").mkdir()
    ci.main(["submit", "--repo", str(repo), "--test-script", "run.sh"])
    sha = git(repo, "rev-parse", "HEAD")
    wt = ci.WORKTREES / "proj" / sha[:12]
    assert git(wt, "rev-parse", "HEAD") == sha
    [gh] = calls(log, "gh")
    assert f"repos/FilyCode/EnzymeFinder/statuses/{sha}" in gh and "state=pending" in gh
    assert "context=scc-tests" in gh and "submitted" in gh
    test_q, follow_q = calls(log, "qsub")
    assert f"PROJECT_ROOT={wt}" in test_q and f"VENV_DIR={repo}/.venv" in test_q and test_q.endswith("run.sh")
    assert "-hold_jid 101" in follow_q and "-pe omp 1" in follow_q and "--job-id 101" in follow_q
    out = capsys.readouterr().out
    assert "101" in out and "202" in out and "pytest_qsub.101.out" in out


def test_submit_reuses_existing_worktree(env):
    repo, _ = env
    ci.main(["submit", "--repo", str(repo), "--test-script", "run.sh"])
    ci.main(["submit", "--repo", str(repo), "--test-script", "run.sh"])


def test_refuses_sha_not_on_remote(env):
    repo, log = env
    (repo / "x").write_text("x")
    git(repo, "add", "x")
    git(repo, "commit", "-qm", "local only")
    with pytest.raises(SystemExit, match="not on any remote branch"):
        ci.main(["submit", "--repo", str(repo)])
    assert not calls(log, "qsub") and not calls(log, "gh")


def test_refuses_dirty_tracked_tree_when_defaulting_to_head(env):
    repo, log = env
    (repo / "run.sh").write_text("changed\n")
    with pytest.raises(SystemExit, match="uncommitted tracked changes"):
        ci.main(["submit", "--repo", str(repo)])
    assert not calls(log, "qsub")


def test_post_truncates_description_to_140(env):
    repo, log = env
    ci.main(["post", "--repo", str(repo), "--sha", "abc", "--state", "failure", "--description", "x" * 300])
    desc = [t for t in calls(log, "gh")[0].split() if t.startswith("description=")][0]
    assert len(desc) == len("description=") + 140


def test_gh_failure_is_fatal(env, tmp_path):
    repo, _ = env
    (tmp_path / "bin" / "gh").write_text("#!/bin/bash\necho 'HTTP 401' >&2; exit 1\n")
    with pytest.raises(SystemExit, match="HTTP 401"):
        ci.main(["post", "--repo", str(repo), "--sha", "abc", "--state", "success", "--description", "d"])


def finish_with(env, tmp_path, monkeypatch, rc, log_text):
    repo, log = env
    wt = tmp_path / "wtdir"
    (wt / "logs").mkdir(parents=True)
    if log_text:
        (wt / "logs" / "pytest_full_7.log").write_text(log_text)
    monkeypatch.setattr(ci, "exit_status", lambda job: rc)
    ci.main(["finish", "--repo", str(repo), "--sha", "abc", "--job-id", "7", "--worktree", str(wt)])
    return calls(log, "gh")[0]


def test_finish_success_carries_summary_and_job(env, tmp_path, monkeypatch):
    gh = finish_with(env, tmp_path, monkeypatch, 0, "noise\n===== 9701 passed, 3 skipped in 1534.12s (0:25:34) =====\n")
    assert "state=success" in gh and "9701 passed, 3 skipped in 1534.12s" in gh and "job 7" in gh


def test_finish_failure_on_nonzero_exit(env, tmp_path, monkeypatch):
    gh = finish_with(env, tmp_path, monkeypatch, 1, "2 failed, 9699 passed in 100.00s (0:01:40)\n")
    assert "state=failure" in gh and "2 failed" in gh


def test_finish_error_when_no_exit_status(env, tmp_path, monkeypatch):
    gh = finish_with(env, tmp_path, monkeypatch, None, "")
    assert "state=error" in gh and "job 7" in gh


def test_owner_repo_parses_https_and_ssh(env):
    repo, _ = env
    assert ci.owner_repo(repo) == ("FilyCode", "EnzymeFinder")
    git(repo, "remote", "set-url", "origin", "https://github.com/Foo/bar.git")
    assert ci.owner_repo(repo) == ("Foo", "bar")
