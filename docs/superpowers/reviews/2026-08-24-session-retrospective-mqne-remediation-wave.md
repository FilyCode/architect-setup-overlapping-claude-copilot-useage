# Session retrospective: MqnE panel-review-remediation wave (2026-08-24)

**Purpose of this document.** This is a meta-retrospective on *how the Claude Code session itself
operated* while executing the MqnE_cofactor_finding project's panel-review-remediation SDD plan
(20 tasks, 5 groups, plus a final wave-end fix wave) — not on the science, which has its own
project-level retrospective at
`projects/MqnE_cofactor_finding/docs/superpowers/reviews/2026-08-20-retrospective-why-missed.md`.
Philipp asked for this explicitly: what went well, what went wrong, what workspace/project rules
could have prevented issues, what didn't run smoothly, what could be more efficient, and candidate
rules/additions — **written up here as proposals only**. Nothing in this document has been
implemented; a separate session is intended to review it and decide what to act on.

Where useful, findings cite exact evidence from this session (commit hashes, ledger lines, agent
behavior) rather than general impressions — treat every claim below as checkable against
`projects/MqnE_cofactor_finding/.superpowers/sdd/2026-08-20-panel-review-remediation/progress.md`
and the project's git history.

---

## 1. What went well (worth preserving, not just fixing what's broken)

1. **Self-monitoring SGE jobs instead of delegating the wait.** Once established (after an earlier
   incident — see `feedback_subagent_dispatch.md` memory — burned 1M+ tokens on subagents
   round-tripping to check `qstat`/`qacct`), this session consistently used the `Monitor` tool with
   a bash until-loop against `qacct` for every long job (Task 13's job, Task 16's ~5.3h job), then
   handed the finished result to a *resumed* implementer via `SendMessage` rather than ever letting
   a subagent itself sit in a wait loop across turns. This worked cleanly and cost near-zero
   controller tokens per wait.
2. **Independent, from-scratch re-derivation as the default review posture.** Reviewers were
   consistently instructed to re-derive numbers with their own code/queries rather than re-reading
   the implementer's report, and this repeatedly caught real things: a controller's own first
   attempt at a genus-stratified recompute was wrong until it matched the right filter methodology
   (Task 12); a reviewer independently proved a figure was stale by regenerating it from an archived
   pre-fix CSV and getting a pixel-identical match to the *old* committed figure (figure audit); a
   reviewer fetched an external GitHub reference implementation via `curl` to verify a formula
   claim rather than trusting the implementer's description of it (Task 20).
3. **The governance-file approval gate held, including under real pressure.** After one early,
   unapproved `ARCHITECTURE.md` edit (flagged transparently by the controller, not caught by
   anyone else), the controller was visibly more careful for the rest of the session — asking
   explicitly before Group 2's governance edits even after Philipp had already given fairly broad
   "keep going" instructions, and asking again before the final wave-end fix wave (which touched
   `PROJECT_STATE.md`/`ARCHITECTURE.md`) even though the session was deep into an autonomous
   "keep going" mode by then. The discipline generalized rather than being a one-time reaction.
4. **The SDD fix-loop/re-review cycle caught real issues repeatedly**, not just rubber-stamping:
   Task 16's own generated report was found to violate the very "no hardcoded literals" rule it was
   demonstrating; Task 18's retrospective had a genuine inverted-arithmetic error (±15-window
   saturation) that a second reviewer caught and a fix round corrected; Task 19's workspace-rule
   edit exceeded its approved scope in one place (dropped an "optionally" that the sign-off didn't
   authorize removing) and was caught and fixed.
5. **Wave-end multi-reviewer dispatch (critic-reviewer + alignment-officer + docs-sync in
   parallel) found real, convergent problems that no single per-task review would have caught** —
   all three independently converged on the same root cause (corrections propagate to
   `DECISIONS.md` but not to reader-facing docs) from different angles, which is a strong signal
   the finding is real rather than one reviewer's idiosyncratic take.
6. **The ledger (`progress.md`) was detailed enough to survive a full context compaction mid-wave**
   without losing track of what was done — this session was continued from a compacted summary at
   least once and picked up correctly using the ledger as the recovery map, exactly as the SDD
   skill's design intends.

## 2. What went wrong / friction points, with concrete evidence

### 2.1 `review-package`'s automatic diff range breaks under concurrent/interleaved commits

