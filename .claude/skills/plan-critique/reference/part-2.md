# plan-critique — reference part 2

Old file names in the moved text are retired: `subagent-dispatch.md` is now the skills
`dispatch-brief`, `wave-review` and `plan-critique`; `verification.md` is `verification-patterns`
and `scientific-evidence`; `scc.md` is `running-sge-jobs`.

<!-- BEGIN MOVED TEXT (verbatim; do not edit — source: docs/history/rules-2026-10-14) -->
<!-- from subagent-dispatch.md:516 -->
- a **domain-role** reviewer if the problem is domain-shaped, same pattern as elsewhere in
  this file.

Output is a short written diagnosis + fix approach (root cause, evidence, plan) — not a
fifth guess. Resume via `systematic-debugging` Phase 4 with that in hand, or `writing-plans`
if the fix is big enough to warrant a real plan (which then gets its own plan-review wave
per the section above).

Before committing to a fix approach, run the combined research/review/domain findings
through `pragmatism-officer` — a problem heavy enough to earn a wave still deserves a fix
sized to what's actually at stake, not the largest one the wave surfaced.

<!-- from subagent-dispatch.md:633 -->
## Three-state is a plan-time checklist item, not a review-time catch

W14 ruled the same way five separate times (its R15, R19, R20, R21, R24), each on code written
<!-- from subagent-dispatch.md:636 -->
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

