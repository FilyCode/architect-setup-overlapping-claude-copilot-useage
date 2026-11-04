# REPO/tests/test_bash_guard.py
import subprocess
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "workspace-config" / "hooks"))
import pytest
from bash_guard import decide

P = "/projectnb/liu-scc/philipp/projects/EnzymeFinder"
JOB = {"JOB_ID": "123"}

def d(cmd, cwd=P, env=JOB):
    return decide(cmd, cwd, env)[0]

def test_stash_blocked_variants():
    assert d("git stash") == "deny"
    assert d("git stash push -- src/x.py") == "deny"
    assert d(f"git -C {P} stash pop") == "deny"
    assert d("cd src && git stash") == "deny"

def test_stash_read_only_allowed():
    assert d("git stash list") == "allow"
    assert d("git stash show -p stash@{0}") == "allow"

def test_work_tree_checkout_blocked():
    assert d("git --work-tree=/tmp/x checkout abc123 -- .") == "deny"
    assert d("git show abc123:src/x.py") == "allow"

def test_pytest_needs_job():
    assert d("pytest -q", env={}) == "deny"
    assert d("FOO=1 python -m pytest tests", env={}) == "deny"
    assert d("pytest -q") == "allow"
    assert d("qsub -v PYTEST_ARGS=x scripts/run_pytest_qsub.sh", env={}) == "allow"

def test_rm_recursive_under_projects():
    assert d("rm -rf results/old") == "deny"
    assert d("\\rm -fr logs") == "deny"
    assert d("rm -r -f build", cwd=P) == "deny"
    assert d("rm -rf /scratch/8090063.1.y/claude-768026/x") == "allow"
    assert d("rm results/one_file.tsv") == "allow"

def test_find_delete_warns():
    assert d("find . -name '*.pyc' -delete") == "warn"

def test_unparseable_is_allowed():
    assert d("echo 'unterminated") == "allow"


# Corpus-replay false positives (2026-10-14, 209 denies over 44,870 commands; real command shapes)
SC = "/scratch/7921614.1.p/claude-768026/x/scratchpad/w4b"


def test_variable_target_resolved_from_assignment():
    assert d(f"S={SC}; rm -rf $S/fx; mkdir -p $S/fx") == "allow"
    assert d(f'SC={SC} && \\rm -rf "$SC" 2>/dev/null; mkdir -p "$SC"') == "allow"
    assert d("S=results/old; rm -rf $S") == "deny"


def test_unresolved_variable_is_allowed():
    assert d("rm -rf $UNKNOWN_DIR/tmp") == "allow"


def test_cd_changes_resolution_base():
    assert d(f"cd {SC} && rm -rf p1 && mkdir p1") == "allow"
    assert d(f"cd {P} && rm -rf build") == "deny"


def test_newlines_split_commands():
    assert d(f"rm -rf {SC}/w0b_t2\ncd {P} && git status --short") == "allow"
    assert d("echo done\ngit stash") == "deny"


def test_heredoc_body_ignored():
    assert d("cat >> notes.md <<'EOF'\nrm -rf src\ngit stash\nEOF\necho ok") == "allow"


def test_cache_dirs_allowed():
    assert d("\\rm -rf .mypy_cache") == "allow"
    assert d("rm -rf docs/audits/x/helpers/__pycache__") == "allow"


def test_agent_scratch_areas_allowed():
    assert d('WS=.superpowers/sdd/2026-09-18-w2-plan\n\\rm -rf "$WS"') == "allow"
    assert d("rm -rf .scratch/w1b/T6/mypy_before") == "allow"
    assert d("cd .superpowers/sdd/p/scratch_taskA3 && rm -rf mirrors/cls1") == "allow"
    assert d("rm -rf tests/fixtures/sources") == "deny"


def test_cat_of_large_file_warns(tmp_path):
    big = tmp_path / "big.tsv"
    big.write_bytes(b"x" * 1_100_000)
    small = tmp_path / "small.txt"
    small.write_text("ok\n")
    assert d(f"cat {big}", cwd=str(tmp_path)) == "warn"
    assert d("cat big.tsv", cwd=str(tmp_path)) == "warn"
    assert d(f"cat {small}", cwd=str(tmp_path)) == "allow"
    assert d(f"cat {big} | head -n 20", cwd=str(tmp_path)) == "allow"
    assert d(f"cat {big} | wc -l", cwd=str(tmp_path)) == "allow"
    assert d("cat missing.txt", cwd=str(tmp_path)) == "allow"
    # redirected output never reaches the context (real corpus shapes)
    assert d(f"cat {big} {small} > {tmp_path}/out.faa", cwd=str(tmp_path)) == "allow"
    assert d(f"cat {big} >> cand_all.csv", cwd=str(tmp_path)) == "allow"
    assert d(f"cat {big} >{tmp_path}/o", cwd=str(tmp_path)) == "allow"


