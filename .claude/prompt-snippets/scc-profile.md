# BU SCC Profile (liu-scc)

## Scheduler
- Project: `liu-scc`; Scheduler: SGE; let qsub choose queue by default.

## Resource Defaults
- Cores: 1 (non-parallel), 4/6/8/12/16/20/28 (parallel); extremes: 32/48/64
- Runtime: ≤12h preferred; escalate to 24h/48h/72h when justified
- Memory: `-l mem_per_core=8G`; ceiling 512G (1024G extreme)
- Best scheduling efficiency at 1, 4, 8, 16, 28 cores

## Script Defaults
- `#!/bin/bash -l` when using `module load`
- `-P liu-scc` when project spec is required
- Array jobs: use `SGE_TASK_ID` for many similar tasks

## Monitoring
- `qstat` → active jobs; `qacct` → post-run diagnostics (exit_status, maxvmem); `qgpus` → GPU inventory

## Escalation Triggers
- Repeated OOM or timeout despite profile-conform requests
- Regular need for >28 cores or >512G memory
- Consistent runtimes >12h
