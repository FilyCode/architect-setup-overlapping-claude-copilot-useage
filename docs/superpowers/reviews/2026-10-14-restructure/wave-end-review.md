# Wave-end review, 2026-10-14 setup restructure (Task 20)

Seats: critic-reviewer, alignment-officer, docs-sync, domain-reviewer (agent-harness engineer
role), anomaly-hunter, pragmatism-officer (last). Not run: inventory-auditor (the plan roster
omitted it; no prior inventory findings to close), lean-critic (on request only). Three seats
hit their turn limit; their findings files were the deliverable. The scratch copies were lost
with the node-local scratchpad when the job ended; this file is the record, written by the
controller from the seat outputs.

## Findings

### critic-reviewer
- F1 (Important) `context_nudge.py`: the band ratchet never reset after compaction (the session
  id survives compaction), so only the first climb past 500k was nudged. **Fixed** (c671675).
- F2 (Minor) `bash_guard.py`: lines inside a multi-line quoted argument are parsed as commands
  (false deny). 0 of 46,279 corpus commands; all 14 corpus denies are true positives. Deferred.
- F3 (Minor) the heredoc regex matches `<<<` and `$((1<<2))`; following lines are dropped
  (fail-open). Deferred.
- F4 (Minor) `cd ~` is not expanded (false deny on `cd ~ && rm -rf build`). Deferred.
- Optional: dead backslash branch in `_strip`; `export` untested; `find -delete` warns on
  scratch paths; pytest via `uv run` / `timeout` / `python3 -I -m` evades the deny.
- F5 (Important) `agents/implementer.md` mandated `stub_scan.py` at a workspace path that does
  not exist (skills are linked at user scope). **Fixed** (this wave's governance commit).
- F6 (Important) S4 grader: fails a correct answer with a lowercase placeholder (after run 2 is
  5/5 in substance) and would pass `git commit -a`, `git add -u`, a pathspec without `--`.
  No real run had a false-pass shape. Recorded in `evals/results-after.md`; grader not rewritten.
- F7 (Minor) S3 `must_not` keys on `has_signal\w*`; every run used `signal_peptide`. Recorded.
- F8 (Important) `context_budget.py` never applied ceilings to the user-scope skills.
  **Fixed** (c671675); third-party user skills excluded (graphify body 47,686 B).

### alignment-officer
- A1 Task 11 (Phase 1 measurement) never done and undisposed. Deferred until after this wave's
  fixes, so it measures the final state.
- A2 Spec §5.6 "workspace root clutter list for the owner" never produced. Done this wave
  (`root-clutter.md`).
- A3 lean-critic shipped without `Skill` / ponytail-review (agent-seat-review ruling); spec not
  amended. Spec note added.
- A4 MEMORY.md ceiling 5 KB/50 → 6,656 B/60 by executor ruling. Spec note added; owner ratifies.
- A5 S4 grader widened post hoc; S1/S7 non-discriminating; ledger pairs ambiguous. Recorded.
- A6 Task 19 had no ledger completion line. Added.

### docs-sync
- D1 `ARCHITECTURE.md` stale (old rule pointers, 6 of 14 seats with wrong models, no hooks, no
  layer table). Updated this wave.
- D2/D3 repo and workspace `CLAUDE.md` misstate where skills and agents are linked and which
  skills are explicit-only. Fixed.
- D4 `shell.md` points at a nonexistent `rtk_selftest.sh`; runbook and learnings describe rtk/scc.md
  as live; the rtk skill still describes the live hook. Fixed.
- D5 DECISION-026 lacked deny-vs-warn, investigator, the MEMORY ceiling and the user-scope move
  (U1). Fixed.
- U1 agents and skills moved to user scope with no decision entry and no script to recreate
  the links. `tools/link_user_scope.sh` added.
- M1 ~12 memory files cite retired files or rtk in present tense. Cleaned.

### domain-reviewer (agent-harness engineer)
- F1 (Major) seats have no Skill tool, so they reach only preloaded skills; the
  two-report-filtering rule (hmmsearch `--tblout` vs `--domtblout`) lived only in
  `scientific-evidence`, which `implementer` cannot load. Rule now in the shared seat Environment
  block.
- F2 (Major, executed) `omitClaudeMd` omits launch-time CLAUDE.md only: a seat's first project
  read attaches the project CLAUDE.md and path-scoped rules. The Environment block said
  otherwise; `core.md` is the one rule file that never reaches a seat. Environment block
  corrected and now carries the seat-relevant invariants.
- F3 (Major, rated Moderate) caller-owns-qsub is enforced by instruction only; bash_guard allows
  qsub from a subagent. 12 of 795 subagents ever ran qsub (11 general-purpose), 0 after the
  restructure. Deferred with trigger.
- F4 (Major) the eval cannot detect the restructure's failure mode (no seat, no implicit
  trigger, no `skills_required`). Recorded in `evals/results-after.md`.
- F5 (Moderate) reference-file pointer lines are cut mid-word; preloading seats carry under half
  of verification-patterns. Deferred to the next skill rebuild.
- F6 three-state typing is the rule most likely to be silently missed; scientific-evidence
  pointed at "this file" for it, which is now a different skill. Fixed (rule stated in place).
- Q3 compaction policy sound (nudge lands on a human turn; skills re-attach after compaction).
- Q4 controller-verified: a session started in `projects/EnzymeFinder` loads root and project
  CLAUDE.md but not `core.md`. Fixed by linking `core.md` at user scope.

### anomaly-hunter
- F1 relevant skill invoked 5/5 in S1, S2, S5, S6, S7, S8 (0 Skill calls in the before arm);
  S3/S4 pass from `core.md`; the S4 gain is the new `core.md` rule, not skills. Skill triggering
  is helped by the superpowers SessionStart hook in both arms.
- F2 timeouts (`--max-turns 8`) are a third state graded inconsistently: all three after-arm
  timeouts FAIL, one before-arm timeout PASS. The after arm spends turns loading skills.
- F3 substance regrade: S1 5/5 and 3/3 completed runs have the caller own qsub; S2 failures are a
  path-length artifact; S7's second check is vacuous.
- F4 seat first call is ≈ 12k tokens (n = 20 interactive seats; 10.9k–13.3k), not the 4,772 of
  the n = 1 two-tool probe; pre-restructure 49.6k–55.6k. DECISION-026 corrected.
- F5 the arms also differ in tools (79 → 38), MCP connectors and plugins; do not cite the eval's
  token delta.
- F6 S8 is decided by plan mode, not the rule.
- F7 general-purpose subagents invoked a skill in 1 of 419 transcripts; post-restructure
  general-purpose behaviour is not measured.
- F8 the "calls above 500k ≈ 69 % of main-session cost" figure replicates (0.67–0.68, n = 15
  sessions); no script for it is in the repo. Deferred: add one to `tools/`.

### pragmatism-officer
Retirement of the old rule files stands as "retired with a known, narrow gap"; nothing large
returns to always-loaded text. Fix now: F1, F5, F8, domain F1/F2/F6, C1, the DECISION-026 figure,
the eval-limits note, the docs drift. Defer: bash_guard edge cases, graders, qsub deny, seat core
subset, reference pointers, Task 11. Strongest objection: the eval tested the main session with
`core.md` loaded, not what seats and project-started sessions get; scan the next 10
post-restructure seat transcripts for breaks of core rules 1–4.
