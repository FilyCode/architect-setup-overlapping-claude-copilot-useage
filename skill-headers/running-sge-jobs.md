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

Claude runs inside an SGE job on a compute node (`$JOB_ID` set); the login-node limits below
apply to work started from a login shell.

The rules below are the original workspace text, moved verbatim.
