---
name: plan-critique
description: Reviews an architectural plan before Task 1 — Calibration block and its hard gate, retirement check, plan preflight that executes the plan's claims, critique-wave sizing, three-state check, and the escalation wave after repeated failed fixes. Use before starting an approved plan, when asked for /plan-critique, on a known-heavy problem, or after a third failed fix. Not for review of finished work (wave-review).
effort: high
---

# Plan critique

Use after `writing-plans` and its self-review, before `executing-plans` or
`subagent-driven-development` starts Task 1 (architectural path only; bounded-path in-chat designs
skip it), and for a known-heavy problem or a third failed fix (escalation section).

## Procedure

1. **Calibration block** present and self-fact-checked (below).
2. **Retirement check** (below): one grep, and a hit blocks Task 1.
3. **Preflight:** run the plan's code blocks and resolve every path, symbol and figure it cites
   (EnzymeFinder has `projects/EnzymeFinder/scripts/check_citations.py` for citations).
4. **inventory-auditor** against the plan draft; its findings go into the plan before the critique.
5. **Critique wave** (minimum 3 seats, batched under the concurrency cap; lean-critic, always, is
   one of them: which tasks, files and abstractions the plan can drop or reuse).
6. **pragmatism-officer** over the critique findings.
7. **Fix the plan before Task 1.** Exit: every "run X before/at T" in the critique's required
   changes is copied into the plan as a numbered task row before the plan is marked ready; the
   controller greps the critique for it.

Ask of every new check: what is its third state, and how does it say so?

## Retirement check (R-20261103-1)

**Owner-approved 2026-11-03. One grep, and it blocks Task 1.** For every set the plan proposes to
analyse, `command grep` the project's `DECISIONS.md` and `FINDINGS.md` for that set's **defining
marker and its cut value**, together with `withdrawn|retired|sister`. Paste the hits into the
Calibration block. **Any hit blocks Task 1** until the plan says why the set is still worth measuring.

Why (MeMES_OvoA_search, 2026-11-03): a wave spent 6 of 11 commits on a 93-protein stratum that
`D-014` had retired on 2026-10-22 as a sister family (`DECISIONS.md:115`). A five-seat plan-critique ran before Task 1 and none of its
five findings files mentions D-014: the seats reviewed how the plan measured, never whether the
thing measured had been set aside. Preflight executes a plan's claims; it does not ask whether the
question was already answered. This check asks that question, and it costs one command.

## Acceptance and pre-registration

- **A pre-registration with a write-a-paragraph escape hatch is not a constraint.** If a plan
  pre-registers a sentence, state what evidence, not what reasoning, may overturn it (the same wave
  pre-registered its headline, allowed superseding it "with reason", and published the wrong
  conclusion through eleven green gates).
- Expected values are committed before the first run. Each acceptance metric has a planted-defect
  case that makes it fail, else it is labelled "reproduction", never PASS.
- The pre-registration lists every confound the project's known-limitations and earlier
  pre-registrations name, each controlled, measured or out of scope.
- A result called "confirmed" or a "gain" names its control and the factors in which they differ
  (diff of the run configs).
- Each seat's strongest objection that touches an acceptance check gets a ledger line before
  approval: adopted (task row with a planted-wrong-answer case) or declined with reason.
- A plan whose acceptance is a count of self-agreement names one independent check (a different
  tool, or hand-picked cases) in the task row.
- A forced-failure (or other negative-path) acceptance gets a miniature reachability run (stub
  chain, seconds) as a task row before the real run.
- A sequential multi-step mutation (rename, swap, ledger) lists the state after each step's failure
  and the test covering it.

## The Calibration block — required before the critique wave

Every architectural plan carries a **Calibration** section, written before the critique wave
dispatches, separating what this class of method cannot do from what our implementation does
badly. Why (SSN wave, 2026-08): a validation harness ran for weeks and never cleared its own anchor
floor. Our sub-35% edge recall was 62.5% because of
a DIAMOND sensitivity defect (MA-104), and that fixable 37.5% edge loss hid behind a cited field
limit. The citation was itself wrong: ~35% identity is EFI-EST's SSN edge-drawing threshold, not a
field-wide ceiling for annotation transfer; Zallot 2019 states the transfer sentence without a
citation of its own, and its worked example needs ~58% identity to separate isofunctional clusters
(owner-approved correction 2026-10-28; source
`projects/EnzymeFinder/docs/superpowers/specs/2026-09-06-instrument-not-readout-design.md:271-290`).
Do not quote ~35% as a field-wide transfer limit; cite a project's own low-identity measurements.

Required items:

- **Vision context:** which layer or axis of the project's north-star this serves, at what scale,
  and what the plan is *not* responsible for, so no later reviewer indicts it for that.
- **Realistic target:** what this achieves when it works correctly. Not the aspiration.
- **General limits vs our limits:** every constraint named as field-wide *with a citation* or ours
  to fix. **Anything unattributed defaults to OURS**; a field limit without a citation is an
  untested excuse.
- **Standard:** at least current tool and literature standard, better where we can; name the tool
  and the number matched, not "state of the art".
- **Does the named standard already do this?** Read the named tool's output and say what it already
  delivers (2026-08-30: a plan would partition an SSN by a property EFI-EST's clusters already
  separated, 90.7% of the target mode in one).
- **Any threshold or cutoff: universal, dynamic, or declared dataset-specific.** A number from one
  dataset is that dataset's property until shown otherwise. Prefer deriving it per run (peak
  detection, distribution-based); a constant cites what makes it general.

