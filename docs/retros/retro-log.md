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

## 2026-10-15 ec523-refiner-v1
Scope: EC523 refiner-v1, repo DL_group-project_image-road-segementation, f17eb3c..07be087 on feat/refiner-v1: 26 commits, 2026-10-15 11:42 to 14:33 (ledger progress.md, 154 lines: 12 tasks, rulings R1-R12, final review + 1 fix wave); wave-end seats in findings/2026-10-15/ec523-refiner-v1/.
Cost (wave_stats.py, main transcript, --since 2026-10-14T00:00Z; same output with --since 2026-10-15T12:00Z): main 229 calls, 73.6M summed context, max 545k, 0 compactions, 12.2% of context above 500k. Subagents (summed context): critic-reviewer 18 = 9.5M, implementer 14 = 6.2M, domain 1 = 4.2M, anomaly 1 = 3.8M, inventory 2 = 1.6M, alignment 0.9M, docs-sync 0.7M, pragmatism 0.7M, lean 0.4M. turn_limit_hits: 2 agent ids (domain, anomaly; the seats were resumed, so one row each undercounts their true cost).

### Worked
- Per-task review plus scoped re-review caught real defects before merge: Task 5 "no head saved until end of 3 h job" (ledger l.81), Task 9 resume test that did not fail with the branch disabled (l.100-101: fixed, "fails when resume branch disabled"), Task 10 mutants red (l.113). 4 fix rounds over 12 tasks, none past round 2.
- Ledger rulings with "cost if wrong" (R1-R12) kept deviations visible; R4/R11 flagged scope and the course AI-policy split to the owner instead of the executor deciding.
- The H0 job (8135175) was the first real measurement; the ledger recorded it with run.json and git hash (l.135: dev_A 0.4646, gate >= 0.44, "saturated" logits 12-16). That number is what let domain M1 and anomaly A8 be checked.
- Wave-end domain and anomaly seats found what 12 task reviews and the opus final review (APPROVED, no Critical) did not: D4 (A(4)-A(1) CI > 0 is expected by construction; pre-registration invalid) and A8 (167/404 = 41.3% of road-bearing dev-rural tiles with zero predicted road px). Both were still fixable because no Task 11 experiment had run.
- Findings files written first: both turn-limited seats left durable files and could be resumed (R-20261015-1 from the first entry held).

### Did not work
- Science-level review came last. H0 existed by the time Task 5 closed (ledger l.135), yet domain and anomaly first ran after all 12 tasks and the final review. Findings D4 and A8 would have changed Tasks 9-11 (loss, cap, control arm); the code built on the unexamined framing is now owner-decision material (cap option D4b, pre-registration). Cost: the rework risk, plus 8.0M tokens in two seats at the very end. The plan gate had 3 seats + pragmatism on 2026-10-14 (l.4) but no data seat; no measurement existed then.
- A brief phrase "ran in the preflight" meant a scratch-copy CPU run; implementers read it as "files exist" (twice, per controller). Ledger l.4/21/26 mixes "preflighted", "not preflighted on CPU" with no statement of where the files live. Same class as R-20261015-9 (claim about a run without artifact): recurs (see 2026-10-15 BileAcidDB entry).
- SCC resource trap not in any loaded text: `-l mem_per_core=12G` is a host filter (only 24G/core L40S nodes, 0 free GPUs); job 8132228 sat 70 min in qw before anyone looked (l.114); cost one fix round (Task 5 round 2) and a resubmit, and it blocked Task 10's GPU job (l.118 "pending H0").
- Two wave-end seats hit the turn limit again (domain, anomaly) after the first entry's R-20261015-2 (budget in brief) was left open to accumulate: recurs (see 2026-10-15 restructure entry, 3 hits; BileAcidDB entry, 2). Third wave in a row.
- Process hygiene: an implementer amended a commit after the controller had committed in between (no damage; the final fix wave also ended with "controller ran full suite after amend"); concurrency cap was 2, not the 3 the controller assumed (controller report; not checked in the ledger).

