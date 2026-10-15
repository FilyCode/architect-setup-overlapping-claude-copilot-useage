# Workspace Claude setup restructure — design

**Date:** 2026-10-14 · **Status:** v2, revised after critique wave · **Owner:** Philipp Trollmann
**Scope:** `/projectnb/liu-scc/philipp` workspace config: this repo's `workspace-config/` and
`.claude/skills/`, `~/.claude/settings.json`, `~/.claude/CLAUDE.md`, auto memory. Project repos only
where a workspace file points into them.
**Reviews:** `docs/superpowers/reviews/2026-10-14-restructure/` — critic-reviewer, domain-reviewer
(agent-harness / prompt-engineering role), anomaly-hunter, alignment-officer, inventory-auditor,
pragmatism-officer. Finding IDs below are `seat:F#`.

## 1. Intent

- **Outcome:** keep the evidence discipline; cut what every session and every subagent pays for;
  make the rules that matter actually fire.
- **Owner's words:** reduce token use majorly; shift rules into skills; optimise personas; slim
  documents; restructure the setup; aggressive budget, but do not cut anything important.
- **Owner decisions already made:** aggressive budget (moderate allowed); review waves become
  skills that a core line says when to run; rtk hook and lore removed; narratives move verbatim to
  `docs/history/`.
- **What this restructure can and cannot move (honest scope, anomaly:F3, domain close):**
  - It cuts the static load on every call. Measured effect of a ~30k-token cut on every call:
    **≈ −5.6 % of main-session cost, ≈ −20.5 % of subagent cost** (anomaly:F3, simulated over the
    transcript corpus). Subagents are the larger arena, so this is worth doing.
  - Most main-session cost (≈ 69 % of cost units) sits in calls above 500k context. That lever is
    behaviour (clearing, compacting, handing long work to seats), not config. This spec adds one
    core line and a measurement for it (§5.7) and leaves the rest to owner question Q1.
  - Adherence is mostly a **mechanism** problem: of six "rule existed and was not followed"
    incidents, one was burial in a long file; three were fixed by a mechanism (anomaly:F6). So:
    slimming is for cost, hooks and structure are for adherence.

## 2. Measured baseline (2026-10-14)

Unit: **bytes** for files; tokens only where measured from transcript `usage`. The bytes→tokens ratio
on this text is ≈ 3.0 bytes/token (regression, n = 755 subagents; one within-version check gave 2.44),
not 4 (anomaly:F1).

| Quantity | Value | Source |
|---|---|---|
| Main session, first-call context | 77.6k–100.0k tokens (8 sessions); grew 78.5k → 100k in four weeks, ≈ 14k of that ours, most of the rest MCP connector attachments (deferred tools 5.4 → 16.1 KB, MCP instructions 2.2 → 6.2 KB) | transcripts; anomaly:F7 |
| Our always-loaded text | ≈ 125 KB ≈ 41k tokens: subagent-dispatch.md 54.8 KB, verification.md 45.8 KB, MEMORY.md 14.1 KB, scc.md 5.4 KB, CLAUDE.md ×2 2.4 KB, plus agent descriptions (3.6 KB ours) | `wc -c`; instructions attachment |
| Share of first-call context that is ours | ≈ 41 % main, ≈ 80 % of a named review seat | anomaly:F1 |
| MEMORY.md in subagents | **yes — 757/757 subagent transcripts** carry it in the instructions attachment (docs say otherwise) | controller re-derivation; domain:F1, anomaly:F2 |
| Subagent spend by type | general-purpose **81.2 % of subagent context tokens** (n = 411 of 757); critic-reviewer 7.9 %, domain-reviewer 3.8 %, others < 2.5 % each. Cost-unit share 79 % (anomaly:F4) — a different column | controller re-derivation |
| General-purpose baseline not ours | ≈ 28k tokens (tool schemas, listings) vs 4.6k–7.0k for named seats | anomaly:F4 |
| Sessions start where | only `-projectnb-liu-scc-philipp` exists under `~/.claude/projects/` → all sessions start at the workspace root | `ls` |
| Where Claude runs | inside SGE job 8090063 on compute node `scc-yf3`, not a login node | critic:F6 |
| Plugins always-on (CLI estimate) | superpowers ≈ 840 (+ 3.7 KB SessionStart injection), pr-review-toolkit ≈ 2,035, diagram-design ≈ 416, ponytail ≈ 641 (off → 0 bytes injected, verified), hookify ≈ 294; synced account plugins ≈ 2.7k in descriptions | `claude plugin details` |

