# Shared Claude config

Skills, cross-project context, and design history for the liu-scc workspace.

Published repo: [FilyCode/architect-setup-overlapping-claude-copilot-useage](https://github.com/FilyCode/architect-setup-overlapping-claude-copilot-useage)

> The name is historical. This was a shared Claude Code + GitHub Copilot instruction layer
> until **2026-08-17**, when Copilot was retired after its usage limits were cut. The Copilot
> half is archived at `_archive/2026-08-17-copilot-layer/` in the workspace and recoverable
> from git history. Renaming the repo means renaming the GitHub remote, so it was left alone.

## What belongs here

- `workspace-config/` — the workspace root's Claude Code config (`CLAUDE.md`,
  `ARCHITECTURE.md`, `DECISIONS.md`, `rules/`, `agents/`). The workspace root is not a git
  repo, so these live here and are symlinked back. This is the version-controlled copy.

- `.claude/skills/` — `council`, `storm`, `ccusage`, `rtk`, `caveman`, `workspace-audit`.
  All explicit-invocation only, so they cost no context until typed.
- `.claude/context/` — `runbook.md`, `domain-glossary.md`, `learnings.md`.
- `docs/superpowers/` — specs and plans from skill-building work.

## What does not belong here

- **Workspace rules.** Those live at the workspace root in `CLAUDE.md` and `.claude/rules/`,
  which Claude Code loads automatically. Rules placed here do not load.
- Project-specific architecture or sprint state.
- One-off work notes — those go in the active project's docs.

## Layout it assumes

- Workspace-wide rules: `/projectnb/liu-scc/philipp/CLAUDE.md` and `.claude/rules/`
- Workspace subagents: `.claude/agents/` (`critic-reviewer`, `alignment-officer`, `scc-monitor`)
- Project rules: `projects/<project>/.claude/`
- Project state: `projects/<project>/phases/` and `projects/<project>/docs/`