### Proposals
- [ ] R-20261015-11 skill-headers/wave-review.md (and sdd/subagent-driven-development ledger template): dispatch a domain + anomaly seat on the first real measurement (H0, or the first run whose output a later task consumes), as a mid-wave gate before the next task that depends on it; wave-end keeps only a delta pass — evidence: D4/A8 found only after 12 tasks and a passing final review, H0 available at Task 5 (l.135) — expected: science-level findings land before the code that embeds them, and wave-end seats need fewer turns.
- [ ] R-20261015-12 skill-headers/dispatch-brief.md: replace "ran in the preflight" style wording with a required line per verified claim: "verified in scratch copy <path>; files do not exist in the repo yet" or "exists at <path>@<commit>" — evidence: two implementer misreads, ledger l.4/21/26 — expected: no "files exist" assumption; fold into R-20261015-9 (same artifact-citation rule) rather than a second rule.
- [ ] R-20261015-13 skill-headers/running-sge-jobs.md: add one line: `-l mem_per_core=N` is a host filter on SCC (only the 24G/core GPU nodes match 12G), use `-pe omp` plus a lower value, and check `qstat -j <id>` scheduler info if a job is in qw > 10 min; if the skill has a submit checklist, make it a checklist item — evidence: job 8132228, 70 min qw, one fix round (l.114) — expected: no silent queue stalls.
- [ ] R-20261015-14 skill-headers/dispatch-brief.md (or tools/wave_stats.py): apply R-20261015-2 now: brief states seat turn budget and "findings file at turn 1, final message = path + count"; wave_stats names which seat ids hit the limit — evidence: 2 more turn-limit hits (this wave), 3 + 2 earlier; recurs — expected: no resumes; I do not count this as new, it is the evidence R-2 was waiting for.
- [ ] R-20261015-15 skill-headers/dispatch-brief.md: implementer brief: "never amend or rebase; add a new commit" and the controller commits only while no implementer is live on that branch — evidence: amend after interleaved controller commit; no damage here — expected: no lost commits (one wave of evidence; apply only if it recurs).
## 2026-10-15 EnzymeFinder W4c (measure what ships, change no number)
Range 1dd87ea8..6b8b9a88 (EnzymeFinder, w4c-measure): 32 commits, one impl session 2026-10-15; ledger progress.md (224 lines), 7 wave-end seat files in docs/superpowers/reports/w4c-wave-end/.

### Scope and cost
- Scope: T1-T8 (tasks 2, 3a, 3b, 4, 5a-d, 6, 7 each with fix round 1), no number moved; F4 and F5 of T3b reverted; deferred items MA-283..288 routed to W4d/W4e.
- Cost (`wave_stats.py --since 2026-10-15`, main transcript): main 308 calls, 102.5M summed context, max 567k, 0 compactions, 26.3% of calls above 500k. Subagents (summed context): implementer x11 66.7M, critic-reviewer x23 22.1M, investigator x2 7.4M, domain 3.3M, anomaly 3.4M, docs-sync 1.8M, alignment 1.3M, pragmatism 1.3M, inventory 0.4M, retro 0.02M. `turn_limit_hits`: 7 agent ids (ledger names 6 seats plus the preflight investigator).

### Worked
- Per-task scoped re-review with mutation proof: fix rounds closed with RED mutants (T3b: 5 mutants red, F4 best-state mutant fails the new test; T4, T7 likewise), and every task ledger line shows "fix round 1/5" then complete (none reached round 2 except the latch handled by revert).
- The reviewer, not the implementer, caught the env-gated module-path guard (ledger l.59: unset W4C_EXPECT_SRC printed and passed); the controller ruled it unconditional plan-wide and batched the fix, 613ed47d.
- Implementer pushed back on a controller error: it rejected the relayed p=0.059 as a cross-scoring comparison (ledger, bc341d7b), and the re-review recomputed 7 sign tests with scipy.
- Pragmatism seat turned the F5 latch (critic F-1) into "revert by removal" 9b04e33b, avoiding a third review round; latch probe went to COMPLETE donor A.
- Seat findings files were non-empty for all 7 seats despite turn limits (R-20261015-1 holds); no artifact lost.

### Did not work
- No task gate saw the T2 mypy +1: batch exit stayed 0, the count (132 -> 133) was read from logs only after T4 batch 8131976. Located by the controller by hand, fixed in T3a round (613ed47d). Cost: two tasks of drift plus a manual git-archive mypy run. Same later: a stray `src/enzymefinder/enzymefinder/` (732 files, an unset-variable `cp`) doubled mypy to 264 and was found only from the count, again by hand.
- Plan text was wrong in executable places and every one cost a round: wrong interpreter for the arch job (8133458 exit 1, statsmodels missing, empty outdir left), the env-gated guard copied into T1, T2, T3a, T3b, T4 drafts, and the brief claimed a falsy-entry mutation could move (donor, primary_ec), which it cannot (reviewer, l.59). The plan was not dry-run against the repo before dispatch.
- Controller relayed claims without artifacts: p=0.059 (cross-scoring), a "biased low" echo rate (implementer measured 0 isoform-suffixed ids in 3,684), and a user-facing summary repeating the mixed RQ-39 framing (withdrawn). Cost: one rewrite round (bc341d7b) and a user correction. Recurs (see 2026-10-15 BileAcidDB entry, R-9, and ec523 entry, R-12).
- The F4 revert cited the owner's cut line before its trigger (a third review round) was met (ledger F-A, caught by a wave-end seat); a later ledger Ruling needed owner ratification. Science-level seats ran only at wave end again (critic F-1 latch, anomaly F3/F4 landed after T3b closed), recurs (see ec523 entry, R-11).
- Seat logistics: 6-7 turn-limit hits (recurs, third entry in a row, R-20261015-2/-14 still unapplied), the 2-agent cap refused one dispatch, qmaster outage at 16:5x failed 3 final-cert qsubs (no job ids; no duplicates since checked), and seat briefs repeated two errors: no `literature/` dir (second time since 2026-09-23) and echo_rows.txt vs .tsv. Brief text was not corrected at source after the first occurrence.

