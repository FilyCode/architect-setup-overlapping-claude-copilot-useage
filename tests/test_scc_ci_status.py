import hashlib
import json
import os
import subprocess
import time
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
    (repo / "requirements-dev.lock").write_text("pillow==12.3.0\n")
    git(repo, "add", "run.sh", "requirements-dev.lock")
    git(repo, "commit", "-qm", "one")
    git(repo, "remote", "add", "origin", str(origin))
    git(repo, "push", "-q", "origin", "main")
    git(repo, "remote", "set-url", "origin", "git@github.com:FilyCode/EnzymeFinder.git")
    git(repo, "config", "url.%s.insteadOf" % origin, "git@github.com:FilyCode/EnzymeFinder.git")
    bindir = tmp_path / "bin"
    bindir.mkdir()
    (bindir / "qsub").write_text(STUB % 'case "$*" in *scc_ci_post*) echo 202;; *scc_ci_venv*) echo 100;; *) echo 101;; esac')
    (bindir / "gh").write_text(STUB % '[[ "$*" == */commits/* ]] && cat "$STUB_DIR/statuses.json"; true')
    (bindir / "qdel").write_text(STUB % "")
    (bindir / "qstat").write_text(STUB % 'cat "$STUB_DIR/qstat.txt"')
    (bindir / "qacct").write_text(STUB % 'cat "$STUB_DIR/qacct.txt"; exit $(cat "$STUB_DIR/qacct.rc")')
    (tmp_path / "qstat.txt").write_text("")
    (tmp_path / "statuses.json").write_text("[]")
    (tmp_path / "qacct.rc").write_text("0")
    for f in bindir.iterdir():
        f.chmod(0o755)
    log = tmp_path / "stub.log"
    monkeypatch.setenv("STUB_LOG", str(log))
    monkeypatch.setenv("STUB_DIR", str(tmp_path))
    monkeypatch.setattr(ci, "QACCT_WAIT", 0)
    monkeypatch.setenv("PATH", f"{bindir}:{os.environ['PATH']}")
    monkeypatch.setattr(ci, "WORKTREES", tmp_path / "wt")
    monkeypatch.setattr(ci, "VENVS", tmp_path / "wt" / "venvs")
    return repo, log


def calls(log, name):
    return [ln for ln in log.read_text().splitlines() if ln.startswith(name + " ")] if log.exists() else []


def test_submit_posts_pending_then_qsubs_test_and_held_followup(env, capsys):
    repo, log = env
    sha = git(repo, "rev-parse", "HEAD")
    wt = ci.WORKTREES / "proj" / sha[:12]
    venv = ci.VENVS / "proj" / hashlib.sha256(b"pillow==12.3.0\n").hexdigest()[:12]
    (venv).mkdir(parents=True)
    (venv / ci.MARKER).write_text("")
    ci.main(["submit", "--repo", str(repo), "--test-script", "run.sh"])
    assert git(wt, "rev-parse", "HEAD") == sha
    [gh] = calls(log, "gh")
    assert f"repos/FilyCode/EnzymeFinder/statuses/{sha}" in gh and "state=pending" in gh
    assert "context=scc-tests" in gh and "submitted" in gh
    test_q, follow_q = calls(log, "qsub")
    assert f"PROJECT_ROOT={wt}" in test_q and f"VENV_DIR={venv}" in test_q and test_q.endswith("run.sh")
    assert "hold_jid" not in test_q
    assert "-hold_jid 101" in follow_q and "-pe omp 1" in follow_q and "--job-id 101" in follow_q
    out = capsys.readouterr().out
    assert "101" in out and "202" in out and "pytest_qsub.101.out" in out


def test_submit_builds_missing_venv_in_a_job_and_holds_test_on_it(env):
    repo, log = env
    ci.main(["submit", "--repo", str(repo), "--test-script", "run.sh"])
    build_q, test_q, follow_q = calls(log, "qsub")
    h = hashlib.sha256(b"pillow==12.3.0\n").hexdigest()[:12]
    venv = ci.VENVS / "proj" / h
    assert str(ci.BUILD_SCRIPT) in build_q and f"VENV_DIR={venv}" in build_q and "LOCKFILE=requirements-dev.lock" in build_q
    assert "-pe omp 1" in build_q and "h_rt=1:00:00" in build_q and "mem_per_core=8G" in build_q
    assert "-hold_jid 100" in test_q and f"VENV_DIR={venv}" in test_q
    assert "-hold_jid 101" in follow_q


