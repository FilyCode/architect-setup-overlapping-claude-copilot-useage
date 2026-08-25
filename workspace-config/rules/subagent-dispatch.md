# Subagent dispatch: review gate and model/effort tiering

## Never dispatch "wait and report" as a subagent's task

A dispatched subagent's context is expensive to reload — every "still waiting, check
again" round-trip re-pays its full accumulated history. A real incident burned 1M+ tokens
this way: an implementer subagent was told to wait for an SGE job and report back, and
polled `qstat`/`qacct` across ~4 separate round-trips at ~230k tokens each.

Do not dispatch a subagent whose task is, or includes as a multi-turn loop, "wait for
job/agent X to finish, then report." Instead:

- If a subagent's task genuinely needs to wait on something external as one internal
  step, it must do so inside a single `Bash(run_in_background=true)` shell-level loop
  (see `scc.md`'s "Waiting on a job without burning tokens") — never repeated foreground
  status-check calls across turns.
- If the wait is the *entire* reason for dispatch, don't dispatch at all — the caller
  (main session or a fork) checks directly instead; it is near-free there since it is not
  reloading a subagent's accumulated history each time, and only dispatches the real
  downstream-processing subagent once the artifact exists.
- The same applies to waiting on another dispatched subagent/fork: never re-message or
  nudge it on a timer to ask if it is done — either it delivers a task notification on
  completion, or (for `/loop` dynamic pacing) use `ScheduleWakeup` with a delay sized to
  the actual expected duration, never a short fixed interval "just in case."

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

**Every review dispatch must warn about the `rtk` filter.** A reviewer's job is mostly
negative checks — "unmodified", "no stale reference", "no matches", "nothing swept in" — and
rtk's Bash hook produces exactly that class of false result. Include this line verbatim in
every review dispatch: *"`rtk` rewrites Bash commands and can invert a result; confirm any
negative finding with `RTK_DISABLED=1 <cmd>` or `rtk proxy <cmd>`, and never treat an exit code
from an rtk-wrapped command as evidence. A pipeline is NOT a bypass — it is rewritten too. Never
conclude a file does not exist from `rtk find`, which silently omits hidden and gitignored
paths."* Details and the verified failure list are in `verification.md`. This costs one sentence
per dispatch; without it a reviewer reports a clean bill of health it never actually
established — and note that this round's reviewers found four independent holes in the exclusion
list itself, including two escape hatches this file had documented backwards.

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

For a non-trivial design decision during `brainstorming`, dispatch `research-scout`
first (see its own description for scope). Skip it for small/obvious decisions.

**One external premise check at project start, and at any reframing.** Before building an
analysis pipeline around an assumed premise about the target itself, do one PDB/PubMed (or
domain-equivalent database) lookup directly on the target — not just on the surrounding method.
Make it a standing habit to resolve any external ID (PDB/accession/etc.) that a pipeline returns
repeatedly, rather than treating the repetition as an incidental curiosity; a project's own top
structural-search hit turning out to be the query's own already-published structure is exactly the
kind of premise error this catches cheaply.

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
