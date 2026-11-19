---
name: wave-review
description: Runs the wave-end review in this workspace — which seats to dispatch for this kind of wave, in batches under the concurrency cap, with pragmatism triage last, then the retro and aim check, a ran/not-ran list and the ledger rules for closing. Use at the end of a multi-task wave or when asked for /wave-review. For a quick ad hoc review of one change use superpowers requesting-code-review or /code-review instead. Seat briefs come from dispatch-brief.
effort: high
---

# Wave-end review

Use at the end of a wave, before finishing a branch, or after a big task (or several smaller ones
have accumulated). Self-verification is not independent review. For a small ad hoc check of one
change, superpowers `requesting-code-review` stays available; seat briefs come from `dispatch-brief`.

## Roster by wave type

- **critic-reviewer**, always (correctness, quality, tests, efficiency, simplicity).
- **alignment-officer** (completeness, scope) and **docs-sync** (governance-doc drift) when a plan
  or phase doc exists.
- **domain-reviewer** for domain work, naming the professional role.
- **anomaly-hunter** when the wave produced a new measurement; skip on pure bug-fix or doc-only waves.
- **inventory-auditor** when the wave added capability.
- **lean-critic**, always, on the wave's diff (it preloads ponytail).
- **pragmatism-officer** last, once findings exist.
- **retro-officer**, always, as the final step: give it the ledger path, the findings (files or
  reports), the commit range per repo and the main transcript path
  (`~/.claude/projects/<project>/<session id>.jsonl`). It appends one entry to
  `docs/retros/retro-log.md` in the config repo.

**Analysis-wave trial (owner 2026-11-08, next 3 analysis waves, then decide):** a wave whose output
is a measurement or finding, not code, runs domain-reviewer, anomaly-hunter and
pragmatism-officer; critic-reviewer only when the wave changed a gate or test; lean-critic,
inventory-auditor and docs-sync only at a doc-heavy close; retro-officer as always, recording
"trial n/3" and any later finding a dropped seat would have caught. Code waves keep the roster above.

## Procedure

1. Pin the review to one commit and name its HEAD in the close. Commits after it, such as features
   the owner adds at review, get a short second critic pass before merge.
2. Dispatch in batches under the concurrency cap (2 on the smaller account, 3 on the larger):
   science seats first (domain-reviewer, anomaly-hunter), then critic-reviewer and
   alignment-officer, then docs-sync, inventory-auditor and lean-critic, so governance text is
   drafted after the findings it must not contradict. A spawn refused at the cap is not queued:
   re-dispatch it when a slot frees.
3. Every dispatch ends with the unenumerated-objection slot (below). Findings files go in the
   findings dir (`.superpowers/findings/<date>/` in the config repo, persistent), never the
   scratchpad, which dies with the job.
4. A seat is not "ran" until its findings file has its closing section
   (`command grep -q '^## CLOSING' <file>`) and `wave_stats.py` lists it under no
   `turn_limit_by_seat`. A truncated seat or a `Not covered` entry is re-dispatched on those
   areas, not accepted. If a seat put findings only in its message, re-run it; only as a last
   resort write them into its file, marked controller-written, before closing.
5. pragmatism-officer over all findings, before the fixes are commissioned; then retro-officer;
   then the aim check.
6. The close lists every seat as ran or not-ran, with the reason. When the wave's evidence is only
   self-consistency, say so in the close and keep a standing row for one held-out evaluation.

## Closing and ledger rules

- **Nothing is called done before the close line.** Nothing that says built, verified, merged,
  closed, answered or resolved (status docs, findings, commit subjects, headline prose in FINDINGS,
  replies to the owner) is written or pushed before the roster has run and the close line exists;
  before that it says "candidate" with its measurement, or is marked DRAFT. A headline is not a
  status doc, so this failed 4 times. "Push at wave end" means after that line, and a /compact
  keep-line says "push after review close" (R-20261030-1/-9: SenC and MeMES pushed claims hours
  before the review, one headline later retracted).
- **A vacuity deferral blocks GREEN** (R-20261117-2). A ledger deferral saying a gate, guard or
  fixture "passes on" a default, "has no true case" or is unvalidated is not deferrable: it
  becomes a register row or a re-open, and the step is not GREEN.
- **MERGE GATE.** A branch that is not merged, or whose full suite could not run, carries the line
  "MERGE GATE: full suite on the merge commit, job spec written" in its ledger and plan status,
  with the job spec's path; the wave is not marked closed without that line.
- A post-refresh test failure recorded in a handoff becomes a ledger item with an owner and the
  next refresh as its gate, never only a note.
- A CI check that is red with no job log (minutes exhausted) is recorded as not run; the PR
  carries the local equivalent's command and output.

## Aim check, after the retro

Before any new wave or fix round, dispatch `aim-keeper` with the project path, the wave's Goal line
and commit range, and the next step on the table (say whether the owner or Claude proposed it).
Put its owner question to the owner with AskUserQuestion (core rule 15) and record the answer in
the ledger. The `aim_nudge` hook reminds at retro dispatch and at the third fix round.