Happened at least twice this session: once earlier (Task 2's fix rounds, when an unrelated
repo-cleanup sweep landed between BASE and HEAD and blew the diff to 93MB including binary AF3
zips), and again for Task 16 (25MB, from Tasks 17/18/19/20 landing on the branch while Task 16's
SGE job ran in parallel). Both times the fix was manual: discard the auto-generated package, hand-
build a scoped diff via `git show <commit> -- <specific paths>` instead.

**Why this matters going forward:** this session ran tasks in parallel deliberately (per Philipp's
own "if independent, go parallel while waiting" instruction) specifically *because* Task 16's job
took ~5.3 hours — exactly the condition that makes other tasks land on the branch in the meantime.
Parallelizing independent work while a slow job runs is a good pattern this session validated: the
diff-packaging tool just doesn't yet expect it.

### 2.2 Reviewer subagents stopping mid-check without delivering a final verdict

Happened at least twice: Task 20's reviewer ended its turn on "Now let me check the Foldseek afdb50
citation claim and do a final sweep..." with 45 tool calls already spent and no verdict; the
wave-end critic-reviewer's first pass ended on "I'll start by reading the plan and the ledger, then
work outward to the governance docs" — a *plan to begin*, after 45 tool calls, also with no
findings delivered. Both required a full resume round-trip (`SendMessage`) to get the actual
review, each re-paying a meaningful slice of that agent's accumulated context.

This reads as a turn-budget/scope-size problem specific to large, open-ended review dispatches
(whole-plan reviews, multi-file audits) rather than a one-off fluke, since it happened on two
different large-scope reviews and never on a small, single-commit scoped review.

### 2.3 `rtk`'s output-filtering false negatives were independently rediscovered by multiple agents

This is a known gotcha (see `feedback_rtk_filter_false_negatives.md` memory), but this session it
was *independently rediscovered* by at least three different actors who each had to work around it
themselves: Task 16's implementer (a `diff` gave a false "identical," caught only because it also
ran an `md5sum`), the wave-end docs-sync agent ("direct shell `grep` against these files
intermittently returned wrong/short results under the `rtk` PreToolUse filter... I cross-checked
every load-bearing search with a plain Python line scan"), and the wave-end critic-reviewer ("`rtk`
returned a false-negative on an `ARCHITECTURE.md` script-number grep... computed programmatically
rather than by grep"). The workaround (verify negatives via hash or an alternate method) is
currently only in the *controller's* memory, not in anything a freshly-dispatched subagent
automatically inherits — so every subagent re-discovers the same trap at its own expense rather
than being warned up front.

### 2.4 A cost-saving review decision, later found to be inverted, was never revisited

Group 2 (Tasks 6-14, the governance-doc corrections) got no independent reviewer dispatch — a
deliberate controller judgment call at the time, reasoned as "these are doc corrections drawing on
Group 1's already-adversarially-reviewed data, not novel computation, so direct controller
verification is enough." Task 18's own retrospective later established that this reasoning was
*backwards* relative to what the whole remediation wave was actually about: every one of the
panel's original findings lived in exactly this doc-framing layer, not in novel computation. The
retrospective flagged this explicitly as "an open risk... inverted relative to this wave's own
cause" — and then nothing acted on that flag. The wave-end review subsequently found real
propagation defects sitting in Group 2's own output (the GNAT structural-signal contradiction, the
`SUMMARY.md:171` overclaim), which is exactly the kind of thing an independent Group-2 review might
have caught 8 tasks earlier.

The pattern worth naming: a retrospective/self-critique correctly identified a risk mid-wave, and
the session's own process had no mechanism forcing a decision on that flag (re-review now? accept
the risk explicitly? revisit at wave-end?) — it just sat in the ledger as prose until a *later*,
unrelated review incidentally confirmed it.

### 2.5 Corrections landing in `DECISIONS.md` don't reliably propagate to reader-facing docs

