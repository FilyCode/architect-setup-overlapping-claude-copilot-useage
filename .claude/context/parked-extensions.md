# Parked extensions

Disabled 2026-08-17, not uninstalled. The files stay in the plugin cache, so re-enabling is
instant and pulls the version already on disk — no re-download, no hand-copying.

Each was carrying a listing cost in every session with no recorded use across 284 startups.
Nothing here was judged useless; it was judged *unused*. If a project starts needing one,
turn it back on.

| Parked | What it gives you | Cost while enabled | Re-enable |
|---|---|---|---|
| `example-skills` | 17 skills: `skill-creator`, `frontend-design`, `web-artifacts-builder`, `theme-factory`, `webapp-testing`, `mcp-builder`, `canvas-design`, `brand-guidelines`, `doc-coauthoring`, `internal-comms`, `algorithmic-art`, `slack-gif-creator`, `pdf`, `docx`, `xlsx`, `pptx`, `claude-api` | ~1,950 est. tokens/session | `claude plugin enable example-skills@anthropic-agent-skills --scope user` |
| `research-skills` | `litreview`, `grants`, `patent`, `dossier` | ~255 est. tokens/session | `claude plugin enable research-skills@claude-code-skills --scope user` |
| `planning-with-files` | `/plan`, `/pwf`, `/status`, plan-attest / doctor / goal / loop commands | ~92 est. tokens/session | `claude plugin enable planning-with-files@planning-with-files --scope user` |
| `graphify-enzymefinder` MCP | `graph_stats`, `god_nodes`, `get_community`, `shortest_path` over the EnzymeFinder graph | deferred (~0 tokens) | remove from `disabledMcpjsonServers` in `.claude/settings.local.json` |

## When to un-park

- **`research-skills`** — starting a grant application or a systematic literature review.
  `grants` (funder-fit scoring, NIH/NSF/ARPA structure) and `litreview` (PRISMA/PICO) are
  the two with real pull for this work.
- **`example-skills`** — BileAcidDB's web launch (Phase 4). `frontend-design`,
  `web-artifacts-builder` and `theme-factory` are the relevant three. Also `skill-creator`
  if building a new skill from scratch, and `claude-api` for any LLM-integration work.
- **`planning-with-files`** — only if `superpowers:writing-plans` and `executing-plans`
  stop being enough. They absorbed the job: 14 and 1 uses against this plugin's 1.
- **graphify MCP** — probably never. The CLI (`python -m graphify query`) re-reads from
  disk and is strictly fresher; the MCP caches `graph.json` at session start and goes stale
  after any rebuild. The graph itself is unaffected — the `post-commit` hook still rebuilds
  it automatically at zero token cost. See `.claude/rules/codebase-navigation.md`.

## Also changed

`enableAllProjectMcpServers` was flipped from `true` to `false`. A future MCP server added
to `.mcp.json` will now need explicit enabling rather than starting automatically. That is
the safer posture for project-supplied config, but it is a behaviour change — flip it back
if you would rather new servers auto-start.

## Still enabled

`superpowers` (331 uses — heavily used), `pyright-lsp` (Python code intelligence, installed
2026-08-17), `diagram-design` (installed 2026-08-17, too new to judge).
