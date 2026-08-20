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

### [2026-08-17] [DECISION-016]: Remove the evidence-before-completion Stop hook (DECISION-013 superseded)

**Change**: The prompt-based `Stop` hook added in DECISION-013 is removed from
`~/.claude/settings.json`. `.claude/rules/verification.md` remains as the only mechanism —
advisory, not enforced.

**Rationale**: Every single run of the hook failed with "Hook evaluator API error ... model
(haiku) ... may not exist or you may not have access to it" — 100% failure rate, all
session, both with an explicit `"model": "haiku"` and with the field omitted (the omitted
case still resolved to haiku internally, confirmed by the identical error text, so the
default was already the cheap model — this was never a cost problem). The failure is in the
hook evaluator's own access path, not a config choice; no `availableModels` restriction or
`ANTHROPIC_DEFAULT_HAIKU_MODEL` override was found to explain it, and normal chat calls to
haiku via `--model haiku` succeed. A `hook_non_blocking_error` never blocked a turn, but its
stderr surfaced in every session — pure noise for zero enforcement, the opposite of the
intended effect.

**Impact**: Chat noise stops. The evidence-before-completion rule is advisory again, same as
before DECISION-013. Revisit if the hook evaluator's haiku access is ever fixed upstream —
the hook config itself was correct schema-wise and can be restored by re-adding the `Stop`
block removed here.

---

### [2026-08-17] [DECISION-017]: Replace it with a deterministic, size-gated check

**Change**: A command-type `Stop` hook replaces
the removed prompt hook. No model call, so it cannot fail the way DECISION-016 describes.
It reads the transcript's tail, measures the current turn (files touched, characters
changed via Edit/Write/MultiEdit), and is a silent no-op below 4 files / ~4,000 changed
characters. Above that threshold, it checks `last_assistant_message` against a completion-
claim regex and an evidence-signal regex (test counts, exit codes, qacct/qstat, file:line
refs, fenced code blocks); if it reads as a bare claim with no evidence signal nearby, it
exits 2 and sends the turn back with what to point to. Any exception anywhere in the script
exits 0 — a broken check must never become a new source of spurious blocking.

The script lives in `workspace-config/hooks/large-change-check.py`, symlinked to
`~/.claude/hooks/large-change-check.py` — same pattern as DECISION-015, so this piece of
config is version-controlled too rather than repeating that gap for a new file.

**Rationale**: The user asked for something cheap that only checks after large changes, not
every small thing. Gating by size cannot be done in hook config — `Stop` supports neither a
`matcher` nor an `if` field — so the gate lives inside the script itself, which is why it
must be fast: measured at 42-52ms against real session transcripts, including a 3.9MB one,
comparable to the rtk `PreToolUse` hook's own 55ms median. Validated offline against 5
synthetic scenarios (small/no-claim, large/bare-claim, large/with-evidence, unreadable
transcript, large/no-claim-language) before being wired into the live session.

**Impact**: Small turns cost nothing — same as before DECISION-013 ever existed. Large turns
get a real, working check, at the cost of one extra turn only when it actually fires.
Traded semantic judgment (what the broken LLM evaluator would have done, had it worked) for
keyword heuristics that cannot silently fail — matches recorded shapes in
`.claude/rules/verification.md` only approximately, and can misfire on phrasing in both
directions. Acceptable tradeoff per the user's explicit choice over the log-only alternative.

---

### [2026-08-18] [DECISION-018]: Second-round audit — subagent memory, external-scan step, doc drift cleanup

