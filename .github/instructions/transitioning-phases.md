# Phase Transitions

When asked to close a phase, start the next phase, archive a session, or run Memory Curator:
Apply the workflow from `projects/EnzymeFinder/.claude/skills/transitioning-phases/SKILL.md`.

Trigger phrases: "phase transition", "archive session", "close phase", "next phase", "memory curator", "phase handoff"

Key rules:
- Architect owns PROJECT_STATE.md and _index.md (requires human approval to commit).
- Memory Curator produces CURATION_SUMMARY.md as a proposal — human approves before promotion.
- Issue Portfolio Agent syncs GitHub after human approves the curation.
- No persistent changes commit without explicit human approval.