## Rules, most consequential first

### Self-verification is not independent review

Do not skip dispatching a reviewer for a task because it "looks like" a governance-doc correction
rather than novel computation. The MqnE retrospective found a whole task group closed on that
reasoning without independent review, and every one of that project's biggest missed findings
lived in the doc-framing layer, exactly the layer that rationale skipped.

### Minor-triage content test

Before filing a review finding as Minor, answer in writing: *if this finding is correct, does any
currently-stated conclusion change?* If yes, it is not a Minor, however small the edit looks: a
wording complaint ("stated unhedged", "unacknowledged") can be a category error underneath, and
misclassified severity is how defects survive several review rounds. Cheap backstop: re-read the
parked Minor list at every wave's end, not only the wave it was filed in.

### Run the fast gates per task, not at wave end

A task is not done until the repo's fast gates pass on it: the linter on changed paths, the task's
own tests and any cheap project checker, in its definition of done and in the dispatch. The full
suite (and `qsub`) belongs to wave close. W14 (2026-09-06): an `F841` on two dead variables
survived three approving reviews; it meant an `--ec-column` option was a complete no-op and a
header-bearing input got a 6-column header over 14-column rows.

### A suite run needs a quiet tree, and the wave owns keeping it quiet

Before submitting: assert no tracked modifications, no stray files under the test directory, and
record HEAD; then make no commits and run no agents until it returns. Tell every dispatched agent,
reviewers included: never create a file under `tests/`, not even briefly. W14: `#$ -cwd` ran
against the live tree and a docs commit landed mid-run (the provenance guard caught it:
`RACED: HEAD moved during the run`), and a reviewer's temporary test file copied into `tests/`
was collected and its failures counted.

### Unenumerated-objection slot

Every review dispatch, wave-end or ad hoc, ends with: *"list the strongest objection to this work
that I did not ask you about."* It turns an occasional unprompted habit into routine. It targets
enumeration, not tone: there is no evidence adversarial wording changes what a reviewer finds.

### Name the uncommitted files when implementers are still running

A review dispatch issued while implementers are running names the files currently
uncommitted-modified and tells the reviewer to check `git status` before filing any
documentation-drift finding. Otherwise it files findings against text a concurrent agent already
fixed (2026-09-01: an auditor would have filed against three status docs already corrected).

### Anomaly-hunter: the only seat whose job is to reopen things

Every other seat is biased toward closure: critic-reviewer on "the code does what it says",
domain-reviewer on "plausible given what we know", which is exactly what buries a real discovery.
`anomaly-hunter` attacks the confirming results, checks the instrument floor on every absence
claim, names the third state and follows the weird number (its file has the checks; the rule is in
`scientific-evidence`). Do not skip it because a wave's results look clean: that is the condition
it exists for. Created 2026-09-25 after known biology closed an anomaly three times in one session.

### Domain-reviewer as routine, not only after a crisis

A correctness, completeness or drift review cannot produce a premise-level or
domain-plausibility finding; only a domain-role pass can, and by the time a crisis convenes one
the defect has shipped. Name the professional role in the dispatch (computational enzymologist,
structural biologist, cheminformatician); the agent file carries the rest. Evidence: an ad hoc
domain seat produced W2b-1's only Blocking finding (a hygiene fix that moved a shipped tier
boundary) plus five Importants five other seats missed.

### Inventory-auditor closes its own loop

When the wave introduced new functions, modules or scripts, `inventory-auditor` catches duplication
within the wave and capability rebuilt instead of wired to something existing. If a plan-time
inventory pass recommended wiring in or extending something, this dispatch checks the wave did it,
so the recommendation does not evaporate; that alone is reason to run it on a wave that added no
capability. Its findings feed pragmatism triage.

### Pragmatism-officer: the lever for fewer rounds

Once findings exist and before fixes are commissioned, `pragmatism-officer` separates what must be
fixed now from what is real but can be documented and deferred, and rejects scope creep. It has no
authority over severity or correctness and runs on top of the Minor-triage content test, not
instead of it. Skip it when the wave produced zero findings. W14: 24 rulings over 17 fix rounds,
several of which expanded scope.

### One integration seat, mid-wave

Path-scoped per-task review cannot see across tasks; both W14 defects that reached wave close lived
in that gap. Around the midpoint, dispatch `critic-reviewer` (or a generic agent if its budget does
not fit) once, with a prompt scoped only to what no task owns: the gates as a whole, the tree as a
whole, and any file every task read and none owned.

### critic-reviewer's docs-sync reminder

On an APPROVED wave-end verdict, critic-reviewer closes with a one-line reminder to consider
docs-sync. Ignore it when docs-sync already ran that wave or the review was an ad hoc
`requesting-code-review` check. (A `SubagentStop`-hook version was reverted: DECISION-024.)