## 3. Premises from current Claude guidance — corrected per model

Each was checked against Anthropic's docs on 2026-10-14 (domain-reviewer re-checked all ten).

1. **Verification instructions are model-dependent (domain:F2, Blocking, fixed here).** Opus 5.x
   verifies unprompted; generic "verify / double-check" instructions over-verify there. Sonnet 5.5
   and Haiku 5.5 skip checks at low effort and Anthropic adds a verification paragraph for them.
   Three classes:
   - **Specific** — a strong model without this workspace could not have written it (`qacct
     exit_status 0` is not success; shell `grep` skips gitignored paths; `--cut_tc` gates tblout and
     domtblout differently). Keep everywhere.
   - **Method** — how to verify ("a gate counts only after you have seen it fail"; RED-proof module
     path). Models do not do this by default. Keep everywhere.
   - **Generic** — "verify before claiming done". Drop on Opus seats; keep one line plus the
     keep-working paragraph on Sonnet/Haiku seats.
2. **Emphasis:** no "CRITICAL/MUST"; at most one IMPORTANT line in core, added only after an eval shows
   that rule skipped.
3. **Explain why in one clause;** keep worked cases of ≤ 3 lines — numbers are what let a rule override
   the model's prior (domain:F6).
4. **Positive form,** except safety prohibitions.
5. **Delegation:** Opus 5 delegates readily; independent review at a boundary stays (code.claude.com
   best-practices "adversarial review step"); self-verification by subagent does not.
6. **Reviewers:** report everything, triage in a separate pass (platform Opus 5 page). Code
   best-practices says to tell reviewers to flag only correctness gaps; report-all plus
   pragmatism-officer satisfies both (domain:F10).
7. **Effort is per model:** Opus 5.5 at medium ≈ Opus 5 at high; Sonnet/Haiku seats at low skip
   checks → minimum medium (domain:F5).
8. **Agent frontmatter facts (docs + critic:F2/F3, unverified items marked):**
   - `omitClaudeMd: true` drops CLAUDE.md files and unscoped project rules; path rules still load on
     file touch. **Unverified: whether it drops the MEMORY.md attachment** → Phase 0 probe.
   - `skills:` preload injects the full body; a skill with `disable-model-invocation: true` **cannot**
     be preloaded (docs, verbatim) and is skipped silently. **Unverified: preload when `tools:` omits
     `Skill`** → Phase 0 probe.
   - Agent and skill discovery walks from the start directory up to the repository root; the workspace
     root is not a repo. Today all sessions start at the root, so root config loads. New skills go in
     the workspace `.claude/skills/` as now; a session started inside `projects/<name>` is a Phase 0
     probe (inv:F2, DECISION-010).
9. **Skills:** only name + description load at startup; every model-invocable description costs every
   turn. After compaction only the first 5,000 tokens of each invoked skill are re-attached (25k
   shared) → put rules first, examples after, worked cases in `reference/` (domain:F4).
10. **`CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS`** refuses the over-limit spawn with a do-not-retry message;
    it does not queue (critic:F4, domain:F3).

## 4. Approach

**B — core invariants always on; knowledge moves to skills; seats preload what they need; mechanisms
carry adherence.** A (trim in place) is too small; C (adopt an external stack) loses domain lessons.

**MOVE is separate from REWRITE (pragmatism §6).**
- **Rewrite** only what is always loaded: `core.md`, root `CLAUDE.md`, `~/.claude/CLAUDE.md`, the
  memory index, seat bodies. That is where the tokens are.
- **Move skill bodies verbatim** (light headings, split to fit the 5k-token compaction window).
  Skill bodies load rarely; rewriting them saves little and risks meaning — this workspace's rule text
  has carried errors twice after confident rewrites (TC–NC).
- Any rewrite of a lesson is read old-beside-new by a review seat before commit.

## 5. Design

### 5.1 Layers and budget