**Change**: Verified (against the live current docs at `code.claude.com`, not a third-party
repo's claim) that Claude Code subagents support a `memory: user|project|local` frontmatter
field for persistent, cross-invocation memory separate from main-session auto-memory,
plus `maxTurns`, `disallowedTools`, `effort`, `color`. Added `memory: project` to
`scc-monitor` so recurring SGE failure signatures accumulate instead of resetting every
invocation, and `maxTurns: 40` to `critic-reviewer` as insurance against a runaway opus
review loop. Extended the `workspace-audit` skill with a new optional step 6 ("External
scan") covering Anthropic doc/model changes and new repos/plugins, addressing a real gap:
the skill only ever looked inward. Fixed a stale model pin (`claude-sonnet-4-6`) left in
the shared repo's own `.claude/settings.json` since the DECISION-009 dual-tool era, a dead
permission entry for the deleted `.claude/bin/claude` binary, a dead `AGENTS.md` reference
in this workspace's own governance list (archived under DECISION-011), the missing
`bileaciddb.md` row in ARCHITECTURE.md's rule table, and dead `ROADMAP.md` links in the
"Related Documents" footers of this file and ARCHITECTURE.md — `ROADMAP.md` was planned in
DECISION-002 but per DECISION-015 was deliberately never moved/created; the historical
decision text recording that is left untouched, only the current-state footer links (which
implied the file exists) were removed.

**Not changed**: `~/.claude/settings.json`'s `autoMode.environment` block still describes
the workspace root as having "no remotes configured" and assumes a single repo, which is
wrong — the workspace root holds multiple independent project git repos (see DECISION-021
for the corrected, verified count), each pushing to a private `FilyCode/*` GitHub remote.
An edit attempt was blocked by the Claude Code auto-mode classifier (self-modification of
trust/permission config); left for the user to fix directly or explicitly re-authorize.

**Also researched, not adopted**: `getagentseal/codeburn` (multi-tool usage tracker —
redundant with the already-installed `ccusage` skill while only Claude Code is in active
use) and `dietrichgebert/ponytail` (active minimalism nudge — overlaps existing
`simplify`/`code-review` skills and this workspace's own CLAUDE.md philosophy). Full
itemized findings from `shanraisshan/claude-code-best-practice` in
`.claude/context/repo-research-2026-08-18.md`.

**Impact**: `scc-monitor` should get measurably better at repeat-pattern diagnosis over
time; `critic-reviewer` has a safety bound it didn't have before; the monthly audit process
now has an external-facing half instead of only checking its own drift; five small
doc-accuracy gaps closed. The `autoMode.environment` staleness remains open.

---

### [2026-08-18] [DECISION-019]: Expand the agent roster; make review additive, not manual-only

**Problem**: The user has been manually asking for `critic-reviewer` after each wave of
work. Superpowers' own `requesting-code-review` skill always dispatches a generic
`general-purpose` subagent with its own bundled template — it has no concept of this
workspace's named agents and never will, since editing the plugin's own skill files
would silently fork from upstream (the same anti-pattern documented three times already
in `learnings.md`). Separately, the old DECISION-001 12-agent topology had a
`Context Engineer` whose job — detecting drift between actual work and `ARCHITECTURE.md`/
governance docs — has no equivalent today, and this very audit found exactly that kind
of drift by hand (stale table rows, dead cross-references) three separate times this
month.

**Change**: Added two new project-scope agents and one new always-on rule file, rather
than editing the plugin:

- `docs-sync` (sonnet, `memory: project`, read-only) — a trimmed revival of the old
  Context Engineer's actual job (detect doc/reality drift, propose exact fixes) without
  its PR-based workflow or `.github/` assumptions, which don't fit how this workspace
  actually operates. Never edits governance files directly — same approval gate as
  everything else.
- `research-scout` (haiku, `effort: low`) — a deliberately cheap, single-agent
  best-practices/alternatives check for brainstorming, distinct from a full multi-agent
  research fan-out (the pattern this session itself used for the repo-research task
  earlier today, which is not meant to run on every design decision).
- `.claude/rules/subagent-dispatch.md` (new always-on rule) — states when to dispatch
  which agent (wave-end: `critic-reviewer` + `alignment-officer` + `docs-sync` in
  parallel, additive to superpowers' generic reviewer, not a replacement for it;
  brainstorming: `research-scout` for non-trivial decisions only) and a model/effort
  tiering table for **any** subagent dispatch, not just the named agents.

**Why the tiering table, and why it can only be guidance**: Claude Code subagents default
to `model: inherit` unless a dispatch sets otherwise. Superpowers' own SKILL.md files are
procedural markdown with no programmatic model/effort control — confirmed against the
actual `requesting-code-review` and `subagent-driven-development` skill sources, not
assumed. This means every `general-purpose` worker superpowers spawns silently inherits
whatever the parent session is running (e.g. every micro-task review at opus if the main
session is on opus), a real, community-documented limitation of the framework, not a
Claude Code bug. Claude Code itself has no hook-level mechanism to force a model
selection on a dispatch, so the tiering table is prose guidance like the rest of this
workspace's rules — it depends on being applied each time, same limitation already
recorded for every other non-hook rule here.

**Tested before committing to it**: `skills: [simplify]` preload on `critic-reviewer` was
tried and confirmed (via a live dispatch, not assumed) to silently do nothing — native
skills aren't resolvable through that mechanism, at least not `simplify`. Reverted; the
manual "Simplicity and reuse" checklist item added earlier today (before this entry)
remains the actual working fix for that gap.

**Not changed**: `alignment-officer` gained `memory: project` for the same accumulation
rationale as `scc-monitor`. `critic-reviewer` deliberately did **not** get a `memory`
field — its entire value is re-deriving correctness fresh from source each time; cached
"patterns" would work against that design.

**Impact**: Wave-end review no longer depends on the user remembering to ask for it —
codified in a rule, though rules remain guidance, not a hard gate. Adds real per-wave
cost (up to 3 additional subagent dispatches instead of 0-1); the tiering table is the
counterweight, aimed at keeping that cost proportionate rather than eliminating it.

---

### [2026-08-18] [DECISION-020]: Remove `memory` from `docs-sync` — the grant is unscoped and unrevokable

**Problem**: `docs-sync` (added in DECISION-019) was given `memory: project` on the same
reasoning as `scc-monitor`/`alignment-officer`. Its core value proposition, unlike
theirs, was framed as a **hard** guarantee — "never edits governance files directly."
Live-tested (not assumed): a `memory`-enabled subagent's Write/Edit tools worked on an
arbitrary file with no restriction to the memory directory, no block, no prompt. Adding
`disallowedTools: Write, Edit` alongside `memory` was tested as a fix and also failed to
revoke the grant. Full writeup in `.claude/context/learnings.md`.

**Change**: Removed `memory` from `docs-sync` entirely, restoring `tools: Read, Grep,
Glob, Bash` as the complete tool set — no Write/Edit exist for this agent at all now.
Traded the recurring-drift-pattern accumulation benefit for keeping the guarantee this
agent was specifically built to provide. `alignment-officer` and `scc-monitor` keep
`memory: project` unchanged — their existing prose constraints ("do not write
implementation code," "never change source") were never claiming a harder guarantee than
the rest of this workspace's advisory rules, so this finding doesn't newly weaken them.

**Also verified same session**: the GSD/GSTACK frameworks raised as a possible
superpowers replacement are real, but switching was declined — the actual gap (no native
model/effort routing) was already closed via DECISION-019's tiering rule, which works
regardless of skill framework. Independently confirmed GSD's creator ran a crypto-token
rug-pull and the original repo was archived 2026-06-26 — a real trust/security finding,
not taken on the word of the source that raised it. Full detail:
`.claude/context/repo-research-2026-08-18.md`. `workspace-audit`'s external-scan step now
also checks a candidate tool's maintainer/trust status, not just technical fit.

**Impact**: `docs-sync` is read-only in fact, not just in its own prompt. One documented,
reusable finding (`memory` + `disallowedTools` interaction) that would otherwise have
been silently wrong the next time anyone reached for this pattern.

---

### [2026-08-18] [DECISION-021]: Correct a hardcoded "two repos" assumption — caught by the user

**Problem**: DECISION-018 and a `~/.claude/settings.json` fix both asserted "two real
repos (architect-setup-overlapping-claude-copilot-useage, projects/EnzymeFinder)" under
the workspace root. The user caught this as misleading: more project repos already exist
and more get added over time.

**Verified** (`git remote -v` across every `projects/*/` directory, not assumed): the
workspace root actually holds — the shared config repo, plus `projects/Bile_acid_database`,
`CaMES_homologue_search`, `EanB_homologue_search`, `EnzymeFinder`, `K4-K26`, and
`Sulfotrans` (all with `FilyCode/*` GitHub remotes), plus `projects/MqnE_cofactor_finding`
(a git repo, no remote yet), plus `projects/TBI` (not a git repo at all).

**Change**: Corrected the `settings.json` line to state the general fact — check
per-directory, don't assume a fixed list — with the verified 2026-08-18 count included as
a snapshot, not a claim about the future. Corrected DECISION-018's text to point here
instead of repeating the wrong count.

**Impact**: A workspace-fact claim should either be phrased so it can't go stale (state
the general rule) or explicitly dated as a snapshot — not asserted as if it were a fixed
architectural constant, especially for something as fast-changing as "how many project
repos exist."

---

### [2026-08-18] [DECISION-022]: Security baseline — added `security-specialist`, closed an active credential-read gap, fixed EnzymeFinder CI

**Problem**: User asked for an end-of-project (pre-production/publication) security
checklist plus lighter ongoing dev-time enforcement, and explicitly asked for a
multi-agent brainstorm (best-practice research + security specialist + senior-dev
critique) to find gaps in a draft. Initial scouting wrongly concluded EnzymeFinder has a
live FastAPI server; a `critic-reviewer` validation pass (dispatched via `Workflow`,
`agentType: critic-reviewer`) caught this and two other wrong premises before anything
was finalized — full verdict cited below, not summarized from memory.

**Corrected premises** (re-derived from live source, not assumed):
- No project has a built web/API/DB-with-users surface. EnzymeFinder's P14a REST API and
  Bile_acid_database's public launch are both planned, not built — `fastapi` isn't even a
  dependency anywhere. Confirmed by the user separately: EnzymeFinder → software app now,
  web use later; Bile_acid_database → public webservice later; the other 6 projects are
  publication pipelines only, no web surface planned, but still must never carry secrets.
- EnzymeFinder already runs real security automation this design didn't credit:
  `.pre-commit-config.yaml` (bandit, detect-private-key), `.github/workflows/secret-scan.yml`
  (gitleaks), `.github/workflows/codeql.yml` (CodeQL weekly), and a bandit CI job.
- **A currently-active gap, not a future one**: the `permissions.deny` credential-read
  block (blocking `.env`/`*.pem`/`*credentials*`/`secrets/**`) existed only in the shared
  config repo's own `.claude/settings.json` — which only applies when a session's trust
  root IS that repo. Verified Claude Code does not cascade settings across directory
  levels (fetched from `code.claude.com/docs/en/settings`, not assumed). This session's
  actual trust root (the workspace root) and all 8 project repos had **no deny block at
  all** — confirmed via grep across every `.claude/settings.json` in the workspace. Fixed
  immediately: added the same deny block to the workspace root's `.claude/settings.json`
  and to all 8 project repos' `.claude/settings.json` (backups kept only for the 3 repos
  where the file isn't git-tracked: `K4-K26`, `MqnE_cofactor_finding`, `TBI`).
- **`settings.local.json` pre-approved `Bash(git push *)` with no permission prompt**,
  directly contradicting `CLAUDE.md`'s own "pushing needs explicit approval" rule — every
  push-confirmation in this workspace's history was this session's own conversational
  discipline, not anything technically enforced. User chose to remove it (asked, not
  assumed) — `git push` now goes through a real prompt.
- The one incident that actually happened (`.ncbi/api_key`) predates `secret-scan.yml`
  entirely and would not have been caught by it — GitHub's `gitleaks-action` scans a
  push's new commits, not full history. The manual hash-comparison method used at the
  time remains the only thing that actually caught it.

**Change**: Added `security-specialist` (opus, `maxTurns: 25`, no `memory`, report-only)
as a release/publication-gate agent — deliberately not wave-end, not an always-on rule,
and not a separate gate skill (`critic-reviewer` argued convincingly for cutting both of
those: their entire function is 3-4 sentences, already covered by `subagent-dispatch.md`
and by `critic-reviewer`'s own item 6). Registered it there instead, alongside a
corrected, context-specific checklist: the original 19-item consumer-SaaS list's biggest
gap was **prompt injection / agent trust boundary** — this workspace runs an LLM with
broad Bash/Python access ingesting untrusted `WebFetch`/NCBI/KEGG content, which the
original checklist didn't address at all despite covering session cookies. Added:
supply-chain/CI pinning, key rotation runbook, data-licence compliance (real blocker for
Bile_acid_database's HMDB-derived data), denial-of-wallet framing (not just login
rate-limiting — the realistic abuse target for a public scientific API is expensive
queries), SSRF, PHI handling, backup/integrity. De-prioritized (not deleted): password
KDF, session cookies, bot-protection-on-signup, RLS — a public **read-only** API/DB
plausibly has no accounts at all; the agent's Step 1 checks this before applying them.

**Fixed in EnzymeFinder's CI** (approved explicitly, since CLAUDE.md gates touching CI):
wired `pip-audit` into `ci.yml`'s security job — it was already declared in
`pyproject.toml:71`'s `[dev]` extras and never invoked anywhere; SHA-pinned
`actions/checkout`, `actions/setup-python`, `github/codeql-action/{init,analyze}`,
`actions/upload-artifact`, and `gitleaks/gitleaks-action` in `codeql.yml`/`secret-scan.yml`
(resolved via `gh api` against the real tags, not guessed — `codeql-action@v3` and
`gitleaks-action@v2` are both annotated tags, dereferenced to their actual commit SHAs);
added top-level `permissions: contents: read` to `ci.yml` and `secret-scan.yml`
(`codeql.yml` already had job-scoped permissions).

**Not done**: `research-scout`'s recommendation of Gitleaks+TruffleHog as a dual
pre-commit/CI gate was not adopted wholesale — gitleaks is already in place; TruffleHog
and a pre-push full-history scan (to actually catch what CI's incremental scan can't)
remain open for a future session. `osv-scanner` for future non-Python dependencies
(R/Bioconductor) not evaluated. `CLAUDE.md`/`ARCHITECTURE.md`'s agent list and rule count
were also stale (listed 3 of 6 agents, "2 always-on" vs actual 3) — fixed as part of this
round since `critic-reviewer` flagged them in the same pass.

**Impact**: One active security gap (workspace-wide credential-read protection) closed
immediately rather than left as a future design item — found only because a validation
pass re-derived the claim instead of trusting the plan's own narrative, which is exactly
the failure shape `verification.md` exists to catch. `security-specialist` is real but
intentionally low-cost today (most runs terminate at "not applicable" until a web
surface exists) and does real work once P14a or Bile_acid_database's launch lands.

---

### [2026-08-20] [DECISION-023]: Added a `SubagentStop` hook to nudge docs-sync after a clean critic-reviewer pass

**Superseded by DECISION-024 the same day** — the hook described below was found broken
and reverted. Read this entry as history of what was tried and why, not as current state.

**Problem**: User reported recurring documentation drift — governance docs going stale
because dispatching `docs-sync` after a wave depends on the main session remembering the
prose rule in `subagent-dispatch.md`, with nothing enforcing it. Also asked me to
research `ruvnet/ruflo` as a possible framework adoption.

**ruflo**: dispatched to `research-scout` (haiku). Verdict: skip. It's a general-purpose
agent meta-harness (vector memory, multi-agent swarms, cross-LLM federation) solving
problems this workspace doesn't have — the 6 purpose-built agents already outperform 100
generic ones for our specific gate points. Consistent with the earlier GSD/GSTACK
rejection (DECISION-021/022 area): heavier frameworks keep getting evaluated and
correctly declined in favor of the lightweight, purpose-built dispatch system already in
place.

**docs-sync nudge — brainstormed via `superpowers:brainstorming` (bounded path)**:
classified bounded (existing hook pattern + existing rule file to extend, not a new
subsystem). Two decisions made with the user: (1) trigger scoped to `critic-reviewer`
only, not `alignment-officer` too — one docs-sync dispatch per wave is enough, and
critic-reviewer is the agent that always runs; (2) soft non-blocking nudge, not a hard
block — `SubagentStop`'s exit-2 block prevents the *subagent itself* from stopping (per
the Claude Code hooks schema, confirmed by grepping the installed CLI binary for the
`SubagentStop`/`agent_type`/`hookSpecificOutput` strings and cross-checking against the
full settings.json JSON schema returned by the `update-config` skill), not the parent
session — the wrong target, since critic-reviewer has no `Agent` tool to dispatch
docs-sync with anyway.

**A WebFetch summary of `code.claude.com/docs/en/hooks` was not trusted at face value**:
it read suspiciously fluent (invented an undocumented `PostToolBatch`/`TaskCompleted`
framing, an exact `last_assistant_message` field name) — WebFetch summarizes through a
small model that can hallucinate specifics. Verified independently by grepping the
installed `claude` binary's strings for the real event/field names before building
anything on top of the claim, per this workspace's own verification discipline.

**Built**: `workspace-config/hooks/docs-sync-nudge.py` (symlinked into
`~/.claude/hooks/`, same pattern as `large-change-check.py`), registered in
`~/.claude/settings.json` under `hooks.SubagentStop` with `matcher: "critic-reviewer"`.
Deterministic keyword heuristic (no API calls) parses the subagent's closing message
(falling back to tailing `transcript_path` if `last_assistant_message` is absent) for a
clean-verdict pattern, and suppresses the nudge if issue-indicating language is also
present. **A real bug was caught during pipe-testing**: the issue-word list included the
bare word "blocking", which also fired on the negated phrase "no blocking issues found",
silently suppressing the nudge on a genuinely clean review. Fixed by reusing
`large-change-check.py`'s own negation-window technique (an issue-word match only counts
if not preceded within ~25 chars by a negation word). Re-tested against a clean-verdict
case, an issues-found case, a wrong-`agent_type` case, and malformed/empty input — all
behave as intended.

`subagent-dispatch.md`'s wave-end review section updated with a note describing the hook
as a backstop, not a replacement for the prose rule.

**Not yet done**: a live end-to-end smoke test (an actual `critic-reviewer` dispatch,
confirming the `additionalContext` really surfaces in the parent session's next turn) —
flagged to the user as the one part of this design that couldn't be fully verified
through static analysis alone.

---

### [2026-08-20] [DECISION-024]: Reverted the DECISION-023 `SubagentStop` hook — replaced with a one-line agent-side reminder

**Problem**: dispatched a real `critic-reviewer` review of DECISION-023's own new hook
(`docs-sync-nudge.py`) as the promised live smoke test. It came back CHANGES REQUIRED
with two blocking findings, both re-derived from real artifacts rather than from the
hook's own docstring:

**B1 (verified independently, not taken on faith — and re-verified a second time after a
follow-up review flagged the first count as unreproducible)**: the `ISSUE_RE`/
`NEGATION_RE` negation-window technique, copied from `large-change-check.py`, does not
transfer to review prose. Real reviews negate *after* the keyword or by count —
`"0 Blocking"`, `"Blocking: none"`, `"non-blocking"` — none of which the hook's
preceding-word negation check catches, since it only looks for a negator *before* the
match. The original review reported "0 of 16 genuinely clean reviews out of 47
review-shaped messages"; a later independent replay of the restored hook against the
real transcript corpus (`~/.claude/projects/*/*/subagents/agent-*.jsonl` — note the extra
`*/`, corrected from this entry's first draft, which had omitted the session-uuid level
and matched zero files) could not reproduce those exact counts under two reasonable
definitions, but got the same direction and conclusion: 0/7 fired on transcripts with an
explicit `Verdict: APPROVED` line, 0/10 fired when loosened to "APPROVED appears anywhere
in the final message" across all subagent types, plus one false-positive fire on a
`CHANGES REQUIRED` transcript — strengthening, not weakening, the case against the hook.
The cited negation phrasings themselves were confirmed present in real transcripts both
times. Treat "the heuristic never fires on a real clean review" as the verified claim;
treat any specific count before this correction as approximate.

**B2 (claimed the hook's `additionalContext` targets the subagent, not the parent,
based on decompiling the installed Claude Code binary)**: live-tested this directly
rather than trusting either the original docstring's assumption or the review's
counter-claim. Swapped the hook for a version that unconditionally emits a unique marker
string, dispatched a trivial `critic-reviewer` (haiku) task, then grepped every relevant
transcript for the marker. Result was **inconclusive, not confirmatory of B2**: the
marker appeared in neither the subagent's own transcript nor cleanly in the parent's (the
two "hits" in the parent transcript were self-referential — my own `Write` and `grep`
commands echoing the search string back, not an injected context block). The test was
also confounded by the hook firing once on an unrelated internal event
(`agent_type: ""`, tied to a `ScheduleWakeup` check-in) despite the `critic-reviewer`
matcher, which overwrote the capture file before the real dispatch's payload could be
inspected. Whether `additionalContext` reaches the parent or the subagent on a genuine
named-agent completion remains unsettled from this session; not worth a second smoke
test since B1 alone already kills the design.

**Decision**: adopted the review's own "optional" alternative instead of trying to patch
the regex. Deleted `hooks/docs-sync-nudge.py` (both the repo copy and the
`~/.claude/hooks/` symlink) and the `hooks.SubagentStop` entry in `~/.claude/settings.json`.
Added one line to `agents/critic-reviewer.md`'s Output section instead: on an APPROVED
verdict, close with a reminder to consider dispatching docs-sync. This needs no regex, no
transcript parsing, and no question about hook delivery targets — the reminder travels
through the ordinary Task/Agent result, exactly the way critic-reviewer's review text
always has.

**Also observed, not chased further**: the smoke-test critic-reviewer (haiku) subagent's
own transcript showed repeated "waiting for task content" / "standing by" turns instead
of doing the one assigned action — an anomaly in that dispatch, not something this
decision depends on resolving.

**Impact**: caught before the hook could cause real harm — it had only fired once for a
real critic-reviewer completion (a CHANGES REQUIRED verdict, correctly silent either way)
before this reversal. Reinforces `verification.md`'s point again: a live smoke test,
promised and actually run, is what caught a design that four synthetic pipe-tests and a
plausible-sounding docstring both missed.

---

## Related Documents

- [ARCHITECTURE.md](ARCHITECTURE.md) — System design
- [PROJECT_STATE.md](PROJECT_STATE.md) — Current sprint
- [.claude/rules/](.claude/rules/) — Scheduler, storage, verification and language rules
