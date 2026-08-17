# Decision Log: liu-scc (Workspace-Wide)

**Last updated**: 2026-05-06
**Format**: `[YYYY-MM-DD] [DECISION-XXX]: Title | Rationale | Impact`
**Scope**: Only workspace-wide decisions live here. Project-specific decisions live in `projects/<project>/DECISIONS.md` and `projects/<project>/phases/<phase>/DECISIONS.md`.

---

## Foundational Decisions

### [2026-04-03] [DECISION-001]: Adopt 12-agent system with Memory Curator and Context Engineer

**Rationale**: Original 10-agent system had no mechanism to capture session learnings into project memory, and no agent owned keeping docs synchronized. Two specialized agents close these gaps.

**Alternatives rejected**: Extending Architect to handle both (too many responsibilities); manual human curation (too slow).

**Impact**: Cleaner separation of concerns; session learnings preserved automatically; adds ~5min approval gate per release cycle.

---

### [2026-04-03] [DECISION-002]: Separate governance into 4 files per scope

**Files**: `PROJECT_STATE.md` (current sprint), `ROADMAP.md` (future), `DECISIONS.md` (why), `ARCHITECTURE.md` (how).

**Rationale**: A single file becomes cluttered; agents collide on writes; mixed scope makes it hard to distinguish sprint state from long-term design.

**Impact**: Each file has one clear owner; Memory Curator syncs PROJECT_STATE + DECISIONS; Context Engineer maintains ARCHITECTURE.

---

### [2026-04-03] [DECISION-003]: Three-tier memory system (session → project → workspace)

**Scopes**: Session (`/memories/session/`, transient); Project (`projects/<project>/phases/`, persistent); Workspace (`.github/` and root docs, persistent).

**Rationale**: Prevents scope mixing; session memory avoids context restarts; project memory avoids re-learning; workspace docs stay generic.

**Impact**: Sessions resume cleanly; project context always available; workspace docs stay lean.

---

### [2026-04-03] [DECISION-004]: Human-in-the-loop gates on AI-generated code

**Gates**: Critic + Alignment Officer sign-off → Release Gate PASS/FAIL → human approves before push; Memory Curator proposes, human approves before persistence.

**Rationale**: AI can generate insecure or incorrect code confidently; human review catches logic errors and security flaws; audit trail requires human sign-off.

**Impact**: Higher confidence in production code; clear accountability; slightly slower cycle time.

---

### [2026-04-03] [DECISION-005]: Enforce SCC defaults via `.github/SCC_PROFILE.md`

**Defaults**: Project `liu-scc`; 1 core (non-parallel); 4–28 cores (parallel); 8G/core memory; ≤12h runtime.

**Rationale**: Prevents resource waste; smaller requests place faster in SGE; single source of truth for all agents.

**Impact**: Faster job scheduling; reduced OOM/timeout failures; consistent across all agents.

---

### [2026-04-03] [DECISION-006]: Semantic commit messages with decision ID links

**Format**: `[ai-generated] <conventional commit> per DECISION-XXX`

**Rationale**: Provenance tracking (which decision drove each commit); easier debugging and compliance auditing.

**Impact**: Auditable change history; adds ~2min per commit for Commit Agent.

---

### [2026-04-03] [DECISION-007]: Token-efficiency baseline and model routing

**Routing**: Low complexity → low-cost model; Medium → balanced; High (architecture, security) → high-capability. Escalate when context is large, ambiguity remains, or cross-file design is needed.

**Impact**: Lower average cost without reducing review depth where it matters.

---

### [2026-04-04] [DECISION-008]: Project-local phases as canonical project memory

**Files**: `projects/<project>/phases/<phase>/PLAN.md`, `DECISIONS.md`, `ENGINEER_TASKS.md`, `SESSION_LOG.md`.

**Rationale**: Root workspace docs stay generic; project memory lives close to code; session memory gets curated into phase docs after review.

**Impact**: EnzymeFinder and future projects get a durable, scoped docs scaffold; workspace docs stay lean.

---

### [2026-05-05] [DECISION-009]: Shared Claude Code + GitHub Copilot instruction layer

**Structure**: `CLAUDE.md` at repo root (both tools read this); `.claude/prompt-snippets/` as shared content; `.claude/skills/` as shared skills; `.github/instructions/` as source of truth for path-scoped rules; `.claude/agents/` as thin wrappers pointing to `.github/agents/`.

**Rationale**: Avoids maintaining parallel instruction files; both tools pick up the same standards; thin wrappers minimize duplication.

**Impact**: One update propagates to both tools; slight wrapper overhead but no content drift.

---

## Pending Decisions

### [PENDING] Code ownership enforcement mechanism

**Question**: Pre-commit hook, linting rule, or manual review to prevent agents from editing each other's files?

**Recommendation**: Pre-commit hook (automated) + manual fallback in PRs.

---

### [PENDING] Memory Curator run frequency

**Question**: After every release, or batched weekly?

**Recommendation**: After every Release Gate pass — keeps memory fresh; benefits next session's context.

---

### [PENDING] Context Engineer trigger

