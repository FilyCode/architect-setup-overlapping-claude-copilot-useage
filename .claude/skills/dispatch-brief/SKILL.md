---
name: dispatch-brief
description: Builds the brief for an implementer or review seat in this workspace, on top of superpowers subagent-driven-development's templates — verified claims or UNVERIFIED labels, file ownership, environment block, job-spec handoff, and the review template (findings file first, objection slot). Use when dispatching an implementer or a review seat. Which seats run at wave end: wave-review; plan review: plan-critique.
---

# Dispatch brief

Every brief carries: verified claims (or `UNVERIFIED — check before relying on it`), the files
the agent owns and the ones it must not touch, the environment block from the agent file, the
job-spec handoff (the agent never waits on SGE), and the closing line *"report anything in
this brief that you found to be wrong."* Review briefs add the review-dispatch template below:
findings file created as the first action (in the findings dir, never the scratchpad), ranked areas with a drop order, HEAD/status checked
at start and end, the minor-triage question, and the unenumerated-objection slot.

**Which seat.** Code tasks, SDD tasks included, go to `implementer` (`model: opus` for
cross-module or contract changes, or a retry); ad hoc questions to
`investigator`; "where is X" to Explore with `model: haiku`. Never general-purpose. The
implementer runs only its own tests and the linter, and stops instead of asking: this
overrides the SDD template. Name the project: seats omit CLAUDE.md.

**Turn budget, first line of every implementer brief:** *"Commit your finished work and write
your report by turn 40 of 60; leave the rest as a listed remainder."* W4d hit the 60-turn cap
12 times, each leaving uncommitted work and no report (retro R-20261019-2, third proposal;
owner-approved 2026-10-19).

The rules below are the original workspace text, moved verbatim; incident detail explains why
each exists. The index of where every old rule went is
`architect-setup-overlapping-claude-copilot-useage/docs/history/rule-index.md`.

## Reference files (read the one you need)

- See [reference/part-2.md](reference/part-2.md) — "The brief is wrong" is a first-class finding.** A retrospec; Concurrent dispatches need declared file ownership; Model and effort tiering for any subagent dispatch; Every dispatch carries the environment-invariants block; **Name the repo's own test-environment traps**: autouse fixt; Generate a task's brief at dispatch time, not up front; The review-dispatch template — because recall is the failur
- See [reference/part-3.md](reference/part-3.md) — Fifteenth: `cp` after a `--write` is a fifth shared-worktree; Twelfth item, and it belongs with the contradiction slot: sa

Old file names in the moved text are retired: `subagent-dispatch.md` is now the skills
`dispatch-brief`, `wave-review` and `plan-critique`; `verification.md` is `verification-patterns`
and `scientific-evidence`; `scc.md` is `running-sge-jobs`.

<!-- BEGIN MOVED TEXT (verbatim; do not edit — source: docs/history/rules-2026-10-14) -->
<!-- from subagent-dispatch.md:3 -->
## Never dispatch "wait and report" as a subagent's task

A dispatched subagent's context is expensive to reload — every "still waiting, check
again" round-trip re-pays its full accumulated history. A real incident burned 1M+ tokens
this way: an implementer subagent was told to wait for an SGE job and report back, and
polled `qstat`/`qacct` across ~4 separate round-trips at ~230k tokens each.

Do not dispatch a subagent whose task is, or includes as a multi-turn loop, "wait for
job/agent X to finish, then report." Instead:

<!-- from subagent-dispatch.md:13 -->
- **A subagent that submits an SGE job does not wait for it.** It submits, reports the job
  id and what artifact it expects, and stops. The caller waits (one backgrounded loop, per
  `scc.md`) and resumes the subagent with the result. Observed 2026-08-29: four subagents in
  one session each ended their turn mid-wait anyway — one after 350k tokens and 171 tool
  calls, another after 555k — and the caller had to check the job regardless. The
  backgrounded-loop bullet below was written for exactly this case and did not hold, because
  **a loop inside a subagent still ends when that subagent's turn ends.** Making the handoff
  explicit costs one message; leaving it implicit costs a stalled agent *plus* the check.
<!-- from subagent-dispatch.md:21 -->
- If a *non-SGE* wait genuinely must happen inside a subagent as one internal step, it must
  do so inside a single `Bash(run_in_background=true)` shell-level loop — never repeated
  foreground status-check calls across turns. Note that `scc.md`'s "Waiting on a job without
  burning tokens" is **entirely SGE-specific** (`qstat`/`qacct`, `Eqw`/`hqw` states,
  `h_rt`-derived deadlines); only its shape generalises — one backgrounded loop, a deadline,
  and no repeated foreground polling. Do not follow its `qstat` mechanics for a non-SGE wait.