| Layer | Loads | Ceiling (bytes) | Contents |
|---|---|---|---|
| `~/.claude/CLAUDE.md` | every session + non-omitting subagents | 1 KB | English only; home quota |
| root `CLAUDE.md` | same | 3 KB | environment, governance gate, where things live |
| `rules/core.md` (no `paths`) | same | 9 KB | §5.2 |
| path-scoped rules | on matching files | unchanged | bileaciddb, enzymefinder, codebase-navigation, python, r, shell |
| MEMORY.md index | main **and every subagent** (measured) | 5 KB, ≤ 50 one-line entries | pointers only |
| skill descriptions (ours) | every turn | 0.5 KB each | what + when + boundary clause |
| skill bodies | on invoke / preload | ≤ 15 KB each, rules first | §5.3 |
| `docs/history/` | never auto | — | verbatim narratives + `rule-index.md` (old title → new home) |

Ceiling for our always-loaded text ≈ **20 KB (≈ 6.5k tokens)**, down from ≈ 125 KB. One budget
definition, enforced by `context_budget.py` (attribution of our files) and judged by
`measure_context.py` (gate of record: first-call context from transcript attachments, which also sees
connectors, deferred tools and plugin injections our files cannot) — critic:F12, anomaly:F7.

### 5.2 `core.md` — always on

Selection test: *would an ordinary session make a costly mistake without this line, and is it not
default model behaviour?* Draft:

1. **Evidence:** an artifact on disk is evidence; an exit code or a narrative is not. Check its mtime
   against the change. A gate counts only after you have seen it fail.
2. **Third state:** unknown is its own typed state, never `bool | None`; list every consumer when you
   introduce one.
3. **Absence and counts:** `command grep` for absence (shell `grep` skips gitignored paths); a parser,
   not grep, for counts; an absence is only as good as the instrument's headroom in that stratum.
4. **Figures:** a relayed number carries its n, its column and its artifact; numbers from plans or
   subagent reports are unverified until re-derived.
5. **SGE:** never run pytest or long work outside an SGE job (`$JOB_ID` unset). The caller owns every
   `qsub`; wait in one backgrounded loop with a deadline; verify the output artifact. Details:
   `running-sge-jobs`.
6. **Shared git trees:** commit with explicit paths, then `git show --stat`; read past commits with
   `git show <c>:<path>`; no `git stash` or `--work-tree` checkout in a shared tree. Recovery recipe:
   `dispatch-brief`. (Worktree isolation is **not** adopted — critic:F1.)
7. **Scratch and outputs:** scratch in the session scratchpad, namespaced per agent; delete only files
   you created, by name; output directories are read-only to reviewers; never create files under
   `tests/` outside your task; no `--write` tool or `cp` onto tracked files in a shared tree.
8. **When to load which process** (one line each): dispatching an implementer or review seat →
   `dispatch-brief`; before Task 1 of an architectural plan → `plan-critique`; wave end → `wave-review`;
   third failed fix or a known-heavy problem → escalation section of `plan-critique`; release or
   publication → security-specialist; new project or reframing → one external premise check, and
   `command grep` `.superpowers/` for prior work before any research dispatch; self-verification is
   not independent review.
9. **Scope:** deliver what was asked; change only what the task needs and match the surrounding style;
   report unrelated dead code instead of deleting it; a fix that belongs in a file you do not own
   becomes a dispatched task, not a comment. (Karpathy "surgical changes" folded here — §5.9.)
10. **Context hygiene:** clear between unrelated tasks; compact deliberately with an instruction; hand
    long investigations to a seat rather than reading them into the main session.
11. **Governance:** `ARCHITECTURE.md`, `DECISIONS.md`, `CLAUDE.md`, `PROJECT_STATE.md`, pushes, issues
    and CI need explicit approval.

### 5.3 Skills (workspace `.claude/skills/`, symlinked from this repo as today)

All seven are model-invocable (no `disable-model-invocation`) so core can trigger them and seats can
preload them. Descriptions open with the situation, list trigger phrases, end with a boundary clause
naming the sibling (domain:F6/F7).

