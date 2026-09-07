# Subagent dispatch: review gate and model/effort tiering

## Never dispatch "wait and report" as a subagent's task

A dispatched subagent's context is expensive to reload — every "still waiting, check
again" round-trip re-pays its full accumulated history. A real incident burned 1M+ tokens
this way: an implementer subagent was told to wait for an SGE job and report back, and
polled `qstat`/`qacct` across ~4 separate round-trips at ~230k tokens each.

Do not dispatch a subagent whose task is, or includes as a multi-turn loop, "wait for
job/agent X to finish, then report." Instead:

- **A subagent that submits an SGE job does not wait for it.** It submits, reports the job
  id and what artifact it expects, and stops. The caller waits (one backgrounded loop, per
  `scc.md`) and resumes the subagent with the result. Observed 2026-08-29: four subagents in
  one session each ended their turn mid-wait anyway — one after 350k tokens and 171 tool
  calls, another after 555k — and the caller had to check the job regardless. The
  backgrounded-loop bullet below was written for exactly this case and did not hold, because
  **a loop inside a subagent still ends when that subagent's turn ends.** Making the handoff
  explicit costs one message; leaving it implicit costs a stalled agent *plus* the check.
- If a *non-SGE* wait genuinely must happen inside a subagent as one internal step, it must
  do so inside a single `Bash(run_in_background=true)` shell-level loop — never repeated
  foreground status-check calls across turns. Note that `scc.md`'s "Waiting on a job without
  burning tokens" is **entirely SGE-specific** (`qstat`/`qacct`, `Eqw`/`hqw` states,
  `h_rt`-derived deadlines); only its shape generalises — one backgrounded loop, a deadline,
  and no repeated foreground polling. Do not follow its `qstat` mechanics for a non-SGE wait.
- If the wait is the *entire* reason for dispatch, don't dispatch at all — the caller
  (main session or a fork) checks directly instead; it is near-free there since it is not
  reloading a subagent's accumulated history each time, and only dispatches the real
  downstream-processing subagent once the artifact exists.
- The same applies to waiting on another dispatched subagent/fork: never re-message or
  nudge it on a timer to ask if it is done — either it delivers a task notification on
  completion, or (for `/loop` dynamic pacing) use `ScheduleWakeup` with a delay sized to
  the actual expected duration, never a short fixed interval "just in case."

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

## A follow-up note is a task, not a comment

When an agent finds that the fix belongs in a file it does not own, that finding becomes a
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

## `git stash` is a third shared-index hazard

Already recorded: a bare `git commit` sweeps another agent's **staged** files, and
`git commit -- <paths>` sweeps their **unstaged** ones. **`git stash push -- <paths>` races
too.** On 2026-09-05 a RED check's stash briefly captured a concurrent agent's uncommitted
work; it was recovered with `git stash pop` and nothing was lost, but only because the
collision was noticed.

**For a RED check under concurrency, copy the pre-fix file with `git show HEAD:<path>` into
scratch instead.** Reading a blob does not mutate shared state; stashing does.

## Every relayed figure carries its column, not only its n

The rule that a stratified figure carries its `n` is necessary and **not sufficient**. Two
agents measured the same wire on the same corpus and reported **1,577 (10.79%)** and
**1,459 (9.98%)** — both correct, on `top_hit_identity` and `identity_to_donor` respectively.
Separately, two artifacts disagreed on 87 rows because one `fuse()` call silently omitted a
signal, and each was quoted as "the b10 corpus".

An `n` without the column it was measured on is how **one number acquires two
independent-looking sources**. State the artifact, the column, and the arm.

## A dispatch's factual claims become code

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

**Every stratified or conditional figure carries its n, in the brief and in the finding.** A
rate without a denominator propagates and cannot be checked by the agent receiving it. This
failed **three times in one wave** on 2026-09-01 — twice *after* the same correction had already
been made and committed. `0.0717` travelled through a plan, a task brief and a backlog entry
before anyone established it was 16/223 with a 48-row comparator.

