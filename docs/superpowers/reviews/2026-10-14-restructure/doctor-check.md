# Setup review note for the restructure session (2026-10-14)

From a parallel read-only review session. No files were changed. All figures were measured on
2026-10-14 between 17:15 and 17:45. Items your commits through `ee05c3f` already closed are listed
at the end. `docs/superpowers/reviews/2026-10-14-restructure/doctor-check.md` says the doctor checks
were never run. This note contains them: the owner ran `/doctor` here.

## Open findings, ranked

1. **The plan's measurements draw on a contaminated, shrinking transcript pool.**
   `cleanupPeriodDays` = 30. Only 74 main transcripts remain under `~/.claude/projects/*/*.jsonl`,
   and 59 of them are dated 2026-10-14 (eval and probe runs). Real-work sessions before about
   2026-09-14 are already deleted. Both `measure_context.py` (the gate of record) and the eval
   before-arm read this pool, and the after-week will be dominated by eval runs.
   - Snapshot the corpus now.
   - Run evals under a separate `CLAUDE_CONFIG_DIR`, or tag them so they can be excluded.
   - Raise `cleanupPeriodDays` only after moving `~/.claude/projects` (1.3 GB) out of the
     quota-capped home.
2. **The allowlist still contradicts the rules.** `/projectnb/liu-scc/philipp/.claude/settings.local.json`
   still has `Bash(git commit -m ' *)` (a commit without paths, the known sweep hazard) and
   `Bash(python *)`. `git stash *` and the rtk rules are gone. It also holds many one-off rules
   (`sed -n` line ranges, single pytest node ids, `qacct -j 5738688`). Prune explicitly. The user
   scope still has `Bash(git add *)` and `graphify …` rules, and `graphify` is not on PATH.
3. **Four plugins are enabled and do nothing useful** (`~/.claude/settings.json` `enabledPlugins`, all `true`):
   - **hookify:** no rule files found (`~/.claude/hookify*`, workspace `.claude/`, `projects/*/.claude/`).
     Its pre- and post-tool hooks still run on every Bash/Read/Write call, at a median of about
     97 ms + 79 ms per Bash call (n = 120 / 108), and its Stop hook peaks at 2.8 s.
     Its `pluginUsage` of 435 counts hook firings, not use. Disable it.
   - **pyright-lsp:** the `pyright` program is missing everywhere (`.venv/bin`, `~/.local/bin`, PATH).
     There were **0 LSP calls in 840 transcripts** (main sessions and subagents).
     `codebase-navigation.md` step 1 ("code intelligence") has therefore never worked.
     Install pyright under `software/` (recommended; see the graphify section) or disable the plugin.
   - **pr-review-toolkit:** 0 lifetime uses and about 2k tokens every session. Decide now rather
     than waiting for Q3.
   - **diagram-design:** 0 lifetime uses. Disable it.
4. **The biggest lever is still behaviour, not rule bytes.** The spec's own numbers: calls above
   500k context are about 69 % of main-session cost, while the static cut is worth about −5.6 %.
   `CLAUDE_CODE_AUTO_COMPACT_WINDOW` is now set, which is good. Measure it before investing more
   in Phase 2 rewrites. Recommended sequence: finish Phase 1 → one week of `measure_context.py`
   → decide how far to take Phase 2.
5. **The Claude Docs connector loads 3 tools in full.** It is not deferred, and its long server
   instructions push the model to create a document reflexively, which clashes with the rules.
   Unless it is used from Claude Code, hide it there (see Connectors).
6. **Seat `effort`:** still unset on every seat except research-scout (Task 10). Now that the
   global effort is `medium`, seats inherit medium, including the opus seats that the spec sets
   to `high` (domain-reviewer, anomaly-hunter, security-specialist). That is a quality regression
   until Task 10 lands.
7. **Minor:** `caveman` is listed twice when the working directory is inside the config repo
   (once from the workspace and once repo-scoped). Harmless.

## Doctor results (read-only)

- **Install health:** one native install, 2.1.300, which is the latest. Background auto-updates
  are off. All settings files, `~/.claude.json` and `.mcp.json` parse. All 11 agent files and all
  skill frontmatter are valid. `~/.claude/skills/synced/` has no `SKILL.md`.
