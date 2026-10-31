# Learnings Log

Cross-project patterns promoted here once proven — not a dumping ground for one-off mistakes. Promotion bar: the same pattern recurs 3+ times across 2+ distinct tasks/projects. Below that bar, a pattern stays in personal session memory; above it, it belongs here so every project (and any agent working from this repo) inherits the fix instead of re-learning it.

Each entry: what recurred, why it happened, how to apply the fix. Delete or rewrite entries that turn out wrong — this file is a working tool, not an audit trail.

## SCC login-node process reaper kills long-running commands silently

**Recurred:** lost full pytest runs on the login node multiple times before the pattern was written down (EnzymeFinder).

**Why:** the SCC login node kills any process over ~30s CPU with no error message — looks like the command just never finished.

**Fix:** never run `pytest` or any process >~15s directly on the login node; always route through `qsub`. Full procedure: `.claude/context/runbook.md`.

## Hand-copied skill files go stale and shadow the real thing

**Recurred:** three times — (1) EnzymeFinder's 12 hand-copied superpowers skill stubs went undiscoverable and unnoticed for weeks; (2) 3 stub skills (`brainstorming`, `systematic-debugging`, `verification-before-completion`) shadowed the real 139-296 line superpowers-plugin versions under the same names; (3) `planning-with-files` was hand-copied into this repo at v2.37.0 and drifted 70+ releases behind the real upstream (`OthmanAdi/planning-with-files`, v3.8.1) before anyone noticed, found only during a 2026-07-23 audit.

**Why:** hand-copying a skill file feels like the fast path, but it silently forks from upstream — no update ever reaches it again, and if a plugin with the same skill name gets installed later, one copy shadows the other with no error.

**Fix:** before hand-copying any skill, check whether it has a real Claude Code plugin marketplace first (`gh api search/repositories` on the skill/tool name usually surfaces it, the way it did for `planning-with-files`'s 25,661-star upstream). If one exists, `claude plugin marketplace add` + `claude plugin install --scope user` it instead of copying files. Only hand-author skill files for genuinely custom, workspace-specific content with no upstream (e.g. `caveman`, `council`, `storm`).

## Watch item: search/changelog summaries have been wrong twice — not yet promoted

Once wrongly claimed superpowers "5.0.7 remains latest" against an actual 6.1.1 (caught via primary-source WebFetch); once conflated a whole 343-skill monorepo's CHANGELOG version with a single 4-skill bundle's own version inside it (caught by reading the marketplace manifest directly). Same root cause both times: summarized/derived version claims, not the primary manifest. Below the 3x bar for now — always verify a version claim against the actual manifest/registry file before acting on it, and promote this if it recurs once more.

## `permissions.additionalDirectories` does not load skills or agents

**Recurred:** twice — the 12 hand-copied superpowers skills in `projects/EnzymeFinder/.claude/skills/`
(2026-07-01), and the 8 `.claude/agents/` definitions in the shared repo, which were never
loadable in any session started at the workspace root and were only discovered during the
2026-08-17 audit. In between, `.github/AGENTS.md` declared a mandatory gate naming agents
that could not be invoked.

**Why:** `additionalDirectories` grants *file access*, not config discovery. Skills load from
that directory only on demand, when a file inside it is touched. Agents are resolved at
session start and never load from there at all.

**Fix:** agents belong in `.claude/agents/` at the project root or `~/.claude/agents/`.
Always verify a config actually loaded — `/context` for memory files, the available-agent
list for subagents — rather than assuming it did because the file exists.

## Prose rules do not hold; hooks do

**Recurred:** six documented incidents of completion claimed without evidence — stale figures
shipped after a fix landed, `qacct exit 0` for a ColabFold run that produced no structure, a
comment describing a flag removal that never happened, a join-detection check structurally
incapable of firing, a checkpoint silently dropping a field, a cached column reported as live.

**Why:** every one was already covered by a written rule. CLAUDE.md and rules are context, not
enforcement — the docs say so explicitly.

**Fix:** anything that must hold every time goes in a hook — but the guarantee depends on
what kind. A **command hook** (script/shell) is deterministic: the rtk `PreToolUse` hook (retired 2026-10-14,
DECISION-026) ran 2,100+ times this workspace's history with zero failures. A **prompt hook** adds a model
call in the loop, and that call can fail independently of the logic being sound: the
completion-evidence `Stop` hook added under DECISION-013 had a 100% API-error rate against
the evaluator's default fast model (haiku access failing in that specific code path, not a
config mistake — confirmed by testing both an explicit and an omitted `model` field) and was
removed the same day (DECISION-016). It produced zero real evaluations, only visible error
noise every turn — worse than the prose it replaced, which at least sometimes worked.

