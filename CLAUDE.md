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

Globally active for all projects: `ccusage`, `rtk`, `caveman`, `planning-with-files`
Project-specific (EnzymeFinder only): `superpowers` (in `.claude/skills/`), `graphify`
Excluded: `everything-claude-code`, `GSD`, `ruflo`, `claude-mem`
