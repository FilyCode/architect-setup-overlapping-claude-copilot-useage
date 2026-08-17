# Shared config repo

Owner: Philipp Trollmann. Originally the instruction layer shared between Claude Code and
GitHub Copilot. **Copilot was retired 2026-08-17** (usage limits); the Copilot mirror is at
`_archive/2026-08-17-copilot-layer/` and is fully recoverable from git.

Workspace-wide rules for Claude Code are **not** here — they live at the workspace root in
`/projectnb/liu-scc/philipp/CLAUDE.md` and `.claude/rules/`, which load automatically.
This repo now carries only what has no workspace-root equivalent.

## Layout

- `.claude/skills/` — `council`, `storm`, `ccusage`, `rtk`, `caveman`, `workspace-audit`.
  All explicit-invocation only.
- `.claude/context/` — `runbook.md`, `domain-glossary.md`, `learnings.md` (cross-project
  patterns; promotion bar is 3+ recurrences across 2+ projects), `parked-extensions.md`
  (plugins disabled but still on disk, with re-enable commands — check it before installing
  anything new).
- `docs/superpowers/` — specs and plans from skill-building work.

## Conventions

- Rules belong in the workspace root `.claude/rules/`, not here. This repo is for skills,
  context and history.
- Do not hand-copy a skill that has an upstream marketplace — install the plugin instead.
  This has gone wrong three times; see `.claude/context/learnings.md`.
- The repo name still mentions Copilot. Renaming means renaming the GitHub remote too —
  left alone deliberately rather than done silently.