**Prefer a short brief of verified claims to a long brief of relayed ones.** In that same wave,
**eleven of twelve implementers found at least one factual error in the controller's brief**.
The single agent that found none had the shortest brief: entirely verified against source
beforehand, naming one specific prior error rather than restating a dozen measurements.
Relaying a reviewer's number without checking it makes it the repo's number — the classes that
failed most were figures without their n, line-number citations (which drift as a wave adds
lines), and *mechanism* descriptions, where being right that something failed does not make you
right about why.

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

**Reviewers write findings down as they confirm them, not at the end.** A wave-end
`critic-reviewer` on 2026-08-29 burned 162,646 tokens over 49 tool calls and returned a single
sentence, because it was exploring five equally-weighted areas before composing one report, and
hit its turn limit with everything still in its head. On the resume it was told to append each
finding to a file the moment it was confirmed, to rank the areas, and to drop the bottom two if
turns ran short — it then produced one Blocking and three lesser findings from the same budget.
So: give reviewers a findings file, rank what you want checked, say explicitly what to drop, and
prefer instructing them to *execute* a small script over reading more source. A short report
with three confirmed findings beats an exhaustive one that never lands.

**"The brief is wrong" is a first-class finding.** A retrospective on the MqnE_cofactor_finding
project (2026-08-24) found reviewers repeatedly and correctly identifying that a plan or brief's
*premise* — not the implementation — was wrong, then filing it as "plan-quality issue, not this
task's fault" and stopping there with no escalation, because the fix is upstream prose rather
than a code change. When a reviewer flags that the brief itself is wrong, escalate it at the
severity its content would warrant if it were an implementation bug, and route it back to
whoever owns the plan — don't let the out-of-scope label itself close it out.

## Concurrent dispatches need declared file ownership

Never dispatch two implementers that touch the same file. When several tasks queue behind one
shared file, say in each dispatch exactly which files it owns and which are off-limits because
another agent holds them.

**Every dispatch that may commit ends with: run `git show --stat` after each commit and
confirm it touched only your files.** Prescribing the form is not enough. On 2026-09-01, with
six-plus concurrent agents, **two shared-index collisions occurred in opposite directions** —
one agent ran `git commit -m "..."` without the trailing `-- <paths>` and swept another's
staged file; another's staged work was swept into a third agent's bare commit. Both agents had
read the explicit-path rule; one understood it and got the **flag order** wrong. **Both were
caught by the same thing: running `git show --stat` afterwards.** Nothing was lost either time.
Include the recovery in the dispatch, because it is not obvious under pressure:
`git reset --soft HEAD~1`, then `git reset -- <the other agent's files>`, then re-commit
path-scoped. Also tell agents to stage untracked files individually by name — `git add <dir>/`
sweeps a neighbour's new files just as effectively as a bare commit.

An agent that waited while other commits landed is working from a stale read: tell it what
changed underneath it and instruct it to re-read before editing. Also tell it which currently
failing checks are *not* its own, or it will start repairing someone else's work.

## Wave-end review (additive — the generic reviewer stays available)

At the end of a wave, before finishing a branch, or after a big task (or several
smaller ones have accumulated): dispatch `critic-reviewer` (correctness/quality/tests/
efficiency/simplicity), and, when a plan or phase doc exists to check against,
`alignment-officer` (completeness/scope conformance) and `docs-sync` (governance-doc
drift). Run these in parallel — none depends on another's output. This does not replace
superpowers' `requesting-code-review` for smaller, ad hoc checks; that stays available.

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

**Every review dispatch must state the `rtk` position.** A reviewer's job is mostly negative
checks — "unmodified", "no stale reference", "no matches", "nothing swept in" — which is exactly
the class rtk used to corrupt. Since 2026-08-25 rtk filters **only `cat`**, so this is now a
short line rather than a hazard list. Include verbatim: *"`rtk` filters only `cat` (to
`rtk read`); every other command runs raw, so grep/find/diff/git output is trustworthy. Two
exceptions: `head -N`/`tail -N` are still rewritten and under-deliver — use `head -n N` — and no
exit code from an rtk-wrapped command is evidence. If anything looks structurally odd, re-run it
with an `RTK_DISABLED=1` prefix; a pipeline is not a bypass."* Detail in `verification.md`.

Worth remembering why this line exists at all: when rtk did filter everything, one review round
found four independent holes in a six-entry exclusion list, including two escape hatches this
file had documented backwards.

