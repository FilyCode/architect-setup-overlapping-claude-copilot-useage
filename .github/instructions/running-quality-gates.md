# Quality Gates

When asked to run quality gates, critic review, alignment check, or release gate:
Apply the workflow from `projects/EnzymeFinder/.claude/skills/running-quality-gates/SKILL.md`.

Trigger phrases: "run quality gates", "critic review", "alignment check", "release gate", "quality gate", "gate sequence"

Key rules:
- Load: active phase PLAN.md + DECISIONS.md + git diff. Do NOT reload AGENTS.md in full.
- Sequence: Critic → Alignment Officer → Release Gate → (PASS: Commit Agent | FAIL: Engineer).
- Agent definitions are in `.github/agents/`.
- Write gate verdict to `/memories/session/gate_decision.md`.