def test_submit_keys_venv_on_lockfile_content_and_option(env):
    repo, log = env
    (repo / "other.lock").write_text("filelock==4.2.6\n")
    git(repo, "add", "other.lock")
    git(repo, "commit", "-qm", "two")
    git(repo, "push", "-q", "origin", "main")
    ci.main(["submit", "--repo", str(repo), "--test-script", "run.sh", "--lockfile", "other.lock"])
    build_q = calls(log, "qsub")[0]
    assert f"VENV_DIR={ci.VENVS}/proj/{hashlib.sha256(b'filelock==4.2.6\n').hexdigest()[:12]}" in build_q
    assert "LOCKFILE=other.lock" in build_q


def test_submit_without_lockfile_stops_before_posting_or_qsub(env):
    repo, log = env
    with pytest.raises(SystemExit, match="nope.lock not found"):
        ci.main(["submit", "--repo", str(repo), "--test-script", "run.sh", "--lockfile", "nope.lock"])
    assert not calls(log, "qsub") and not calls(log, "gh")


def test_build_script_skips_when_marker_exists_and_builds_nothing(tmp_path):
    """The flock-guarded build script exits 0 without touching an already-marked venv."""
    venv = tmp_path / "v"
    venv.mkdir()
    (venv / ci.MARKER).write_text("")
    (venv / "keep").write_text("x")
    p = subprocess.run(["bash", str(ci.BUILD_SCRIPT)], capture_output=True, text=True,
                       env={**os.environ, "PROJECT_ROOT": str(tmp_path), "VENV_DIR": str(venv), "PY311": "/nonexistent"})
    assert p.returncode == 0 and "already built" in p.stdout and (venv / "keep").exists()


def test_build_script_failure_leaves_no_marker(tmp_path):
    venv = tmp_path / "v"
    p = subprocess.run(["bash", str(ci.BUILD_SCRIPT)], capture_output=True, text=True,
                       env={**os.environ, "PROJECT_ROOT": str(tmp_path), "VENV_DIR": str(venv), "PY311": "/nonexistent"})
    assert p.returncode != 0 and not (venv / ci.MARKER).exists()


def test_sweep_prune_removes_only_venvs_unused_for_more_than_days(env, tmp_path):
    old, recent, used = (ci.VENVS / "proj" / n for n in ("old", "recent", "used"))
    for v in (old, recent, used):
        v.mkdir(parents=True)
        (v / ci.MARKER).write_text("")
    long_ago = time.time() - 30 * 86400
    for v in (old, used):
        os.utime(v / ci.MARKER, (long_ago, long_ago))
    (ci.WORKTREES / "proj").mkdir(parents=True, exist_ok=True)
    (ci.WORKTREES / "proj" / "abc.json").write_text(json.dumps(
        {"sha": "abc", "repo": str(env[0]), "context": "scc-tests", "test_job": "1", "follow_job": "2",
         "worktree": "w", "venv": str(used), "submitted": time.time() - 86400}))
    (tmp_path / "statuses.json").write_text(json.dumps([{"context": "scc-tests", "state": "success"}]))
    ci.main(["sweep", "--prune", "7"])
    assert not old.exists() and recent.exists() and used.exists()


def test_sweep_without_prune_keeps_old_venvs(env):
    old = ci.VENVS / "proj" / "old"
    old.mkdir(parents=True)
    os.utime(old, (1, 1))
    ci.main(["sweep"])
    assert old.exists()


def test_submit_reuses_existing_worktree(env):
    repo, log = env
    ci.main(["submit", "--repo", str(repo), "--test-script", "run.sh"])
    ci.main(["submit", "--repo", str(repo), "--test-script", "run.sh"])
    assert len(calls(log, "qsub")) == 6  # build + test + follow-up per run: the stub never writes the marker


def test_submit_refuses_worktree_at_another_sha(env):
    repo, log = env
    sha1 = git(repo, "rev-parse", "HEAD")
    (repo / "y").write_text("y")
    git(repo, "add", "y")
    git(repo, "commit", "-qm", "two")
    git(repo, "push", "-q", "origin", "main")
    sha2 = git(repo, "rev-parse", "HEAD")
    stale = ci.WORKTREES / "proj" / sha2[:12]
    stale.parent.mkdir(parents=True)
    git(repo, "worktree", "add", "--detach", str(stale), sha1)
    with pytest.raises(SystemExit, match="is not at"):
        ci.main(["submit", "--repo", str(repo), "--sha", sha2, "--test-script", "run.sh"])
    assert not calls(log, "qsub")