A read skill is not an applied one when a template carries the value: 2026-10-31, the SGE skill
was loaded before 424 of 435 joined jobs, yet 209 of 247 multi-slot jobs used under half their
cores, because K was copied from `train_refiner.qsub` and `f1_reference_runs_qsub.sh` (14 days:
9143 core-h reserved, 3242 used). Fix the template and gate the value (`qsub_guard`).

**Revised rule:** prefer a command hook for invariants when the check can be scripted at
all. Reach for a prompt hook only when the judgment genuinely needs a model, and verify it
is actually succeeding (check `hookEvent` + `type` in transcript attachments) before trusting
it as enforcement — don't assume a hook "holds" just because it's configured.

**Recurred 2026-10-21 (seat turn limits; EnzymeFinder, BileAcidDB, SenC, setup):** a turn-40
commit line in every implementer brief left the 60-turn hit rate at 22.0% (n=59) vs 21.9%
(n=64) before; seven proposals re-stated it in prose across five retro entries. The fix was
structural: raise `maxTurns` (eda994d). Measure a prose rule's effect before re-proposing it.

**Recurred 2026-10-28/29 (register and withdrawal rules; MeMES, SenC):** 5-6 retro entries
(R-20261028-3/-5, R-20261029-1/-3/-9 in both entries) report register close-or-carry and
withdrawal rules written as prose that never fired; only a gate did. **And a hook guards only
the path it matches:** the 2026-10-24 MEMORY.md guard matched Write|Edit, every index write
came through Bash, so it fired 0 times in 6 days (DECISION-030). Before trusting a guard, list
the routes a write actually takes in the transcripts.

## `memory:` on a subagent grants unrestricted Write/Edit — `disallowedTools` cannot revoke it

**Found:** 2026-08-18, while building `docs-sync`, a deliberately read-only agent meant to
propose governance-doc fixes without ever applying them itself.

**Why it matters:** Claude Code's own docs state `memory: user|project|local` "automatically
enables Read, Write, and Edit tools so the subagent can manage memory files." Tested
live, not assumed: a `memory`-enabled agent's Edit tool worked on an arbitrary file
completely outside its memory directory, no block, no permission prompt. Adding
`disallowedTools: Write, Edit` alongside `memory` did **not** revoke the grant either —
tested a second time, same result. There is currently no documented frontmatter
combination that gives a memory-enabled subagent a hard, tool-level read-only guarantee.