**Question**: Automatic (after Critic flags style drift), manual, or scheduled?

**Recommendation**: Manual + weekly audit. Prevents noise; catches systematic drift.

---

### [2026-08-17] [DECISION-010]: Move workspace instructions to path-scoped `.claude/rules/`

**Change**: Root `CLAUDE.md` cut from ~70 lines to ~30. Content split into
`.claude/rules/{scc,verification}.md` (always-on) and
`.claude/rules/{python,shell,r,enzymefinder,codebase-navigation}.md` (path-scoped).

**Rationale**: An audit found the SCC profile — the least guessable and most expensive-to-miss
context in the workspace — was never loaded in a normal session. It was imported by a
CLAUDE.md sitting *below* the working directory, so it only entered context after touching a
file in that repo. Path-scoped rules load at launch and cost nothing where they don't apply.

**Impact**: SCC defaults now reachable everywhere. Always-on instruction bytes roughly halved.

---

### [2026-08-17] [DECISION-011]: Retire the 13-agent topology; keep three real subagents

**Change**: `.github/AGENTS.md` and the eight `.claude/agents/` thin wrappers archived to
`_archive/2026-08-17-agents/`. Three full definitions written at project scope:
`critic-reviewer`, `alignment-officer`, `scc-monitor`.

**Rationale**: None of the eight were ever loadable — they sat behind
`permissions.additionalDirectories`, which does not load agents. Meanwhile AGENTS.md declared
a gate ("no completion claim without Critic verdict and Alignment report") naming agents that
could not be invoked. Superpowers covers planning, TDD, review-request and verification;
what it does not cover is scope-conformance checking and SGE diagnosis. Model pins were also
two generations stale (`claude-sonnet-4-6`, `claude-opus-4-7`) and now use aliases.

**Impact**: The agents named in docs can actually be summoned. Ten roles retired.

---

### [2026-08-17] [DECISION-012]: Retire the GitHub Copilot instruction layer

**Change**: `.github/` (workspace and shared repo), `AGENTS.override.md`, and
`.claude/prompt-snippets/` archived to `_archive/2026-08-17-copilot-layer/`.
`.claude/rules/` is now the single source of truth.

**Rationale**: Copilot was dropped after its usage limits were cut. The mirror cost no
context but required hand-syncing every rule to a tool no longer in use, and had already
drifted. Everything is git-tracked and recoverable.

**Impact**: One instruction layer instead of two. Supersedes DECISION-008's dual-tool structure.

---

### [2026-08-17] [DECISION-013]: Enforce evidence-before-completion with a Stop hook

**Change**: A prompt-based `Stop` hook checks whether a turn claiming completion has
supporting evidence in the transcript. Advisory duplicates removed from prose.

**Rationale**: Six separate documented incidents of completion claimed on reasoning rather
than artifact — stale figures shipped after a fix, `qacct exit 0` for a job that produced no
structure, a comment describing a flag removal that never happened, a check structurally
incapable of firing. Each was already covered by a written rule. Prose is advisory; hooks are
deterministic.

**Impact**: The most-violated rule stops depending on Claude choosing to follow it.

---

### [2026-08-17] [DECISION-014]: GitHub issue board is no longer the status source of truth

**Change**: Documented in `projects/EnzymeFinder/.claude/CLAUDE.md`. No issues closed —
that decision is left to the human.

**Rationale**: Board last touched 2026-05-17 and covers P5/P6 work packages only. Real
tracking moved in-repo to `phases/`, `PLANS.md` and `AUDIT-*.md` docs with finding IDs in
commit messages. An abandoned tracker that still looks authoritative is a trap.

**Impact**: Status reads go to `PROJECT_STATE.md`. Board needs a human decision: reconcile or close.

---

### [2026-08-17] [DECISION-015]: Version-control the workspace root config via symlinks

**Change**: `CLAUDE.md`, `ARCHITECTURE.md`, `DECISIONS.md`, `.claude/rules/` and
`.claude/agents/` moved into `architect-setup-.../workspace-config/`. The workspace root now
holds symlinks to them.

**Rationale**: The workspace root is not a git repository. After DECISION-010 and 011 moved
the instruction layer there, the most important config in the setup had no version control,
no history and no rollback beyond `_archive/`. Committing both repos made this obvious: the
files that matter most appeared in neither commit. Claude Code resolves symlinks in
`.claude/rules/`, `.claude/agents/` and for `CLAUDE.md`, so loading is unchanged.

**Impact**: Config is versioned and diffable. Editing either path edits the same file.
Replacing a symlink with a copy would silently fork the two — the same failure mode as the
hand-copied skills in `learnings.md`.

**Not moved**: `PROJECT_STATE.md` and `ROADMAP.md` — they change often enough that tracking
them here would churn the config repo. Still unversioned; revisit if that matters.

---

## Related Documents

- [ARCHITECTURE.md](ARCHITECTURE.md) — System design
- [ROADMAP.md](ROADMAP.md) — Future phases
- [PROJECT_STATE.md](PROJECT_STATE.md) — Current sprint
- [.claude/rules/](.claude/rules/) — Scheduler, storage, verification and language rules
