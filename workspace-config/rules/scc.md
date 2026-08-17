# BU SCC (liu-scc)

Scheduler is SGE. Project is `liu-scc`. Let `qsub` place jobs — do not force a queue.

## Job defaults
- Cores: 1 non-parallel; 4 / 8 / 16 / 28 parallel (best scheduling efficiency at these). 32/48/64 only for extreme cases.
- Memory: `-l mem_per_core=8G`. Ceiling 512G; 1024G only for extreme workloads.
- Runtime: `-l h_rt` ≤12h preferred. Escalate to 24/48/72h only when justified.
- `#!/bin/bash -l` whenever the script uses `module load`.
- `-P liu-scc` when a project spec is required. Array jobs use `SGE_TASK_ID`.
- `export NCBI_EMAIL=phitro@bu.edu` before any job that hits NCBI.

## Login node
The process reaper silently kills anything over ~30s CPU — no error, all output lost.
Never run `pytest` or any long process on the login node. Route it through `qsub`.

Safe on the login node (<15s): syntax/import checks, a single tiny test file.

## Verifying a job
`qacct` `exit_status 0` does **not** prove success — a tool that catches its own errors
(network timeouts, partial batch failures) exits 0 having produced nothing. Always check
that the expected output artifact exists on disk before treating a job as successful.

Do not submit many jobs that hit the same external API at once; stagger them or chain
with `qsub -hold_jid`.

## Storage
Home (`/usr3/graduate/phitro`) is capped at 10GB with a 7-day grace. Anything large —
model weights, caches, envs, node_modules, container images — belongs under
`/projectnb/liu-scc/philipp/software/<tool>/`, never in home.

Before installing a heavyweight tool, point its cache/data env var at `software/`. If it
has no override, install then move + symlink (`software/bin/scc_home_migrate.sh`).
`software/bin/scc_storage_audit.sh` reports current usage.

Gotchas: `rm` is aliased to `rm -i` and will hang with no stdin — use `\rm -f`. A cross-filesystem
`mv` of a large dir is slow and not resumable — prefer `rsync -av src/ dest/`, which also merges
correctly instead of nesting when the destination already exists.
