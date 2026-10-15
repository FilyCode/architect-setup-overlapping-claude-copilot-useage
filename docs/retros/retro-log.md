# Retro log

One entry per wave, appended by the `retro-officer` seat at the end of `wave-review`. A weekly
integration session (skill `workspace-audit`, retro step) applies, defers or rejects each open
proposal, ticks it with the outcome, and updates the line below. The `context_nudge` hook
reminds once per session when proposals are open and integration is over 7 days old.

Last integrated: 2026-10-15

Proposal lines: `- [ ] R-<date>-<n> <target file>: <change> — evidence: <…> — expected: <…>`.
Ticked when integrated: `- [x] R-… — applied <commit> | rejected: <reason> | merged into R-…`.

---

## 2026-10-15 2026-10-14/15 Claude Code setup restructure + project setup wave
- Scope: config repo 39 commits eef6a3f..d3d3e7d (20-task restructure: core.md + 7 skills, bash_guard/context_nudge hooks, seats, eval harness); 9 project repos, 25 commits since 2026-10-14 (EF 8, Bile 7, CaMES 2, EanB 2, others 1; `git log --since`).
- Cost (wave_stats.py, main transcript since 2026-10-14T00:00Z): 570 main calls, 180.7M summed context tokens, max context 595k, 2 compactions (one idle auto at preTokens 595,034); 27 subagents (general-purpose 5 = 10.1M, domain-reviewer 3 = 9.2M, anomaly-hunter 2 = 7.2M, critic 2 = 5.8M, implementer 5 = 4.0M, rest <2.7M each); 3 turn-limit hits (af1e29f5…, aad8b9db…, a1a4ea9c…).

### Worked
- RED→GREEN tests per fix caught plan-code defects before install: bash_guard corpus replay showed 196 of 209 false denies (ledger T7); state keyed per session, path-token regex, nudge re-arm (T8, Final F1) all found by tests/probes.
- Old-beside-new review and verbatim skill bodies plus a traceability checker (rule_map 185 items, 0 problems; T12/T13/T15) made the rule retirement auditable; wave-end review still found only 1 gap class (core.md not loaded in project-started sessions, C1), fixed.
- Ledger "Ruling … cost if wrong" lines made later audit possible: alignment-officer could list unratified executor rulings (A3/A4 → owner ratified MEMORY ceiling 2026-10-15).
- Controller reverted an implementer lowering the census baseline 94→88 (ledger "Project wave: EF"), census 27/27 afterwards.
- Anomaly-hunter corrected a headline figure before it propagated (seat first call ≈12k, n=20, not 4,772 from n=1; DECISION-026 fixed, F4).

### Did not work
- Seat findings lived in node-local scratchpad: 3 turn-limited wave-end seats wrote findings files first (good), then the files died with job 8090063 and were reconstructed from controller context (ledger Note 2026-10-15). Reconstruction means wave-end-review.md is second-hand. Cost: lost artifacts, controller context spent re-deriving.
- Two project-audit seats created findings files but put findings only in their final messages (files empty; project-audit.md header says so). Same failure class as above: the durable-file rule is not enforced.
- Eval grader moved after results were seen: S4 widened (T16, both arms re-graded), S8 narrowed after 3/5 false positives; critic F6/F7 and anomaly F2/F3/F6 then showed timeouts graded inconsistently, S1/S7 non-discriminating, arms differ in tools 79→38 and plugins. Eval ended as "no longer a gate" (Final ruling) — a plan task spent on an instrument that could not carry the claim.
- Three of five wave-end seats hit their turn limit (40–45 turns each) with 5–9M summed context each. domain-reviewer alone cost 9.2M tokens.
- Plan code had Important defects reaching commits before review: implementer gate path wrong (F5), ceilings skipping user-scope skills (F8), nudge never re-arming (F1), core.md linked only at workspace (C1). Retrospective Task 11 measurement never done (A1, deferred).

### Proposals
- [x] R-20261015-1 — applied 001d948 (findings dir `.superpowers/findings/<date>/`, non-empty check in wave-review) — workspace-config/seat-environment.md (and tests/test_agents.py drift check): replace "scratch is node-local" prose with a rule that a seat's findings file goes under the config repo's docs/…/reviews/<wave>/ (never scratchpad), and add a check in wave-review that every seat's findings file is non-empty before the seat is marked done — evidence: 3 files lost with job 8090063, 2 audit seats left empty files — expected: no reconstruction from controller context.
- [ ] R-20261015-2 skill-headers/dispatch-brief.md: review seats get a stated turn budget and "write findings file at turn 1, append per finding, final message = path + count"; raise review-seat max turns or cut seat count — evidence: 3 turn-limit hits of 5 wave-end seats — expected: zero turn-limit losses.
- [ ] R-20261015-3 evals/ runner (tools): freeze graders in a committed hash before the after arm runs; a later grader change must re-grade both arms and fail the gate unless the commit says so — evidence: S4 and S8 graders changed after results; F6/F2 misgrades — expected: no post-hoc widening without record.
- [x] R-20261015-4 — applied 001d948 (`share_above_500k` in wave_stats.py; raw context, not cost-weighted) — tools/ (new script from anomaly F8): save the 69 %/5.6 %/20.5 % cost-share script and run it in wave_stats.py — evidence: figure replicated (0.67–0.68, n=15) but no script exists — expected: next retro measures nudge effect instead of re-deriving.
- [ ] R-20261015-5 skill-headers/wave-review.md: add the pragmatism-officer's check "next 10 post-restructure seat transcripts for breaks of core rules 1–4" as a dated follow-up in the retro-log integration step — evidence: eval tested main session with core.md only; general-purpose invoked a skill in 1 of 419 transcripts (F7) — expected: seat compliance gets measured, not assumed.

_Controller check 2026-10-15: corrected the turn-budget figure (the eval's `--max-turns 8` had been read as the seat budget), the skill count and three target paths._

### Integration 2026-10-15
- Applied: R-20261015-1, R-20261015-4 (commit 001d948).
- Left open to accumulate: R-20261015-2 (turn budgets; one wave of evidence, raising limits costs
  tokens, R-1 already removes the loss — apply if turn-limit hits recur), R-20261015-3 (grader
  freeze; only matters if the eval is reused as a gate), R-20261015-5 (seat compliance check;
  needs the next 10 post-restructure seat transcripts).
