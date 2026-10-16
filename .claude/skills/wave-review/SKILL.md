---
name: wave-review
description: Runs the wave-end review in this workspace — which seats to dispatch for this kind of wave, in batches under the concurrency cap, with pragmatism triage last and a ran/not-ran list. Use at the end of a multi-task wave or when asked for /wave-review. For a quick ad hoc review of one change use superpowers requesting-code-review or /code-review instead. Seat briefs come from dispatch-brief.
effort: high
---

# Wave-end review

Roster by wave type: critic-reviewer always; alignment-officer and docs-sync when a plan or
phase doc exists; domain-reviewer for domain work; anomaly-hunter when the wave produced a new
measurement (skip on pure bug-fix or doc-only waves); inventory-auditor when the wave added
capability; lean-critic, always, on the wave's diff (it preloads ponytail); pragmatism-officer last, once findings exist; then
retro-officer, always, as the final step: give it the ledger path, the findings (files or
reports), the commit range per repo and the main transcript path
(`~/.claude/projects/<project>/<session id>.jsonl`). It appends one entry to
`docs/retros/retro-log.md` in the config repo.

Dispatch in batches under the concurrency cap (2 on the smaller account, 3 on the larger). A
spawn refused at the cap is not queued: re-dispatch it when a slot frees. The close lists every
seat as ran or not-ran, with the reason. Findings files go in the findings dir (`.superpowers/findings/<date>/` in the config repo,
persistent), never the scratchpad, which dies with the job. A seat is not "ran" until its
findings file is non-empty (`test -s`); if a seat put findings only in its message, write them
into its file before closing. When the wave's evidence is only self-consistency, say
so in the close and keep a standing row for one held-out evaluation.

The rules below are the original workspace text, moved verbatim.

Old file names in the moved text are retired: `subagent-dispatch.md` is now the skills
`dispatch-brief`, `wave-review` and `plan-critique`; `verification.md` is `verification-patterns`
and `scientific-evidence`; `scc.md` is `running-sge-jobs`.

<!-- BEGIN MOVED TEXT (verbatim; do not edit — source: docs/history/rules-2026-10-14) -->
<!-- from subagent-dispatch.md:213 -->
## Wave-end review (additive — the generic reviewer stays available)

At the end of a wave, before finishing a branch, or after a big task (or several
smaller ones have accumulated): dispatch `critic-reviewer` (correctness/quality/tests/
efficiency/simplicity), and, when a plan or phase doc exists to check against,
`alignment-officer` (completeness/scope conformance) and `docs-sync` (governance-doc
drift). Run these in parallel — none depends on another's output. This does not replace
superpowers' `requesting-code-review` for smaller, ad hoc checks; that stays available.

<!-- from subagent-dispatch.md:222 -->
**Self-verification is not independent review.** Don't skip dispatching a reviewer for a task
just because it "looks like" a governance-doc correction rather than novel computation. The same
MqnE retrospective above found this reasoning used to close a whole task group without any
independent review — and every one of that project's biggest missed findings lived in the
doc-framing layer, not the computation layer, i.e. exactly the layer that rationale skipped.

`critic-reviewer`'s own Output section (item 5) backs this up: on an APPROVED verdict from
a wave-end-shaped review, it closes with a one-line reminder to consider dispatching
docs-sync now, since it already knows its own verdict — no separate mechanism needed to
reconstruct that. Ignore the reminder when docs-sync already ran that wave, or the review
was one of the smaller ad hoc `requesting-code-review` checks this section explicitly
keeps separate from wave-end review — a docs-sync suggestion doesn't apply there. (An
earlier `SubagentStop`-hook version of this nudge was built, tested, and reverted the same
day — see DECISION-024 for what it got wrong and how that was verified.)