**Unenumerated-objection slot.** Every review dispatch — wave-end or ad hoc — ends with: *"list
the strongest objection to this work that I did not ask you about."* Reviewers already do this
occasionally unprompted; the slot converts it into routine rather than luck. This targets the
enumeration specifically, not tone: adding adversarial-sounding language to a dispatch is cheap and
harmless, but there is no evidence tone changes what a reviewer actually finds — enumeration does.

**Domain-role reviewer at wave end, not only after a crisis.** Alongside critic-reviewer/
alignment-officer/docs-sync, include a reviewer in the target domain's professional role (e.g. a
biologist-role pass on a biology project) as a routine part of wave-end review, not something
convened only after an external panel or incident forces it. A correctness/completeness/drift
review is structurally unable to produce a premise-level or domain-plausibility finding — only a
domain-role pass can, and by the time a crisis convenes one, the defect has usually already shipped
for a while. No dedicated domain-role agent exists yet — dispatch a generic agent with an explicit
domain-role prompt and explicit `model`/`effort` per this file's tiering section. Fold it into the
same wave, not necessarily the same parallel batch, given the account's concurrency cap
(`feedback_subagent_dispatch.md` memory: 2-3 concurrent, account-dependent).

**Pragmatism-officer runs last, after findings exist.** Once critic-reviewer/alignment-officer/
docs-sync/domain-role have filed, dispatch `pragmatism-officer` to triage the wave's own
findings for proportionality — what actually needs fixing now versus what's real but low-impact
and can be documented and deferred, and what's scope creep to reject outright. It has no
authority over severity or correctness (see its own file); it runs on top of the Minor-triage
content test above, not instead of it. Skip it when the wave produced zero findings — there is
nothing to triage.

## Release/publication gate: security-specialist

Before a project goes to production or publication (a public code release, a public
API/DB launch, a paper submission with a code/data release) — not every wave, and not
routine development: dispatch `security-specialist`. Its own file carries the full
checklist and surface detection; don't duplicate that here. Applies even to pure-batch
projects with no web surface — "publication" for those means a paper + public code
release, and the universal checks (secrets, licence, CI pinning) still apply. Check
what CI already automates first (e.g. EnzymeFinder already runs `bandit`,
`detect-private-key`, `gitleaks`, CodeQL) rather than having the agent re-derive it by
hand. Complementary to the native `/security-review` skill, which is diff-scoped, not a
full-project gate.

## Brainstorming: research-scout

**Before dispatching any research task, `command grep` the gitignored workspace directories for
prior work on the same question.** `.superpowers/` holds every previous wave's ledgers, briefs
and reports, and this workspace's `grep` is a shell function that **skips gitignored paths** —
so the controller's own prior-art search silently misses them. On 2026-09-01 a calibration
literature review was dispatched that partly duplicated a **713-line, 48 KB review from three
days earlier**; the agent found it immediately with `command grep`. `verification.md` already
warns about this hazard for *reviewers' absence claims*; it binds the controller's own searches
too.

For a non-trivial design decision during `brainstorming`, dispatch `research-scout`
first (see its own description for scope). Skip it for small/obvious decisions.

**One external premise check at project start, and at any reframing.** Before building an
analysis pipeline around an assumed premise about the target itself, do one PDB/PubMed (or
domain-equivalent database) lookup directly on the target — not just on the surrounding method.
Make it a standing habit to resolve any external ID (PDB/accession/etc.) that a pipeline returns
repeatedly, rather than treating the repetition as an incidental curiosity; a project's own top
structural-search hit turning out to be the query's own already-published structure is exactly the
kind of premise error this catches cheaply.

## Plan review before implementation

