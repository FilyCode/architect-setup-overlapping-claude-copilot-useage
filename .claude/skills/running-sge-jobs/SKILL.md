---
name: running-sge-jobs
description: How to submit, wait for and verify BU SCC SGE jobs for project liu-scc — resource defaults, the backgrounded wait loop with a deadline, reading appended logs, artifact checks, storage limits. Use when writing or submitting a qsub script, waiting on a job, or reading a job log. Diagnosing a failed job is scc-monitor's job.
---

# Running SGE jobs

## When to use

Writing or submitting a qsub script, waiting on a job, or reading a job log on the BU SCC
(scheduler SGE, project `liu-scc`). Diagnosing why a job failed is `scc-monitor`'s job.

## Procedure

1. Write the script from the defaults below; request the cores the job uses.
2. Submit and let `qsub` place it: do not force a queue. A subagent's qsub is denied (core.md
   rule 5): it writes the job spec and the caller submits.
3. Wait in one backgrounded loop with a deadline (below), never repeated `qstat` calls.
4. When the loop exits, check the output artifact exists on disk, read the log's last run, and
   run `tools/sge_efficiency.py job <id>`.

Claude runs inside an SGE job on a compute node (`$JOB_ID` set); the login-node limits apply
only to work started from a login shell. **Full test suite for a PR (2026-11-01):** run it
through `tools/scc_ci_status.py submit`, which posts the `scc-tests` status on the commit.

## Job defaults

- Cores: 1 non-parallel; 4 / 8 / 16 / 28 parallel (best scheduling efficiency at these);
  32/48/64 only for extreme cases. Request what the job uses (next section).
- Memory: `-l mem_per_core=8G`. Ceiling 512G; 1024G only for extreme workloads.
- Runtime: `-l h_rt` ≤12h preferred. Escalate to 24/48/72h only when justified.
- `#!/bin/bash -l` whenever the script uses `module load`.
- `-P liu-scc` when a project spec is required. Array jobs use `SGE_TASK_ID`.
- `export NCBI_EMAIL=phitro@bu.edu` before any job that hits NCBI.
- Do not submit many jobs that hit the same external API at once; stagger them or chain with
  `qsub -hold_jid`.

## Cores: request what the job uses

SGE charges every reserved core. Over 14 days our jobs reserved 9143 core-h and used 3242
(35%); the EC523 arrays held 4-8 slots and used 1.1-1.25 (2026-10-31). So:

- 1 slot unless a command in the script runs K threads; then put `# cores: <that command>` on
  the `-pe` line (`#$ -pe omp 8  # cores: diamond --threads $NSLOTS`) and pass `$NSLOTS` to it.
- Never add slots to get memory: SCC enforces memory loosely (owner, 2026-10-31).
- Before choosing K for a job that ran before: `tools/sge_efficiency.py lookup <name>` (config
  repo) shows its measured cores used. After every job, with the artifact check:
  `tools/sge_efficiency.py job <id>`; OVER-RESERVED means lower K next time, and
  `qalter -pe omp <k> <id>` fixes array tasks still queued.
- Hook `qsub_guard` enforces this on qsub/qrsh/qalter: K > 1 without a `# cores:` note is
  denied; a note contradicted by >= 2 measured runs is denied once.

## Host filters

`-l mem_per_core=N` (relop `<=`, `qconf -sc`, 2026-10-21) keeps only hosts with at least N per
core; 12G matched only the 24G/core GPU nodes and job 8132228 sat 70 min in qw: keep
mem_per_core at 8G or less. A job in qw over 10 min: read the scheduling info in
`qstat -j <id>`. CPU test and eval jobs whose wheels need AVX2 (FBGEMM, torch CPU) request
`-l avx2`: job 8171407 on a non-AVX2 host gave 6 false failures.

## Waiting on a job without burning tokens

Watch a submitted job with a single backgrounded shell loop (one
`Bash(run_in_background=true)` call), never repeated foreground `qstat`/`qacct` calls or
"check again" round-trips: each round-trip re-pays the full accumulated context. Use this form:

```bash
deadline=$(( $(date +%s) + H_RT_SECONDS + 3600 )); absent=0
while [ $absent -lt 3 ]; do
  [ $(date +%s) -ge $deadline ] && { echo "TIMEOUT: check qstat -u phitro (Eqw/hqw?)"; break; }
  qstat -u phitro 2>/dev/null | grep -q "^ *<jobid> " && absent=0 || absent=$((absent+1))
  sleep 45
done
```

Both guards are load-bearing:

- **Deadline (2026-10-14).** A job stuck in `hqw` (held) or `Eqw` (error, will never start; see
  `scc-monitor`) stays in the queue indefinitely, so a loop without a bail-out spins forever.
  Derive the deadline from the job's `h_rt` and pad well past it: a real 12h job here queued
  10-15 min before starting.
- **Listing form with 3 consecutive absences.** `qstat -j <jobid>` returns non-zero
  transiently under qmaster load, so `while qstat -j ...; do` can exit while the job is still
  running: on 2026-08-24 such a loop exited with the job in state `r` at 2 of 20 tasks, and
  only an artifact count caught it.
- A 30-60s sleep interval costs zero tokens per iteration (only the final notification costs anything),
  so do not stretch it toward the job's runtime. Stretch past ~60s only on multi-hour jobs, to
  avoid hammering the qmaster.
- Neither the loop exiting nor `qacct` `exit_status 0` proves success: check the artifact (next
  section). `qacct` can lag briefly after a job leaves the queue ("job id not found"); retry
  once after a few seconds before treating that as a failure.
- `scc-monitor` is for diagnosing *why* a job failed or a reported success can't be trusted,
  not a target for repeated "is it done yet" checks.

## Verifying a job

`qacct` `exit_status 0` does **not** prove success: a tool that catches its own errors
(network timeouts, partial batch failures) exits 0 having produced nothing. Always check that
the expected output artifact exists on disk before treating a job as successful.

## Reading a job log

**SGE appends to `-o` logs, it does not truncate.** A log path reused across runs accumulates
them, oldest first. On 2026-08-24 one sweep log held four runs, three of them pre-fix showing
`significant=0`, and reading its head twice nearly produced a false failure report. Always:

- check the log's mtime against the job's `end_time` from `qacct` before believing it;
- anchor on the LAST `=== ... started:` line, not the head of the file;
- remember a differently-named job writes a different log: a stale log at the path you
  expected is not evidence the new job failed.

## Storage

Home (`/usr3/graduate/phitro`) is capped at 10GB with a 7-day grace. Anything large (model
weights, caches, envs, node_modules, container images) belongs under
`/projectnb/liu-scc/philipp/software/<tool>/`, never in home.

Before installing a heavyweight tool, point its cache/data env var at `software/`. If it has no
override, install then move + symlink (`software/bin/scc_home_migrate.sh`).
`software/bin/scc_storage_audit.sh` reports current usage.

Gotchas: `rm` is aliased to `rm -i` and will hang with no stdin; use `\rm -f`. A
cross-filesystem `mv` of a large dir is slow and not resumable; prefer `rsync -av src/ dest/`,
which also merges correctly instead of nesting when the destination already exists.
