# Agent Gates

- Do not modify global governance files (ARCHITECTURE.md, DECISIONS.md, CLAUDE.md) without explicit user approval.
- Validate behavior after meaningful edit groups — not after every micro-change.
- Follow the handoff path: plan → implement → review → gate → commit.
- Keep project-specific changes under `projects/<project>/`; workspace-wide rules stay in root and `.github/`.
- Ask before expanding scope or taking actions that affect shared state (pushing code, creating issues, modifying CI).
