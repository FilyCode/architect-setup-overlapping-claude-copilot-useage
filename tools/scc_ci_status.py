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
  scc_ci_status.py sweep [--repo <path>] [--prune DAYS]
      for each record written by submit: if the status is still `pending` and the test job is in an
      error state (Eqw) or neither job is in qstat, post `error` and qdel the held follow-up; with
      --prune, `git worktree remove --force` worktrees whose status is final and older than DAYS.
  A submit whose qsub fails posts `error` (and qdels the test job if only the follow-up failed).
  `pending` and `error` mean unknown, never passed; only `success` counts.

Environment of the test job: the script's bootstrap_env.sh honours `VENV_DIR`, so the job is
given the main repo's `.venv` that way (a fresh worktree has none and would fall back to the
workspace venv, a different Python). A script that ignores VENV_DIR just uses its own default.
Stdlib only; needs `git`, `gh` (authenticated) and, for submit/finish, SGE's `qsub`/`qacct`.
"""
import argparse
import getpass
import json
import re
import subprocess
import sys
import time
from pathlib import Path

QACCT_TRIES = 10
QACCT_WAIT = 30  # seconds between qacct retries; accounting lags job end
WORKTREES = Path("/projectnb/liu-scc/philipp/software/scc-ci")
STATES = ("pending", "success", "failure", "error")
SUMMARY_RE = re.compile(r"^=*\s*(\d+ (?:passed|failed|error|errors|skipped|xfailed|deselected)\b.*? in [\d.]+s.*?)\s*=*$")


def run(cmd, **kw):
    """Run a command; on a non-zero exit stop with the command and its stderr."""
    p = subprocess.run(cmd, capture_output=True, text=True, **kw)
    if p.returncode:
        sys.exit(f"scc_ci_status: `{' '.join(map(str, cmd))}` exited {p.returncode}: {p.stderr.strip() or p.stdout.strip()}")
    return p.stdout.strip()


def why(exc):
    """The stderr part of run()'s SystemExit message (the full command would eat the 140-char description)."""
    m = re.search(r"exited \d+: (.*)", str(exc), re.S)
    return m.group(1) if m else str(exc)


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
    run(["git", "-C", str(repo), "fetch", "--quiet", "--prune", "origin"])
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
    try:
        job = run(["qsub", "-terse", "-v", envs, script], cwd=wt)
    except SystemExit as e:
        post_status(repo, sha, "error", f"submit failed, test job not queued: {why(e)}", args.context)
        raise
    me = Path(__file__).resolve()
    out = WORKTREES / repo.name / f"finish_{sha[:12]}.{job}.out"
    try:
        follow = run(["qsub", "-terse", "-V", "-b", "y", "-hold_jid", job, "-pe", "omp", "1", "-l", "h_rt=0:15:00",
                      "-P", "liu-scc", "-N", f"scc_ci_post_{sha[:7]}", "-j", "y", "-o", str(out), sys.executable, str(me),
                      "finish", "--repo", str(repo), "--sha", sha, "--job-id", job, "--worktree", str(wt),
                      "--context", args.context])
    except SystemExit as e:
        subprocess.run(["qdel", job], capture_output=True, text=True)  # an unobserved test job must not run
        post_status(repo, sha, "error", f"submit failed, follow-up not queued, test job {job} deleted: {why(e)}", args.context)
        raise
    record_path(wt).write_text(json.dumps({
        "sha": sha, "repo": str(repo), "context": args.context, "test_job": job,
        "follow_job": follow, "worktree": str(wt), "submitted": time.time()}))
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


def record_path(wt):
    """JSON record next to the worktree dir, written by submit and read by sweep."""
    return Path(wt).parent / f"{Path(wt).name}.json"


