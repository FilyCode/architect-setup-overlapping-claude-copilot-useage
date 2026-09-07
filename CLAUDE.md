# Shared config repo

Owner: Philipp Trollmann. Originally the instruction layer shared between Claude Code and
GitHub Copilot. **Copilot was retired 2026-08-17** (usage limits); the Copilot mirror is at
`_archive/2026-08-17-copilot-layer/` and is fully recoverable from git.

**The workspace root config lives here now** (2026-08-17). The workspace root is not a git
repository, so `CLAUDE.md`, `ARCHITECTURE.md`, `DECISIONS.md`, `.claude/rules/` and
`.claude/agents/` had no version control at all. The real files moved into
`workspace-config/` in this repo; the workspace root holds symlinks back to them, so Claude
Code loads them exactly as before while git tracks the content.

Edit either path — they are the same file. Do not replace a symlink with a copy.

## Layout

- `workspace-config/` — the workspace root's config, symlinked back to `/projectnb/liu-scc/philipp/`:
  - `CLAUDE.md`, `ARCHITECTURE.md`, `DECISIONS.md` → workspace root
  - `rules/*.md` → `.claude/rules/` (9 files, all read on demand via prose references from
    `CLAUDE.md` or other rules — no hook auto-injects any of them; a file only reaches a
    session if something actually points to it, verified 2026-09-06)
  - `agents/*.md` → `.claude/agents/` (`critic-reviewer`, `alignment-officer`, `scc-monitor`,
    `docs-sync`, `research-scout`, `security-specialist`, `pragmatism-officer`)
  - `rtk/config.toml` → `~/.config/rtk/config.toml`, and `rtk/rtk_selftest.sh` →
    `software/bin/rtk_selftest.sh`. Same symlink rule: a missing or unparseable rtk config
    silently restores "rewrite every Bash command" with no warning, so it is version-controlled
    rather than left loose in a quota-capped home. See DECISION-025.
- `.claude/skills/` — `council`, `storm`, `ccusage`, `rtk`, `caveman`, `workspace-audit`.
  All explicit-invocation only except `caveman`; also symlinked into the workspace root's
  `.claude/skills/` so they load project-wide rather than only inside this repo.
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
