# Workspace Instructions

**Owner**: Philipp Trollmann
**Scope**: Workspace-wide; applies to all projects under `projects/`.
Project-specific overrides live in `projects/<project>/.claude/CLAUDE.md`.

---

## Coding Standards

@.claude/prompt-snippets/coding-standards.md
[Coding Standards](./.claude/prompt-snippets/coding-standards.md)

---

## Token Efficiency and Model Routing

@.claude/prompt-snippets/token-efficiency.md
[Token Efficiency](./.claude/prompt-snippets/token-efficiency.md)

---

## BU SCC Profile

@.claude/prompt-snippets/scc-profile.md
[SCC Profile](./.claude/prompt-snippets/scc-profile.md)

---

## Agent Gates

@.claude/prompt-snippets/agent-gates.md
[Agent Gates](./.claude/prompt-snippets/agent-gates.md)

---

## Memory Layout

- Session memory: `/memories/session/` (cleared after curation)
- Project memory: `projects/<project>/phases/` (persistent)
- Workspace memory: `.github/` and root docs (persistent)

---

## Approved Tools

Globally active for all projects: `ccusage`, `rtk`, `caveman`, `planning-with-files`, `superpowers` (global Claude Code plugin, scope: user), `frontend-design`, `mcp-builder`, `skill-creator`, `webapp-testing` (via `example-skills` plugin from the `anthropic-agent-skills` marketplace, scope: user)
Project-specific (EnzymeFinder only): `graphify`
Excluded: `everything-claude-code`, `GSD`, `ruflo`, `claude-mem`, `skill-finder` (no real skill by that name), `task-observer` (overlaps `memory-curator` agent), `impeccable` (defer until BileAcidDB web launch)
