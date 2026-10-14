# Workspace Claude setup restructure — design

**Date:** 2026-10-14 · **Status:** DRAFT — pre critique wave · **Owner:** Philipp Trollmann
**Scope:** `/projectnb/liu-scc/philipp` workspace config (this repo's `workspace-config/`,
`.claude/skills/`, user `~/.claude/settings.json`, auto memory). Project repos are out of scope
except where a workspace file points into them.

## 1. Intent (as agreed in session 2026-10-14)

- **Outcome:** the same safety and evidence discipline at a fraction of the token cost, with
  rules Claude actually follows because they are no longer buried.
- **Owner's words:** reduce token use majorly; shift most of the rules into skills; slim and
  re-tune personas; slim documents; restructure how the setup is organised; aggressive budget,
  but do not cut anything important just to hit a number.
- **Decided:** aggressive always-loaded budget (moderate allowed where needed); review waves
  become skills that a core rule says when to run; rtk hook and lore removed; incident
  narratives move verbatim to `docs/history/`.
- **Assumptions (mine, open to correction):** the lessons themselves are correct and stay; the
  10 existing seats are kept unless the wave shows a merge is safe; the user's synced
  account plugins are managed on the desktop side, so we only recommend changes there.

## 2. Measured baseline (2026-10-14)

| Quantity | Value | How measured |
|---|---|---|
| Main session, context at first call | 77.6k–100.0k tokens (8 sessions) | `usage` in `~/.claude/projects/-projectnb-liu-scc-philipp/*.jsonl` |
| Subagent, context at first call | 49.6k–72.5k (8 subagents) | same, `*/subagents/*.jsonl` |
| Our always-loaded text | ~122 KB ≈ 30k tokens | `wc -c`: subagent-dispatch.md 54.8K, verification.md 45.8K, MEMORY.md 14.1K, scc.md 5.4K, CLAUDE.md ×2 2.4K |
| Long session total context | up to 1.83B tokens / 3,714 calls | same transcripts (mostly cache reads) |
| Plugins always-on (CLI `claude plugin details`) | superpowers ~840, pr-review-toolkit ~2,035, diagram-design ~416, ponytail ~641 (off → 0 injected), hookify ~294 | CLI estimate |
| Synced account plugins (skill descriptions only) | writing-skills ~1,050, bio-research ~710, writing-process ~450, humanize-kit ~370, humanizer ~90 | description chars / 4 |

`subagent-dispatch.md` is 752 lines and `verification.md` 553; Anthropic's guidance is under
200 lines per always-loaded file because longer files "consume more context and reduce
adherence" (code.claude.com/docs/en/memory).

## 3. What current Claude guidance changes about our premises

These come from Anthropic's own docs, read 2026-10-14, and each one touches a rule we hold:

1. **Over-verification.** Opus 5 "verifies its own work without being told to"; generic
   instructions such as "include a final verification step" or "use a subagent to verify"
   cause over-verification and should be removed (prompting-claude-opus-5). Self-correction
   prompts ("double-check", "re-verify") likewise add cost without improving results.
   → Keep our **specific** failure knowledge (which artifact, which instrument, which third
   state). Drop **generic** "verify before claiming" duplication: today it exists in
   CLAUDE.md, `verification.md`, superpowers `verification-before-completion`, and the Stop
   hook — four layers.
2. **Emphasis.** Current models overtrigger on aggressive language; "CRITICAL: You MUST" should
   become "Use X when…". If many lines are emphasised, none stands out (best-practices).
3. **Explain why, briefly.** Context or motivation behind an instruction improves targeting —
   one clause, not an incident report.
4. **Positive phrasing.** "Tell Claude what to do instead of what not to do."
5. **Subagents.** Opus 5 delegates readily; "do not use subagents to verify or double-check
   your own work". Independent review at a boundary is still endorsed (best-practices:
   adversarial review step). Deterministic caps exist:
   `CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS`, `CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH`.
6. **Reviewers.** Telling a reviewer "only report high severity" makes it report less; ask for
   everything and filter in a separate pass — this is exactly our pragmatism-officer pattern,
   so it stays.