def test_test_qsub_failure_posts_error_not_pending_forever(env, tmp_path):
    repo, log = env
    (tmp_path / "bin" / "qsub").write_text("#!/bin/bash\necho 'Unable to run job: bad project' >&2; exit 1\n")
    with pytest.raises(SystemExit, match="bad project"):
        ci.main(["submit", "--repo", str(repo), "--test-script", "run.sh"])
    states = [ln for ln in calls(log, "gh") if "state=" in ln]
    assert "state=pending" in states[0] and "state=error" in states[-1] and "bad project" in states[-1]


def test_followup_qsub_failure_posts_error_and_deletes_test_job(env, tmp_path):
    repo, log = env
    (tmp_path / "bin" / "qsub").write_text(
        STUB % 'if [[ "$*" == *scc_ci_post* ]]; then echo "queue full" >&2; exit 1; else echo 101; fi')
    with pytest.raises(SystemExit, match="queue full"):
        ci.main(["submit", "--repo", str(repo), "--test-script", "run.sh"])
    assert calls(log, "qdel") == ["qdel 101"]
    last = calls(log, "gh")[-1]
    assert "state=error" in last and "follow-up not queued" in last


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


QACCT_OK = "qname all.q\nfailed       0\nexit_status  0\n"
SUMMARY_OK = "noise\n===== 9701 passed, 3 skipped in 1534.12s (0:25:34) =====\n"


def finish_with(env, tmp_path, qacct, log_text, rc=0):
    """Run `finish` against a stubbed qacct record; return the single gh call."""
    repo, log = env
    wt = tmp_path / "wtdir"
    (wt / "logs").mkdir(parents=True)
    if log_text:
        (wt / "logs" / "pytest_full_7.log").write_text(log_text)
    (tmp_path / "qacct.txt").write_text(qacct)
    (tmp_path / "qacct.rc").write_text(str(rc))
    ci.main(["finish", "--repo", str(repo), "--sha", "abc", "--job-id", "7", "--worktree", str(wt)])
    return calls(log, "gh")[0]


def test_finish_success_carries_summary_and_job(env, tmp_path):
    gh = finish_with(env, tmp_path, QACCT_OK, SUMMARY_OK)
    assert "state=success" in gh and "9701 passed, 3 skipped in 1534.12s" in gh and "job 7" in gh


def test_finish_failure_on_nonzero_exit(env, tmp_path):
    gh = finish_with(env, tmp_path, "failed 0\nexit_status 1\n", "2 failed, 9699 passed in 100.00s (0:01:40)\n")
    assert "state=failure" in gh and "2 failed" in gh and "exit 1" in gh


def test_finish_failure_on_nonzero_failed_even_with_exit_zero(env, tmp_path):
    gh = finish_with(env, tmp_path, "failed 100\nexit_status 0\n", SUMMARY_OK)
    assert "state=failure" in gh and "failed=100" in gh


def test_finish_error_on_exit_zero_without_pytest_summary(env, tmp_path):
    gh = finish_with(env, tmp_path, QACCT_OK, "")
    assert "state=error" in gh and "no pytest summary" in gh


@pytest.mark.parametrize("qacct", ["failed 0\nexit_status 3\n", "failed 100\nexit_status 0\n"])
def test_finish_error_not_failure_when_job_failed_before_pytest_ran(env, tmp_path, qacct):
    # job 8388548: exit 3 from bootstrap_env.sh, log has no pytest output
    gh = finish_with(env, tmp_path, qacct, "")
    assert "state=error" in gh and "tests did not run" in gh


def test_finish_failure_when_summary_reports_failed_despite_exit_zero(env, tmp_path):
    gh = finish_with(env, tmp_path, QACCT_OK, "1 failed, 5 passed in 1.00s\n")
    assert "state=failure" in gh


def test_finish_error_when_qacct_has_no_record(env, tmp_path):
    # rc 1 with a record-shaped stdout: only the returncode check can reject this
    gh = finish_with(env, tmp_path, QACCT_OK, SUMMARY_OK, rc=1)
    assert "state=error" in gh and "job 7" in gh


def test_finish_reads_the_exit_status_field_not_a_lookalike_line(env, tmp_path):
    record = "category  -l exit_status 0\nfailed 0\nexit_status 1\n"
    gh = finish_with(env, tmp_path, record, "1 failed in 1.00s\n")
    assert "state=failure" in gh and "exit 1" in gh


