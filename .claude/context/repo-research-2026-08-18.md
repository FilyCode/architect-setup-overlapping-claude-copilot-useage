# External repo research — 2026-08-18

Deep-dive research done for a future Claude session to act on. Nothing here has been
implemented yet — this is a saved reference, not a decision log (that's `DECISIONS.md`).
Judged against this workspace's actual shape as of 2026-08-18: path-scoped `.claude/rules/`,
3 subagents (`critic-reviewer` opus, `alignment-officer` sonnet, `scc-monitor` haiku),
superpowers plugin, a `workspace-audit` skill, a deterministic Stop hook
(`large-change-check.py`), graphify CLI (MCP server disabled), memory under
`~/.claude/projects/.../memory/`.

## shanraisshan/claude-code-best-practice (64.6k★) — full deep dive

Not a tool — a curated knowledge-base repo (best-practice docs, "power-up" tips, trend
reports, toy example agents/skills). Its `.claude/` directory is mostly demo scaffolding
(weather-agent, time-agent) illustrating concepts, not something to install wholesale. The
value is in `best-practice/*.md` and `reports/*.md`.

| Concept | What it is | Fit verdict | Source in repo |
|---|---|---|---|
| Per-subagent memory (`.claude/agent-memory/<agent>/MEMORY.md`, scopes `user`/`project`/`local`) | A subagent reads/writes its own persistent `MEMORY.md` (200-line cap, same shape as our main auto-memory) across invocations — separate from main-session memory. | **Adopt.** `scc-monitor` currently starts cold every run and re-derives SGE diagnosis patterns each time. A project-scope, version-controlled `.claude/agent-memory/scc-monitor/MEMORY.md` could accumulate recurring failure signatures (OOM patterns, exit codes, module-load gotchas) instead of resetting. Low cost, clear win — the single most actionable item in this research. | `best-practice/claude-memory.md`, `reports/claude-agent-memory.md` |
| Subagent frontmatter: `disallowedTools`, `maxTurns`, `effort`, `color`, `skills` (preload) | Finer controls beyond `tools`/`model`, unused here. | **Adopt selectively.** `maxTurns` on `critic-reviewer` (opus, currently unbounded) is cheap insurance against a runaway review loop. `effort` on `scc-monitor` probably fine at default. | `best-practice/claude-subagents.md` |
| CLAUDE.md monorepo loading semantics (ancestors always load, descendants lazy, siblings never load) | Confirms our path-scoped `.claude/rules/` design already matches the recommended pattern. | Already covered — validates DECISION-010, no action. | `best-practice/claude-memory.md` |
| Skill/command frontmatter: `when_to_use`, `allowed-tools`/`disallowed-tools`, `metadata`, `license`/`compatibility` | We already use `disable-model-invocation` and `context: fork`; `allowed-tools`/`disallowed-tools` per-skill is unused. | **Partially new.** Could tighten `workspace-audit` (it probably shouldn't have Edit/Write outside `.claude/` and memory) — worth a look, not urgent. | `best-practice/claude-skills.md`, `best-practice/claude-commands.md` |
| MCP guidance: "most devs use only 4 servers," resist enabling many | Validates disabling the graphify MCP server in favor of the CLI. | Already covered, no action. | `best-practice/claude-mcp.md` |
| Settings hierarchy detail (`managed-settings.d/*.json`, `claudeMdExcludes`, sandbox/permission internals) | Mostly enterprise/team features, irrelevant to a single-researcher workspace. `cleanupPeriodDays` already set. | Not relevant except what's already adopted. | `best-practice/claude-settings.md` |
| Cost control: `--max-budget-usd`, `--max-turns` CLI flags, `/cost` | Direct answer to the earlier cost-spike scare from the broken haiku Stop hook — a CLI habit, not a config change. | **Surface to the user** as a lightweight safety net, not a file change. | `reports/claude-usage-and-rate-limits.md` |
| Skills-in-monorepos guidance (namespace prefixes, `SLASH_COMMAND_TOOL_CHAR_BUDGET`) | We're at 6 shared skills + EnzymeFinder's domain skills — well below the scale this matters at. | Not relevant yet. | `reports/claude-skills-for-larger-mono-repos.md` |
| RPI workflow (Research→Plan→Implement, 8 role-agents) | Heavyweight product-team simulation for feature-shipping teams. | **Not relevant** — same shape as the 13-agent topology already retired in DECISION-011; superpowers' brainstorming/writing-plans/executing-plans covers the useful subset for a solo researcher. | `development-workflows/rpi/rpi-workflow.md` |
| 30-event hook catalog (sound-effect demo, but documents `PostToolUseFailure`, `SubagentStop`, `PreCompact`, `WorktreeCreate`, handler types `command`/`prompt`/`agent`/`http`) | We use only `PreToolUse` + `Stop`, `command` handlers. | Reference only. `SubagentStop` could log agent-memory writes; `PostToolUseFailure` could catch SGE submission errors early — neither justified today given the "hooks only for real invariants" stance. | `.claude/hooks/HOOKS-README.md` |
| Power-ups tour (`@file` refs, `/rewind`, `/tasks`, `/mcp`, `/model`, `/effort`, `/remote-control`) | Baseline features, already known or not applicable (no remote-control need). | Not new. | `best-practice/claude-power-ups.md` |

**Bottom line for this repo:** the one clearly-actionable, low-risk item is **project-scope
agent memory for `scc-monitor`** (and possibly `critic-reviewer`), so SGE diagnosis patterns
accumulate instead of resetting every invocation.

## getagentseal/codeburn (9.5k★) — light pass

Local-first, offline usage/cost tracker across 41 AI coding tools (Claude Code, Cursor,
Codex, Copilot, Gemini, etc.), with terminal/web/menubar dashboards, `npx codeburn` to run.
Overlaps with the `ccusage` skill already installed, but is multi-tool where `ccusage` is
Claude-Code-specific. Since Copilot was retired 2026-08-17 and no other AI tool is in active
use, the multi-tool angle buys little right now.

**Verdict: skip.** `ccusage` already covers the single-tool case. Revisit only if another AI
coding tool comes into active use again.

## dietrichgebert/ponytail (105k★) — light pass

A plugin/marketplace skill enforcing a "does this need to exist → is it already here → can
stdlib do it" decision ladder before writing code; claims 54% less code / 20% less cost / 27%
faster in its own benchmarks. Installs via `/plugin marketplace add DietrichGebert/ponytail`.
Substantially overlaps with this workspace's own CLAUDE.md philosophy ("don't add features
beyond what the task requires... no premature abstraction") and the existing `simplify`/
`code-review` skills, which do the same audit reactively. The differentiator is
`/ponytail-audit` for a full-repo minimalism sweep and an active per-turn nudge rather than a
review-time check.

**Verdict: marginal, optional.** Not worth installing now given existing coverage; worth a
second look only if the user later finds Claude over-engineering despite current instructions.

## GSD and GSTACK (raised later same day, verified via WebSearch not taken on trust)

User asked whether to switch from superpowers to **GSD** (`gsd-build/get-shit-done`) for
native per-phase model routing. Verdict: **do not switch** — the actual gap (no
model/effort tiering in superpowers) was closed more surgically the same day via
`model`/`effort` fields on this workspace's own `.claude/agents/*.md` files plus
`.claude/rules/subagent-dispatch.md`, which work regardless of skill framework. A full
migration (69 commands, 24 agents) is large, disruptive churn for a solo research
workspace to capture a benefit already captured.

**Security finding, independently verified, not assumed from a pasted claim**: GSD's
creator ran a `$GSD` crypto-token rug-pull, vanished (no contact since April 2026), and
the original repo was archived 2026-06-26. Confirmed across the actual GitHub issue
(`gsd-build/get-shit-done#3897`), the fork announcement (`open-gsd/gsd-core` discussion
#109), and independent crypto-news coverage — not taken at face value from the source
that raised it. Community development continued at `@opengsd/get-shit-done-redux`
(`open-gsd/gsd-core`). The original creator retains npm publish rights to the old
package; classified as exit fraud, not a confirmed malware injection, but real residual
supply-chain risk for anyone already on the original package. Never installed here.

**GSTACK** — real, a role-based governance/persona skill pack (28 commands simulating a
dev team: CEO review, QA, security audit), not a cost-routing tool. Different concern
than what prompted the question; not evaluated further.

**Lesson for future tool adoption**: verify a new tool's maintainer/trust status via an
independent search before adopting it, not just its technical feature fit — this
incident is a concrete case where the two diverged sharply. Folded into
`workspace-audit`'s external-scan step.

## Not re-litigated here

Repos already evaluated and skipped in the 2026-08-17 audit (ECC, SuperClaude, BMAD, Archon,
claude-squad, claude-mem, headroom, OmniRoute) were not revisited — see `learnings.md`'s
2026-08-17 audit-trail entry for why each was skipped.
