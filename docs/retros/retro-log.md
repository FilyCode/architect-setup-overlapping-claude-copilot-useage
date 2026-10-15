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

## 2026-10-15 BileAcidDB wave D + handoff session
Range 16bc42e^..c33194b (Bile_acid_database, branch source-refresh-census): 80 commits, 10-12 19:39 to 10-15 13:09, plus the 10-15 handoff session. Ledger progress.md, 7 wave-end seat files in findings/2026-10-15/.

### Scope and cost
- Scope: wave D (cited parent, origin_basis, ester flip, record_tier, judge run 1, T1c columns, label v0.3.1-A8), refresh #14, then census-failure fix, handoff, and the live-lookup gate (bcec53b, 00da90e, c33194b).
- Cost, today's main transcript only (`wave_stats.py --since 2026-10-15`): main 70 calls, 9.9M summed context, max 203k, 0 compactions. Subagents (summed context): implementer x2 8.0M, domain 6.9M, anomaly 5.7M, critic 4.1M, investigator x2 2.7M, docs-sync 1.8M, alignment 0.9M, inventory 0.4M, pragmatism 0.3M, retro 0.04M. `turn_limit_hits` lists 2 agent ids; the transcript text shows more resumes (see brief check below).

### Worked
- Seats wrote findings files first and appended, so the 7 seat files survive on disk (findings dir, R-20261015-1 of the entry above applied). Cost of the earlier node-local loss did not recur.
- Mutation testing by the critic of the gate fix: 7+ mutants each RED (m1 `if False` and m2 `get(k,0)` fail the tests), so the new tests actually bind the gate. Commits 00da90e, bcec53b.
- An investigator explaining 7,019 name changes found the root cause (reuse refused, breaker open on 14,408 rows) in one round; findings.md line 12 first called it "UNVERIFIED", bcec53b then measured it (file stamp 7.89 d passed, row provenance 8.30 d refused, 14,830 rows sent live).
- Independent expected-move sets before code (1e4e8f3 969 rows, 7e04607) gave G5 455/455 on origin moves, and T1a/T1b/T1c full-release invariance jobs (100/100) made origin changes attributable.
- Alignment seat measured G5 by hand when the g5_label_diff job had never run (460 observed, 455 matched, 5 unexpected), so the claim was not taken from the handoff.

### Did not work
- Handoff said #14 "reused the 10-07 lookups"; reuse was refused (reused 0), breaker opened, chain.ok was still written because circuit_open only warned. Previous session committed ba4d05b "chain.ok written" and a handoff (5aa0e83) unaware. Cost: 7,019 name changes, 14,228 rows lost pubchem_cid (176,575 -> 190,803 N/A), an investigator round, 3 gate commits, and a #15 that needs 8-12 h. The claim was a plan, not a reading of run output; the ledger already held the `reused: 0` block.
- Every wave D gate compares code with a re-implementation of the same predicate (G5 455/455, parent_fit sums), so none could see a wrong predicate: domain F1 found 64 of 362 ester flips are GNPS crude-synthesis library rows (name-string test "known isomers"), also pivaloyl esters, artemisinin hybrids. The only external check, the judge (kappa 0.847, n=54), sampled coarse rows only, 59 of 74,207.
- Readers were added, not consolidated: inventory counts 6 independent face/C-5 readers; anomaly A1: c3_stereo contradicts parent_class_stereo on 10,789 of 52,921 comparable C-3 rows (20.4%), 3,742 of 21,861 on exact-parent rows. Nothing compares the two columns.
- Governance docs not touched since wave B close: `grep -ci 'wave D'` = 0 in DECISIONS, PROJECT_STATE, ARCHITECTURE, CLAUDE, ROADMAP; PROJECT_STATE says A7/#13 (docs-sync S1, S2). Waves C and D absent. Recurs in kind with ledger line 376/415 (docs pass deferred to wave close).
- Seat logistics: resumes were needed for several seats (transcript has "turn limit (partial result; SendMessage ...)" 15+ times), 2-agent cap blocked one spawn, two finished agents held slots "waiting on background work" until stopped. Turn-limit hits recur (see 2026-10-15 restructure entry, R-20261015-2, left open "if hits recur": they recurred). Also another agent moved HEAD under the alignment seat (bcec53b -> 00da90e).

### Proposals
- [ ] R-20261015-6 Bile_acid_database scripts/refresh_chain.py + tests/test_chain.py: chain.ok requires `live_gate` pass on the ledger (done in 00da90e); add the same check to the handoff/commit step as a test that fails when `data/raw/refresh_runs/*/ledger.jsonl` of the HEAD release has circuit_open > 0 or reused == 0 with a reuse flag set — evidence: #14 committed ba4d05b with 22,528 degraded lookups — expected: a degraded release cannot be committed as "built" without a stated override.
- [ ] R-20261015-7 Bile_acid_database docs/plans (wave template) + tools/: one external panel per label_version: ~200 rows drawn stratified by label, including `library_candidate_structure`, esters, drug hybrids, labelled by a non-code source (literature table or blinded judge), and every wave-end gate must report agreement against it, not only code-vs-predicate — evidence: G5 455/455 passed 64 library flips, pivaloyl, artemisinin; judge covered 59 coarse rows — expected: predicate defects show as panel disagreements at the gate.
- [ ] R-20261015-8 Bile_acid_database tests/ (census): add an invariant comparing `c*_stereo` with `parent_class_stereo` per position on exact-parent rows, and a plan rule "a task that adds a reader names the reader it replaces or the test that ties it to the others" — evidence: 6 readers, 3 stereo vocabularies, 10,789 C-3 contradictions, nothing compares them — expected: contradiction count becomes a tracked number, readers stop multiplying.
- [ ] R-20261015-9 skill-headers/dispatch-brief.md: handoff and brief claims about run output must cite the artifact line (ledger block, log path) — "reused", "passed" without one is marked UNVERIFIED in the receiving brief; the controller re-derives before relaying — evidence: "reused the 10-07 lookups" relayed from handoff, false; controller corrected it only via investigator. Replaces nothing; one sentence. Alternative if rejected: leave as is, the gate in R-6 covers this instance.
- [ ] R-20261015-10 tools/wave_stats.py + skill-headers/wave-review.md: make seat dispatch for wave-end review sequential in two batches of 2 (cap is 2), have the controller stop a seat after its final message, and apply R-20261015-2 now (stated turn budget, write file at turn 1) — evidence: turn-limit resumes, 1 blocked spawn, 2 slots held; R-2 was left open "if hits recur" and they did — expected: no resumes, no held slots.

Controller brief check: (a) brief says "reuse refused per-row 8.3 d > 8.0": bcec53b shows the FILE stamp passed at 7.89 d and only row provenance (8.30 d) failed; the diff findings' "REUSE_MAX_AGE_DAYS 7.5" was marked UNVERIFIED and e3480ba's 7.5-day owner decision is not what the run applied (8.0 limit). (b) "14,408 enrich rows" is circuit_open only; degraded set is 14,830 (adds 12 error, 399 hit, 11 no_hit; domain seat). (c) "four seats hit turn limits": wave_stats lists 2 ids since 10-15; the transcript shows more resume messages; I did not reconcile n.