| Skill | Trigger | Preloaded into | Content (moved verbatim unless noted) |
|---|---|---|---|
| `dispatch-brief` | dispatching an implementer or review seat (not every Task) | implementer | **delta over superpowers SDD templates** (inv:F5): verify-or-UNVERIFIED, stop rule, contradiction slot, lossy-summary line, file ownership + commit recovery, env-invariants block, caller owns qsub (submit = job spec in report), brief at dispatch time, model/effort table **per model**, **the review-dispatch template** (findings file first, ranked areas, HEAD start/end, minor-triage test, objection slot, remove-the-guard) so ad hoc reviews keep it (critic:F8) |
| `wave-review` | wave end; `/wave-review` | — | roster by wave type, seat-count line (lean-critic not default; anomaly-hunter skipped on bug-fix-only waves), batching under the concurrency cap ("refused = re-dispatch; close lists ran / not-ran per seat"), integration seat, pragmatism last, quiet tree for suite runs, "no negative control" close line, clean-worktree baseline |
| `plan-critique` | before Task 1; `/plan-critique` | — | wave sizing, Calibration block + hard-gate triggers, plan preflight = **wire `projects/EnzymeFinder/scripts/check_citations.py`** (inv), tests-in-brief-are-drafts, three-state at plan time, research-questions file, plan-writing inventory dispatch, escalation wave |
| `verification-patterns` | description match | critic-reviewer, lean-critic, **implementer** (critic:F9) | the shapes catalogue incl. positive-control corollary and the three general lessons from the rtk section (match command as invoked; convenient fixture proves nothing; check the aggregate's distribution) — critic:F10 |
| `scientific-evidence` | description match | domain-reviewer, anomaly-hunter, figure-auditor | instrument headroom, both branches, attack confirming results, composition effects, two-report filtering, metric triple-check; bio worked cases in `reference/` |
| `running-sge-jobs` | qsub, SGE, job | scc-monitor | scc.md body; **fix the listing-form wait loop (no deadline, never exits on `Eqw`)** (domain:F6) |
| `completion-check` | `/completion-check`; "is this finished / does it run" | critic-reviewer, implementer | stub scan (`pass`, `NotImplementedError`, `TODO`, `except: return []/None`, `shortcut:`), `ruff` unused-code rules, **generalised `audit_reachability.py` from EnzymeFinder** (not vulture — rejected in EF W10 because test references count as use; inv:F3), **run the changed entry point on a real downsampled fixture** (align:F3), silent-failure checklist (from pr-review-toolkit). `mutmut`/`diff-cover` deferred (D3) |

Unchanged: `caveman`, `ccusage`, `council`, `storm`. `workspace-audit` gains the budget check, the
upstream-drift check for vendored skills, and drops its superseded "40 lines" prose budget (inv:F5).
`thermo-nuclear-code-quality-review` (vendored 2026-10-14) **drops `disable-model-invocation`** in a
local frontmatter override so it can be preloaded (critic:F2) — the only edit to the vendored file,
recorded in its `SOURCE.md`. `rtk` skill retired.

### 5.4 Seats

Every seat: `omitClaudeMd: true` (subject to Phase 0), explicit `effort`, preloads per §5.3, and an
env block: venv path, scratchpad, read-only outputs, no files under `tests/`, `command grep`, report a
job spec instead of submitting, no `--write`/`cp` onto tracked files, `git show <c>:<path>`, HEAD and
status at start and end (domain:F8). Sonnet/Haiku seats carry the keep-working-until-done paragraph and
one generic verification line (domain:F2/F5).

| Seat | Model / effort | Change |
|---|---|---|
| **implementer (new, named)** | sonnet / medium (opus / medium for cross-cutting) | replaces general-purpose for SDD tasks: `tools:` allowlist, preloads `dispatch-brief`, `verification-patterns`, `completion-check`. Largest measured lever (anomaly:F4) |
| critic-reviewer | opus / medium | item 7 (simplicity) kept but shortened; item 5 (docs-sync reminder) moves to `wave-review`; pointers to skills |
| domain-reviewer | opus / high | — |
| anomaly-hunter | opus / high | remove the verbatim rtk block |
| alignment-officer | sonnet / medium | boundary vs docs-sync: *scope delivered vs promised*; no `verification-patterns` preload (align:F4) |
| docs-sync | sonnet / medium | boundary: *governance docs vs reality*; |
| inventory-auditor | sonnet / medium | stays "does it already exist?" only (align:F2) |
| pragmatism-officer | sonnet / medium | **gains the ponytail ladder at plan stage** (need it? exists? stdlib? native? installed dep? one line?) — it already owns proportionality |
| lean-critic (new) | sonnet / medium | **on demand**, not in the default roster until yield data exist; preloads thermo-nuclear + verification-patterns; `tools` include `Skill` so it can run `/ponytail-review`; guard: never cuts trust-boundary validation, data-loss handling or evidence rules — the guard is why it exists beside code-simplifier/ponytail-audit (inv:F7) |
| figure-auditor | opus / medium | — |
| security-specialist | opus / high | — |
| research-scout | sonnet / medium (from haiku/low) | add Anthropic's search line |
| scc-monitor | haiku / medium | preload `running-sge-jobs`; fix pointer |

Persona merges are decided from a **seat-yield tabulation** over the last 3–5 waves (unique,
acted-on findings per seat), not now (anomaly:F5, align:F4).

### 5.5 Hooks and settings

Constraints on every hook (critic:F6/F7, inv:F9, domain:F8): command-type only; a tokenising parser,
not a regex over the raw string; versioned under `workspace-config/hooks/` and symlinked like
`large-change-check.py`; demonstrated blocking its target, passing near-misses, **firing inside a
subagent**, and replayed over the real transcript corpus (DECISION-024 method). Warn first; block only:
- `git stash push|save|pop` and `git --work-tree … checkout` in project repos (not `git stash list`;
  match `git -C <dir> stash` too);
- `pytest` / `python -m pytest` when `$JOB_ID` is unset (not `qsub … pytest`);
- `rm -rf`/`rm -fr`/`\rm` with `-r` under `projects/` (warn only on `find -delete`).
The "warn on commit without `--`" hook is dropped: it nudges toward the second sweep hazard.

Settings: remove the rtk `PreToolUse` hook (supersedes DECISION-025; retire `rtk_selftest.sh`); add
`env.CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS` at the smaller account's cap (2) as a backstop; prune
allowlists to recurring patterns; keep the Stop hook; ponytail stays `defaultMode: off`.

### 5.6 Documents and governance

- `docs/history/` + `rule-index.md` mapping every old item title to its new home — the answer for the
  100+ historical citations (D1). Live pointers are updated: 4 agent files, `rules/{python,shell}.md`,
  root `CLAUDE.md`, `projects/EnzymeFinder/.claude/CLAUDE.md`, EF `running-quality-gates` skill,
  `projects/EanB_homologue_search/CLAUDE.md`, this repo's `CLAUDE.md` (also: rules *do* auto-load;
  11 agents not 10).
