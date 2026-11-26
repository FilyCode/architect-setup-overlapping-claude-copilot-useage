---
name: dispatch-brief
description: "Builds the brief for an implementer or review seat in this workspace, on top of superpowers subagent-driven-development's templates — verified claims or UNVERIFIED labels, file ownership, environment block, job-spec handoff, and the review template (findings file first, objection slot). Use when dispatching an implementer or a review seat. Which seats run at wave end: wave-review; plan review: plan-critique."
---

# Dispatch brief

Use when writing the brief for an implementer, review or analysis seat. The checklists come first;
the rules below them say why each line is there. Worked incidents:
[reference/incidents.md](reference/incidents.md). Old-rule index: config repo `docs/history/rule-index.md`.

## Every brief carries

- A claim about an API's SHAPE — importable, a function, a unique key, a column exists — pastes
  the command and its output, not a line number. Values were right and shapes were assumed in
  both 2026-11-25 brief errors: `273`'s rule was inline in `main()` and could not be imported as
  the brief said, and `anchor_gff_id` is not a unique key (60 anchors returned 79,098 rows).
- Claims as pasted command output (source, n, denominator) or `UNVERIFIED — check before relying
  on it`, absences and external facts too. Every signature, exit code, path or flag it cites is
  copied from a grep run in this turn, with file:line.
- A state line pasted from `git log -1 --format=%h; git status --porcelain`, never typed; a file
  list for a changed symbol pasted from `command grep -rln <symbol> scripts/ src/ tests/`.
- Files the agent owns, and files it must not touch because another agent holds them.
- The environment block from the agent file, and the job-spec handoff (it never waits on SGE).
- The project name and the pasted path of its domain-context file(s); seats omit CLAUDE.md.
- The closing line *"report anything in this brief that you found to be wrong."*
- A re-derivation that contradicts a seat lists every category the number ranges over with its
  contribution (UNRESOLVED/UNKNOWN as their own row); a commit saying a seat overstated waits for a
  second seat to re-derive it.
- A multi-seat brief names one owner (file or seat) per shared fact (a count, a register row);
  other seats cite it rather than re-derive it.
- An analysis brief opens with a TARGET sentence and what a result would have to show to answer
  it; the domain seat checks the headline against it.

## Implementer briefs

- **Turn budget, first line:** *"Commit your finished work and write your report by turn 70 of
  100; leave the rest as a listed remainder."* A task that still hits 100 is too big: split it.
- Never amend or rebase; add a new commit.
- The implementer runs its importing tests first, then only its own tests and the linter, and
  stops instead of asking: this overrides the SDD template.
- *"Lean checks before commit: no pass-through wrappers, no assert, gate, control arm or oracle
  that cannot fail: each ships a fail proof (one input that changes only the field it reads, where
  it differs from the passing value, reaching the failing verdict; both values pasted) or is
  labelled 'cannot fail' and never prints PASS/ok; an oracle lists the inputs it shares with the
  code; a docstring naming a published rule has a toy test where rule and variant differ, or says
  'variant of'; no test that re-implements the code under test, and each error message says what
  the check does."*
- **DONE line:** the exact test command and its pass count; for a changed return contract or
  cache producer, the pasted callers grep and the digest/namespace bumped; the project's
  governance tests (its CLAUDE.md or CI list) run; the report written to
  `<findings dir>/<task>-implementer.md` before the reply, so a restart does not lose it; a
  `RESULT:` line per headline number, unrounded (3 significant figures) with its n, which the
  controller quotes verbatim and recounts from the artifact before writing it into a doc.
- A plan box is ticked only against the promise's quoted wording, else `partial: <what is missing>`.
  Before each implementer dispatch, re-read the session's done-condition and the wave's Goal line.

## Review briefs

The seat's literal first action, before it reads the rest of the brief, is creating its findings
file (findings dir, never the scratchpad), written by the seat itself with Write or a Bash heredoc
(every seat but research-scout can). A missing file, or one without `## CLOSING`, means re-run the
seat; controller transcription is the last resort and is marked. A seat that answers only in its
message has not followed its brief. Also:

