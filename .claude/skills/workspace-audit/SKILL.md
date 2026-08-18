---
name: workspace-audit
description: Periodic health check of the Claude Code / Copilot setup — instruction drift, unused skills, stale plugin versions, home-quota creep, promotion of recurring patterns into learnings.md, and an optional external scan for new Anthropic docs, model changes, and new repos/plugins worth evaluating. Run after finishing a development branch, after a broad maintenance pass, or roughly monthly.
disable-model-invocation: true
allowed-tools: Read Grep Glob WebFetch WebSearch Bash(du *) Bash(ls *) Bash(claude plugin *) Bash(curl -s https://api.github.com/*)
---

# Workspace audit

Explicit invocation only. This runs at most monthly; it is not a per-session check.

## When it is worth running

- After finishing a development branch or any multi-step build.
- At the end of a broad audit or maintenance pass.
- When the same friction or mistake appears a second time in one session — that is a
  promotion candidate, note it even if you do not run the full audit.

## Steps

**1. Instruction drift.** Read the workspace `CLAUDE.md`, `.claude/rules/*.md`, and
`~/.claude/CLAUDE.md`. For each instruction ask: would Claude do this anyway? Is it fixing
a weakness that no longer exists? Does it contradict anything else? Cut what fails all
three. Target: root `CLAUDE.md` under ~40 lines, each rule file under ~40.

Run `/context` to see what actually loaded, and `/doctor`, which proposes CLAUDE.md trims
independently.

**2. Skills and plugins.** A skill or plugin untouched for 30+ days is a prune candidate.
Every enabled plugin costs listing space in every session whether or not it is used, so
check before adding one.

Usage is measurable, not a guess — `~/.claude.json` carries `skillUsage` and `pluginUsage`
(lifetime counts since install) and `numStartups` for scale. A plugin with 0 uses across
hundreds of startups is carrying pure listing cost. **Before flagging a skill as unused,
check whether it auto-triggers**: `caveman` had 93 uses and `disable-model-invocation`
would have silently killed its auto-trigger.

Already-parked extensions and their re-enable commands are in
`.claude/context/parked-extensions.md` — check there before installing something new, in
case it is already sitting on disk disabled.

Verify installed versions against the **primary manifest** — the marketplace
`plugin.json`, not a changelog summary or a search result. Derived version claims have been
wrong twice here.

```bash
claude plugin list
cat ~/.claude/plugins/installed_plugins.json
```

**3. Home quota.** Home is capped at 10GB.

```bash
/projectnb/liu-scc/philipp/software/bin/scc_storage_audit.sh
du -sh ~/.local/share/claude/versions/*   # old versions accumulate at ~300MB each
du -sh ~/.claude/projects                 # session transcripts; cleanupPeriodDays controls retention
```

Anything large that is not the current version belongs under `software/` or deleted.

**4. Non-English planning-with-files skills.** The plugin ships 10 non-English skill and
command entries that reappear after every plugin update. Re-run:

```bash
/projectnb/liu-scc/philipp/software/bin/strip_pwf_translations.sh
```

**5. Promotion.** Compare recurring patterns against the bar in
`.claude/context/learnings.md`: the same pattern must recur 3+ times across 2+ distinct
tasks or projects. Promote what clears it; leave the rest in session memory.

**6. External scan (optional, run at most monthly, separate from steps 1-5).** Steps 1-5
only look inward. This step looks outward: has anything changed upstream that this
workspace should adopt or react to?

- Fetch `https://code.claude.com/docs/en/overview`, `.../whats-new`, and `.../sub-agents` —
  diff against what this workspace currently assumes (frontmatter fields it doesn't use yet,
  new hook events, changed defaults). Cross-check any claim from a third-party repo against
  these primary docs before acting on it — a claimed feature that turns out to be the repo's
  own invention has cost real time here before.
- Spot-check for model changes (`claude-api` skill's reference data, or the models page) —
  new model IDs, deprecated aliases, changed default effort levels.
- `WebSearch` for new Claude Code plugins/skills/repos released since the last run (search
  something like `claude code skill plugin <month> <year>` or check
  `github.com/hesreallyhim/awesome-claude-code` for recent additions). For any new tool
  under real consideration, also check its maintainer/trust status independently (repo
  archived? maintainer active? any rug-pull/security incident?) — do not evaluate on
  technical fit alone. A 2026-08-18 case (GSD/`gsd-build`) found a real creator rug-pull
  and repo archival that a feature-only evaluation would have missed entirely; see
  `.claude/context/repo-research-2026-08-18.md`. Judge fit against
  this workspace's actual shape — most will be redundant with something already adopted;
  see `.claude/context/repo-research-*.md` for the standard of evaluation expected (concept
  broken out per-item, verdict against what's already here, not a README summary).
- Save findings to a new `.claude/context/repo-research-<date>.md` (one file per run, do not
  overwrite prior ones — they're a dated record) following the format of the existing files
  in that directory. Only implement something from this step immediately if it's a strict,
  low-risk improvement with no design tradeoff (a stale reference, a confirmed-real feature
  with an obvious fit); anything bigger goes in the file for a deliberate decision later,
  same as steps 1-5 feed `learnings.md` rather than auto-applying.

**7. Log it.** Append the audit date and outcome to the bottom of `learnings.md`, even when
nothing changed. An audit with no trail did not happen.