- `DECISION-026` (restructure, supersedes DECISION-025) and `ARCHITECTURE.md` update — approval needed.
  `DECISIONS.md`/`ARCHITECTURE.md` are not auto-loaded; no slimming needed for tokens (align).
- Memory: index to ≤ 50 one-line entries; delete entries duplicating rules; fix
  `feedback_subagent_dispatch` (completion notifications exist; its blocking `qstat -j` loop contradicts
  "caller owns qsub" — critic:F5).
- Root `PROJECT_STATE.md`: stale since 2026-06-10 — owner Q4.
- Vendored skill exception and parked plugins: as recorded in v1 (thermo-nuclear has no Claude
  marketplace of its own; the three parked plugins need reinstall + disable by the owner — the
  classifier blocked it in session).
- Workspace root clutter listed for the owner; delete only on approval.

### 5.7 Measurement

- `measure_context.py` (gate of record): first-call context and per-call context distribution by
  session and agent type from transcript `usage` + `attachment` sizes; reuses the hook's transcript
  reader (inv). Reports the share of calls above 500k and what tools they ran.
- `context_budget.py`: bytes of our always-loaded files and skill descriptions vs §5.1 ceilings; also
  flags skill bodies over 15 KB.

### 5.8 Writing standard for rewritten (always-loaded) text

- One rule per bullet, imperative, present tense, "— because <one clause>" where it helps.
- Narratives go to history; a worked case of ≤ 3 lines may stay, in `<example>` tags.
- No CAPS; at most one IMPORTANT in core, only after an eval shows that rule skipped.
- Positive form except safety prohibitions; one glossary (*seat, wave, brief, artifact, gate, third
  state*).
- Grammatical, terse English; caveman compression is not used for instructions.
- Demonstrated by domain-reviewer on three real sections: 6,978 → 2,856 bytes (−59 %) with one clause
  of precision at risk, kept.

### 5.9 Dispositions for the owner's other asks

- **Karpathy guidelines:** not installed as a file (overlaps core, superpowers and ponytail; competes
  with the budget). "Surgical changes" and "report dead code, don't delete" folded into core item 9;
  "state assumptions / ask when ambiguous" is already harness behaviour.