<!-- from subagent-dispatch.md:237 -->
**Minor-triage content test.** Before filing a review finding as Minor, answer in writing: *if
this finding is correct, does any currently-stated conclusion change?* If yes, it is not a Minor,
no matter how small the suggested edit looks — a finding phrased as a wording complaint ("stated
unhedged," "unacknowledged") can still be a category error underneath, and severity
misclassification of a real finding is how defects survive multiple review rounds undetected.
Optional, cheap mechanical backstop: re-read the parked Minor list again at every wave's end, not
only the wave it was filed in — Minors otherwise never get revisited.

**A review dispatch issued while implementers are still running must name the files that are
currently uncommitted-modified**, and tell the reviewer to check `git status` before filing any
documentation-drift finding. On 2026-09-01 a cross-wave auditor reported that without that
check it *"would have filed F5-scale findings against all three"* of `ARCHITECTURE.md`,
`CAPABILITY_STATUS.md` and `KNOWN_LIMITATIONS.md` — files a concurrent agent had already
corrected. A reviewer auditing a tree that is mid-edit files findings against text that is
already right, and the controller then has to disprove its own reviewer.

<!-- from subagent-dispatch.md:266 -->
**Unenumerated-objection slot.** Every review dispatch — wave-end or ad hoc — ends with: *"list
the strongest objection to this work that I did not ask you about."* Reviewers already do this
occasionally unprompted; the slot converts it into routine rather than luck. This targets the
enumeration specifically, not tone: adding adversarial-sounding language to a dispatch is cheap and
harmless, but there is no evidence tone changes what a reviewer actually finds — enumeration does.

<!-- from subagent-dispatch.md:272 -->
**Domain-role reviewer at wave end, not only after a crisis.** Alongside critic-reviewer/
alignment-officer/docs-sync, include a reviewer in the target domain's professional role (e.g. a
biologist-role pass on a biology project) as a routine part of wave-end review, not something
convened only after an external panel or incident forces it. A correctness/completeness/drift
review is structurally unable to produce a premise-level or domain-plausibility finding — only a
domain-role pass can, and by the time a crisis convenes one, the defect has usually already shipped
for a while. **`domain-reviewer` now exists** (`.claude/agents/domain-reviewer.md`, opus/45 turns),
created 2026-09-23 after an ad hoc domain seat produced W2b-1's only Blocking finding — a hygiene
fix that silently moved a shipped tier boundary — plus five Importants that five other seats
missed. Name the professional role in the dispatch (computational enzymologist, structural
biologist, cheminformatician); the agent file carries the rest. Fold it into the
same wave, not necessarily the same parallel batch, given the account's concurrency cap
(`feedback_subagent_dispatch.md` memory: 2-3 concurrent, account-dependent).

<!-- from subagent-dispatch.md:286 -->
**Anomaly-hunter at wave end — the only seat whose job is to REOPEN things.** Alongside
critic-reviewer/alignment-officer/docs-sync/domain-role, dispatch `anomaly-hunter`
(`.claude/agents/anomaly-hunter.md`, opus/45 turns, added 2026-09-25). Every other seat is
structurally biased toward closure: critic-reviewer closes on *"the code does what it says"*,
domain-reviewer on *"this is plausible given what we know"* — and *plausible given what we know*
is exactly the instrument that buries a surprising result, because a real discovery is by
definition not plausible given what we know. This seat owns the opposite instinct.

