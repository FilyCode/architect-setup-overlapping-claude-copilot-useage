---
name: dispatch-brief
description: Builds the brief for an implementer or review seat in this workspace, on top of superpowers subagent-driven-development's templates — verified claims or UNVERIFIED labels, file ownership, environment block, job-spec handoff, and the review template (findings file first, objection slot). Use when dispatching an implementer or a review seat. Which seats run at wave end: wave-review; plan review: plan-critique.
---

# Dispatch brief

Every brief carries: claims as pasted command output (source, n, denominator) or `UNVERIFIED —
check before relying on it`, absences and external facts too; a state line is pasted `git log -1
--format=%h; git status --porcelain` output, never typed; a file list for a changed symbol is
pasted `command grep -rln <symbol> scripts/ src/ tests/` output; the implementer runs its
importing tests first. A re-derivation that contradicts a seat lists every category the number
ranges over with its contribution (UNRESOLVED/UNKNOWN as their own row); a commit saying a seat
overstated waits for a second seat to re-derive it. Also: files the agent owns and must not touch, the environment block from
the agent file, the job-spec handoff (it never waits on SGE), and the closing line *"report
anything in this brief that you found to be wrong."* Review briefs add the template below:
findings file created first (findings dir, never scratchpad; scripts you write for evidence go in `<findings dir>/probes/<seat>/`, never the scratchpad), at most 4 ranked areas with a drop
order, `git log -1 --format=%h` re-run before each finding's evidence line (cited file
changed: mark it `RE-DERIVE`; the controller edits no file a running seat reads), the minor-triage question, and the
unenumerated-objection slot. A multi-seat brief names one owner (file or seat) per shared fact
(a count, a register row); other seats cite it rather than re-derive it.

**Which seat.** Code tasks (SDD included) go to `implementer` on its default sonnet; `model:
opus` only for a cross-module or contract change or a retry, with that reason in the brief's
first line (DECISION-028). Ad hoc questions go to `investigator`; "where is X" to Explore with
`model: haiku`. Never general-purpose. The implementer runs only its own tests and the linter,
and stops instead of asking: this overrides the SDD template. Name the project: seats omit
CLAUDE.md. At most 2 subagents at once (3 on the larger account); queue the rest.
Every implementer brief also carries: *"Lean checks before commit: no pass-through wrappers, no
assert that cannot fail, no test that re-implements the code under test, and each error message
says what the check does."* Review seats other than research-scout can write their findings file
with a Bash heredoc; a seat that answers only in its message has not followed its brief.

**Turn budget, first line of every implementer brief:** *"Commit your finished work and write
your report by turn 70 of 100; leave the rest as a listed remainder."* A task that still hits
100 is too big: split it. A plan box is ticked only against the promise's quoted wording, else
`partial: <what is missing>`. Before each implementer dispatch, re-read the session's
done-condition and the wave's Goal line. Every review brief ends with: *"Append each finding to your findings
file as you find it; the file is your report. Before your last turn, append `## CLOSING`:
objection, errors in this brief, what you did not cover. Your final message is at most 10 lines:
verdict, counts, the file path."*

The rules below are the original workspace text, moved verbatim. Old-rule index: config repo
`docs/history/rule-index.md`.
