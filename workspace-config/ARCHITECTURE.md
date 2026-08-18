# System Architecture: liu-scc Workspace

**Last updated**: 2026-08-17
**Scope**: Workspace-wide governance, SCC integration, and agent configuration
**Audience**: Engineers, agents, and future collaborators

---

## Layers

1. **Workspace governance** — root docs (`CLAUDE.md`, this file, `DECISIONS.md`,
   `PROJECT_STATE.md`) and `.claude/rules/` (`ROADMAP.md` was planned in DECISION-002 but
   never created — not tracked here until it exists)
2. **Project execution** — code and phase-based docs under `projects/<project>/`
3. **Session memory** — auto memory at `~/.claude/projects/<project>/memory/`

---

## System Components

### Project Workflows (`projects/`)

```
projects/<project>/
  ARCHITECTURE.md       # project system design (authoritative)
  DECISIONS.md          # cross-phase project decisions
  PROJECT_STATE.md      # current state — canonical status ledger
  docs/history/         # closed investigations and incident write-ups
  phases/<phase>/
    PLAN.md             # objective + acceptance criteria
    DECISIONS.md        # phase-specific decisions
    ENGINEER_TASKS.md   # next steps
    SESSION_LOG.md      # completion record
  reference/            # stable reference material
  _archive/             # dated snapshots (do not modify)
```

### SGE Job Submission Layer

**Templates** (`general/*.sh`): R and Python templates for single-core, parallel, array jobs.

**Flow**: `User/Agent → script from template → qsub → SGE queue → qstat/qacct → verify artifact`

**Defaults** (source of truth: [.claude/rules/scc.md](.claude/rules/scc.md)):
Project `liu-scc`; 1 core non-parallel; 4/8/16/28 parallel; 8G per core; `h_rt` ≤12h.

A clean `exit_status` is not evidence of success — the artifact check is part of the flow,
not an optional extra.

---

## Claude Code Configuration

**Where these files physically live.** The workspace root is not a git repository, so the
real files sit in `architect-setup-.../workspace-config/` and the workspace root holds
symlinks to them. Claude Code resolves symlinks normally in `.claude/rules/`,
`.claude/agents/` and for `CLAUDE.md`. Editing either path edits the same file; never
replace a symlink with a copy, or the two will drift.

Loaded automatically every session:

| What | Where | Loads |
|---|---|---|
| Personal preferences | `~/.claude/CLAUDE.md` | always |
| Workspace instructions | `CLAUDE.md` | always |
| Always-on rules | `.claude/rules/scc.md`, `verification.md`, `subagent-dispatch.md` | always |
| Path-scoped rules | `.claude/rules/{python,shell,r,enzymefinder,codebase-navigation,bileaciddb}.md` | when a matching file is touched |
| Auto memory index | `~/.claude/projects/<project>/memory/MEMORY.md` | always (first 200 lines) |
| Memory topic files | same directory | on demand |
| Project instructions | `projects/<project>/.claude/CLAUDE.md` | when working in that project |

Not always-on: skills load their descriptions only; subagents run in isolated context;
hooks run outside the conversation.

**Subagents** (`.claude/agents/`, project scope): `critic-reviewer` (senior review,
re-derives correctness from source, no `memory` — stays fresh rather than trusting cached
patterns), `alignment-officer` (scope conformance, `memory: project`), `scc-monitor` (SGE
diagnosis, `memory: project`), `docs-sync` (governance-doc drift after a wave, read-only
by design, deliberately **no** `memory` field — see the memory/Write-Edit gotcha below),
`research-scout` (cheap single-agent best-practices check during brainstorming,
haiku/low-effort), `security-specialist` (release/publication-gate security checklist,
opus, surface-aware — most 2026 runs correctly terminate at "not applicable" since no
project has a built web surface yet). A previous 13-agent
topology was archived 2026-08-17 — it was never executable in Claude Code and superpowers
covers most of what it described. Dispatch rules (when to run which, model/effort
tiering for any subagent) live in `.claude/rules/subagent-dispatch.md`.

**Enforcement** vs **guidance**: rules and `CLAUDE.md` shape behaviour but are advisory.
Anything that must hold every time is a hook in `~/.claude/settings.json`.

**Skills**: workspace skills in `architect-setup-.../.claude/skills/`, symlinked into
`.claude/skills/` so they load project-wide; EnzymeFinder domain skills in
`projects/EnzymeFinder/.claude/skills/`, on demand there. Plugin skills come from
`superpowers`, `pyright-lsp` and `diagram-design`. `example-skills`, `research-skills` and
`planning-with-files` are parked — disabled, still on disk; see
`.claude/context/parked-extensions.md`.

**MCP**: `.mcp.json` defines `graphify-enzymefinder`, currently disabled — it served a
cached graph that went stale after every rebuild. Use the graphify CLI, which reads from
disk. The graph itself rebuilds on every commit via a `post-commit` hook, at zero token
cost. See [.claude/rules/codebase-navigation.md](.claude/rules/codebase-navigation.md).

---

## Key Architectural Decisions

| Decision | Rationale |
|---|---|
| Path-scoped `.claude/rules/` over one large CLAUDE.md | Instructions load only where they apply; adherence degrades in long files |
| Three real subagents, not a documented topology | An agent that cannot be invoked is worse than none — it gets planned around |
| Hooks for invariants, prose for judgment | Advisory rules were violated repeatedly; hooks are deterministic |
| Phase-based project docs | Scoped and self-contained per phase |
| Human-in-the-loop on governance and outward-facing actions | Safety and auditability |
| SCC defaults in one rule file | Prevents ad-hoc resource drift |
| Claude Code only (Copilot retired 2026-08-17) | Removes a dual-maintenance layer that had already drifted |

---

## Constraints

1. **Reproducibility over speed**: keep run metadata and versions traceable
2. **SCC resource caps**: respect the profile; justify escalations
3. **Home quota**: 10GB hard cap — large data belongs under `software/`
4. **English-only**: all documentation, comments and responses
5. **Project docs stay in `projects/`**: workspace docs stay short and generic

---

## Related Documents

- [.claude/rules/](.claude/rules/) — scheduler, storage, verification, language and project rules
- [DECISIONS.md](DECISIONS.md) — workspace-wide decision log
- [PROJECT_STATE.md](PROJECT_STATE.md) — current state