- **Ponytail persona:** plan stage → pragmatism-officer ladder; code stage → lean-critic on demand,
  which may call `/ponytail-review`; `/ponytail-audit` available ad hoc.
- **pstack:** not installed (routing hook competes with superpowers); thermo-nuclear vendored.
- **Codex loop:** out of scope (no subscription).
- **code-modernization:** out of scope — built for legacy-estate rewrites with proof of behavioural
  equivalence; our repos are active Python, not legacy; `/modernize-assess` can be run ad hoc on
  EnzymeFinder once if wanted.
- **Humanizers / document skills (account-synced, owner manages on desktop):** papers use the owner's
  `science-writing-edit` first, `humanizer` as a de-AI checklist pass, then a numbers-and-citations diff
  against the original. Disable `humanize-kit` (detector evasion conflicts with journal AI-use
  disclosure policies; adds a SessionStart hook). `writing-skills`: keep plain-language,
  orwells-rules, google-dev-docs; disable the character voices (~1k tokens of descriptions).
  `bio-research`: keep only if nf-core / scvi skills get used.

## 6. Calibration

- **Vision context:** the harness layer for every project here. Not responsible for project
  correctness; responsible for making the right lesson available at the right moment at least cost.
- **Realistic target:** our always-loaded text ≈ 125 KB → ≈ 20 KB; ≈ −5 % main-session cost and
  ≈ −20 % subagent cost from that cut, more for general-purpose work moved to the implementer seat;
  eval behaviour no worse (§7).
- **General vs our limits:** skill selection by description is a documented general limit
  (platform skills best-practices). Stochastic behaviour limits what k = 5 evals can show — general.
  Budget overrun, duplicated layers, stale memory, missing mechanisms — ours.
- **Standard:** Anthropic: CLAUDE.md files < 200 lines, SKILL.md < 500 lines, progressive disclosure,
  no aggressive emphasis. We beat it by enforcing the ceiling with a script and measuring in
  transcripts.
- **Does the standard already do this?** `/doctor prompt-audit` (in 2.1.299) proposes cuts — run it as
  input in Phase 2. `claude-md-management` is not installed.
- **Thresholds:** byte ceilings are declared workspace-specific, from the 200-line guidance and our
  measured line length; revisit after one week of `measure_context.py`.

## 7. Acceptance

1. **Traceability:** unit = every heading, bold-lead and top-level bullet of the three old files (186
   by alignment-officer's extractor). A script asserts each maps to exactly one destination (core line,
   skill section, hook, history, or "deleted: default behaviour" with reason) and renders
   `docs/history/rule-index.md`.
2. **Behavioural evals:** 8–10 scenarios — the six incident-derived cases from anomaly:F6 plus two
   negatives (an ordinary edit must not load `wave-review`; claiming done on a small fix loads ≤ 1
   skill) and one "6 seats in, 6 reports out". k ≥ 5 runs per arm; "before" arm captured in Phase 0 on
   the untouched config, same account. Pass: after ≥ before − 1 per scenario. Runner is a job spec the
   caller submits.
3. **Budget:** `context_budget.py` passes; `measure_context.py` after one week shows the reduction on
   real sessions, per agent type.
4. **Hooks:** each meets every §5.5 constraint.
5. **Rewrites:** every rewritten lesson read old-beside-new by a seat.

## 8. Phasing

- **Phase 0 — probes, no config change:** throwaway `omitClaudeMd` agent (MEMORY.md attachment? rules?
  preload without `Skill` in tools?); a PreToolUse hook firing inside a subagent; one `count_tokens`
  call; connectors on/off first-call diff (double-send hypothesis, anomaly); a session started in an EF
  directory; what the > 500k calls were doing; capture the "before" eval arm; seat-yield tabulation.
- **Phase 1 — low-risk wins, no lesson relocated:** memory compress + fixes; rtk hook removal +
  DECISION-026; env var; allowlists; seat frontmatter (effort, model, env block, boundary sentences);
  named implementer; the two scripts; hooks warn-first; false statements in CLAUDE.md files.
- **Phase 2 — rule migration:** traceability script first; history move; skills (verbatim); `core.md`
  and CLAUDE.md rewrite; live pointers; evals; old files retired only after the evals pass.