**Fix:** if an agent's core value is a technical (not prose) guarantee that it cannot
write outside a scope, do not give it `memory:` at all — the accumulation benefit is not
worth silently losing the guarantee. `docs-sync` ships with no `memory` field for exactly
this reason. Agents whose "don't touch X" was already prose-only before this (e.g.
`critic-reviewer`'s "do not edit source," `alignment-officer`'s "do not write
implementation code") are unaffected in practice — they were never claiming a harder
guarantee than the rest of this workspace's rules provide.

## Claims without a checked artifact recur until the brief carries the output

**Recurred:** controller-written claims (figures, state lines, absence claims) that were not
checked against an artifact: R-20261015-9, -12, -18, R-20261018-4 (BileAcidDB), R-20261019-7,
R-20261022-3 (MeMES), R-20261023-9, R-20261024-3 (EnzymeFinder): 8 entries, 3 projects. The
prose rule ("verified or UNVERIFIED") stood for 9 days unapplied; only the seats' "errors in this
brief" slot caught them.

**Fix:** the brief pastes command output (source, n, denominator), a pasted state line and a
pasted `command grep -rln` file list (dispatch-brief, 2026-10-24). See verification-patterns
"Plausibility is not provenance".

## A gate is accepted before anyone has seen it fail

**Recurred:** R-20261022-2 (MeMES), R-20261022-6, R-20261023-4, R-20261024-1 (EnzymeFinder):
acceptance harnesses and parity gates signed off without a planted fault. 4 entries, 2 projects.

**Fix:** the cheap form is to re-run the gate over an old artifact with one planted bad row and
quote the non-zero exit (core.md rule 1; verification-patterns).

## Audit trail

- **2026-07-23:** full workspace audit. Plugin versions checked against primary manifests (not changelog summaries): superpowers 6.1.1 = latest, example-skills and research-skills current. Found and fixed `planning-with-files` stale hand-copy (see entry above). No skill has sat provably unused 30+ days yet (too early to tell — this is the first audit). Added `permissions.deny` hardening to shared `settings.json`, wired `continuous-improvement.md` into `CLAUDE.md`, wired `.claude/settings.json` pointer files into 4 previously-unwired projects. Evaluated `research-ops-skills` and `K-Dense-AI/scientific-agent-skills` — both real, both skipped, no concrete active need yet.
- **2026-08-17:** full instruction-stack audit against current Anthropic docs plus 24 external
  repos. Adopted path-scoped `.claude/rules/` (DECISION-010); retired the 13-agent topology for
  3 real subagents (011); retired the Copilot layer (012); added the evidence Stop hook (013,
  removed same day as 016 — the hook evaluator's haiku access failed 100% of the time, pure
  noise for zero enforcement); recorded that the GitHub issue board is no longer authoritative
  (014). Memory consolidated
  35 files -> 18, with closed investigations moved into `projects/<p>/docs/history/`. Freed
  ~1.2 GB in home (superseded Claude versions) and 472 MB in project space (dead binaries).
  Installed `pyright-lsp` and `diagram-design`. Skipped ECC, SuperClaude, BMAD, Archon,
  claude-squad, claude-mem, headroom and OmniRoute -- each either duplicates something already
  in place or adds listing bloat this audit exists to remove.

**2026-10-21 (workspace-audit step 0 only).** Retro integration over 42 proposals (2026-10-15..20):
5 applied in eda994d (maxTurns raised; CLOSING check; 650k firm nudge; science-first seat
order; SGE host filters) plus the wave_stats turn-limit regex fix; 9 handed to projects; 3 left
open as cluster heads (R-20261016-3 measure_context table, R-20261019-1 measured rulings,
R-20261019-7 claims table). Setup check: lean-critic ran with ponytail preloaded in 10 of 13
reviews (misses: a session started before e30779a); nudge fires and is relayed but compaction
lags hours. `context_budget.py` fails on MEMORY.md (8,321 bytes > 6,656; >60 entries) — owner
to trim. Steps 1-6 not run. Evidence: `.superpowers/findings/2026-10-21/`.

**2026-10-24 (workspace-audit step 0 + token check 2).** Retro integration over 27 open
proposals: 10 applied in 5 edits (dispatch-brief claims sentence and 4-area cap; core.md rule 14
measured rulings; enzymefinder.md branch gates), 1 done earlier (R-20261023-5, eda994d), 16
deferred with triggers, 2 learnings promoted (above). R-20261024-6..9 arrived during the run and
stay open. Token check: DECISION-029 (main model pinned to opus-5-5; dispatch_guard and
memory_budget hooks). MEMORY.md trimmed to budget twice; old CLI versions 2.1.308/309 deleted
(home 5.4 → 4.9 GB). Evidence: `.superpowers/findings/2026-10-24/investigator-*.md`.

**2026-10-30 (workspace-audit steps 0-5 + token check 3).** `claude doctor`: no installation
issues (2.1.314). Retro: 19 open (2 more already applied: R-20261025-9, R-20261029-6); 6 applied
(dispatch-brief R-20261025-7, R-20261028-1, R-20261029-8, R-20261024-6; wave-review R-20261025-10;
scientific-evidence R-20261025-8; wave_stats R-20261029-2 in 1bd49eb), the rest deferred or handed
to their projects; R-20261029-1..5 were issued twice by two entries (IDs not unique). One learning
sub-line (above). DECISION-030: aim-keeper seat + aim_nudge, core rule 15 + ask_guard,
model_guard, memory guard on Bash, provenance sidecars, transcript move script. Home 5.6 of 10 GB
(transcripts 3.2 GB). Evidence: `.superpowers/findings/2026-10-30/investigator-*.md`.

**2026-10-31 (SGE audit + fix-round check).** 14 d accounting: 35% of reserved cores used; one
EC523 session 78% of the waste. `qsub_guard` hook + `tools/sge_efficiency.py`; running-sge-jobs
cores block; templates dispatched in EC523 and EnzymeFinder. Fix rounds did not fall: EF fix
commits per task 0.83 (P0, before 10-24) vs 0.67-1.62 after (n=5 waves; F1d had a fix repairing
the previous fix twice). Applied R-20261030-1/-9 (wave-review) and -4 (verification-patterns).
Evidence: `.superpowers/findings/2026-10-31/investigator-{sge-usage,fixrounds}.md`.
