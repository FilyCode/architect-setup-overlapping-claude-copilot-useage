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
  - `rules/*.md` → `.claude/rules/`. Unscoped rules load in every session and every subagent
    that does not set `omitClaudeMd`; path-scoped rules (`paths:` frontmatter) load when a
    matching file is touched. Only `core.md` may be unscoped (`tools/context_budget.py`).
  - `agents/*.md` → `.claude/agents/` (review seats plus `implementer`; list them with
    `ls workspace-config/agents/` rather than trusting a list here — it went stale twice).
  - `rtk/` — retired 2026-10-14 (DECISION-026); kept for history, see `rtk/RETIRED.md`.
- `.claude/skills/` — `council`, `storm`, `ccusage`, `caveman`, `workspace-audit`, and the
  process skills built from `skill-headers/` by `tools/build_skills.py`.
  All explicit-invocation only except `caveman`; also symlinked into the workspace root's
  `.claude/skills/` so they load project-wide rather than only inside this repo.
- `.claude/context/` — `runbook.md`, `domain-glossary.md`, `learnings.md` (cross-project
  patterns; promotion bar is 3+ recurrences across 2+ projects), `parked-extensions.md`
  (plugins disabled but still on disk, with re-enable commands — check it before installing
  anything new).
- `docs/superpowers/` — specs, plans and reviews. `docs/history/` — retired rule text and
  `rule-map.tsv` (where every old rule went).

## Conventions

- Rules belong in the workspace root `.claude/rules/`, not here. This repo is for skills,
  context and history.
- Do not hand-copy a skill that has an upstream marketplace — install the plugin instead.
  This has gone wrong three times; see `.claude/context/learnings.md`. Exception: a skill
  with no Claude marketplace may be vendored with its LICENSE and a `SOURCE.md` pinning the
  upstream commit (`thermo-nuclear-code-quality-review`).
- The repo name still mentions Copilot. Renaming means renaming the GitHub remote too —
  left alone deliberately rather than done silently.
