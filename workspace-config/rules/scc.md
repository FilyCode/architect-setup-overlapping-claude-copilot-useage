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

## Waiting on a job without burning tokens

Watch a submitted job with a single backgrounded shell loop, never repeated foreground
`qstat`/`qacct` calls or "check again" round-trips — each round-trip re-pays the full
accumulated context (see `subagent-dispatch.md` for the incident that motivates this).

- Wrap the wait in one `Bash(run_in_background=true)` call, with a bail-out: `qstat -j
  <jobid>` keeps returning exit code 0 indefinitely for a job stuck in `hqw` (held) or
  `Eqw` (error, will never start — see `.claude/agents/scc-monitor.md`), so a bare
  `until ! qstat -j <jobid> ...` loop can spin forever. Give it a deadline derived from
  the job's `h_rt` (see "Job defaults" above; a real 12h job here has been observed to
  queue 10-15 min before starting, so pad well past `h_rt` alone), e.g.:
  `deadline=$(( $(date +%s) + <h_rt_seconds> + 3600 )); while qstat -j <jobid> >/dev/null 2>&1; do [ $(date +%s) -ge $deadline ] && { echo "TIMEOUT: job <jobid> still in the queue system after deadline — check state with qstat -u phitro"; break; }; sleep 45; done`
- A 30-60s sleep interval is fine and costs zero tokens per iteration — only the final
  notification costs anything, so there is no reason to stretch it toward the job's
  runtime (that only delays the notification for no savings). Stretch past ~60s only on
  multi-hour jobs, and only to avoid hammering the qmaster with `qstat` calls.
- Neither the loop exiting nor a `qacct` `exit_status 0` alone proves success — always
  check the output artifact exists on disk once the loop exits (see "Verifying a job"
  above). `qacct` can also lag briefly right after a job leaves the queue ("job id not
  found") — retry once after a few seconds before treating that as a real failure.
- Never dispatch a subagent whose task is "wait for job X and report back" — see
  `subagent-dispatch.md`. Do the wait yourself (or in the dispatching session/fork); it is
  near-free there and expensive to re-pay inside a subagent's reloaded context.
- **`qstat -j <jobid>` returns non-zero transiently** under qmaster load, so `while qstat -j
  ... ; do` can exit while the job is still running. This is the opposite failure to the
  `hqw`/`Eqw` one above and bit a real wait loop on 2026-08-24: the loop exited with the job
  in state `r` at 2 of 20 tasks, and only an artifact count caught it. Wait on the LISTING
  form instead, and require several consecutive absences before declaring a job finished:
  `absent=0; while [ $absent -lt 3 ]; do qstat -u phitro 2>/dev/null | grep -q "^ *<jobid> " && absent=0 || absent=$((absent+1)); sleep 45; done`
- `scc-monitor` is for diagnosing *why* a job failed or a reported success can't be
  trusted — not a target for repeated "is it done yet" checks.

## Reading a job log

**SGE appends to `-o` logs, it does not truncate.** A log path reused across runs accumulates
them, oldest first. On 2026-08-24 one sweep log held four runs, three of them pre-fix showing
`significant=0`, and reading its head twice nearly produced a false failure report. Always:

- check the log's mtime against the job's `end_time` from `qacct` before believing it;
- anchor on the LAST `=== ... started:` line, not the head of the file;
- remember a differently-named job writes a different log — a stale log at the path you
  expected is not evidence the new job failed.

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