7. **Effort.** `low`/`medium` are strong on Opus 5; use them liberally per seat.
8. **Agent frontmatter.** `omitClaudeMd: true` starts a subagent without CLAUDE.md files (path
   rules still load on matching files); `skills:` preloads full skill text; `isolation:
   worktree` gives an agent its own checkout; `effort`, `maxTurns`, `background` exist.
9. **Skills.** Only name + description load at startup; SKILL.md body under 500 lines;
   references one level deep; scripts are executed, not read; descriptions third person,
   what + when; no time-sensitive text in the body.
10. **Auto memory.** First 200 lines or 25 KB of `MEMORY.md` load in the main session only, not
    in subagents (forks excepted).

## 4. Approaches considered

| | Approach | Token win | Risk | Verdict |
|---|---|---|---|---|
| A | Trim prose in place, keep structure | ~8–10k | low | too small; keeps adherence problem |
| **B** | **Core invariants always on; knowledge as skills; seats preload only what they need** | **~22–25k main, ~20–25k per seat** | **medium: a lesson may not load when needed** | **recommended** |
| C | Adopt an external stack (pstack / ponytail-led) and drop custom rules | large | high: loses domain lessons no public stack has | rejected |

B's risk is controlled by §9 (traceability + behavioural evals).

## 5. Target architecture

### 5.1 Layers

| Layer | Loads when | Budget | Contents |
|---|---|---|---|
| L0 `~/.claude/CLAUDE.md` | every session, every non-omitting subagent | ≤ 15 lines | English only; home quota; nothing else |
| L1 root `CLAUDE.md` | same | ≤ 45 lines | environment, governance gate, where things live, which skill to load when |
| L1 `rules/core.md` (no `paths`) | same | ≤ 150 lines | the invariants (§5.2) |
| L2 path-scoped rules | on matching files | as today | bileaciddb, enzymefinder, codebase-navigation, python, r, shell — unchanged |
| L3 skills | on description match or explicit call; or preloaded into a seat | ≤ 500-line body each | §5.3 |
| L4 `docs/history/` | never auto | unlimited | verbatim incident narratives, linked as "why" |
| Memory index | main session only | ≤ 60 one-line entries | pointers; no duplicates of rules |

Target for L0+L1+memory index: **≤ 32 KB (~8k tokens)**, stretch ~24 KB (~6k). The number is a
ceiling enforced by a script (§5.6), not a goal to cut toward.

### 5.2 `core.md` — what stays always on

Selection test per line: *would Claude make a costly mistake in an ordinary session if this
line were absent, and is it not already default behaviour?* Draft contents:

1. **Evidence:** an artifact on disk, not an exit code or a narrative, is evidence; check mtime
   against the change. A gate counts only after you have seen it fail.
2. **Three-state values:** unknown is its own state — typed, never `bool | None`; list every
   consumer when introducing one.
3. **Absence claims:** use `command grep` (shell `grep` skips gitignored paths); use a parser,
   not grep, to count. An absence is only as good as the instrument's headroom in that stratum.
4. **Figures:** every relayed number carries its n, its column and its artifact; a number from
   a plan or a subagent report is unverified until re-derived.
5. **SCC:** never run pytest or anything >15 s on the login node — use `qsub`. The caller owns
   every `qsub` and waits in one backgrounded loop; verify the output artifact. Details: skill
   `running-sge-jobs`.
6. **Git in shared trees:** commit with explicit paths, then `git show --stat`; read past
   commits with `git show <c>:<path>`, never stash or `--work-tree` checkout in a shared tree.
   Concurrent implementers run in `isolation: worktree`.
7. **Scratch and outputs:** scratch in the session scratchpad, namespaced per agent; never
   `rm -rf` in a project tree; output directories are read-only to reviewers; never create
   files under `tests/` outside your own task.
8. **Process gates (when, not how):** before Task 1 of an architectural plan → `/plan-critique`;
   at wave end → `/wave-review`; any dispatch → build the brief with `dispatch-brief`.
