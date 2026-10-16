---
name: plan-critique
description: Reviews an architectural plan before Task 1 — Calibration block and its hard gate, plan preflight that executes the plan's claims, critique-wave sizing, three-state check, and the escalation wave after repeated failed fixes. Use before starting an approved plan, when asked for /plan-critique, or after a third failed fix. Not for review of finished work (wave-review).
effort: high
---

# Plan critique

Order: Calibration block present and self-fact-checked → preflight (run the plan's code blocks
and resolve every path, symbol and figure it cites; EnzymeFinder has
`projects/EnzymeFinder/scripts/check_citations.py` for citations) → inventory-auditor → critique
wave (minimum 3 seats, batched under the concurrency cap; lean-critic, always, is one of
them: which tasks, files and abstractions the plan can drop or reuse) → pragmatism-officer → fix the plan
before Task 1. Ask of every new check: what is its third state, and how does it say so?

The rules below are the original workspace text, moved verbatim.

## Reference files (read the one you need)

- See [reference/part-2.md](reference/part-2.md) — a **domain-role** reviewer if the problem is domain-shaped, ; Three-state is a plan-time checklist item, not a review-time; during that wave to fix that class**: a check that could not

Old file names in the moved text are retired: `subagent-dispatch.md` is now the skills
`dispatch-brief`, `wave-review` and `plan-critique`; `verification.md` is `verification-patterns`
and `scientific-evidence`; `scc.md` is `running-sge-jobs`.

<!-- BEGIN MOVED TEXT (verbatim; do not edit — source: docs/history/rules-2026-10-14) -->
<!-- from subagent-dispatch.md:339 -->
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

<!-- from subagent-dispatch.md:361 -->
## Plan writing: inventory-auditor

Before a plan's task list is locked in — during `writing-plans`, alongside or just before
the Calibration block below — dispatch `inventory-auditor` against the plan draft (or,
before one exists, the problem statement). It searches the codebase and project history for
anything the plan proposes to build that already exists, exists-but-unwired, or was already
tried and rejected. Motivated by a planning round (2026-09-11) that proposed four things
that already existed — one already owner-approved as a decision, one built and marked
`DONE, reach: yes` but never wired into the pipeline — and the checks that caught them were
nine wave-end review seats rather than one dedicated inventory pass.

Feed its findings into the plan before the critique wave runs, the same way the Calibration
block's findings shape the plan before critique — a plan-critique wave should not have to
independently rediscover that a task rebuilds something that already works, or that an
"artifact this project has never had" is already committed under a different name.

`inventory-auditor` is also available at wave end (see the wave-end review section above)
for the retrospective direction: catching duplication a wave introduced, or capability it
rebuilt instead of calling.

<!-- from subagent-dispatch.md:381 -->
## Plan review before implementation