1. Evidence scripts go in `<findings dir>/probes/<seat>/`, never the scratchpad; no other writes,
   nothing under the project tree, its `.claude/agent-memory/` included (R-20261110-2: a seat's
   memory write nearly failed a running build's tree guard). Any tool with a `--write` mode is
   off-limits in a shared worktree: render to scratch and diff there.
2. At most 4 ranked areas with a drop order; prefer executing a small script over reading more source.
3. HEAD moves during review: never tell a seat the tree is clean. It runs `git log -1` and
   `git status --porcelain` at start and end, says whether they moved, and re-runs
   `git log -1 --format=%h` before each finding's evidence line (cited file changed: mark it
   `RE-DERIVE`). The controller edits no file a running seat reads; name which files are
   concurrently modified, and by whom.
4. `command grep` for absence claims; exit codes checked outside a pipe (`| tail` masks them).
5. A guard, gate or check under review is verified by removing it and watching its test fail.
6. The minor-triage question, answered in writing; what is already known and accepted.
7. The unenumerated-objection slot: *"list the strongest objection to this work that I did not ask
   you about."*
8. A review that closes a register row re-measures the row's premise against the real source
   (live call, fixture vs claim), not only the diff.

Every review brief ends with: *"Append each finding to your findings file as you find it; the file
is your report. By turn limit minus 8, append `## CLOSING`: objection, errors in this brief, what
you did not cover. Your final message is at most 10 lines: verdict, counts, the file path."*

## Which seat

