# Continuous Improvement

## When to check
- After finishing a development branch or any multi-step build.
- At the end of a broad audit/maintenance pass.
- When the same friction or mistake shows up a 2nd time in a session — flag it as a promotion candidate.

## What to do
- Compare the pattern against `.claude/context/learnings.md`'s promotion bar (3+ recurrences across 2+ distinct tasks/projects). Promote if it clears the bar; otherwise it stays in session memory.
- Skill audit: a skill or plugin untouched for 30+ days is a prune candidate. Check before adding a new one — every active plugin adds session-listing overhead regardless of whether it gets used.
- Version check: confirm installed plugins are still current against the marketplace/plugin manifest itself, not a summarized changelog — changelog summaries have been wrong before (see `learnings.md`).
- Log the audit date and outcome at the bottom of `learnings.md`, even when nothing changed. An audit with no trail didn't happen.
