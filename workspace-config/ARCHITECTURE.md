# System Architecture: liu-scc Workspace

**Last updated**: 2026-10-15
**Scope**: Workspace-wide governance, SCC integration, and agent configuration
**Audience**: Engineers, agents, and future collaborators

---

## Layers

1. **Workspace governance** — root docs (`CLAUDE.md`, this file, `DECISIONS.md`), the
   always-loaded `core.md`, path-scoped `.claude/rules/` and the process skills. The root `PROJECT_STATE.md` was archived 2026-10-14; each project keeps
   its own. (`ROADMAP.md` was planned in DECISION-002 but never created.)
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

**Defaults** (source of truth: skill `running-sge-jobs`; old rule text in
`docs/history/rules-2026-10-14/scc.md` of the config repo):
Project `liu-scc`; 1 core non-parallel; 4/8/16/28 parallel; 8G per core; `h_rt` ≤12h.

A clean `exit_status` is not evidence of success — the artifact check is part of the flow,
not an optional extra.

---

## Claude Code Configuration

**Where these files physically live.** The workspace root is not a git repository, so the
real files sit in `architect-setup-.../workspace-config/` and `.../.claude/skills/`. The root
`CLAUDE.md` and the path-scoped rules are symlinked at the workspace root; `core.md`, the seats,
the process skills and the hooks are symlinked at user scope (`~/.claude/{rules,agents,skills,hooks}`)
so they also load in sessions started inside a project. `tools/link_user_scope.sh` recreates the
user-scope links. Editing either path edits the same file; never replace a symlink with a copy.

What loads, and the ceilings `tools/context_budget.py` enforces (DECISION-026):

| Layer | Loads | Ceiling (bytes) | Contents |
|---|---|---|---|
| `~/.claude/CLAUDE.md` | every session; not in seats | 1,024 | English only; home quota |
| root `CLAUDE.md` | sessions under the workspace; not in seats | 3,072 | environment, governance gate, where things live |
| `~/.claude/rules/core.md` | every session; not in seats | 9,216 | 11 invariants + "when to load which process" |
| path-scoped rules | when a matching file is read, also in seats | none | `python`, `shell`, `r`, `enzymefinder`, `bileaciddb`, `codebase-navigation` (`projects/**`) |
| memory index `MEMORY.md` | main session (seats: not measured) | 6,656, ≤ 60 entries | one-line pointers |
| skill descriptions | every session | 512 each | what + when + boundary |
| skill bodies | on invoke, or preloaded by a seat | 15,360 each | process rules |
| project `CLAUDE.md` | when working in that project, also in seats | none | project facts only |
| `docs/history/` | never | none | retired rule text, `rule-index.md`, `rule-map.tsv` |

**Subagents** (15 seats in `workspace-config/agents/`; list them with `ls`). Every seat sets
`omitClaudeMd: true`, an explicit model, effort and `maxTurns`, and preloads its skills; seats
have no `Skill` tool. Their shared Environment block (`workspace-config/seat-environment.md`)
carries the invariants they need, since `core.md` never reaches them.

| Seat | Model / effort | Preloads | Role |
|---|---|---|---|
| implementer | sonnet / medium | verification-patterns, completion-check | code tasks; replaces general-purpose |
| investigator | sonnet / medium | verification-patterns | ad hoc questions, web research |
| critic-reviewer | opus / medium | verification-patterns, completion-check | correctness review |
| domain-reviewer | opus / high | scientific-evidence | domain-role review |
| anomaly-hunter | opus / high | scientific-evidence | reopens settled results |
| figure-auditor | opus / medium | scientific-evidence | rendered-figure audit |
| security-specialist | opus / high | — | release/publication gate |
| alignment-officer | sonnet / medium | — | scope delivered vs promised (`memory: project`) |
| docs-sync | sonnet / medium | — | governance-doc drift, read-only |
| inventory-auditor | sonnet / medium | — | does it already exist |
| pragmatism-officer | sonnet / medium | — | proportionality triage (`memory: project`) |
| lean-critic | sonnet / medium | ponytail:ponytail (plugin), thermo-nuclear-code-quality-review, verification-patterns | debloat review; always in plan-critique and wave-review (owner, 2026-10-16) |
| research-scout | sonnet / medium | — | best-practice check while brainstorming |
| scc-monitor | haiku / medium | running-sge-jobs | SGE job diagnosis |
| retro-officer | sonnet / medium | — | last wave-end step: appends worked / did not / proposals to `docs/retros/retro-log.md` |