def accounting(job):
    """(exit_status, failed) ints from qacct, retried because accounting lags job end; None if never available."""
    for _ in range(QACCT_TRIES):
        p = subprocess.run(["qacct", "-j", job], capture_output=True, text=True)
        m = re.search(r"^exit_status\s+(\d+)", p.stdout, re.M)
        f = re.search(r"^failed\s+(\d+)", p.stdout, re.M)
        if p.returncode == 0 and m and f:
            return int(m.group(1)), int(f.group(1))
        time.sleep(QACCT_WAIT)
    return None


def verdict(acct, summ, job):
    """(state, description). success needs exit 0, failed 0 and a pytest summary with no failed/error count."""
    if acct is None:
        return "error", f"no accounting record for job {job} (never ran, deleted while queued, or accounting missing)"
    rc, failed = acct
    if rc != 0:
        return "failure", f"{summ or 'no pytest summary line in log'}; job {job} exit {rc}"
    if failed != 0:
        return "failure", f"{summ or 'no pytest summary line in log'}; job {job} SGE failed={failed}"
    if summ is None:
        return "error", f"job {job} exited 0 but the log has no pytest summary line (log not copied?)"
    if re.search(r"\b\d+ (?:failed|errors?)\b", summ):
        return "failure", f"{summ}; job {job} exited 0 but the summary reports failures"
    return "success", f"{summ}; job {job}"


def finish(args):
    state, desc = verdict(accounting(args.job_id), pytest_summary(args.worktree, args.job_id), args.job_id)
    post_status(args.repo, args.sha, state, desc, args.context)
    print(f"posted {state}: {desc[:140]}")


def current_state(repo, sha, context):
    """Newest state of `context` on sha (GitHub lists statuses newest first), or None if never posted."""
    owner, name = owner_repo(repo)
    rows = json.loads(run(["gh", "api", f"repos/{owner}/{name}/commits/{sha}/statuses"]) or "[]")
    return next((r["state"] for r in rows if r["context"] == context), None)


def queue_states():
    """{job id: state letters} for the current user's jobs in qstat."""
    states = {}
    for line in run(["qstat", "-u", getpass.getuser()]).splitlines():
        cols = line.split()
        if len(cols) > 5 and cols[0].isdigit():
            states[cols[0]] = cols[4]
    return states


def sweep(args):
    """Resolve stale `pending` statuses and optionally prune finished worktrees (see module docstring)."""
    queued = queue_states()
    for rec_file in sorted(WORKTREES.glob("*/*.json")):
        rec = json.loads(rec_file.read_text())
        if args.repo and Path(rec["repo"]).resolve() != Path(args.repo).resolve():
            continue
        test, follow = rec["test_job"], rec["follow_job"]
        state = current_state(rec["repo"], rec["sha"], rec["context"])
        reason = None
        if state == "pending":
            if "E" in queued.get(test, ""):
                reason = f"test job {test} is stuck in state {queued[test]}"
            elif test not in queued and follow not in queued:
                reason = f"neither job {test} nor {follow} is in qstat and no result was posted"
        if reason:
            post_status(rec["repo"], rec["sha"], "error", f"sweep: {reason}", rec["context"])
            if follow in queued:
                run(["qdel", follow])
            state = "error"
            print(f"{rec['sha'][:12]}: error, {reason}")
        if args.prune is not None and state in ("success", "failure", "error") \
                and test not in queued and follow not in queued \
                and time.time() - rec["submitted"] > args.prune * 86400:
            run(["git", "-C", rec["repo"], "worktree", "remove", "--force", rec["worktree"]])
            rec_file.unlink()
            print(f"{rec['sha'][:12]}: pruned worktree {rec['worktree']}")


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
    w = sub.add_parser("sweep")
    w.add_argument("--repo", help="only records of this repo (default: all under WORKTREES)")
    w.add_argument("--prune", type=float, metavar="DAYS",
                   help="remove worktrees with a final status and no queued job, older than DAYS")
    w.set_defaults(fn=sweep)
    args = ap.parse_args(argv)
    args.fn(args)


if __name__ == "__main__":
    main()
