# Agent Gates

IMPORTANT: Do NOT modify governance files (ARCHITECTURE.md, DECISIONS.md, CLAUDE.md, AGENTS.md) without explicit user approval.
IMPORTANT: Do NOT push code, open GitHub issues, or modify CI without explicit user instruction.
IMPORTANT: Do NOT claim a task complete without validation evidence (test output, qacct exit_status, or lint results).

- Validate behavior after meaningful edit groups — not after every micro-change.
- Follow the handoff path: plan → implement → review → gate → commit.
- Keep project-specific changes under `projects/<project>/`; workspace-wide rules stay in root and `.github/`.
- Ask before expanding scope.