- **Phase 3:** lean-critic, completion-check tooling, thermo override, writing-skill recommendations,
  owner Q3.

## 9. Risks

| Risk | Mitigation |
|---|---|
| A moved lesson does not load when needed | core "when" lines (item 8); preloads; evals incl. negatives; Phase 0 load-path probes |
| Rewrite changes a lesson's meaning | move verbatim; rewrite only always-loaded text; old-beside-new review |
| `omitClaudeMd` seats lose context they need | env block; dispatch passes project paths; path rules load on touch; Phase 0 probe before adoption |
| Skills overtrigger / collide with superpowers | narrow descriptions with boundary clauses; negative evals; D6 |
| Concurrency cap silently drops seats | batching line + ran/not-ran close |
| Hooks block legitimate work | §5.5 constraints, warn-first, corpus replay |

## 10. Known issues and deferred (triaged 2026-10-14, pragmatism-officer)

- **D1 Historical citations** (100+ files cite the old rule files): records of what was true; not
  rewritten. `docs/history/rule-index.md` maps titles to new homes. Revisit only if a script parses
  them.
- **D2 EnzymeFinder project skills overlap** (`submitting-scc-jobs` vs `running-sge-jobs`;
  `running-quality-gates` vs `wave-review`): project scope; add to EF backlog; revisit if one wins
  wrongly in an EF session.
- **D3 `mutmut` and `diff-cover`:** not installed, CPU-heavy, no measured yield, new external tools
  trigger the Calibration hard gate. Revisit after Phase 3's stub scan / reachability / smoke run have
  served one real wave.
- **D4 Slimming the three largest seat bodies** (security-specialist 8.2 KB, anomaly-hunter 7.0 KB,
  domain-reviewer 5.7 KB): load only on dispatch; ≈ 2–3k tokens each. Revisit with yield data.
- **D5 Context-size nudge hook:** the lever is real (≈ 69 % of main cost above 500k context) but its
  design depends on what those calls do — Phase 0 measures it; owner Q1.
- **D6 superpowers `verification-before-completion`** overlaps at "done": plugin-owned; decide from the
  "≤ 1 skill on small-fix done" eval after Phase 2.

## 11. Owner questions

- **Q1 Metric and scope:** (A) static baseline only; (B) A + named implementer + seat count per wave +
  context-hygiene line and measurement — **recommended, and what this spec now does**; (C) B + a
  context-size nudge hook now. And: is the meter you care about the usage limit or cost?
- **Q2 Global `effortLevel: high`** on Opus 5.5: keep / medium / per project. Recommended: trial medium,
  judged on the eval set.
- **Q3 pr-review-toolkit** (≈ 2k tokens every session): decide at end of Phase 3 once
  `completion-check` carries the silent-failure checklist.
- **Q4 Root `PROJECT_STATE.md`:** archive and point CLAUDE.md to project state files — recommended.
- **Q5 (only if Phase 0 shows double-sent connector deltas):** disable unused claude.ai connectors.

## Amendments after execution (2026-10-15)

Recorded by the wave-end review (`docs/superpowers/reviews/2026-10-14-restructure/wave-end-review.md`).

- **lean-critic** ships without the `Skill` tool and without the `/ponytail-review` clause
  (§5.4, §5.9): adopted from `agent-seat-review.md`. Ponytail stays reachable from the main
  session (`/ponytail-review`), not from the seat.
- **MEMORY.md ceiling** is 6,656 B and 60 entries, not 5 KB and 50 (§5.1, §5.6): executor ruling
  (Task 4) after the 13 rule-duplicate entries were dropped; owner to ratify.
- **`core.md` and the seats, process skills and hooks** are linked at user scope
  (`~/.claude/`), not at the workspace root: a session started inside a project loaded neither
  the root's agents/skills (Phase 0 P4) nor its rules (verified 2026-10-14). Recreated by
  `tools/link_user_scope.sh`.
- **New seat `investigator`** (ad hoc questions; replaces general-purpose for them).
- **Seats see project rules**: `omitClaudeMd` drops launch-time CLAUDE.md only; a seat's first
  project read attaches the project CLAUDE.md and path-scoped rules. `core.md` never reaches a
  seat, so the seat Environment block carries the invariants seats need.
- **Seat first-call context** is ≈ 12k tokens (n = 20 interactive seats), not the 4,772 of the
  Phase 0 probe.
