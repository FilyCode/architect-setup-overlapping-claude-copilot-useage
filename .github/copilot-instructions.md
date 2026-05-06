# Copilot Workspace Instructions

Primary source: [CLAUDE.md](../CLAUDE.md)

## Shared Snippets

[Coding Standards](../.claude/prompt-snippets/coding-standards.md)
[Token Efficiency](../.claude/prompt-snippets/token-efficiency.md)
[SCC Profile](../.claude/prompt-snippets/scc-profile.md)
[Agent Gates](../.claude/prompt-snippets/agent-gates.md)

## Scope

- `projects/` is the home for all project work.
- Workspace-wide rules live in `CLAUDE.md` and `.github/`.
- Project overrides live in `projects/<project>/.claude/`.

## Operating Rules

1. Follow shared instruction layer before proposing edits.
2. Keep responses concise and actionable.
3. Ask before changing governance files (ARCHITECTURE.md, DECISIONS.md, CLAUDE.md).
4. Approved tools: ccusage, rtk, caveman, planning-with-files (all projects); superpowers, graphify (EnzymeFinder only).
5. Respect the handoff path: plan → implement → review → gate → commit.

## References

- [.github/AGENTS.md](../AGENTS.md)
- [.github/SCC_PROFILE.md](../SCC_PROFILE.md)
- [.github/TOKEN_EFFICIENCY.md](../TOKEN_EFFICIENCY.md)
