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
On `main` the cache is **CWD-relative** (`SearchPipelineConfig.cache_dir` defaults to `.cache/enzymefinder`,
`stages.py` uses `<project_dir>/cache`): run from the project root and set
`-wd /projectnb/liu-scc/philipp/projects/EnzymeFinder` in qsub scripts. `ENZYMEFINDER_CACHE_DIR` never existed.

From the CDB wave (branch `cdb`, until merged) one function picks the store:
`cache/resolve.py::resolve_cache_store`. Set `cdb.root` (absolute path; `ENZYMEFINDER_CDB__ROOT`, or `[cdb] root`
in the project/user/site `enzymefinder.toml`) to use the shared DuckDB shard store; the owner-only root is
`/projectnb/liu-scc/philipp/software/enzymefinder/cdb/`. Unset, each run caches in `<output_dir>/<run_name>/cache`
with one WARNING; nothing defaults under `~`. `CacheConfig.cache_dir` is deprecated and selects nothing.
A run's shard becomes visible to other runs only after the run-end merge.

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
Results land in `logs/pytest_qsub.$JOB_ID.out`. Track with a single backgrounded wait
loop, not repeated `qstat -j <JOB_ID>` checks — see the `running-sge-jobs` skill's "Waiting on a job
without burning tokens".

## Known limitations and optimization register (core.md 12-13)
The register is `phases/W9-BACKLOG.md`, with one row per item and its routing line in
`phases/ROW_ASSIGNMENTS.tsv`. Route each item to the wave that owns its fix. When no wave owns
it yet, route it to `OPT`, the planned pre-P14 optimization phase (WAVES in
`scripts/build_open_tasks.py`, row in `phases/PLANS.md`).

Then regenerate with `scripts/build_open_tasks.py` and run `--check`, which must report
0 UNASSIGNED and 0 STALE. `docs/IMPROVEMENT_OPTIONS.md` is free text that the check never
reads, so it is not a substitute.

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
