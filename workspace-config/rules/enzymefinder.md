---
paths:
  - "projects/EnzymeFinder/**"
---

# EnzymeFinder conventions

## Status sync (binding)
A phase status change updates all three surfaces in the same commit:
1. `PROJECT_STATE.md` — canonical ledger
2. `phases/_index.md` — index row
3. `phases/<PHASE>/PLAN.md` — header status block

Vocabulary: `PLANNED | READY | IN_PROGRESS | COMPLETE | DEPLOYED | ARCHIVED`, each with
`(verified YYYY-MM-DD)` appended. Also update `phases/PLANS.md` — `Approved` date when a
plan is approved, `Completed` when it finishes. External `~/.claude/plans/` files are the
content source; `PLANS.md` is the in-repo pointer and is what makes a plan discoverable.

## Cache location
The cache is **CWD-relative**: `SearchPipelineConfig.cache_dir` defaults to
`Path(".cache/enzymefinder")`, and `stages.py` uses `<project_dir>/cache`. There is no
`ENZYMEFINDER_CACHE_DIR` env var — a P4-MVP note describes one, but it was never
implemented, so do not rely on it.

Consequence: the cache lands wherever the process starts. **Run the pipeline from the
project root**, and set `-wd /projectnb/liu-scc/philipp/projects/EnzymeFinder` (or `cd`
first) in any qsub script, so caches never accumulate in a home directory or a scratch
path that gets swept.

## Tests
Full suite is ~11 min — always via `qsub`, never on the login node.

```bash
mkdir -p logs
qsub scripts/scc-submissions/run_pytest_qsub.sh                              # full suite
qsub -v PYTEST_ARGS="tests/test_foo.py" scripts/scc-submissions/run_pytest_qsub.sh
qsub -v PYTEST_FILTER="not 019f" scripts/scc-submissions/run_pytest_qsub.sh
qsub -v PYTEST_LASTFAILED=1 scripts/scc-submissions/run_pytest_qsub.sh       # --last-failed
```

Never embed `-k` inside `PYTEST_ARGS` — shell word-splitting breaks it. Use `PYTEST_FILTER`.
Results land in `logs/pytest_qsub.$JOB_ID.out`. Track with `qstat -j <JOB_ID>`.

## Comparison data for end-to-end runs
Use real results from the other projects as baselines rather than synthetic fixtures:
EanB, CaMES/MeMES, MqnE/MqnC, K4-K26. Before calling a mismatch a defect, rule out the
two expected confounds — upstream database drift since the other project's run, and
different search parameters (hitlist size, E-value, tier). A real bug looks like a hit
present in both snapshots that EnzymeFinder drops or misclassifies, or a confidence tier
inconsistent with the evidence EnzymeFinder itself recorded — not simply a different hit count.

## Building new capability
When a gap analysis surfaces a missing capability, build the general version, not the
minimum that satisfies the project that exposed it. Ask explicitly whether the design
would serve a user with a different scoring need. Worth a design pass with independent
proposals before implementing.
