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
what kind. A **command hook** (script/shell) is deterministic: the rtk `PreToolUse` hook has
run 2,100+ times this workspace's history with zero failures. A **prompt hook** adds a model
call in the loop, and that call can fail independently of the logic being sound: the
completion-evidence `Stop` hook added under DECISION-013 had a 100% API-error rate against
the evaluator's default fast model (haiku access failing in that specific code path, not a
config mistake — confirmed by testing both an explicit and an omitted `model` field) and was
removed the same day (DECISION-016). It produced zero real evaluations, only visible error
noise every turn — worse than the prose it replaced, which at least sometimes worked.

**Revised rule:** prefer a command hook for invariants when the check can be scripted at
all. Reach for a prompt hook only when the judgment genuinely needs a model, and verify it
is actually succeeding (check `hookEvent` + `type` in transcript attachments) before trusting
it as enforcement — don't assume a hook "holds" just because it's configured.

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