**Hard gate when ANY of these hold:** the critique rejects a plan whose Calibration block is
missing, incomplete, or carries an unattributed limit, exactly as a Blocking finding. The plan:

- introduces a new capability or layer (as opposed to extending one that already runs);
- has 5 or more tasks;
- introduces an external tool, database, or data source;
- asserts any accuracy, coverage, recall, or performance expectation.

Otherwise soft: one honest paragraph, no gate. The triggers are deliberately mechanical: "this scope
is small and known" is judged most confidently when a wave is rushed.

**Self fact-check before dispatching.** The caller verifies the Calibration block's own claims
first: every number resolves to a measurement on disk, every field-limit claim to a citation that
was actually read. Otherwise 3-10 seats inherit the error (2026-08-29: ten caller claims caught
downstream by the contradiction slot).

**Unsettled questions become a research task, during plan-writing.** What the Calibration block
could not answer goes into the project's research-questions file (EnzymeFinder:
`docs/RESEARCH_QUESTIONS.md`): numbered, answerable, why it matters, what the answer would change;
the owner researches it before Task 1. A question whose
answer changes no decision does not belong there.

## Plan review before implementation: the critique wave

Same mechanics as wave-end review in `wave-review` (parallel seats, unenumerated-objection slot,
minor-triage content test); the plan-critique wave targets the plan text and its spec, not a diff,
before work starts.

- **Seats.** Minimum 3, lean-critic always among them; the defaults are `critic-reviewer`
  (plan-shaped: feasibility, missing tasks, edge cases) and a `domain-reviewer` (name the role),
  plus issue-specific angles from what the plan touches. Premise-checking a stage earlier, so a bad
  premise is caught before every task inherits it.
- **Scale the number of dispatches to the plan's size and complexity**, minimum 3, up to ~10 for a
  large or high-stakes plan: one per major task-cluster or risk axis (correctness, domain,
  security, performance, data-integrity, concurrency, external API, backward-compat, test gaps,
  premise/instrument). The concurrency cap still
  applies (2-3 concurrent, `feedback_subagent_dispatch.md`): run in batches.
- **Tell each dispatch to verify cheap claims empirically:** grep that a referenced function or
  signature exists; run a two-line script on real data when the plan asserts library or format
  behaviour. This catches "a plan's own example code carries the bug" (`verification-patterns`).
- **Blocking and Important findings are fixed in the plan doc before Task 1.** "The brief is wrong"
  is a first-class finding here too.
- **A reviewer may surface an unrelated pre-existing defect.** Report it and judge case by case:
  file overlap with a task is no automatic block, and a fix in a file a task already touches can be
  folded into that task (declare ownership, `dispatch-brief`). Otherwise document what, where and
  when to fix it (follow-up task, `DECISIONS.md` entry or known-issues note in the plan), never a
  chat-only mention.
- **pragmatism-officer runs over the plan-critique findings** before deciding the plan rewrite, so
  one bounded issue does not trigger five rounds of rewrites before Task 1.

## Three-state is a plan-time checklist item, not a review-time catch

Ask once per new check, at plan time: **what is this check's third state, and how does it say it
out loud?** Nearly always "account for it explicitly and report the count", nearly never "exclude
it". W14 ruled this five times (R15, R19-R21, R24), each on code written during that wave to fix that
class: a check that could not express "deliberately absent", fixed by removing the thing from view
(rows excluded not accounted for, a claim reworded so the checker stops matching).
`verification-patterns` catches the collapse at review; this asks before the check is written.

## Plan writing: inventory-auditor

Before a plan's task list is locked (during `writing-plans`, alongside the Calibration block),
dispatch `inventory-auditor` against the plan draft, or the problem statement before one exists.
It finds what the plan would build that already exists, exists unwired, or was tried and rejected.
Feed its findings into the plan before the critique wave, so the critique need not rediscover them
(2026-09-11: a plan proposed four existing things, one built but never wired). It also runs at wave end (`wave-review`) for
duplication a wave introduced.

## Escalate to a research/review wave instead of continuing to guess

Either trigger alone is sufficient:

- **Known-heavy problem, before any attempt:** it matches a pattern that has previously eaten a lot
  of time or tokens (a recurring class, flagged as hard in history or memory, or architecturally
  uncertain). Escalate immediately; do not spend 3 attempts to earn it.
- **`systematic-debugging`'s own 3+-failed-fixes gate** (Phase 4.5, "discuss with your human
  partner"): here that discussion is this wave, not a chat exchange.

Then stop fixing in-thread and dispatch, scaled like the plan-review wave (minimum ~2-3, cap applies):

- a **research** pass (`research-scout` or a web-search-capable dispatch) for prior art and known
  issues with this failure mode, library or pattern;
- a **review/audit** pass (`critic-reviewer`-shaped) that re-derives what is actually happening from
  current real source, with fresh eyes rather than the accumulated hypothesis trail;
- a **domain-role** reviewer if the problem is domain-shaped, as elsewhere.

Output: a short written diagnosis and fix approach (root cause, evidence, plan), not a fifth guess.
Run it through `pragmatism-officer` so the fix is sized to the stake, then resume in
`systematic-debugging` Phase 4, or `writing-plans` (with its own plan-critique) if the fix is big.

## Brainstorming: research-scout

For a non-trivial design decision during `brainstorming`, dispatch `research-scout` first; skip it
for small or obvious decisions. **Before dispatching any research task, `command grep` the gitignored
workspace directories (`.superpowers/`) for prior work:** the shell `grep` skips gitignored paths
(2026-09-01: a dispatched review duplicated a 713-line review from three days earlier).
