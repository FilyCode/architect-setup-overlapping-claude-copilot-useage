# liu-scc workspace

Owner: Philipp Trollmann (phitro@bu.edu). Bioinformatics research on the BU SCC.
Projects live under `projects/<name>/`; each is its own git repo. A project's own
`CLAUDE.md`, `PROJECT_STATE.md` and `phases/` are its source of truth — read them before
changing anything in it.

## Environment

- No sudo. Installs go to a project `.venv` or `~/.local`, never system-wide.
- Workspace venv: `.venv/` (`/projectnb/liu-scc/philipp/.venv/bin/python`).
- Claude runs inside an SGE job on a compute node; `$JOB_ID` is set there. SGE details:
  skill `running-sge-jobs`.
- Shared config is version-controlled in
  `architect-setup-overlapping-claude-copilot-useage/`; root `CLAUDE.md`, rules and agents
  are symlinks into it. Edit either path; never replace a symlink with a copy.

## Always-on rules

`.claude/rules/core.md` holds the invariants. Process detail lives in skills:
`dispatch-brief`, `plan-critique`, `wave-review`, `verification-patterns`,
`scientific-evidence`, `running-sge-jobs`, `completion-check`. History and the old rule
text: `architect-setup-overlapping-claude-copilot-useage/docs/history/`.

## Until the skills land (removed in Task 15)

- Evidence before claiming done: `.claude/rules/verification.md`.
- Any subagent dispatch or review wave: `.claude/rules/subagent-dispatch.md`.

## Approval needed

Governance files (`ARCHITECTURE.md`, `DECISIONS.md`, any `CLAUDE.md`, `PROJECT_STATE.md`),
files under `.claude/rules/`, `.claude/agents/` and `.claude/skills/`, pushes, opening or
closing GitHub issues, and CI changes.

## Tooling

`caveman`, `ccusage`, `council`, `storm`, `graphify`, `ponytail` (off by default;
`/ponytail-review`, `/ponytail-audit` on demand). Installed plugins announce themselves.

## Compact instructions

When compacting, keep: files modified and not yet committed; running SGE job ids and the
artifact each should produce; findings-file and ledger paths; open owner approvals; every
figure still labelled UNVERIFIED; the skill in use (re-invoke it after compaction).
