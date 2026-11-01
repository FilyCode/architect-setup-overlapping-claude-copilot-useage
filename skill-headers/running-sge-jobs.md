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

**Cores: request what the job uses (2026-10-31; replaces "Cores" under Job defaults).** SGE
charges every reserved core. Over 14 days our jobs reserved 9143 core-h and used 3242 (35%); the
EC523 arrays held 4-8 slots and used 1.1-1.25. So:
- 1 slot unless a command in the script runs K threads; then put `# cores: <that command>` on the
  `-pe` line (`#$ -pe omp 8  # cores: diamond --threads $NSLOTS`) and pass `$NSLOTS` to it.
- Never add slots to get memory: SCC enforces memory loosely (owner, 2026-10-31).
- Before choosing K for a job that ran before: `tools/sge_efficiency.py lookup <name>` (config
  repo) shows its measured cores used. After every job, with the artifact check:
  `tools/sge_efficiency.py job <id>`; OVER-RESERVED means lower K next time, and `qalter -pe omp
  <k> <id>` fixes array tasks still queued.
- Hook `qsub_guard` enforces this on qsub/qrsh/qalter: K > 1 without a `# cores:` note is denied;
  a note contradicted by >= 2 measured runs is denied once. A subagent's qsub is denied (rule 5).

**Host filters (2026-10-21, `qconf -sc`).** `-l mem_per_core=N` (relop `<=`) keeps only hosts
with at least N per core; 12G matched only the 24G/core GPU nodes and job 8132228 sat 70 min in
qw: keep mem_per_core at 8G or less. A job in qw over 10 min: read the
scheduling info in `qstat -j <id>`. CPU test and eval jobs whose wheels need AVX2 (FBGEMM,
torch CPU) request `-l avx2`: job 8171407 on a non-AVX2 host gave 6 false failures.

Claude runs inside an SGE job on a compute node (`$JOB_ID` set); the login-node limits below
apply to work started from a login shell.

**Full test suite for a PR (2026-11-01):** run it through `tools/scc_ci_status.py submit`, which posts the `scc-tests` status on the commit.

The rules below are the original workspace text, moved verbatim.