After `writing-plans` produces a plan doc (architectural path only — bounded-path short
in-chat designs skip this, the dispatch cost isn't justified) and its own self-review, but
before `executing-plans`/`subagent-driven-development` starts Task 1: dispatch a
<!-- from subagent-dispatch.md:386 -->
**plan-critique wave** against the plan and its spec. Same mechanics as wave-end review
above (parallel, rtk position stated verbatim, unenumerated-objection slot, minor-triage
content test) — the difference is what it targets (the plan text, not a diff) and when it
runs (before work starts, not after).

<!-- from subagent-dispatch.md:391 -->
- Reuse `critic-reviewer` (plan-shaped: feasibility, missing tasks, edge cases) and a
  `domain-reviewer` (see the wave-end section's domain-role paragraph; name the role in
  the dispatch) — this is the same premise-checking discipline, just moved a stage earlier so
  a bad premise is caught before it is copied into every task that inherits it.
<!-- from subagent-dispatch.md:395 -->
- Scale the number of dispatches to the plan's size and complexity: **minimum 3**
  (critic-reviewer + one domain-role reviewer + one issue-specific angle, chosen from what
  the plan actually touches — security, data-integrity, concurrency, etc.), up to **~10**
  for a large or high-stakes plan — one per major task-cluster or distinct risk axis
  (correctness, domain plausibility, security, performance, data-integrity, concurrency,
  external-API/rate-limit behavior, backward-compat, test-coverage gaps, premise/instrument
  choice). Pick the count from the plan's actual content, not a fixed default. The
  account's concurrency cap still applies (2-3 concurrent, `feedback_subagent_dispatch.md`)
  — a 10-agent wave runs in batches, not literally at once.
<!-- from subagent-dispatch.md:404 -->
- Tell each dispatch to verify cheap claims empirically, not just read the plan — grep that
  a referenced function/signature actually exists, run a two-line script against real data
  if the plan asserts a library or format behavior. This is what catches "a plan's own
  example code carries the bug" (`verification.md`) before it propagates into every task
  that copies it.
<!-- from subagent-dispatch.md:409 -->
- Blocking/Important findings against the plan get fixed in the plan doc directly, before
  Task 1 starts — "the brief is wrong" is a first-class finding here too (see above),
  applied one stage earlier than a wave-end review would catch it.
<!-- from subagent-dispatch.md:412 -->
- A reviewer may surface an unrelated pre-existing codebase defect while checking the plan.
  Report it, then judge case by case whether fixing it fits this plan — file overlap with a
  plan task is not an automatic block; a fix that belongs in the same file a task already
  touches can be folded into that task directly (still declare ownership per "Concurrent
  dispatches need declared file ownership" above so the fix and the task edit don't race).
  If it doesn't fit this plan's scope or timing, don't fix it blind — document it: what it
  is, where, and when it should be fixed (a follow-up task, a `DECISIONS.md` entry, or a
  known-issues note in the plan doc itself), so it doesn't evaporate as a chat-only mention.
<!-- from subagent-dispatch.md:420 -->
- Once the plan-critique wave's findings are in, dispatch `pragmatism-officer` over them
  before deciding what actually goes into the plan rewrite — same proportionality triage as
  wave-end review, applied to plan-stage findings instead of a diff. A critique wave scaled
  up to ~10 dispatches produces a lot of adversarial output; this is what keeps one bounded
  issue from triggering five rounds of plan rewrites before Task 1 even starts.

<!-- from subagent-dispatch.md:426 -->
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

<!-- from subagent-dispatch.md:439 -->
- **Vision context** — which layer or axis of the project's north-star this serves, and at what
  scale. One layer is not the system. State what this plan is *not* responsible for, so a later
  reviewer does not indict it for failing to do something it was never meant to do.
<!-- from subagent-dispatch.md:442 -->
- **Realistic target** — what this achieves when it works correctly. Not the aspiration.
<!-- from subagent-dispatch.md:443 -->
- **General limits vs our limits** — every constraint named as either field-wide *with a
  citation* or ours to fix. **Anything unattributed defaults to OURS.** A field limit without a
  citation is not a field limit; it is an untested excuse, and it is the specific move that cost
  the SSN wave.
<!-- from subagent-dispatch.md:447 -->
- **Standard** — the bar is *at least* current tool and literature standard, better where we can.
  Name the tool and the number being matched, not "state of the art".
<!-- from subagent-dispatch.md:449 -->
- **Does the named standard already do this?** Check the tool you just named as the bar, and say
  what it already delivers of what you are proposing to build. Added 2026-08-30 because its
  absence was not hypothetical: a plan proposed partitioning an SSN by a property its own named
  comparison tool already separated — EFI-EST's existing cluster assignment put 90.7% of the
  target mode in one cluster — and neither the author nor the self-fact-check noticed, because
  both were checking whether the *limits* were attributed correctly rather than whether the
  *capability* was already delivered. Naming a standard and not reading its output is how a wave
  gets spent rebuilding it.
<!-- from subagent-dispatch.md:457 -->
- **Any threshold or cutoff: universal, dynamic, or declared dataset-specific.** A number derived
  from one dataset is a property of that dataset until shown otherwise. State which of the three
  it is. Prefer deriving it per run (a peak-detection or distribution-based rule that re-computes
  on the data in hand) over a constant, and where a constant is genuinely right, cite what makes
  it general. A hardcoded cut fitted to one corpus silently becomes a wrong cut on the next one,
  and nothing in the pipeline will say so — the same shape as a score whose meaning depends on
  the run that produced it.

<!-- from subagent-dispatch.md:465 -->
**Hard gate when ANY of these hold** — the critique wave rejects a plan whose Calibration block
is missing, incomplete, or carries an unattributed limit, exactly as it would any Blocking
finding:

<!-- from subagent-dispatch.md:469 -->
- introduces a new capability or layer (as opposed to extending one that already runs)
<!-- from subagent-dispatch.md:470 -->
- has 5 or more tasks
<!-- from subagent-dispatch.md:471 -->
- introduces an external tool, database, or data source
<!-- from subagent-dispatch.md:472 -->
- asserts any accuracy, coverage, recall, or performance expectation

Otherwise soft: one honest paragraph, no gate. The trigger list is deliberately mechanical —
"this scope is small and known" is a judgement that gets made most confidently when a wave is
rushed, which is exactly when calibration errors happen.

<!-- from subagent-dispatch.md:478 -->
**Self fact-check before dispatching.** The caller verifies the Calibration block's own claims
first: every number resolves to a measurement on disk, every field-limit claim to a citation
that was actually read. This is the cheapest stage at which to catch a caller's error — the
alternative is 3-10 agents inheriting it, which is the failure mode the whole
"a dispatch's factual claims become code" section above exists to prevent. On 2026-08-29 ten
caller claims were caught downstream by the contradiction slot; each would have been cheaper to
catch here.

<!-- from subagent-dispatch.md:486 -->
**Unsettled questions become a research task, during plan-writing.** Whatever the Calibration
block could not answer gets written into the project's research-questions file (for EnzymeFinder,
`docs/RESEARCH_QUESTIONS.md`) as a numbered topic with specific answerable questions, stating
*why it matters* and *what would change depending on the answer*. The human partner researches
externally and feeds results back, so expectations are corrected **before Task 1** rather than by
a wave discovering mid-flight that its premise was wrong. A question whose answer changes no
decision does not belong there.

<!-- from subagent-dispatch.md:494 -->
## Escalate to a research/review wave instead of continuing to guess

Two triggers replace further ad hoc trial-and-error with a dispatched wave. Either is
sufficient on its own — recognizing a problem as heavy up front is a valid trigger by
itself, not just a fallback after burning several failed attempts:

<!-- from subagent-dispatch.md:500 -->
- **Known-heavy problem, before any attempt** — matches a pattern that's previously eaten a
  lot of time/tokens (a recurring class of issue, something flagged in project history or
  memory as hard, or an area you can already tell is architecturally uncertain). Trigger
  this immediately, don't spend the 3 attempts first just to "earn" the escalation.
<!-- from subagent-dispatch.md:504 -->
- **`systematic-debugging`'s own 3+-failed-fixes gate** (Phase 4.5: "discuss with your human
  partner before attempting more fixes"). In this workspace, that discussion is this wave,
  not just a chat exchange.

When triggered: stop attempting more fixes in-thread. Dispatch, scaled like the plan-review
wave above (minimum ~2-3, more for a genuinely hard problem, concurrency cap applies):

<!-- from subagent-dispatch.md:511 -->
- a **research** pass (`research-scout` or a web-search-capable dispatch) for prior art /
  known issues with this exact failure mode, library, or pattern;
<!-- from subagent-dispatch.md:513 -->
- a **review/audit** pass (`critic-reviewer`-shaped) that re-derives what's actually
  happening from current real source — fresh eyes, not the accumulated hypothesis trail
  already stuck in this conversation;
