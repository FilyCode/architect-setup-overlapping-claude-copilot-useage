# Phase 0 probes — 2026-10-14

Run natively in the controller session (SGE job 8090063, compute node `scc-yf3`, Claude Code 2.1.299).
Each probe: what was run, what came back, what it decides.

## P1 — `omitClaudeMd`, skill preload, `disable-model-invocation`

Throwaway agent `probe-omit` (`omitClaudeMd: true`, `tools: Read, Bash`, `skills: [caveman,
thermo-nuclear-code-quality-review]`) run once via `claude -p` in plan mode.

- Subagent transcript has **no `instructions` attachment at all**: no CLAUDE.md, no unscoped rules,
  **no MEMORY.md**. First-call context **4,772 tokens** (named seats today: median 48–54k, n = 115
  critic-reviewer … 19 alignment-officer, `measure_context.py`).
- `caveman` body arrived as a skill message ("Respond terse like smart caveman" present twice) →
  **preload works without `Skill` in `tools`**.
- `thermo-nuclear-code-quality-review` absent (0 hits for "Thermo-Nuclear") → a
  `disable-model-invocation` skill is **skipped silently**, as the docs say.

Decides: Task 10 adds `omitClaudeMd: true` to every seat (≈ −45k tokens per seat dispatch);
Task 18's frontmatter override on the vendored skill is required.

## P2 — hook inside a subagent; PreToolUse `additionalContext`

Temporary second `PreToolUse` Bash hook logging `agent_type` and returning
`additionalContext: PROBE-CONTEXT-7731`; settings restored from backup immediately after
(`jq '.hooks.PreToolUse|length'` → 1).

- Log: `{"agent_type": null, "cmd": "echo there"}` (main) and
  `{"agent_type": "general-purpose", "cmd": "echo hi"}` → **fires inside subagents**.
- Both the main session and the subagent reported "PreToolUse:Bash hook additional context:
  PROBE-CONTEXT-7731" → **`additionalContext` reaches the model**. Settings reload live (the
  controller session also received it).

Decides: Task 7 keeps the warn branch as `additionalContext`.

## P3 — does a skill's `effort:` persist past its turn?

Probe skill with `effort: high`, body `EFFORT=${CLAUDE_EFFORT}`; then a resumed second turn.

- Turn 1 printed `EFFORT=high`; transcript `perTurnEffort: "high"`.
- Turn 2 transcript `perTurnEffort: "medium"` → **the override does not persist**.
- Side observation: headless `-p` turns ran at `medium` although `~/.claude/settings.json` has
  `effortLevel: "high"` — headless runs may not read it, or Opus 5.5's default applies. Not
  investigated further; affects nothing in the plan except that eval runs are at medium in both arms.

Decides: Task 8 keeps the effort *hint* (no `deep-work` skill). Skills that declare
`effort: high` (`plan-critique`, `wave-review`) get high only for the turn they are invoked.

## P4 — session started inside a nested project repo

`cd projects/EnzymeFinder && claude -p "List only the names of the skills and the subagent types…"`.

- Listed: EnzymeFinder's own skills, plugin and user skills, built-in and plugin agents.
- **Absent: every workspace-root skill (`caveman`, `council`, `storm`, `workspace-audit`, …) and
  every workspace agent (`critic-reviewer`, `domain-reviewer`, …).** Discovery stops at the
  project repo's root, as the docs describe.

Decides: Tasks 10 and 13 also link workspace agents and skills into `~/.claude/agents/` and
`~/.claude/skills/`. (Today all transcripts are under the root project, so no past session was
affected; future sessions started in a project would be.)

## P5 — connector attachments sent twice?

**NOT RUN** — needs the owner to toggle claude.ai connectors. Carried to owner-actions (Task 19).

## P6 — what the > 500k-context calls do (`tools/big_calls.py`)

Main sessions only; tool_use blocks aggregated per message id (one message spans several lines).

- 8 sessions contain calls above 500k; those 5,840 calls used: Bash 4,406, text-only 964,
  Agent 407, SendMessage 152, Write 84, Read 62, AskUserQuestion 34, Skill 16, Edit 16.
- A session first reaches 400k at call **median 109** (min 80, max 146; n = 9 sessions).

Reading: the expensive tail is long working sessions that keep running shell work and dispatches
after ~110 calls, not a few huge reads. A nudge at 400k fires around call 110 — early enough to
matter. Threshold stays as declared.

## P7 — seat-yield tabulation

Dispatched to a read-only background agent; results in `phase0-p7-seat-yield.md`.

**P7 result** (`phase0-p7-seat-yield.md`): only Bile_acid_database left parseable seat findings (3 waves, 49 files
after md5 dedup); "acted-on" is pragmatism-officer's triage verdict, so circular. Highest Blocking shares: domain
15/65, anomaly 5/18, critic 8/67. Too thin to merge or drop any seat: roster unchanged, lean-critic on demand.