def test_unbounded_find_from_root_or_home_warns():
    assert d("find / -name '*.fa'") == "warn"
    assert d("find ~ -name x") == "warn"
    assert d("find $HOME -type f") == "warn"
    assert d("command find / -name x") == "warn"
    assert d("find / -maxdepth 3 -name x") == "allow"
    assert d("find . -name '*.py'") == "allow"
    assert d("find /projectnb/liu-scc/philipp/projects -name x") == "allow"


# R-20261104-1: a switch/merge that OVERWRITES a git-ignored file on disk with the target's tracked version.
# (Probe 2026-11-04: stale tracks big.csv "old"; main untracks+ignores it; disk holds new data; `git checkout stale`
# succeeds silently and big.csv reads "old".)
def _git(repo, *args):
    subprocess.run(["git", "-C", str(repo), "-c", "user.email=t@t", "-c", "user.name=t", *args],
                   check=True, capture_output=True)


@pytest.fixture
def overwrite_repo(tmp_path):
    r = tmp_path / "repo"
    r.mkdir()
    _git(r, "init", "-q", "-b", "main")
    (r / "big.csv").write_text("old\n")
    (r / "other.txt").write_text("o\n")
    _git(r, "add", ".")
    _git(r, "commit", "-qm", "1")
    _git(r, "branch", "stale")
    _git(r, "rm", "-q", "--cached", "big.csv")
    (r / ".gitignore").write_text("big.csv\n")
    _git(r, "add", ".gitignore")
    _git(r, "commit", "-qm", "2")
    (r / "big.csv").write_text("NEW_PRECIOUS\n")
    return r


def test_switch_overwriting_ignored_file_denied(overwrite_repo):
    r = str(overwrite_repo)
    for cmd, cwd in (("git checkout stale", r), ("git switch stale", r), (f"git -C {r} checkout stale", "/"),
                     (f"cd {r} && git checkout stale", "/")):
        verdict, reason = decide(cmd, cwd, JOB)
        assert verdict == "deny", cmd
        assert "OVERWRITE 1 git-ignored" in reason and "big.csv" in reason, reason


def test_merge_adding_ignored_path_denied(overwrite_repo):
    r = overwrite_repo
    _git(r, "checkout", "-q", "-b", "feat")
    (r / "scratch.dat").write_text("feat\n")
    (r / ".gitignore").write_text("big.csv\nscratch.dat\n")
    _git(r, "add", "-f", ".gitignore", "scratch.dat")
    _git(r, "commit", "-qm", "3")
    _git(r, "checkout", "-q", "main")
    (r / "scratch.dat").write_text("PRECIOUS\n")
    (r / ".gitignore").write_text("big.csv\nscratch.dat\n")  # current tree ignores it
    verdict, reason = decide("git merge --ff-only feat", str(r), JOB)
    assert verdict == "deny" and "scratch.dat" in reason, reason


def test_switch_override_allowed(overwrite_repo):
    assert d("ALLOW_IGNORED_OVERWRITE=1 git checkout stale", cwd=str(overwrite_repo)) == "allow"


def test_checkout_paths_and_new_branch_allowed(overwrite_repo):
    r = str(overwrite_repo)
    assert d("git checkout -- other.txt", cwd=r) == "allow"
    assert d("git checkout stale -- other.txt", cwd=r) == "allow"
    assert d("git checkout -b new", cwd=r) == "allow"
    assert d("git switch -c new2", cwd=r) == "allow"


def test_switch_not_touching_ignored_file_allowed(overwrite_repo):
    r = overwrite_repo
    (r / "big.csv").unlink()  # nothing on disk to overwrite
    assert d("git checkout stale", cwd=str(r)) == "allow"


def test_unresolvable_target_fails_open(overwrite_repo, tmp_path):
    assert d("git checkout no-such-ref", cwd=str(overwrite_repo)) == "allow"
    assert d("git checkout stale", cwd=str(tmp_path)) == "allow"  # not a git repo
