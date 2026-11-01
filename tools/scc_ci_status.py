#!/usr/bin/env python3
"""Run a project's full test suite on SCC and post the result as a GitHub commit status.

Why: GitHub Actions minutes run out each month, so the full suite runs on the cluster and
only the verdict goes to GitHub (owner decision, 2026-11-01).

  scc_ci_status.py submit --repo <path> [--sha S] [--test-script scripts/scc-submissions/run_pytest_qsub.sh]
      checks S is on the remote, makes a detached worktree at S under WORKTREES, posts `pending`,
      qsubs the test script with PROJECT_ROOT=<worktree>, then qsubs a 1-slot follow-up held on
      it that posts success / failure / error. Nobody has to wait.
  scc_ci_status.py post --repo <path> --sha S --state <s> --description <d>   manual path
  scc_ci_status.py finish ...   what the follow-up job runs (reads qacct, posts the verdict)

Environment of the test job: the script's bootstrap_env.sh honours `VENV_DIR`, so the job is
given the main repo's `.venv` that way (a fresh worktree has none and would fall back to the
workspace venv, a different Python). A script that ignores VENV_DIR just uses its own default.
Stdlib only; needs `git`, `gh` (authenticated) and, for submit/finish, SGE's `qsub`/`qacct`.
"""
import argparse
import re
import subprocess
import sys
import time
from pathlib import Path

WORKTREES = Path("/projectnb/liu-scc/philipp/software/scc-ci")
STATES = ("pending", "success", "failure", "error")
SUMMARY_RE = re.compile(r"^=*\s*(\d+ (?:passed|failed|error|errors|skipped|xfailed|deselected)\b.*? in [\d.]+s.*?)\s*=*$")


def run(cmd, **kw):
    """Run a command; on a non-zero exit stop with the command and its stderr."""
    p = subprocess.run(cmd, capture_output=True, text=True, **kw)
    if p.returncode:
        sys.exit(f"scc_ci_status: `{' '.join(map(str, cmd))}` exited {p.returncode}: {p.stderr.strip() or p.stdout.strip()}")
    return p.stdout.strip()


def owner_repo(repo):
    """('FilyCode', 'EnzymeFinder') from the origin URL (ssh or https form)."""
    url = run(["git", "-C", str(repo), "config", "--get", "remote.origin.url"])
    m = re.search(r"github\.com[:/]([^/]+)/([^/]+?)(?:\.git)?/?$", url)
    if not m:
        sys.exit(f"scc_ci_status: origin URL {url!r} is not a github.com owner/repo URL, so the status cannot be addressed")
    return m.group(1), m.group(2)


def post_status(repo, sha, state, description, context):
    """POST a commit status through `gh api`; a failure stops the tool (never silently unposted)."""
    owner, name = owner_repo(repo)
    run(["gh", "api", f"repos/{owner}/{name}/statuses/{sha}", "-f", f"state={state}",
         "-f", f"context={context}", "-f", f"description={description[:140]}"])


def resolve_sha(repo, sha):
    """Full SHA to test. Refuses a SHA not on the remote, and a dirty tracked tree when defaulting to HEAD."""
    if sha is None and run(["git", "-C", str(repo), "status", "--porcelain", "--untracked-files=no"]):
        sys.exit(f"scc_ci_status: {repo} has uncommitted tracked changes; the job tests a commit, "
                 "so commit and push first (or pass --sha of a pushed commit)")
    full = run(["git", "-C", str(repo), "rev-parse", "--verify", f"{sha or 'HEAD'}^{{commit}}"])
    run(["git", "-C", str(repo), "fetch", "--quiet", "origin"])
    if not run(["git", "-C", str(repo), "branch", "-r", "--contains", full]):
        sys.exit(f"scc_ci_status: {full[:12]} is not on any remote branch of {repo}; push it first, "
                 "otherwise GitHub has no commit to attach the status to")
    return full


