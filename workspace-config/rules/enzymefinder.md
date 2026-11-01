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
For a wave with no `phases/<WAVE>/` directory, surface 3 is the plan header under
`docs/superpowers/plans/`. (CDB had none, and the header kept asserting "Task 13 not built" above
its own ticked checkboxes until the wave-end review caught it.)

## Cache location
One function picks a run's cache store: `cache/resolve.py::resolve_cache_store`. It is the only constructor of a
cache store outside `enzymefinder.cache`, guarded by an AST test
(`tests/test_cdb_resolve_store.py::test_all_cache_constructions_use_resolver`) — do not build a store anywhere else.
Set `cdb.root` to an absolute path (`ENZYMEFINDER_CDB__ROOT`, or `[cdb] root` in the project / user / site
`enzymefinder.toml`) to use the shared DuckDB shard store; the owner-only root is
`/projectnb/liu-scc/philipp/software/enzymefinder/cdb/`. Unset, each run caches in
`<output_dir>/<run_name>/cache` with one WARNING per process; nothing defaults under `~`.
`CacheConfig.cache_dir` is deprecated and selects nothing; an explicit `--cache-dir` still names a per-run file cache.

Visibility is merge-then-visible: a run sees its own shard plus the current merged generation, never another run's
unmerged shard. A non-array run merges at run end; **array tasks do not** — submit one
`qsub -hold_jid <array> ... enzymefinder cache merge` job and hold downstream readers on it. Layout, health check,
rollback, move-a-root and snapshot restore: `docs/HPC_DATABASE_SETUP.md`, section "Shared cache store (CDB root)".

Pre-CDB history: the cache was CWD-relative (`.cache/enzymefinder`, `stages.py` under `<project_dir>/cache`).
Setting `-wd /projectnb/liu-scc/philipp/projects/EnzymeFinder` in qsub scripts is still right, but now because
project-scoped Tier-2 entries key on the resolved project directory, not because the cache follows the CWD.
There is no `ENZYMEFINDER_CACHE_DIR`; the environment name is `ENZYMEFINDER_CACHE__CACHE_DIR` (double underscore,
the nested-key convention), it is outranked by an explicit `--cache-dir`, and it is read by `enzymefinder run` but
deliberately not by every subcommand (`cli/main.py:383-387`, precedence at `:2352-2368`).

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

Branch gates: at the first commit of a branch and again before the PR, run
`pre-commit run --hook-stage push --all-files` and `python3 scripts/build_open_tasks.py --verify`
(CI runs `--verify`, not `--check`). Run each gate as its own command, never piped into `| tail`,
and quote its exit code, not trimmed output (R-20261022-10, R-20261024-5).

## CI
PR checks on GitHub are the cheap jobs only (Actions minutes run out monthly). The full suite runs on
SCC via `tools/scc_ci_status.py submit` (config repo), which posts the `scc-tests` commit status.
A weekly and a monthly GitHub run on main are the clean-machine check. Failures follow the CI rule
in skill verification-patterns (red blocks merge; every failure gets a cause).

## Reference index (P0, DECISION-138)
A run reaches the Swiss-Prot tier indexes only through the site file named by
`ENZYMEFINDER_SITE_CONFIG` (`/projectnb/liu-scc/philipp/software/enzymefinder/site/enzymefinder.toml`;
no default). Every job script exports it; one that omits the export runs with both tiers
unresolved. `[databases.uniprot]` carries no `release` on purpose: the run records the
`X-UniProt-Release` header it observed.

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
