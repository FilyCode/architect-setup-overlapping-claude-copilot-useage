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

## Continuous Improvement

@.claude/prompt-snippets/continuous-improvement.md
[Continuous Improvement](./.claude/prompt-snippets/continuous-improvement.md)

---

## Memory Layout

- Session memory: `/memories/session/` (cleared after curation)
- Project memory: `projects/<project>/phases/` (persistent)
- Workspace memory: `.github/` and root docs (persistent)

---

## Approved Tools

Globally active for all projects: `ccusage`, `rtk`, `caveman`, `council`, `storm` (custom-built, this repo's `.claude/skills/`), `superpowers` (global Claude Code plugin, scope: user), `planning-with-files` (global Claude Code plugin, scope: user, via `OthmanAdi/planning-with-files` marketplace — v3.8.1, migrated 2026-07-23 off a hand-copied v2.37.0 file that had drifted 70+ releases stale), `frontend-design`, `mcp-builder`, `skill-creator`, `webapp-testing` (via `example-skills` plugin from the `anthropic-agent-skills` marketplace, scope: user), `research-skills` (dossier/grants/litreview/patent, via `claude-code-skills` marketplace, scope: user)
Project-specific (EnzymeFinder only): `graphify`
Excluded: `everything-claude-code`, `GSD`, `ruflo`, `claude-mem`, `skill-finder` (no real skill by that name), `task-observer` (overlaps `memory-curator` agent), `impeccable` (defer until BileAcidDB web launch), `research-ops-skills` and `K-Dense-AI/scientific-agent-skills` (both real and evaluated 2026-07-23; skipped — no concrete active need, and stacking more onto an already-large skill listing works against the token-efficiency goal, not for it)