Dispatch rules live in skill `dispatch-brief`, the wave roster in `wave-review`.

**Hooks** (`workspace-config/hooks/`, registered in `~/.claude/settings.json`): `bash_guard.py`
(PreToolUse) denies `git stash`, `--work-tree` checkout, recursive `rm` under `projects/`
outside caches and scratch, and pytest with `$JOB_ID` unset; it warns on `cat` of files over
1 MB, `find` from `/` or home without `-maxdepth`, and `find -delete` under `projects/`.
`context_nudge.py` (UserPromptSubmit) nudges from 300k at a task boundary (a commit since the
last prompt, or 30+ min idle) and firmly from 500k, once per 100k band and again after a
compaction. `large-change-check.py` (Stop). Auto-compaction window 650k (DECISION-028); idle
compaction is live. The rtk hook was retired (DECISION-026).

**Enforcement** vs **guidance**: rules and `CLAUDE.md` shape behaviour but are advisory.
Anything that must hold every time is a hook in `~/.claude/settings.json`.

**Skills**: process skills (`dispatch-brief`, `wave-review`, `plan-critique`,
`verification-patterns`, `scientific-evidence`, `running-sge-jobs`, `completion-check`) and the
vendored `thermo-nuclear-code-quality-review` at user scope; `council`, `storm`, `ccusage`,
`caveman` and `workspace-audit` at the workspace root; EnzymeFinder domain skills in
`projects/EnzymeFinder/.claude/skills/`, on demand there. Plugin skills come from
`superpowers`, `pyright-lsp` and `ponytail`; `diagram-design`, `hookify` and
`pr-review-toolkit` are disabled. `example-skills`, `research-skills` and
`planning-with-files` are parked — disabled, still on disk; see
`.claude/context/parked-extensions.md`.

**MCP**: `.mcp.json` defines `graphify-enzymefinder`, currently disabled — it served a
cached graph that went stale after every rebuild. Use the graphify CLI, which reads from
disk (EnzymeFinder only; code-only graph of `src/` and `scripts/`). The graph itself rebuilds on every commit via a `post-commit` hook, at zero token
cost. See [.claude/rules/codebase-navigation.md](.claude/rules/codebase-navigation.md).

---

## Key Architectural Decisions

| Decision | Rationale |
|---|---|
| Always-loaded text kept to CLAUDE.md + `core.md`; process detail in skills | ≈ 125 KB → ≈ 20 KB; rule text was 80 % of a seat's first call (DECISION-026) |
| Path-scoped `.claude/rules/` over one large CLAUDE.md | Instructions load only where they apply; adherence degrades in long files |
| Named seats with preloaded skills, not general-purpose agents | Seat first call ≈ 12k tokens vs ≈ 50k; an agent that cannot be invoked is worse than none |
| Hooks for invariants, prose for judgment | Advisory rules were violated repeatedly; hooks are deterministic |
| Phase-based project docs | Scoped and self-contained per phase |
| Human-in-the-loop on governance and outward-facing actions | Safety and auditability |
| SCC defaults in one skill (`running-sge-jobs`) | Prevents ad-hoc resource drift |
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

- `~/.claude/rules/core.md` — invariants; [.claude/rules/](.claude/rules/) — path-scoped language and
  project rules; process skills in the config repo's `.claude/skills/`; retired rule text in its
  `docs/history/`
- [DECISIONS.md](DECISIONS.md) — workspace-wide decision log
