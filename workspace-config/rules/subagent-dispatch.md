# Subagent dispatch: review gate and model/effort tiering

## Wave-end review (additive — the generic reviewer stays available)

At the end of a wave, before finishing a branch, or after a big task (or several
smaller ones have accumulated): dispatch `critic-reviewer` (correctness/quality/tests/
efficiency/simplicity), and, when a plan or phase doc exists to check against,
`alignment-officer` (completeness/scope conformance) and `docs-sync` (governance-doc
drift). Run these in parallel — none depends on another's output. This does not replace
superpowers' `requesting-code-review` for smaller, ad hoc checks; that stays available.

A `SubagentStop` hook (`hooks/docs-sync-nudge.py`, matcher `critic-reviewer`) backs this
up: whenever critic-reviewer's closing message reads as a clean pass (no blocking issues
found), it injects a reminder into the parent session's context to consider dispatching
docs-sync, so the "documentation always seems to go stale" failure mode doesn't depend
purely on the main session remembering. It's a soft, non-blocking, keyword-heuristic
nudge only — not scoped to alignment-officer too, since one docs-sync dispatch per wave
is enough and critic-reviewer is the agent that always runs. Skip or ignore the nudge
when docs-sync already ran that wave or clearly doesn't apply.

## Release/publication gate: security-specialist

Before a project goes to production or publication (a public code release, a public
API/DB launch, a paper submission with a code/data release) — not every wave, and not
routine development: dispatch `security-specialist` for a full checklist pass, tailored
to what the target actually is (see the agent's own Step 1 surface detection). As of
2026-08-18 no project has a built web/API/DB-with-users surface yet (EnzymeFinder's
P14a and Bile_acid_database's public launch are both future), so most runs today
correctly terminate at "not applicable" — that's expected, re-run when a web tier
actually lands. The universal tier (secrets hygiene, git-history secret scan,
dependency scanning, prompt-injection/agent-trust-boundary, supply-chain/CI pinning,
key rotation, data-licence compliance) applies to every project regardless of surface,
including the pure-batch ones — "publication" for those means a paper + public code
release, and secrets/licence checks still apply even with no web surface at all.
Complementary to the native `/security-review` skill (diff-scoped, not a full-project
gate) and to whatever CI a given project already runs (check first — EnzymeFinder
already has `bandit`, `detect-private-key`, `gitleaks`, and CodeQL; don't have the
agent re-derive by hand what CI already automates on every push).

## Brainstorming: research-scout

For a non-trivial design decision during `brainstorming`, dispatch `research-scout`
first — cheap, single-agent, checks the codebase then does one bounded external pass.
Skip it for small/obvious decisions; it exists to catch "there's already a known better
way to do this," not to gate every brainstorm.

## Model and effort tiering for any subagent dispatch

Claude Code subagents default to `model: inherit` — same model as the parent session —
unless the dispatch explicitly sets otherwise. A named agent under `.claude/agents/`
already carries its own tier (see below); a generic dispatch (superpowers'
`general-purpose` workers, `subagent-driven-development` task slices, ad hoc `Agent`
calls) does not, and silently inherits whatever the parent session is running — this is
a real, documented gap in how superpowers itself works (its skills are procedural
markdown with no programmatic model/effort control; the host session decides). Set the
`model` and `effort` parameters explicitly on every dispatch using this mapping, rather
than leaving them on inherit by default:

| Task shape | Model | Effort |
|---|---|---|
| Small check, lint-shaped question, single-file mechanical fix | haiku | low |
| Ordinary coding task, single-module change | sonnet | low-medium |
| Coding task with real design tradeoffs | sonnet | high |
| Large rewrite, cross-cutting architecture, highest-stakes review | opus | medium-high |

This is a judgment call per task, not a lookup table to apply blindly — a "small" task
touching a security-sensitive path still warrants a higher tier. When genuinely unsure,
round up rather than down; the cost of under-reviewing a real risk is higher than one
overpriced haiku call.

This is guidance, not enforcement — there is no hook-level mechanism to force model
selection on a subagent dispatch, so this depends on it actually being applied each
time, same limitation as any other prose rule in this workspace.

## Existing agent tiers (for reference)

`critic-reviewer` opus, `alignment-officer` sonnet, `docs-sync` sonnet, `scc-monitor`
haiku, `research-scout` haiku/low, `security-specialist` opus (release/publication gate
only, not wave-end).
