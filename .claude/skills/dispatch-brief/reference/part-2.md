# dispatch-brief — reference part 2

Old file names in the moved text are retired: `subagent-dispatch.md` is now the skills
`dispatch-brief`, `wave-review` and `plan-critique`; `verification.md` is `verification-patterns`
and `scientific-evidence`; `scc.md` is `running-sge-jobs`.

<!-- BEGIN MOVED TEXT (verbatim; do not edit — source: docs/history/rules-2026-10-14) -->
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

## Every dispatch carries the environment-invariants block

W14 added each of these reactively, after the incident that motivated it. They belong in the
template.

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

## The review-dispatch template — because recall is the failure, not discipline

W14's wave-end reviewer hit its turn limit having written **nothing**: 162,630 tokens, 44 tool calls,
one sentence returned. The rule that prevents this — *reviewers write findings down as they confirm
them* — was already in this file, three paragraphs from the incident that motivated it (162,646
tokens, 49 calls, one sentence). The controller had included the rtk position and the
unenumerated-objection slot in **every** review dispatch that wave, and missed the findings-file
requirement, because those two are prominent and this one sits mid-paragraph.

So the failure was **retrieval, not discipline**, and the fix is mechanical. Every review dispatch
carries all of these; composing one is a single lookup rather than several independent recalls:

1. **A findings file path, created as the agent's FIRST action — before it investigates anything.**
   Then appended to the moment each finding is confirmed. If turns run out, that file is the
   deliverable.

   **The "append as you go" instruction alone is not sufficient — measured twice on 2026-09-07.**
   One reviewer was given no findings file and returned one sentence after 162,630 tokens. A second
   *was* given the file path and the append-as-you-go instruction, and still returned nothing after
   144,164 tokens and 45 tool calls, having never created it. A third, same instruction, wrote
   incrementally and survived its limit intact. So the instruction works sometimes, and "sometimes"
   is not a control. Requiring the file to exist **before** the investigation starts is what makes
   the deliverable independent of whether the agent runs out of turns.
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
11. **When the work under review is a guard, a gate or a check: verify it by REMOVING it and
    confirming the test fails — not by reading it.** Twice in W2 this produced stronger evidence
    than the implementer's own. One reviewer proved "no value was hand-typed" by regenerating
    into a scratch copy and getting `rewrote 0 line(s)`; another proved a liveness guard was
    load-bearing by stripping it and watching the test pass anyway. Reading a guard tells you it
    exists; removing it tells you it works.

Same shape applies to implementer dispatches, whose non-negotiable line is the contradiction slot:
*"report anything in this brief that you found to be wrong."* W14 caught **fourteen** brief errors
that way, nearly all the controller's.

