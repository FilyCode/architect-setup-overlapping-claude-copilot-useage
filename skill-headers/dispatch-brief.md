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

**Which seat.** Code tasks, SDD tasks included, go to `implementer`, on its default sonnet.
Pass `model: opus` only for a cross-module or contract change or a retry, and name that reason
in the brief's first line (DECISION-028). Ad hoc questions go to
`investigator`; "where is X" to Explore with `model: haiku`. Never general-purpose. The
implementer runs only its own tests and the linter, and stops instead of asking: this
overrides the SDD template. Name the project: seats omit CLAUDE.md.

**Turn budget, first line of every implementer brief:** *"Commit your finished work and write
your report by turn 70 of 100; leave the rest as a listed remainder."* The line alone did not
move the 60-turn hit rate (21.9% vs 22.0%), so caps were raised 2026-10-21; a task that still
hits 100 is too big — split it. Every review
brief ends with: *"Append each finding to your findings file as you find it; the file is your
report. Before your last turn, append `## CLOSING`: objection, errors in this brief, what you
did not cover. Your final message is at most 10 lines: verdict, counts, the file path."*
(DECISION-028.)

The rules below are the original workspace text, moved verbatim; incident detail explains why
each exists. The index of where every old rule went is
`architect-setup-overlapping-claude-copilot-useage/docs/history/rule-index.md`.