9. **Scope:** deliver what was asked; a follow-up that belongs in a file you do not own becomes
   a dispatched task, not a comment.
10. **Governance:** `ARCHITECTURE.md`, `DECISIONS.md`, `CLAUDE.md`, `PROJECT_STATE.md`, pushes,
    issues and CI need explicit approval.

Everything else in today's two big files moves to a skill or to history (traceability §9.1).

### 5.3 Skills (new, in `.claude/skills/`, symlinked as today)

| Skill | Invoked by | Preloaded into | Source sections |
|---|---|---|---|
| `dispatch-brief` | any dispatch | — | dispatch claims (verify/UNVERIFIED, stop rule, contradiction slot, lossy-summary line), file ownership + commit recovery, env-invariants block, caller owns qsub, brief at dispatch time, model/effort table |
| `wave-review` | core rule at wave end; `/wave-review` | — | wave-end roster and when each seat runs, review-dispatch template (findings file first, ranked areas, HEAD-moves check, minor-triage test, objection slot, remove-the-guard), integration seat, pragmatism last, quiet tree for suite runs |
| `plan-critique` | core rule before Task 1; `/plan-critique` | — | plan review wave sizing, Calibration block + hard-gate triggers, plan preflight (execute plan claims), tests-in-brief-are-drafts, three-state at plan time, research questions file, escalation wave |
| `verification-patterns` | description match | critic-reviewer, lean-critic, alignment-officer | the "shapes" catalogue, grouped: stale artifacts · gates that cannot fail · tests and fixtures · counting · fixes and blast radius · claims that decay · generated docs |
| `scientific-evidence` | description match | domain-reviewer, anomaly-hunter, figure-auditor | instrument headroom, textbook premise may not close an anomaly, both branches, attack confirming results, composition effects, two-report filtering, metric triple-check, positive controls; bio worked examples in `reference/` |
| `running-sge-jobs` | description match (qsub, SGE, job) | scc-monitor | scc.md body: defaults, wait loop (listing form, 3 absences, deadline), log reading, storage |
| `completion-check` | description match; `/completion-check` | critic-reviewer | stub scan, reachability (import graph), `vulture`, `mutmut` on changed modules, `diff-cover`, silent-failure checklist; ships `scripts/` that run, not read |

Retired: `rtk` skill (with the hook). Kept unchanged: `caveman`, `ccusage`, `council`, `storm`,
`workspace-audit` (gains the budget check), `thermo-nuclear-code-quality-review` (vendored,
verbatim).

### 5.4 Seats (agents)

All review seats get `omitClaudeMd: true`, explicit `effort`, and a preloaded skill set, plus
a short "environment" block in the agent body (venv path, scratchpad, read-only outputs, no
files under `tests/`, `command grep`, report a job spec instead of submitting). Projected
saving ~20–25k tokens per seat.

| Seat | Model / effort (proposed) | Preloads | Change |
|---|---|---|---|
| critic-reviewer | opus / medium | verification-patterns, completion-check | points at skills instead of `rules/verification.md` |
| domain-reviewer | opus / high | scientific-evidence | — |
| anomaly-hunter | opus / high | scientific-evidence | — |
| alignment-officer | sonnet / medium | verification-patterns | — |
| docs-sync | sonnet / low | — | needs governance file paths in body |
| inventory-auditor | sonnet / medium | — | gains the ponytail "ladder" at plan stage (need? exists? stdlib? native? installed dep?) |
| pragmatism-officer | sonnet / medium | — | — |
| figure-auditor | opus / medium | scientific-evidence | — |
| security-specialist | opus / high | — | — |
| research-scout | sonnet / low (from haiku) | — | haiku too weak for synthesis — to be checked by the wave |
| scc-monitor | haiku / low | running-sge-jobs | — |
| **lean-critic (new)** | sonnet / medium | thermo-nuclear-code-quality-review, verification-patterns | wave-end debloat seat on the diff; reports line delta and deletion candidates; may call `/ponytail-review`; never cuts trust-boundary validation, data-loss handling or the evidence rules |