<!-- from subagent-dispatch.md:27 -->
- If the wait is the *entire* reason for dispatch, don't dispatch at all — the caller
  (main session or a fork) checks directly instead; it is near-free there since it is not
  reloading a subagent's accumulated history each time, and only dispatches the real
  downstream-processing subagent once the artifact exists.
<!-- from subagent-dispatch.md:31 -->
- The same applies to waiting on another dispatched subagent/fork: never re-message or
  nudge it on a timer to ask if it is done — either it delivers a task notification on
  completion, or (for `/loop` dynamic pacing) use `ScheduleWakeup` with a delay sized to
  the actual expected duration, never a short fixed interval "just in case."

<!-- from subagent-dispatch.md:36 -->
**An instruction is not a backstop — the caller must own every `qsub`.** On 2026-09-05 two
agents stalled mid-wait at **176k and 285k tokens**, each having been told verbatim in its
brief *"submit, report the job id, and STOP — a wait loop inside a subagent dies when your
turn ends"*, with the same rule already written here and in `scc.md`. That is three written
statements of the rule and two violations in one wave. The instruction is not the problem;
relying on one is. An agent that cannot finish inside its turn does the locally reasonable
thing, exactly as the comment-instead-of-task failure below predicts.

So: **the dispatching side submits every job.** An agent that needs one writes the job spec
(the script, the resources, the artifact it expects) into its report and stops; the caller
submits, waits in one backgrounded loop, and resumes the agent with the result. Waiting then
is not expressible rather than merely forbidden. Cost of the old way, measured: two stalled
agents, two resume cycles, and one dirty tree that raced a suite run.

<!-- from subagent-dispatch.md:50 -->
## A follow-up note is a task, not a comment

When an agent finds that the fix belongs in a file it does not own, that finding becomes a
<!-- from subagent-dispatch.md:53 -->
**dispatched task with declared ownership in the same wave**. It does not become a comment.

The evidence is uncomfortable. In one wave `pipeline/stages.py` gained **94 lines: 81 comment,
1 blank, 12 code** — and two of the twelve were `_confidence_config_snapshot = None` in
branches differing only by the comment above them. The three-state distinction the task existed
to create lived **in the prose and not in the program**. A 55-line comment stated the defect,
named the fix, named the parameter to add, and cited the rule it violated; it was a better bug
report than most bug reports, **and that is precisely why it survived four agents and a
review** — a defect documented that thoroughly is nearly indistinguishable from a defect fixed.

The reviewer's diagnosis, adopted here: one-file-per-agent ownership prevents index collisions
and *systematically manufactures unowned seams*. The next agent reads the comment as context
rather than as an open work item.

**Corollary: a chain of N tasks over N files needs an N+1st whose only job is to `command grep`
for who actually *calls* the new thing.** A four-task chain built a manifest field, wired two
call sites, added a typed enum — and nobody passed the value. Its own test passed the argument
directly and stayed green.

<!-- from subagent-dispatch.md:91 -->
## Every relayed figure carries its column, not only its n

The rule that a stratified figure carries its `n` is necessary and **not sufficient**. Two
agents measured the same wire on the same corpus and reported **1,577 (10.79%)** and
<!-- from subagent-dispatch.md:95 -->
**1,459 (9.98%)** — both correct, on `top_hit_identity` and `identity_to_donor` respectively.
Separately, two artifacts disagreed on 87 rows because one `fuse()` call silently omitted a
signal, and each was quoted as "the b10 corpus".

An `n` without the column it was measured on is how **one number acquires two
independent-looking sources**. State the artifact, the column, and the arm.

<!-- from subagent-dispatch.md:102 -->
## A dispatch's factual claims become code

<!-- from subagent-dispatch.md:104 -->
**A figure relayed from a SUBAGENT'S REPORT is UNVERIFIED, exactly like a figure from a plan.**
This section's rule was being read as binding the controller's own assertions only. It is not.
W2 (2026-09-21) produced **six wrong citations in one wave, every one the controller's, none
self-caught**: three relayed from a subagent's report into a brief without re-derivation, two
from the controller's own grep where a parser was needed, and one — the worst — a SHA
attributed to the wrong action **and pre-labelled** *"if these are identical that is a
copy-paste defect"*, which would have sent a reviewer to file a Critical against correct code.
A relayed figure FEELS verified because somebody measured it. It is not, because the person
putting it in front of an implementer did not.