Code tasks (SDD included) go to `implementer` on its default sonnet; `model: opus` only for a
cross-module or contract change or a retry, argued in the brief's first line as
`Opus because: <reason>` (from the plan row); `dispatch_guard` denies it otherwise (DECISION-033). Ad hoc questions go to `investigator`; "where is X" to Explore with `model: haiku`.
**A SOURCED SURVEY is not a `research-scout` task**: that seat's own budget is one search and at
most two fetches, so asking it for the state of a field gets a memory answer that looks like a
survey. It goes to `investigator`, with a minimum search and fetch count stated in the brief
(2026-11-25: the scout obeyed its budget and the dispatch was wrong; the `investigator` re-run
did 13 searches and 6 fetches and graded each claim by how it was obtained).
Never general-purpose. A named seat's front matter is the source of truth for its model and
effort; a dispatch that overrides it rounds up when unsure (a small task on a security-sensitive
path still warrants a higher tier). A dispatch with no named agent inherits the parent session's
model: set model and effort explicitly (tiers: reference/incidents.md "Model and effort
tiering"). At most 2 subagents at once (3 on the larger account); queue the rest.

## A dispatch's factual claims become code

A subagent cannot tell which of your assertions were verified and will write a wrong count, file
list or dependency claim into commits (2026-08-24: one became the final review's only Critical).
Verify every claim or label it `UNVERIFIED`; counts, site enumerations and dependency claims are
the high-risk classes. **A figure relayed from a subagent's report is unverified too**, and one
carrying a defect hypothesis is the highest-risk form: re-derive it before writing it (W2
2026-09-21: six wrong citations, all the controller's). An item whose figure you have not
re-derived with a parser, or that a report disputes, ends with: *"if your measurement disagrees
with mine, stop and report — do not reconcile toward mine."* Mechanical backstop: EnzymeFinder
`scripts/check_citations.py` preflights `path:line`, paths, arithmetic, sha pins and `--flag`
attribution, not counts. When a subagent challenges a claim, check the artifact before overruling.

- **Brief check before a costly dispatch** (owner 2026-11-26; 37% of 1,680 runs reported a brief
  error, wrong premise or mechanism the largest class): before an opus implementer, an analysis
  brief or a wave's first task, dispatch `investigator` (model sonnet, effort low, 20 turns) with
  the draft: *"list each premise, figure, path and mechanism here that the repo contradicts or you
  cannot confirm, with the command that shows it; do not do the task."* Fix or label each, then
  dispatch. `dispatch_guard` denies once a brief whose backticked paths, `path:N` or `HEAD` sha do
  not resolve; an identical resubmit passes.

- **Every relayed figure carries its column, not only its n:** state the artifact, the column and
  the arm; a stratified or conditional figure carries its n in the brief and in the finding
  (1,577 vs 1,459 on two identity columns; `0.0717` was 16/223).
- **Prefer a short brief of verified claims to a long brief of relayed ones** (2026-09-01: eleven
  of twelve implementers found a factual error in the controller's brief; the shortest brief had none).
  Failure classes: figures without n, drifting line numbers, mechanism claims (being right that it
  failed is not being right about why).
- **Say your summary is lossy and point at the source:** *"the table above is a compression of
  <source>; read the full row there before trusting it, and report any place the compression is
  wrong."* (W2b-1 2026-09-23.)

## Concurrent dispatches need declared file ownership

Never dispatch two implementers that touch the same file; when tasks queue behind one shared file,
each brief names the files it owns and those another agent holds. Every dispatch that may commit
ends with: stage files individually by name (`git add <dir>/` sweeps a neighbour's new files), then
run `git show --stat` after each commit and confirm it touched only your files (2026-09-01: two
index collisions, both caught this way). Recovery: `git reset --soft HEAD~1`, `git reset -- <the
other agent's files>`, re-commit. Shared-worktree hazards: a bare `git commit` with others' staged
files, `git commit -- <paths>`, `git stash push -- <paths>`, `git --work-tree=<dir> checkout`, and
`cp` restoring a file after a generator's `--write` (W2b-1). Give every generator a `--stdout` mode
and say so in `--help`. An agent that waited while commits landed is told what changed and to
re-read before editing, and which failing checks are not its own.

## Never dispatch "wait and report" as a subagent's task

The dispatching side submits every SGE job: an agent that needs one writes the job spec (script,
resources, expected artifact) into its report and stops; the caller submits, waits in one
backgrounded loop, and resumes the subagent with the result. An instruction is not a backstop: a
loop inside a subagent ends when its turn ends (2026-08-29, 2026-09-05: agents stalled at
176k-555k tokens despite the rule in their brief). A non-SGE wait inside a subagent is one
`Bash(run_in_background=true)` loop with a deadline, never repeated foreground checks. If the wait
is the entire reason for a dispatch, do not dispatch: the caller checks directly. Never re-message
a dispatched agent on a timer; wait for its notification, or `ScheduleWakeup` sized to the
expected duration.

## A follow-up note is a task, not a comment

A fix that belongs in a file the agent does not own becomes a dispatched task with declared
ownership in the same wave, never a comment: a thoroughly documented defect reads as a fixed one
(`stages.py`: 81 comment lines, 12 code). A chain of N tasks over N files needs an N+1st whose
only job is to `command grep` for who actually calls the new thing.

## "The brief is wrong" is a first-class finding

When a seat flags that the brief or plan premise is wrong, escalate it at the severity its content
would warrant as an implementation bug and route it to the plan's owner; the out-of-scope label
does not close it (MqnE_cofactor_finding retrospective, 2026-08-24). This is why every implementer
brief has the contradiction slot (2026-08-29: five false claims caught; W14: fourteen).

## Reviewers write findings down as they confirm them

A seat that keeps findings in its head until the end hits its turn limit with nothing written
(162,646 and 162,630 tokens, one sentence each; 144,164 with the append instruction but no file).
A file created before investigation is the deliverable when turns run out (W2b-1: report lost,
file held three findings, one Blocking).

## A review wave has no negative control

Seats ask whether the code does what it says, not whether the system does its job. When a wave's
evidence is entirely self-consistency, say so in its close and carry a standing row for one
held-out evaluation with a stated denominator and a trivial baseline (W2b-1 2026-09-23).

## Every dispatch carries the environment-invariants block

Scratchpad path, namespaced per agent; delete only files you created, by name; no `rm -rf` in
the tree, never create a file under `tests/`, output directories read-only.
**Name the repo's own test-environment traps**: autouse fixtures in `conftest.py` that override
what is deployed, and CI's real `-k`/`-m` filter, checked with `--collect-only` (W14: a `slow`
marker excluded nothing without its env opt-in).

## Generate a task's brief at dispatch time, not up front

A brief that references another task's output is silently invalidated by any resequencing (W14:
a brief told its implementer to run a script a later task would create).