Per-task review: the default per task is the **fast gates** (lint on changed paths, the task's
own tests, `completion-check` stub scan), not extra agents. superpowers'
`subagent-driven-development` per-task reviewer pair stays available but is not mandated on top
of wave-end seats.

### 5.5 Hooks and settings

- Remove the rtk `PreToolUse` hook (binary stays for manual `rtk gain`); remove rtk lore
  everywhere.
- Keep the deterministic Stop hook.
- Add `env`: `CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS=3` — replaces the memory prose cap.
- Convert mechanical prose rules into hooks (hookify or plain `PreToolUse` scripts), each
  removing its text from core: block `git stash` and `git --work-tree … checkout` in project
  repos; block `rm -rf` under `/projectnb/liu-scc/philipp/projects`; block `pytest` when
  `hostname` is a login node; warn on `git commit` without `--` paths.
- Prune the allowlists to recurring patterns (drop one-offs, dead `rtk *`, `git stash *`).
- Ponytail installed with `defaultMode: off` (verified: 0 bytes injected when off, 3,266 when
  `full`).

### 5.6 Budget enforcement and measurement

- `scripts/context_budget.py`: sums the bytes of everything that loads at startup (CLAUDE.md
  chain, unscoped rules, first 200 lines of MEMORY.md, enabled skill descriptions) and fails
  above the ceiling. Run by `workspace-audit` and before any commit that touches the config.
  This is the structural fix for "every incident adds a paragraph and none are removed".
- `scripts/measure_context.py`: first-call context per session and per agent type from
  transcripts — the before/after metric.

### 5.7 Writing standard for every loaded file

- One rule per bullet, imperative, present tense; optionally "— because <one clause>".
- No dates, incident IDs, token counts or war stories in loaded text; link
  `docs/history/<file>.md` instead.
- No CAPS or "CRITICAL/MUST"; bold only the key term, at most one per section.
- Positive form ("do X"), except safety prohibitions.
- One glossary of terms used consistently: *seat, wave, brief, artifact, gate, third state*.
- Skills: third-person description with what + when; body ≤ 500 lines; references one level
  deep; scripts executed, not read.
- Grammatical but terse English. Caveman compression is not used in instructions: precision
  beats the last 20 % of tokens.

### 5.8 Documents and governance

- `docs/history/` with an index; each moved narrative keeps its original text.
- New `DECISION-026` (restructure) and an `ARCHITECTURE.md` update — approval required.
- Root `PROJECT_STATE.md` (last updated 2026-06-10) is stale but is still the pointer root
  `CLAUDE.md` uses. Proposal: CLAUDE.md points to each project's own state files instead;
  workspace `PROJECT_STATE.md` is archived. **Open — owner decides.**
- Memory: compress the index; delete entries that duplicate rules; fix
  `feedback_subagent_dispatch` (background completion notifications do exist).
- This repo's own `CLAUDE.md` says rules are "read on demand via prose references — no hook
  auto-injects any of them (verified 2026-09-06)". That is false for unscoped rules: this
  session's system context contains `scc.md`, `subagent-dispatch.md` and `verification.md`
  verbatim, matching the docs ("Every session"). Correct it in the same change.
- Vendored skills: `learnings.md` forbids hand-copying a skill that has an upstream
  marketplace. `thermo-nuclear-code-quality-review` is the justified exception — its upstream
  (`cursor/plugins`, MIT) ships it as a Cursor plugin only; the repo's Claude marketplace lists
  only `origin-apps`, and the sole Claude route (pstack-claude) brings a routing hook that
  competes with superpowers. `SOURCE.md` pins the SHA; `workspace-audit` gains an upstream-drift
  check.
- Parked plugins: `parked-extensions.md` records `example-skills`, `research-skills` and
  `planning-with-files` as *disabled, not uninstalled*, for instant re-enable. They were
  uninstalled in this session by mistake (zero token gain; disabled plugins cost nothing).
  Restore = reinstall + disable; the auto-mode classifier blocked doing it from the session, so
  the owner runs it.
- `pr-review-toolkit` costs ~2,035 tokens every session (six agent descriptions with long
  examples). Open: keep the plugin, or fold `silent-failure-hunter`'s checklist into
  `completion-check` and disable it.
