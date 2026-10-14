# Critique wave brief — workspace setup restructure spec

Target: `docs/superpowers/specs/2026-10-14-setup-restructure-design.md` (commit `ec42c36`, this repo:
`/projectnb/liu-scc/philipp/architect-setup-overlapping-claude-copilot-useage`).
This is a **plan-critique wave on a spec**, not a code review. Your seat-specific focus is in your
dispatch prompt; this file is shared by all seats.

## Before anything else

Your findings file (path given in your dispatch) must already exist — create it as your first
action, with a header line, before reading further. Append each finding the moment you confirm it.
If you run out of turns, that file is the deliverable.

## What you are reviewing

The owner wants the workspace's Claude Code setup to use far fewer tokens while keeping its
evidence discipline. The spec proposes: an always-on `core.md` of ≤150 lines replacing two
always-on rule files (752 + 553 lines); seven new skills; review seats started with
`omitClaudeMd: true` plus preloaded skills; a new `lean-critic` seat; hooks replacing some prose
rules; removal of the rtk hook; a byte-budget script.

Live files the spec talks about (read them, do not trust the spec's summary of them):
- `/projectnb/liu-scc/philipp/.claude/rules/{subagent-dispatch,verification,scc}.md` (symlinks into
  `workspace-config/rules/`)
- `/projectnb/liu-scc/philipp/.claude/agents/*.md`, `/projectnb/liu-scc/philipp/CLAUDE.md`,
  `~/.claude/CLAUDE.md`, `~/.claude/settings.json`,
  `~/.claude/projects/-projectnb-liu-scc-philipp/memory/MEMORY.md`
- this repo's `.claude/context/{learnings,parked-extensions}.md`, `workspace-config/DECISIONS.md`

## Ranked areas (drop from the bottom if turns run short)

Your dispatch ranks the areas for your seat. Common to all: prefer **executing a small script**
(a grep, a byte count, a frontmatter check, `claude plugin details`, `claude --help`) over reading
more prose. Claims about Claude Code behaviour should be checked against
`https://code.claude.com/docs/en/...` (WebFetch where you have it) or the installed CLI — not
memory.

## Already known and accepted (do not re-derive)

- Measured baseline in spec §2 (first-call context 77.6k–100k main, 49.6k–72.5k subagents).
- The lessons in the old rule files are correct in substance; the question is placement, wording
  and whether they still fire at the right moment.
- Plugins `pr-review-toolkit`, `hookify`, `ponytail` (default off) were installed today with owner
  approval; three parked plugins were uninstalled by mistake and will be restored by the owner.
- Owner decisions: aggressive budget (moderate allowed where needed), review waves as skills that a
  core rule says when to run, rtk hook removed, narratives to `docs/history/`.

## Claims in the spec I have NOT re-derived — if your measurement disagrees, stop and report; do not reconcile toward mine

- "114 headings/bold-lead items" (heuristic count; the plain bullets of verification.md's shapes
  list are not counted).
- Projected savings "~22–25k main, ~20–25k per seat" (projection from byte counts / 4, not measured).
- That `omitClaudeMd` drops `.claude/rules/*.md` unscoped rules as well as CLAUDE.md files (the docs
  say "project rules" are part of the CLAUDE.md set; verify).
- That `skills:` preload works for agents whose `tools:` list omits `Skill`.

## Environment

- `rtk` filters only `cat` (to `rtk read`); every other command runs raw, so grep/find/diff/git
  output is trustworthy. Two exceptions: `head -N`/`tail -N` are still rewritten and under-deliver
  — use `head -n N` — and no exit code from an rtk-wrapped command is evidence. If anything looks
  structurally odd, re-run it with an `RTK_DISABLED=1` prefix; a pipeline is not a bypass.
- Shell `grep` is a function that skips gitignored paths; use `command grep` for absence claims and
  say which you used. Check exit codes outside a pipe.
- HEAD moves during this review is possible but unlikely: run `git -C <repo> log -1 --format=%h` and
  `git -C <repo> status --porcelain` at START and END and report whether they moved.
- Do not edit any file except your findings file. No `--write` tools, no `git stash`, no
  `git --work-tree`, never `rm -rf`, never create files under any `tests/`. Do not install,
  enable or disable plugins. Scratch goes under
  `/scratch/8090063.1.y/claude-768026/-projectnb-liu-scc-philipp/b989fe41-cf40-4244-a6ca-617e36bb6c70/scratchpad/<your-seat>/`.
- This is a login node: nothing over ~15 s CPU. Do not run `claude -p` sessions.

## Finding format

`### F<n> [Blocking|Important|Minor] <one line>` then: evidence (command + output, or file:line),
why it matters, proposed spec change. Before filing anything as Minor, answer in writing: *if this
finding is correct, does any currently-stated conclusion of the spec change?* If yes, it is not
Minor. "The spec's premise is wrong" is a first-class finding.

## Close with

1. Start/end HEAD + status.
2. The strongest objection to this work that I did not ask you about.
3. Anything in this brief you found to be wrong.