The single largest finding of the whole wave-end review, named directly: `DECISIONS.md` (the
one append-only file every task's brief could write to) stayed completely consistent, but
`SUMMARY.md`, `FINDINGS.md`, `PROJECT_STATE.md`, and `ARCHITECTURE.md` — the docs an actual human
reader opens — each froze at whatever a given task's own `Files:` scope happened to include, and
drifted for every task whose scope didn't happen to include them. Concretely: DEC-052 (Task 8)
never reached `FINDINGS.md`; DEC-059 (Task 17) never reached `SUMMARY.md`/`FINDINGS.md`/
`PROJECT_STATE.md`; DEC-061 (Task 16) never reached `FINDINGS.md`; `PROJECT_STATE.md` itself simply
stopped being touched after DEC-053 (2026-08-21) even though 8 more decisions landed after it.

This is the same failure shape Task 19 *just adopted a rule for* (Rule 9: "propagate the caveat
with the claim") — the wave that adopted the rule did not apply it to its own remaining tasks in
real time, only discovered the gap at the very end via a dedicated wave-end pass.

### 2.6 A whole 20-task plan executed against a citation that turned out not to exist

The plan's own opening line cited a "senior-PI adjudication" as part of its authority. Task 18's
retrospective (Task 18 of 20, i.e. near the very end) discovered — and a second, independent
reviewer confirmed via full-text repo grep — that this adjudication was dispatched in the prior
wave but never actually delivered a preserved report anywhere. Four of the plan's five headline
findings were still independently recoverable from surviving panelist text; one (the apo-cofold
artifact, which became Task 13/DEC-056) was not, and traces solely to the plan author's own
one-paragraph gloss.

The actual science was not compromised (Task 13 re-derived the apo-cofold finding from raw
coordinates independently, so it stands on its own regardless of provenance) — but this means nothing
checked the plan's own foundational citation before 17 tasks had already executed against it. Rule
7 (adopted this same wave — "one external premise check... on the target itself") addresses the
scientific-premise version of this problem but not the process-level version: verifying that a
plan's own cited prior artifacts actually exist and are retrievable, before dispatching Task 1.

### 2.7 Dispatch concurrency required repeated live correction from Philipp

The session operated under a "serial, not parallel, for now" instruction (given after an account
API-limit switch), which was then explicitly relaxed twice in this visible segment: once generally
("check on the job and if... the next tasks do not depend on task 16 then just go forward"), and
the controller had to be told this rather than proposing it — despite the situation (an ~5.3h job
with clearly independent downstream tasks queued) being visible to the controller well before
Philipp said anything. The default the session was operating under didn't self-correct to the
obviously-better strategy without a live nudge.

### 2.8 A destructive-action-without-context-check near-miss (from earlier in this session, before
this visible segment, but worth carrying into this retrospective since it's a strong concrete
example)

A subagent was told to `qdel` an unrecognized SGE job without the controller first checking
`ListAgents` for unrecognized concurrent activity — this triggered a harness security warning. The
resolution was benign (the "unrecognized" activity turned out to be the controller's own nested
sub-subagents, and the killed job was permanently stuck anyway), but the sequencing was backwards:
the check that would have resolved the ambiguity (`ListAgents`) happened *after* authorizing a
destructive action, not before.

## 3. Candidate rules / additions (proposals only — not implemented here)

Organized by where each would plausibly live. Numbering is for reference in this document only,
not a priority ranking (see the "if you only pick a few" note at the end).

### For `workspace-config/rules/subagent-dispatch.md`

**R1 — Reviewer dispatches for large/open-ended scopes should end with an explicit verdict-format
contract, and the controller should treat a reviewer's final message as complete only if it
contains that contract.** Every review dispatch already asks for "both required verdicts" —
consider making the controller-side check explicit: before accepting a review as done, confirm the
final message actually contains spec compliance AND quality verdicts; if not, resume once before
doing anything else with the (incomplete) content. This session did this correctly both times it
was needed, but only because the controller happened to notice — worth making it a named step
rather than an implicit habit.

**R2 — For a whole-plan/whole-wave review specifically (as opposed to a single-task review),
consider whether the scope should be pre-chunked** (e.g., "review Groups 1-2" and "review Groups
3-5" as two dispatches) rather than one open-ended "review everything" dispatch, given this
session's evidence that large open-ended review scopes correlate with the agent running out of
turn budget before reaching a verdict.

**R3 — `review-package`'s range-diff should have a size/safety check**, or the skill's own
guidance should tell the controller to expect and pre-empt this: when a wave is known to run tasks
in parallel (e.g., while a long job runs), warn that BASE..HEAD will likely include other tasks'
commits, and default to a path-scoped `git show <commit> -- <paths>` for that task's review package
rather than the full range diff. (This is a `review-package` script/skill-level fix, not a
subagent-dispatch.md-level one, but recorded here since it's the same root cause as R2's context.)

**R4 — When a cost-saving review-scope decision (e.g., "skip independent review for this
task/group, direct verification is enough") is later found by ANY subsequent review to have been
wrong or inverted, that finding should force an explicit decision (re-review now / accept the risk
explicitly and say why / revisit at a named future point), not just get logged as an "open risk" in
a ledger that nothing then acts on.** This session's Group-2-review-skip risk sat flagged and inert
for 8+ tasks before an unrelated review incidentally confirmed the concern.

**R5 — Before a multi-task plan begins execution, verify that any prior artifact the plan cites as
its own authority (a review, an adjudication, another session's report) actually exists and is
retrievable — not after the plan is mostly done.** This is the process-level sibling of the
already-adopted Rule 7 (which is about the scientific target's own premise, not the plan
document's own citations).

### For `workspace-config/rules/verification.md`

**R6 — Bake the `rtk`-false-negative workaround directly into the file, not just into memory.**
Something like: "This workspace's `rtk` PreToolUse filter is known to produce false negatives on
`diff`/`grep` output (see `.claude/rules` on `rtk` and the memory file on this). Before reporting a
negative result from a `diff`, `grep`, or similar filtered-output command as evidence something is
unchanged/absent, confirm it via an independent method (e.g. `md5sum`, a direct Python re-read, or
re-running without relying on the filtered stdout) — this session had at least three different
subagents independently rediscover this gotcha at their own expense." Currently this lives only in
the controller's cross-session memory, which a freshly-dispatched subagent does not inherit.

### For `workspace-config/rules/scc.md` or `subagent-dispatch.md` (destructive-action ordering)

**R7 — Before authorizing any destructive/kill action on unrecognized system state (an unfamiliar
job, process, or agent), check for unrecognized concurrent activity (`ListAgents`, `qstat -u`,
etc.) FIRST, not after.** This session had exactly one incident of this ordering being backwards; it
resolved benignly, but the rule closing the gap is cheap and the failure mode (killing someone
else's real work) is not automatically benign in general.

### Possibly a new, smaller rule file or an addition to CLAUDE.md's project-level conventions
(needs a decision on where — see open question below)

**R8 — For any SDD-plan-driven remediation wave, designate which governance docs are the
"claim's other homes" up front (a short table: this project's status docs and what each is for),
and require every task whose brief corrects/retracts/reframes a claim to grep that table for the
claim's other locations as a completion step — not defer it to a wave-end sweep.** This is really
Rule 9 (already adopted in `verification.md` this same session) operationalized as a *per-task*
checklist item rather than a wave-end catch-all. The wave-end review found this was the single
largest class of defect in the whole wave; a per-task version of the same rule might have caught
each instance at the point of creation instead of 8 tasks later.

## 4. Efficiency observations (not necessarily rules — flagging for judgment, not proposing as-is)

- **Token cost per reviewer dispatch was high across this wave** — several ran 80-220k tokens
  (Task 16's implementer: 270k+; Task 18's fix round: 216k). Much of this is inherent to the
  "re-derive everything from scratch" review posture that caught real errors (section 1, item 2) —
  there is a real tension between rigor and cost here, not a clean fix. Worth a conversation (not
  a rule) about whether some review tiers could use a cheaper first-pass gate (e.g., a quick
  plausibility check) before committing to a full from-scratch re-derivation, reserving the
  expensive version for load-bearing/high-stakes claims specifically.
- **The `.superpowers/sdd/<plan>/progress.md` ledger is gitignored by design** (a deliberate,
  documented choice — local working record, not meant to be a permanent artifact) but this means
  the *only* record that "this plan is 100% done" lives somewhere no one but the controller (and
  someone who thinks to check `.superpowers/sdd/`) will ever see. Section 2.5's `git log` message
  saying "closes all 20 tasks" existing only in git history, not in any doc a reader opens, is the
  same shape of problem as section 2.5 itself, one level up (the plan's own completion status is a
  "claim" that also needs a "home" a reader would actually check).

## 5. If only a few of these get picked up

If bandwidth is limited, the two with the clearest concrete evidence of repeated, costly friction
this session are **R6 (bake the rtk workaround into verification.md so subagents don't each
rediscover it)** and **R8/R4 together (force a decision when a flagged risk or a "claim's other
homes" gap is found, rather than letting it sit inert in a ledger)** — both are cheap to write and
both recurred multiple times with real cost in this session specifically, not just in principle.
