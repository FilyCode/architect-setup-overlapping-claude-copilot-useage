# Runbook

Operational procedures proven across projects. Detail lives here; `.claude/prompt-snippets/scc-profile.md` links to this file rather than embedding it, per token-efficiency context-hygiene rule.

## Running tests on the SCC (never on the login node)

The BU SCC login-node process reaper silently kills anything over ~30s CPU — no error, no output, the run just vanishes. This has cost full test-suite runs multiple times.

- Safe on login node (<~15s): single-file import checks, syntax checks, one tiny test file.
- Anything larger: go through `qsub`.

```bash
mkdir -p logs
qsub scripts/scc-submissions/run_pytest_qsub.sh
# Specific files (PYTEST_ARGS = path args only, no flags):
qsub -v PYTEST_ARGS="tests/test_foo.py" scripts/scc-submissions/run_pytest_qsub.sh
# -k filter (PYTEST_FILTER — never embed -k inside PYTEST_ARGS, shell word-splitting breaks it):
qsub -v PYTEST_FILTER="not some_marker" scripts/scc-submissions/run_pytest_qsub.sh
```

Track with `qstat -j <JOB_ID>`. Results land in `logs/pytest_qsub.$JOB_ID.out`.

Each project that runs pytest on the SCC needs its own `scripts/scc-submissions/run_pytest_qsub.sh` — this runbook entry documents the pattern, not a shared script (job scripts are project-specific: paths, modules, conda envs differ).

## Job lifecycle

`User/Agent → script from template → qsub → SGE queue → qstat/qacct → output`

- `qstat` — active jobs
- `qacct -j <JOB_ID>` — post-run diagnostics (exit_status, maxvmem) once the job leaves the queue
- `qgpus` — GPU inventory