### Proposals
- [ ] R-20261015-16 EnzymeFinder tests/ci (batch script that emits the ratchet report): make the batch job exit non-zero when mypy count exceeds `.mypy-baseline` or when `src/` contains a duplicate package dir (`find src -name enzymefinder -mindepth 2`), and print both in the job tail — evidence: T2 +1 (132 -> 133) passed 2 task gates; stray copy gave 264 — expected: next regression fails the task gate it was introduced in.
- [ ] R-20261015-17 skill-headers/dispatch-brief.md (plan-writing section): before dispatch the controller runs each plan job's command once with `--help` or on a one-row fixture, and greps plan test drafts for `os.environ.get` guards; one line, replaces nothing — evidence: wrong interpreter (8133458), env-gated guard in 5 drafts, unmovable mutation in brief — expected: plan-text defects found before an implementer round.
- [ ] R-20261015-18 skill-headers/dispatch-brief.md: fold into R-20261015-9/-12 (not a new rule): a number or claim relayed into a brief or user summary carries its artifact path or is labelled UNVERIFIED; this wave adds p=0.059 and "biased low" as third instance — evidence: bc341d7b, fb949bb4 notes — expected: relays are checked at the source.
- [ ] R-20261015-19 skill-headers/dispatch-brief.md and the project seat-common.md: apply R-20261015-14 now (turn budget plus findings-at-turn-1 in the seat block), and delete the two known-wrong lines (`literature/`, echo_rows.tsv) in EnzymeFinder seat-common.md after a one-time `ls` check of every path a seat brief names — evidence: 7 hit ids; the recurring path errors — expected: no resumes; no repeated brief errors.
- [ ] R-20261015-20 skill-headers/sdd ledger template: when a ruling cites an owner rule (cut line, gate), the ruling line must state the rule's trigger and whether it is met, else write "by purpose, needs ratification" — evidence: F4 revert F-A — expected: no ruling cites a rule it has not triggered.

## 2026-10-16 Restructure check: sessions before vs after
Source: investigator, `.superpowers/findings/2026-10-16/investigator.md`. Arms: interactive main sessions with usage records only, before 10-01..10-13 (n=3) and after 10-15T12:00 (n=4, all EnzymeFinder W4c). The controller re-derived the after-arm max context, share_above_500k and turn-limit counts for ffc20793 and 9f26edd3 with `wave_stats.py`.
- **Worked:** seat first call is about 50k before (n=2-25 per type) and 12-14k after (n=3-49). Main first call is 91.8k → 62.2k (medians, n=3 vs 4). general-purpose dispatches went 37 → 0. Subagent `git commit -- <path>` went 6 → 0.
- **Did not work:** turn-limit hits went 9 (all in one session) → 16 (in three sessions), at similar call counts (1108 vs 985). The nudge fired in both sessions that crossed 500k, and they still reached 643k and 716k with 0 compactions. Plain `grep` was not displaced by `command grep`; whether any of it backed an absence claim is unknown.
- **Caveat:** whole-session token numbers rest on n=3 vs 4 with a different task mix. Only the startup numbers carry a claim.
- [ ] R-20261016-1 skill-headers/dispatch-brief.md + agent maxTurns: turn-limit hits recur (see 2026-10-15 R-2, R-14, R-19), so R-2's trigger is met. Apply the turn budget and findings-at-turn-1 now — evidence: 16 hits after, 8 and 2 re-derived — expected: zero lost seat runs.
- [ ] R-20261016-2 workspace-config/hooks/context_nudge.py: the nudge is advisory and was not acted on. Test a second, firmer band (for example 650k: "compact before the next task") — evidence: 643k/716k after the nudge, 0 compactions — expected: no session past 650k without a compaction.
- [ ] R-20261016-3 tools/measure_context.py: add `--until` and a per-session table with a nudge count, so an arm comparison needs no scratch script — evidence: investigator needed arms.py — expected: the weekly audit re-runs this in one command.
- [ ] R-20261016-4 agent "claude" (FleetView default): unslimmed, its first call is 36k vs 12k. Stop dispatching it, or slim it — evidence: 1 dispatch in ffc20793 — expected: no 36k seat starts.
