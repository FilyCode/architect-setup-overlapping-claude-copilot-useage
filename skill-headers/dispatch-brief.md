---
name: dispatch-brief
description: Builds the brief for an implementer or review seat in this workspace, on top of superpowers subagent-driven-development's templates — verified claims or UNVERIFIED labels, file ownership, environment block, job-spec handoff, and the review template (findings file first, objection slot). Use when dispatching an implementer or a review seat. Which seats run at wave end: wave-review; plan review: plan-critique.
---

# Dispatch brief

Every brief carries: claims as pasted command output (source, n, denominator) or `UNVERIFIED —
check before relying on it`, absences and external facts too; a state line is pasted `git log -1
--format=%h; git status --porcelain` output, never typed; a file list for a changed symbol is
pasted `command grep -rln <symbol> scripts/ src/ tests/` output; the implementer runs its
importing tests first. Also: files the agent owns and must not touch, the environment block from
the agent file, the job-spec handoff (it never waits on SGE), and the closing line *"report
anything in this brief that you found to be wrong."* Review briefs add the template below:
findings file created first (findings dir, never scratchpad), at most 4 ranked areas with a drop
order, HEAD/status checked at start and end, the minor-triage question, and the
unenumerated-objection slot.

**Which seat.** Code tasks (SDD included) go to `implementer` on its default sonnet; `model:
opus` only for a cross-module or contract change or a retry, with that reason in the brief's
first line (DECISION-028). Ad hoc questions go to `investigator`; "where is X" to Explore with
`model: haiku`. Never general-purpose. The implementer runs only its own tests and the linter,
and stops instead of asking: this overrides the SDD template. Name the project: seats omit
CLAUDE.md.

**Turn budget, first line of every implementer brief:** *"Commit your finished work and write
your report by turn 70 of 100; leave the rest as a listed remainder."* A task that still hits
100 is too big: split it. Every review brief ends with: *"Append each finding to your findings
file as you find it; the file is your report. Before your last turn, append `## CLOSING`:
objection, errors in this brief, what you did not cover. Your final message is at most 10 lines:
verdict, counts, the file path."*

The rules below are the original workspace text, moved verbatim. Old-rule index: config repo
`docs/history/rule-index.md`.