After `writing-plans` produces a plan doc (architectural path only — bounded-path short
in-chat designs skip this, the dispatch cost isn't justified) and its own self-review, but
before `executing-plans`/`subagent-driven-development` starts Task 1: dispatch a
**plan-critique wave** against the plan and its spec. Same mechanics as wave-end review
above (parallel, rtk position stated verbatim, unenumerated-objection slot, minor-triage
content test) — the difference is what it targets (the plan text, not a diff) and when it
runs (before work starts, not after).

- Reuse `critic-reviewer` (plan-shaped: feasibility, missing tasks, edge cases) and a
  domain-role reviewer (same ad hoc dispatch as the wave-end section's domain-role
  paragraph) — this is the same premise-checking discipline, just moved a stage earlier so
  a bad premise is caught before it is copied into every task that inherits it.
- Scale the number of dispatches to the plan's size and complexity: **minimum 3**
  (critic-reviewer + one domain-role reviewer + one issue-specific angle, chosen from what
  the plan actually touches — security, data-integrity, concurrency, etc.), up to **~10**
  for a large or high-stakes plan — one per major task-cluster or distinct risk axis
  (correctness, domain plausibility, security, performance, data-integrity, concurrency,
  external-API/rate-limit behavior, backward-compat, test-coverage gaps, premise/instrument
  choice). Pick the count from the plan's actual content, not a fixed default. The
  account's concurrency cap still applies (2-3 concurrent, `feedback_subagent_dispatch.md`)
  — a 10-agent wave runs in batches, not literally at once.
- Tell each dispatch to verify cheap claims empirically, not just read the plan — grep that
  a referenced function/signature actually exists, run a two-line script against real data
  if the plan asserts a library or format behavior. This is what catches "a plan's own
  example code carries the bug" (`verification.md`) before it propagates into every task
  that copies it.
- Blocking/Important findings against the plan get fixed in the plan doc directly, before
  Task 1 starts — "the brief is wrong" is a first-class finding here too (see above),
  applied one stage earlier than a wave-end review would catch it.
- A reviewer may surface an unrelated pre-existing codebase defect while checking the plan.
  Report it, then judge case by case whether fixing it fits this plan — file overlap with a
  plan task is not an automatic block; a fix that belongs in the same file a task already
  touches can be folded into that task directly (still declare ownership per "Concurrent
  dispatches need declared file ownership" above so the fix and the task edit don't race).
  If it doesn't fit this plan's scope or timing, don't fix it blind — document it: what it
  is, where, and when it should be fixed (a follow-up task, a `DECISIONS.md` entry, or a
  known-issues note in the plan doc itself), so it doesn't evaporate as a chat-only mention.
- Once the plan-critique wave's findings are in, dispatch `pragmatism-officer` over them
  before deciding what actually goes into the plan rewrite — same proportionality triage as
  wave-end review, applied to plan-stage findings instead of a diff. A critique wave scaled
  up to ~10 dispatches produces a lot of adversarial output; this is what keeps one bounded
  issue from triggering five rounds of plan rewrites before Task 1 even starts.

### The Calibration block — required before the critique wave

Every architectural plan doc carries a **Calibration** section, written *before* the critique
wave dispatches. It exists because of the SSN wave (2026-08): a validation harness was built
around an expectation of what an SSN could do, ran for weeks, and could never clear its own
anchor floor — because nobody had separated *what this class of method cannot do* from *what our
implementation does badly*. A literature check afterwards showed both were present at once:
~35% identity really is the field-wide ceiling for reliable annotation transfer (Zallot 2019),
**and** our own sub-35% edge recall was 62.5% because of a DIAMOND sensitivity defect (MA-104).
Conflating them let a fixable 37.5% edge loss hide behind a real citation.

Four items, all four required:

- **Vision context** — which layer or axis of the project's north-star this serves, and at what
  scale. One layer is not the system. State what this plan is *not* responsible for, so a later
  reviewer does not indict it for failing to do something it was never meant to do.
- **Realistic target** — what this achieves when it works correctly. Not the aspiration.
- **General limits vs our limits** — every constraint named as either field-wide *with a
  citation* or ours to fix. **Anything unattributed defaults to OURS.** A field limit without a
  citation is not a field limit; it is an untested excuse, and it is the specific move that cost
  the SSN wave.
- **Standard** — the bar is *at least* current tool and literature standard, better where we can.
  Name the tool and the number being matched, not "state of the art".
- **Does the named standard already do this?** Check the tool you just named as the bar, and say
  what it already delivers of what you are proposing to build. Added 2026-08-30 because its
  absence was not hypothetical: a plan proposed partitioning an SSN by a property its own named
  comparison tool already separated — EFI-EST's existing cluster assignment put 90.7% of the
  target mode in one cluster — and neither the author nor the self-fact-check noticed, because
  both were checking whether the *limits* were attributed correctly rather than whether the
  *capability* was already delivered. Naming a standard and not reading its output is how a wave
  gets spent rebuilding it.
- **Any threshold or cutoff: universal, dynamic, or declared dataset-specific.** A number derived
  from one dataset is a property of that dataset until shown otherwise. State which of the three
  it is. Prefer deriving it per run (a peak-detection or distribution-based rule that re-computes
  on the data in hand) over a constant, and where a constant is genuinely right, cite what makes
  it general. A hardcoded cut fitted to one corpus silently becomes a wrong cut on the next one,
  and nothing in the pipeline will say so — the same shape as a score whose meaning depends on
  the run that produced it.

**Hard gate when ANY of these hold** — the critique wave rejects a plan whose Calibration block
is missing, incomplete, or carries an unattributed limit, exactly as it would any Blocking
finding:

- introduces a new capability or layer (as opposed to extending one that already runs)
- has 5 or more tasks
- introduces an external tool, database, or data source
- asserts any accuracy, coverage, recall, or performance expectation

Otherwise soft: one honest paragraph, no gate. The trigger list is deliberately mechanical —
"this scope is small and known" is a judgement that gets made most confidently when a wave is
rushed, which is exactly when calibration errors happen.

**Self fact-check before dispatching.** The caller verifies the Calibration block's own claims
first: every number resolves to a measurement on disk, every field-limit claim to a citation
that was actually read. This is the cheapest stage at which to catch a caller's error — the
alternative is 3-10 agents inheriting it, which is the failure mode the whole
"a dispatch's factual claims become code" section above exists to prevent. On 2026-08-29 ten
caller claims were caught downstream by the contradiction slot; each would have been cheaper to
catch here.

**Unsettled questions become a research task, during plan-writing.** Whatever the Calibration
block could not answer gets written into the project's research-questions file (for EnzymeFinder,
`docs/RESEARCH_QUESTIONS.md`) as a numbered topic with specific answerable questions, stating
*why it matters* and *what would change depending on the answer*. The human partner researches
externally and feeds results back, so expectations are corrected **before Task 1** rather than by
a wave discovering mid-flight that its premise was wrong. A question whose answer changes no
decision does not belong there.

## Escalate to a research/review wave instead of continuing to guess

Two triggers replace further ad hoc trial-and-error with a dispatched wave. Either is
sufficient on its own — recognizing a problem as heavy up front is a valid trigger by
itself, not just a fallback after burning several failed attempts:

- **Known-heavy problem, before any attempt** — matches a pattern that's previously eaten a
  lot of time/tokens (a recurring class of issue, something flagged in project history or
  memory as hard, or an area you can already tell is architecturally uncertain). Trigger
  this immediately, don't spend the 3 attempts first just to "earn" the escalation.
- **`systematic-debugging`'s own 3+-failed-fixes gate** (Phase 4.5: "discuss with your human
  partner before attempting more fixes"). In this workspace, that discussion is this wave,
  not just a chat exchange.

When triggered: stop attempting more fixes in-thread. Dispatch, scaled like the plan-review
wave above (minimum ~2-3, more for a genuinely hard problem, concurrency cap applies):

- a **research** pass (`research-scout` or a web-search-capable dispatch) for prior art /
  known issues with this exact failure mode, library, or pattern;
- a **review/audit** pass (`critic-reviewer`-shaped) that re-derives what's actually
  happening from current real source — fresh eyes, not the accumulated hypothesis trail
  already stuck in this conversation;
- a **domain-role** reviewer if the problem is domain-shaped, same pattern as elsewhere in
  this file.

Output is a short written diagnosis + fix approach (root cause, evidence, plan) — not a
fifth guess. Resume via `systematic-debugging` Phase 4 with that in hand, or `writing-plans`
if the fix is big enough to warrant a real plan (which then gets its own plan-review wave
per the section above).

Before committing to a fix approach, run the combined research/review/domain findings
through `pragmatism-officer` — a problem heavy enough to earn a wave still deserves a fix
sized to what's actually at stake, not the largest one the wave surfaced.

## Model and effort tiering for any subagent dispatch

Claude Code subagents default to `model: inherit` — same model as the parent session —
unless the dispatch explicitly sets otherwise. A named agent under `.claude/agents/`
already carries its own tier in its front matter; a generic dispatch (superpowers'
`general-purpose` workers, `subagent-driven-development` task slices, ad hoc `Agent`
calls) does not, and silently inherits whatever the parent session is running — this is
a real, documented gap in how superpowers itself works (its skills are procedural
markdown with no programmatic model/effort control; the host session decides). Set the
`model` and `effort` parameters explicitly on every dispatch using this mapping, rather
than leaving them on inherit by default:

| Task shape | Model | Effort |
|---|---|---|
| Small check, lint-shaped question, single-file mechanical fix | haiku | low |
| Ordinary coding task, single-module change | sonnet | low-medium |
| Coding task with real design tradeoffs | sonnet | high |
| Large rewrite, cross-cutting architecture, highest-stakes review | opus | medium-high |

This is a judgment call per task, not a lookup table to apply blindly — a "small" task
touching a security-sensitive path still warrants a higher tier. When genuinely unsure,
round up rather than down; the cost of under-reviewing a real risk is higher than one
overpriced haiku call.

This is guidance, not enforcement — there is no hook-level mechanism to force model
selection on a subagent dispatch, so this depends on it actually being applied each
time, same limitation as any other prose rule in this workspace.

A named agent under `.claude/agents/` already declares its own model/effort in its own
front matter — that is the actual source of truth. Read the agent file rather than
keeping a duplicate lookup table here.

## Run the fast gates per task, not at wave end

W14 (2026-09-06) ran the full suite once, at wave close. `ruff check src/` had been failing since
the task that introduced the file — through **three review passes that all approved it**, including
two that reproduced the implementer's evidence independently. The lint error was `F841`, twice: two
variables computed and never used. It was not style. Those variables were the column names a
`--ec-column` option was supposed to produce, and their being dead meant the option was a **complete
no-op** and that a header-bearing input produced a **6-column header over 14-column data rows** —
i.e. the wave's own delivery rule ("no existing parser broken") violated by the task that existed to
demonstrate it. Nothing else in the wave found it.

**So a task is not done until the repo's fast gates pass on it.** Put them in the task's definition
of done and in the dispatch: the linter on changed paths, the task's own tests, and any cheap
project-specific checker. Seconds per task; it would have converted a wave-close surprise into a
first-round fix. Reserve the full suite (and `qsub`) for wave close, where it belongs.

## A suite run needs a quiet tree, and the wave owns keeping it quiet

Two independent contaminations hit W14's wave-close suite run, and both were the controlling
session's fault:

- **The job raced its own repository.** `#$ -cwd` runs against the LIVE tree, and a docs commit
  landed mid-run. The suite's own provenance guard caught it (`RACED: HEAD moved during the run`)
  — a guard worth having, and no substitute for not doing it.
- **A reviewer's temporary test file was collected.** A review agent copied a test into `tests/` to
  exercise it under the repo's `conftest.py`, and the suite collected it and counted its failures.
  It cleaned up afterwards, so the tree was clean by the time anyone looked — and the run was
  already wrong.

Before submitting: assert no tracked modifications, no stray files under the test directory, and
record HEAD. Then **make no commits and run no agents until it returns.** And tell every dispatched
agent, reviewers included: **never create a file under `tests/`**, not even briefly.

## Every dispatch carries the environment-invariants block

W14 added each of these reactively, after the incident that motivated it. They belong in the
template.

- **Scratch goes in the session scratchpad, namespaced per agent.** A review agent wrote its
  verification output into a pre-existing untracked `logs/` directory and then `rm -rf`'d the
  directory during cleanup, destroying contents it had never read. Untracked, so git had no copy and
  no snapshot existed. One line in a committed report cited a file in there as its evidence; that
  evidence is gone permanently. The agent disclosed it, which is the only reason anyone knows.
- **Never `rm -rf` inside the project tree.** Delete specific files you created, by name.
- **Read output directories; never modify, move or delete them.** They are usually gitignored, so
  nothing there is recoverable, and the shell `grep`/`find` wrappers cannot see them —
  `command find` / `command grep` can.
- **Name the repo's own test-environment traps**: autouse fixtures in `conftest.py` that override
  what is deployed, and CI's real `-k`/`-m` filter expression. A W14 test was marked `slow` and
  would still have run on **every PR**, because this repo's convention pairs that marker with an
  env opt-in and the marker alone excludes nothing. The reviewer found it by running CI's actual
  filter with `--collect-only` rather than reasoning about it.

## Generate a task's brief at dispatch time, not up front

W14 generated all eight briefs early, then reordered two waves for file-contention reasons. A brief
then instructed its implementer to run a script that a not-yet-dispatched task was going to create.
The implementer did the right thing — skipped it and said so — but a brief that references another
task's output is invalidated by any resequencing, silently.

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

## Three-state is a plan-time checklist item, not a review-time catch

W14 ruled the same way five separate times (its R15, R19, R20, R21, R24), each on code written
**during that wave to fix that class**: a check that could not express "deliberately absent", where
the proposed fix removed the thing from view instead of teaching the check to see it — a marker
nobody writes, rows excluded rather than accounted for, a claim rewritten so the checker stops
matching it, a phase whose archived status is never read, a command that cannot tell "not my input"
from "no result".

Ask it at plan time, once per new check: **what is this check's third state, and how does the check
say it out loud?** The answer is nearly always "account for it explicitly and report the count", and
nearly never "exclude it". Same lesson as `verification.md`'s "A three-state value is typed at
introduction, not repaired at review", one stage earlier: that entry catches the collapse at review
time; this one asks the question before the check is even written.

## A pragmatism seat is the lever for fewer rounds

W14 recorded 24 rulings across 17 fix rounds, and several expanded scope — at least one was fixed
against the controller's own minor-triage test, on the argument that a follow-up note becomes a
comment and evaporates. That argument is sound and it is also how a wave grows. `pragmatism-officer`
exists for exactly this: it does not change severity or correctness verdicts, it separates what must
be fixed now from what can be documented and deferred. Dispatch it once a wave's findings exist,
before the fixes are commissioned — not after.

## The review-dispatch template — because recall is the failure, not discipline

W14's wave-end reviewer hit its turn limit having written **nothing**: 162,630 tokens, 44 tool calls,
one sentence returned. The rule that prevents this — *reviewers write findings down as they confirm
them* — was already in this file, three paragraphs from the incident that motivated it (162,646
tokens, 49 calls, one sentence). The controller had included the rtk position and the
unenumerated-objection slot in **every** review dispatch that wave, and missed the findings-file
requirement, because those two are prominent and this one sits mid-paragraph.

So the failure was **retrieval, not discipline**, and the fix is mechanical. Every review dispatch
carries all of these; composing one is a single lookup rather than several independent recalls:

1. **A findings file path**, with the instruction to append each finding the moment it is confirmed.
   If turns run out, that file is the deliverable.
2. **Ranked areas, and what to drop.** Say explicitly which areas to abandon if turns run short. A
   reviewer given five equal areas explores all five and lands none.
3. **"Prefer executing a small script over reading more source."** A ten-line grep that answers the
   question beats reading three files to reason about it.
4. **The rtk position, verbatim**, plus `command grep` for absence claims.
5. **Check exit codes outside a pipe** — `| tail` masks them, and it caught a reviewer in W14.
6. **The environment-invariants block** (scratchpad path, no `rm -rf` in the tree, never create a
   file under `tests/`, output directories are read-only).
7. **Which files are concurrently modified**, and by whom, so drift findings are checked against
   `git status` first.
8. **The minor-triage content test**, stated as a question the reviewer must answer in writing.
9. **The unenumerated-objection slot** — *"list the strongest objection to this work that I did not
   ask you about."* In W14 this produced three of the best findings, including the one that closed a
   hatch the controller would otherwise have shipped open.
10. **What is already known and accepted**, so the reviewer does not re-derive settled ground.

Same shape applies to implementer dispatches, whose non-negotiable line is the contradiction slot:
*"report anything in this brief that you found to be wrong."* W14 caught **fourteen** brief errors
that way, nearly all the controller's.

