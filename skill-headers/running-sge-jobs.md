---
name: running-sge-jobs
description: How to submit, wait for and verify BU SCC SGE jobs for project liu-scc — resource defaults, the backgrounded wait loop with a deadline, reading appended logs, artifact checks, storage limits. Use when writing or submitting a qsub script, waiting on a job, or reading a job log. Diagnosing a failed job is scc-monitor's job.
---

# Running SGE jobs

## Correction to the moved text below (2026-10-14)

The listing-form wait loop in the moved text has no deadline, so it never exits for a job stuck
in `Eqw` or `hqw`. Use this form:

```bash
deadline=$(( $(date +%s) + H_RT_SECONDS + 3600 )); absent=0
while [ $absent -lt 3 ]; do
  [ $(date +%s) -ge $deadline ] && { echo "TIMEOUT: check qstat -u phitro (Eqw/hqw?)"; break; }
  qstat -u phitro 2>/dev/null | grep -q "^ *<jobid> " && absent=0 || absent=$((absent+1))
  sleep 45
done
```

**Host filters (2026-10-21, `qconf -sc`).** `-l mem_per_core=N` (relop `<=`) keeps only hosts
with at least N per core; 12G matched only the 24G/core GPU nodes and job 8132228 sat 70 min in
qw: request memory with `-pe omp K` and a lower value. A job in qw over 10 min: read the
scheduling info in `qstat -j <id>`. CPU test and eval jobs whose wheels need AVX2 (FBGEMM,
torch CPU) request `-l avx2`: job 8171407 on a non-AVX2 host gave 6 false failures.

Claude runs inside an SGE job on a compute node (`$JOB_ID` set); the login-node limits below
apply to work started from a login shell.

The rules below are the original workspace text, moved verbatim.