- **Unused things:** see item 3 for plugins. Skills that only run when called (council, storm,
  ccusage, workspace-audit, thermo-nuclear, graphify) cost nothing per session; keep them.
  `graphify-enzymefinder` is already in `disabledMcpjsonServers`; delete it from `.mcp.json`
  if graphify is retired.
- **Slow hooks:** none over the thresholds. superpowers SessionStart has a median of 371 ms
  and a max of 1.8 s.
- **Permissions:** no `defaultMode` is set anywhere. `"auto"` in `~/.claude/settings.json` would
  need the owner's explicit approval. There were only 3 denials in the window, and none qualifies
  for an allow rule.

## Graphify (EnzymeFinder): retire it, don't roll it out

- **Works mechanically:** the post-commit hook rebuilt `graphify-out/` 36 s after HEAD `364189dd`,
  and a query runs in 5.8 s using 160 MB.
- **Unused:** 0 `graphify query` calls in 840 transcripts. Over the same period there were
  429 `Read` calls and 72 greps on `EnzymeFinder/src`.
- **Poor results** (n = 1 query, the rule's own example, "confidence tier assignment" with
  `--budget 800`): about 28 of the first 30 nodes were generic central classes (`HitRecord`,
  `RunMetadata`, …). The relevant nodes (`AnnotationConfidenceEngine`, `AnnotationConfidence`)
  were buried. A one-line `command grep` for tier definitions went straight to them.
- **Drift:** the graph indexes 1,860 files and 4.7M words (not just code). It has 39,047 nodes
  and 63,845 edges, and 27 % of edges are inferred at an average confidence of 0.65.
  `codebase-navigation.md` still says 188 files, 17.8k nodes, a 463 KB report and a 17.5 MB
  graph; the actual figures are a 1.0 MB report and a 41 MB graph, with 311 MB on disk.
  The installed graphify is 0.7.8; the latest is 0.9.90.
- **Hook risk:** every commit re-extracts all 1,860 files in a `nohup` background process
  (log: `~/.cache/graphify-rebuild.log`). Started from a login node, it would likely be killed
  by the 30 s CPU limit without any message. Rebuilds can also overlap when agents commit at the
  same time (UNVERIFIED).
- **Recommendation:**
  - **(a) Retire it.** Remove the EF post-commit and post-checkout graphify hooks, the graphify
    sections of `codebase-navigation.md`, the `.mcp.json` entry, the user-scope `graphify …`
    allow rules, and `graphify` from the root CLAUDE.md Tooling line.
  - **(b) Or run one bounded A/B first.** Upgrade, restrict the graph to `src/`, and compare
    5 "where is X" questions against grep on tokens and correct hits. Keep it only if it wins.
  - Either way, do not set it up for other projects.
  - Installing pyright, so the existing pyright-lsp plugin works, is the better navigation
    investment for every Python project.

## Connectors (owner question, from the code.claude.com/docs/en/mcp page)

- **Removing a connector on claude.ai** also removes it from Claude Code, because the list is
  fetched at session start. Next session, not live; the docs imply this rather than state it.
- **Hiding a connector in Claude Code only:** use the `/mcp` menu toggle (per project; all sessions
  start at the workspace root), or `deniedMcpServers` with the display name, e.g.
  `"claude.ai BioRender"`. `disableClaudeAiConnectors: true` turns off all of them.
- **Unused deferred connectors** still cost their tool names and server instructions every session.
- **Usage in the window:**
  - Used: Undermind (29 calls), PubMed (24), Google Drive (5), PubCrawl (4), ChEMBL (3), Elicit (1).
  - Unused: bioRxiv, BioRender, Clinical Trials, Claude Docs.
  - Zoom, Otter and Microsoft 365 show only sign-in tools, so they were never connected.
  - Undermind, Elicit and PubCrawl are no longer loaded; confirm that is intended.

## Already closed by your commits (no action)

rtk hook retired (`fc06e8b`); global effort set to `medium`;
`CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS` set; MEMORY.md index compressed; root and home
`CLAUDE.md` rewritten (`ee05c3f`); config-repo `CLAUDE.md` stale claims fixed; `git stash *`
allow rule removed.

## Earlier content of this file (kept verbatim)

# Doctor check 2026-10-14 (read-only)
- Doctor skill refused: disable-model-invocation (user-only /doctor). Manual replication not performed per tool instruction.