It was created after a session in which known biology was used three times to CLOSE an anomaly
rather than open one, and the wave's own best result turned out to be a composition effect
nobody attacked because it was the answer being hoped for. Its checks, in its own file: the
instrument-floor check on every absence claim; attacking the CONFIRMING results rather than
only the surprising ones; naming the third state; following the weird number nobody commented
on; and verifying that a cited paper says what it is being used for on a matching population.
The rule it enforces is in `verification.md` ("An absence is only as good as the instrument's
headroom IN THAT STRATUM, and a textbook premise may not close an anomaly").

Skip it for pure bug-fix or doc-only waves that produced no new measurement. Do NOT skip it
because a wave's results look clean — that is the condition it exists for.

<!-- from subagent-dispatch.md:306 -->
**Inventory-auditor when a wave adds new capability.** Alongside critic-reviewer/
alignment-officer/docs-sync/domain-role, dispatch `inventory-auditor` when the wave
introduced new functions, modules or scripts — it catches duplication introduced within
the wave itself (two tasks solving the same problem without knowing about each other) and
capability the wave rebuilt instead of wiring to something that already existed. **It also
closes its own loop**: if an inventory-auditor pass at plan-writing time recommended wiring
in or extending something instead of building new, this dispatch checks whether the wave
actually did that, rather than letting the recommendation evaporate the way a plan's own
"deferred with reasons" table does when nobody re-checks it at close. Its findings feed
into the same `pragmatism-officer` triage below. Skip it for pure bug-fix or doc-only
waves that added no new capability and no prior inventory findings to close out.

<!-- from subagent-dispatch.md:318 -->
**Pragmatism-officer runs last, after findings exist.** Once critic-reviewer/alignment-officer/
docs-sync/domain-role/inventory-auditor have filed, dispatch `pragmatism-officer` to triage the wave's own
findings for proportionality — what actually needs fixing now versus what's real but low-impact
and can be documented and deferred, and what's scope creep to reject outright. It has no
authority over severity or correctness (see its own file); it runs on top of the Minor-triage
content test above, not instead of it. Skip it when the wave produced zero findings — there is
nothing to triage.

<!-- from subagent-dispatch.md:560 -->
## Run the fast gates per task, not at wave end

W14 (2026-09-06) ran the full suite once, at wave close. `ruff check src/` had been failing since
the task that introduced the file — through **three review passes that all approved it**, including
two that reproduced the implementer's evidence independently. The lint error was `F841`, twice: two
variables computed and never used. It was not style. Those variables were the column names a
`--ec-column` option was supposed to produce, and their being dead meant the option was a **complete
no-op** and that a header-bearing input produced a **6-column header over 14-column data rows** —
i.e. the wave's own delivery rule ("no existing parser broken") violated by the task that existed to
demonstrate it. Nothing else in the wave found it.

<!-- from subagent-dispatch.md:571 -->
**So a task is not done until the repo's fast gates pass on it.** Put them in the task's definition
of done and in the dispatch: the linter on changed paths, the task's own tests, and any cheap
project-specific checker. Seconds per task; it would have converted a wave-close surprise into a
first-round fix. Reserve the full suite (and `qsub`) for wave close, where it belongs.

<!-- from subagent-dispatch.md:576 -->
## A suite run needs a quiet tree, and the wave owns keeping it quiet

Two independent contaminations hit W14's wave-close suite run, and both were the controlling
session's fault:

<!-- from subagent-dispatch.md:581 -->
- **The job raced its own repository.** `#$ -cwd` runs against the LIVE tree, and a docs commit
  landed mid-run. The suite's own provenance guard caught it (`RACED: HEAD moved during the run`)
  — a guard worth having, and no substitute for not doing it.
<!-- from subagent-dispatch.md:584 -->
- **A reviewer's temporary test file was collected.** A review agent copied a test into `tests/` to
  exercise it under the repo's `conftest.py`, and the suite collected it and counted its failures.
  It cleaned up afterwards, so the tree was clean by the time anyone looked — and the run was
  already wrong.

Before submitting: assert no tracked modifications, no stray files under the test directory, and
record HEAD. Then **make no commits and run no agents until it returns.** And tell every dispatched
agent, reviewers included: **never create a file under `tests/`**, not even briefly.

<!-- from subagent-dispatch.md:620 -->
## One integration seat, mid-wave

Per-task reviews are path-scoped by necessity under concurrency, and path-scoped review is
structurally incapable of seeing across tasks. Both W14 defects that survived to wave close lived in
that gap: a lint failure that pointed at a cross-cutting output-format bug, and a ratchet drift
question that belonged to no task. Add one seat, once, around the midpoint, whose only scope is what
no task owns: the gates as a whole, the tree as a whole, and any file every task read and none owned.

No dedicated integration-seat agent exists — same shape as the domain-role reviewer above: dispatch
`critic-reviewer` (or a generic agent, if `critic-reviewer`'s own turn/model budget doesn't fit) with
an explicit integration-scoped prompt naming exactly what no task owns, rather than its usual
single-file brief.

<!-- from subagent-dispatch.md:648 -->
## A pragmatism seat is the lever for fewer rounds

W14 recorded 24 rulings across 17 fix rounds, and several expanded scope — at least one was fixed
against the controller's own minor-triage test, on the argument that a follow-up note becomes a
comment and evaporates. That argument is sound and it is also how a wave grows. `pragmatism-officer`
exists for exactly this: it does not change severity or correctness verdicts, it separates what must
be fixed now from what can be documented and deferred. Dispatch it once a wave's findings exist,
before the fixes are commissioned — not after.