def ensure_worktree(repo, sha):
    """Detached worktree at sha outside any project tree; reused when already there at that sha."""
    path = WORKTREES / Path(repo).resolve().name / sha[:12]
    if path.exists():
        if run(["git", "-C", str(path), "rev-parse", "HEAD"]) != sha:
            sys.exit(f"scc_ci_status: {path} exists but is not at {sha[:12]}; remove it (git worktree remove) and retry")
        return path
    path.parent.mkdir(parents=True, exist_ok=True)
    run(["git", "-C", str(repo), "worktree", "add", "--detach", str(path), sha])
    return path


def submit(args):
    repo = Path(args.repo).resolve()
    sha = resolve_sha(repo, args.sha)
    wt = ensure_worktree(repo, sha)
    venv = repo / ".venv"
    envs = f"PROJECT_ROOT={wt}" + (f",VENV_DIR={venv}" if venv.is_dir() else "")
    post_status(repo, sha, "pending", f"submitted to SCC {time.strftime('%H:%M')}", args.context)
    script = args.test_script if Path(args.test_script).is_absolute() else str(wt / args.test_script)
    job = run(["qsub", "-terse", "-v", envs, script], cwd=wt)
    me = Path(__file__).resolve()
    out = WORKTREES / repo.name / f"finish_{sha[:12]}.{job}.out"
    follow = run(["qsub", "-terse", "-V", "-b", "y", "-hold_jid", job, "-pe", "omp", "1", "-l", "h_rt=0:15:00",
                  "-P", "liu-scc", "-N", f"scc_ci_post_{sha[:7]}", "-j", "y", "-o", str(out), sys.executable, str(me),
                  "finish", "--repo", str(repo), "--sha", sha, "--job-id", job, "--worktree", str(wt),
                  "--context", args.context])
    print(f"test job {job}  follow-up job {follow}  sha {sha}\nworktree {wt}\n"
          f"test log {repo}/logs/pytest_qsub.{job}.out  (pytest output: {wt}/logs/pytest_full_{job}.log)\n"
          f"follow-up log {out}")


def pytest_summary(wt, job):
    """Last pytest summary line of the job's log, or None."""
    log = Path(wt) / "logs" / f"pytest_full_{job}.log"
    if log.is_file():
        for line in reversed(log.read_text(errors="replace").splitlines()):
            m = SUMMARY_RE.match(line.strip())
            if m:
                return m.group(1)
    return None


def exit_status(job, tries=10, wait=30):
    """exit_status from qacct, retried because accounting lags job end; None if never available."""
    for _ in range(tries):
        p = subprocess.run(["qacct", "-j", job], capture_output=True, text=True)
        m = re.search(r"^exit_status\s+(\d+)", p.stdout, re.M)
        if p.returncode == 0 and m:
            return int(m.group(1))
        time.sleep(wait)
    return None


def finish(args):
    rc = exit_status(args.job_id)
    summ = pytest_summary(args.worktree, args.job_id) or "no pytest summary line in log"
    if rc is None:
        state, desc = "error", f"no exit status for job {args.job_id} (killed at h_rt?)"
    else:
        state = "success" if rc == 0 else "failure"
        desc = f"{summ}; job {args.job_id}" + ("" if rc == 0 else f" exit {rc}")
    post_status(args.repo, args.sha, state, desc, args.context)
    print(f"posted {state}: {desc[:140]}")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    def common(p):
        p.add_argument("--repo", required=True)
        p.add_argument("--context", default="scc-tests")
        return p
    s = common(sub.add_parser("submit"))
    s.add_argument("--sha")
    s.add_argument("--test-script", default="scripts/scc-submissions/run_pytest_qsub.sh")
    s.set_defaults(fn=submit)
    p = common(sub.add_parser("post"))
    p.add_argument("--sha", required=True)
    p.add_argument("--state", required=True, choices=STATES)
    p.add_argument("--description", required=True)
    p.set_defaults(fn=lambda a: post_status(a.repo, a.sha, a.state, a.description, a.context))
    f = common(sub.add_parser("finish"))
    f.add_argument("--sha", required=True)
    f.add_argument("--job-id", required=True)
    f.add_argument("--worktree", required=True)
    f.set_defaults(fn=finish)
    args = ap.parse_args(argv)
    args.fn(args)


if __name__ == "__main__":
    main()