def record_for(env, tmp_path, test="101", follow="202", age_days=0.0, current="pending"):
    """Submit through the real code, then set the GitHub status and queue the sweep will see."""
    repo, log = env
    ci.main(["submit", "--repo", str(repo), "--test-script", "run.sh"])
    sha = git(repo, "rev-parse", "HEAD")
    rec_file = ci.WORKTREES / "proj" / f"{sha[:12]}.json"
    rec = json.loads(rec_file.read_text())
    rec["submitted"] -= age_days * 86400
    rec_file.write_text(json.dumps(rec))
    (tmp_path / "statuses.json").write_text(json.dumps([{"context": "scc-tests", "state": current}]))
    log.write_text("")
    return rec, rec_file


def test_submit_writes_record_for_sweep(env, tmp_path):
    rec, _ = record_for(env, tmp_path)
    assert (rec["test_job"], rec["follow_job"], rec["context"]) == ("101", "202", "scc-tests")
    assert rec["sha"] == git(env[0], "rev-parse", "HEAD") and rec["repo"] == str(env[0])


def test_sweep_errors_pending_when_test_job_in_eqw_and_deletes_followup(env, tmp_path):
    repo, log = env
    record_for(env, tmp_path)
    (tmp_path / "qstat.txt").write_text(
        "job-ID prior name user state submit\n---\n101 0.5 t u Eqw 11/01\n202 0.5 f u hqw 11/01\n")
    ci.main(["sweep"])
    [post] = [ln for ln in calls(log, "gh") if "state=" in ln]
    assert "state=error" in post and "101" in post and "Eqw" in post
    assert calls(log, "qdel") == ["qdel 202"]


def test_sweep_errors_pending_when_both_jobs_vanished(env, tmp_path):
    repo, log = env
    record_for(env, tmp_path)
    ci.main(["sweep"])
    [post] = [ln for ln in calls(log, "gh") if "state=" in ln]
    assert "state=error" in post and "neither job" in post
    assert not calls(log, "qdel")


def test_sweep_leaves_healthy_pending_alone(env, tmp_path):
    repo, log = env
    record_for(env, tmp_path)
    (tmp_path / "qstat.txt").write_text("101 0.5 t u r 11/01\n202 0.5 f u hqw 11/01\n")
    ci.main(["sweep"])
    assert not [ln for ln in calls(log, "gh") if "state=" in ln] and not calls(log, "qdel")


def test_sweep_leaves_final_status_alone(env, tmp_path):
    repo, log = env
    record_for(env, tmp_path, current="success")
    ci.main(["sweep"])
    assert not [ln for ln in calls(log, "gh") if "state=" in ln]


def test_sweep_prune_removes_old_finished_worktree_via_git(env, tmp_path):
    repo, log = env
    rec, rec_file = record_for(env, tmp_path, age_days=10, current="success")
    ci.main(["sweep", "--prune", "7"])
    assert not Path(rec["worktree"]).exists() and not rec_file.exists()
    assert rec["worktree"] not in git(repo, "worktree", "list")


def test_sweep_prune_keeps_recent_and_unfinished_worktrees(env, tmp_path):
    repo, _ = env
    rec, rec_file = record_for(env, tmp_path, age_days=1, current="success")
    ci.main(["sweep", "--prune", "7"])
    assert Path(rec["worktree"]).exists()
    (tmp_path / "statuses.json").write_text(json.dumps([{"context": "scc-tests", "state": "pending"}]))
    (tmp_path / "qstat.txt").write_text("101 0.5 t u r 11/01\n")
    rec["submitted"] -= 30 * 86400
    rec_file.write_text(json.dumps(rec))
    ci.main(["sweep", "--prune", "7"])
    assert Path(rec["worktree"]).exists()


def test_fetch_prunes_stale_remote_refs(env, tmp_path, monkeypatch):
    repo, log = env
    (tmp_path / "bin" / "git").write_text(STUB % 'exec /usr/bin/git "$@"')
    (tmp_path / "bin" / "git").chmod(0o755)
    ci.resolve_sha(repo, None)
    assert any(" fetch " in ln and "--prune" in ln for ln in calls(log, "git"))


def test_owner_repo_parses_https_and_ssh(env):
    repo, _ = env
    assert ci.owner_repo(repo) == ("FilyCode", "EnzymeFinder")
    git(repo, "remote", "set-url", "origin", "https://github.com/Foo/bar.git")
    assert ci.owner_repo(repo) == ("Foo", "bar")
