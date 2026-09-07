# liu-scc workspace

Owner: Philipp Trollmann (phitro@bu.edu). Bioinformatics research on the BU SCC.
Projects live under `projects/<name>/`. The active one is named in `PROJECT_STATE.md`.

<!-- Maintainer notes (stripped before context, not visible to Claude):
     Keep this file under ~40 lines. Anything path-specific belongs in .claude/rules/.
     Anything procedural belongs in a skill. Audited 2026-08-17. -->

## Environment

- No sudo. Installs go to a project `.venv` or `~/.local` — never system-wide.
- Home has a hard 10GB quota: anything large belongs under `software/`, not in home.
- Workspace venv: `.venv/`. Terminal setup: `source .path_hook.sh` (already in `.bashrc`).
- SCC scheduler, storage and login-node rules: `.claude/rules/scc.md`.

## Before you finish

- Never claim done, fixed, or passing without evidence — see `.claude/rules/verification.md`.
- Dispatching any subagent — wave-end review, plan-critique wave, research/review
  escalation, model/effort tiering: `.claude/rules/subagent-dispatch.md`.
- Governance files (`ARCHITECTURE.md`, `DECISIONS.md`, `CLAUDE.md`,
  `PROJECT_STATE.md`) need explicit approval before you change them.
- So does anything outward-facing: pushing, opening or closing GitHub issues, touching CI.

## Project work

Read `projects/<name>/phases/` (or the project's own docs) before changing anything in it.
Project-specific rules live in that project's `CLAUDE.md`.

## Tooling

Workspace-specific: `rtk` (PreToolUse hook; since 2026-08-25 it filters **only `cat`** —
everything else runs raw. Why, and the two remaining gotchas: `.claude/rules/verification.md`),
`caveman`, `ccusage`, `council`, `storm`, `graphify`.
Installed plugins announce themselves; no need to list them here.