<!-- from subagent-dispatch.md:114 -->
**A relayed figure carrying a DEFECT HYPOTHESIS is the highest-risk form.** Re-derive it before
writing it, never after: the hypothesis is what makes it actionable, so a wrong one is acted on.

**The stop rule, one sentence, and the only thing that caught an error before publication in
that wave.** When a brief carries a figure the author has not re-derived with a parser, or that
a prior report disputes, end that item with: *"if your measurement disagrees with mine, stop and
report — do not reconcile toward mine."* The implementer that received it resolved every
indirection across 71 shell scripts, found the controller's number inverted, and **wrote
nothing**. The other five errors were all caught after the fact.

<!-- from subagent-dispatch.md:124 -->
**Mechanical backstop: `scripts/check_citations.py`** (EnzymeFinder) preflights a brief, plan or
report — `path:line` citations (printing the cited line, because existence is not correctness),
paths, arithmetic including prose decompositions, `owner/repo@sha` pins, and `--flag`
attribution. It cannot verify a **count**; two of the six were counts, and that is what the stop
rule is for. Validated in both directions: it catches a verbatim reconstruction of all six, and
reports 3 findings across the 9 documents that wave produced.

A subagent cannot tell which of the caller's assertions were verified. It will faithfully
write a wrong count, file list or dependency claim into the repo and into prose. On
2026-08-24 three of the caller's unchecked claims reached commits this way; one ("stage 7c
depends only on stage 1 and stage 7a") became the final review's only Critical finding.

Every factual claim in a dispatch is either verified before sending, or explicitly labelled
`UNVERIFIED — check this before relying on it`. The high-risk classes are counts ("hardcoded
in five files"), enumerations of sites to change, and dependency claims. Verifying costs one
grep; not verifying costs a review round and a commit that has to be undone.

The same applies in reverse: when a subagent challenges one of your claims, check the artifact
before overruling it. On the same day a subagent correctly disputed a stale-exemption claim and
the caller's doubt was the thing that was wrong.

<!-- from subagent-dispatch.md:145 -->
**Every stratified or conditional figure carries its n, in the brief and in the finding.** A
rate without a denominator propagates and cannot be checked by the agent receiving it. This
failed **three times in one wave** on 2026-09-01 — twice *after* the same correction had already
been made and committed. `0.0717` travelled through a plan, a task brief and a backlog entry
before anyone established it was 16/223 with a 48-row comparator.

<!-- from subagent-dispatch.md:151 -->
**Prefer a short brief of verified claims to a long brief of relayed ones.** In that same wave,
<!-- from subagent-dispatch.md:152 -->
**eleven of twelve implementers found at least one factual error in the controller's brief**.
The single agent that found none had the shortest brief: entirely verified against source
beforehand, naming one specific prior error rather than restating a dozen measurements.
Relaying a reviewer's number without checking it makes it the repo's number — the classes that
failed most were figures without their n, line-number citations (which drift as a wave adds
lines), and *mechanism* descriptions, where being right that something failed does not make you
right about why.

<!-- from subagent-dispatch.md:160 -->
**Contradiction slot — every dispatch, not just reviews.** Reviewers get an
unenumerated-objection slot (see the wave-end section below); implementers had no equivalent,
and they are the ones who read a brief closely enough to catch it being wrong. End every
implementer dispatch with: *"report anything in this brief that you found to be wrong."* On
2026-08-29 that slot caught five false claims in one session before any reached the repo: a
benchmark's CLI flags (the run *did* pass `--annotation-tools diamond`; the real mechanism was
no-op degradation), an over-broad "cannot reach the service" claim that was true of only one of
two code paths, an accession asserted to be RefSeq that was EMBL/GenBank, a "permanently
dormant" contradiction that dissolved once commit dates were checked against manifest dates,
and a corpus size understated by half. Each would otherwise have been written in verbatim. The
verify-or-label rule above is the primary defence; this is the backstop for when it slips, and
it costs one sentence.

<!-- from subagent-dispatch.md:173 -->
**Reviewers write findings down as they confirm them, not at the end.** A wave-end
`critic-reviewer` on 2026-08-29 burned 162,646 tokens over 49 tool calls and returned a single
sentence, because it was exploring five equally-weighted areas before composing one report, and
hit its turn limit with everything still in its head. On the resume it was told to append each
finding to a file the moment it was confirmed, to rank the areas, and to drop the bottom two if
turns ran short — it then produced one Blocking and three lesser findings from the same budget.
So: give reviewers a findings file, rank what you want checked, say explicitly what to drop, and
prefer instructing them to *execute* a small script over reading more source. A short report
with three confirmed findings beats an exhaustive one that never lands.