- Workspace root clutter (`14F 14D:`, `.tmp_*`, `scratch_*`, `.bak`): list for owner, delete
  only on approval.

### 5.9 Writing and document skills (recommendations only; synced from the account)

- Papers: `science-writing-edit` (owner's own) first; `humanizer` (blader-based) as the de-AI
  checklist pass. Both preserve claims and numbers.
- `humanize-kit` targets AI-detector evasion and adds a SessionStart hook; not suited to
  academic submissions — recommend disabling.
- `writing-skills`: 17 styles, ~1k tokens of descriptions every session; keep plain-language,
  orwells-rules, google-dev-docs; disable the character voices.
- `bio-research`: its PubMed/bioRxiv MCPs duplicate connectors already present; keep only if
  nf-core / scvi skills get used.

## 6. Calibration

- **Vision context:** this layer serves every project's sessions on this workspace; it is the
  harness, not the science. It is not responsible for project-level correctness, only for
  making the right lesson available at the right moment at least cost.
- **Realistic target:** main first-call context −20k tokens or more; review seats −20k or more;
  zero lessons lost (traceability); unchanged behaviour on the eval scenarios.
- **General limits vs ours:** skill discovery depends on description matching — a general
  limit documented by Anthropic (skills best-practices: "Claude uses it to choose the right
  Skill from potentially 100+"). Everything else — budget overrun, duplicated layers, stale
  memory — is ours.
- **Standard:** Anthropic's guidance (CLAUDE.md < 200 lines/file; SKILL.md < 500 lines;
  progressive disclosure; no aggressive emphasis). Match it; beat it by enforcing the budget
  with a script, which the guidance does not provide.
- **Does the standard already do this?** `/doctor prompt-audit` proposes cuts to CLAUDE.md,
  rules, skills and agents — run it as an input to Task 1, not a replacement for the design.
  `claude-md-management` overlaps the same audit.
- **Thresholds:** 32 KB ceiling = declared workspace-specific (derived from the 200-line
  guidance × the two files we must keep, plus memory index); revisit after measurement.

## 7. Risks

| Risk | Mitigation |
|---|---|
| A lesson exists in a skill but does not load when needed | core keeps the "when" lines; evals (§9.2) test each moved lesson's trigger |
| `omitClaudeMd` seats lose project context they used to get implicitly | env block in each agent; dispatch passes project paths; path rules still load on file touch |
| Description-matched skills overtrigger (Opus 5 is proactive) | narrow descriptions; process skills invoked by core "when" lines |
| Worktree isolation breaks CWD-dependent tests | keep the clean-worktree baseline line in `wave-review` |
| Rewriting loses precise wording that carried meaning | verbatim history kept; traceability table cites the old line range per destination |
| Hooks block legitimate use | warn first, block only for stash / rm -rf / login-node pytest; each hook tested both ways |

## 8. Out of scope

Project repos' own CLAUDE.md files (lazy-loaded, 1–13 KB each); a Codex review loop (no
subscription); pstack install (conflicts with superpowers routing); code-modernization usage.

## 9. Acceptance

1. **Traceability:** every heading/bold-lead section of the old `subagent-dispatch.md`,
   `verification.md`, `scc.md` (114 headings/bold-lead items by heuristic — 63 / 42 / 9 — plus the plain bullets of the verification "shapes" list; the mapping script defines the exact unit) maps to exactly one destination (core line,
   skill section, hook, history, or "deleted: default behaviour" with reason). A script checks
   that the mapping covers every section.
2. **Behavioural evals:** 8 scenario prompts run headless before and after (e.g. dispatch an
   implementer; claim a gene is absent in a clade; submit a pytest run; review a diff that
   swallows an exception; close a wave). Each has a grep-able expected behaviour.
3. **Budget:** `context_budget.py` passes at ≤ 32 KB; `measure_context.py` shows the main and
   seat reductions on real sessions after one week.
4. **Hooks:** each new hook demonstrated blocking its target and passing a near-miss.
