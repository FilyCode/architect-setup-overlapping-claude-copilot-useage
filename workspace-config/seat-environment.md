## Environment

- You start without the workspace CLAUDE.md and `core.md`. Your first read inside a project
  attaches that project's CLAUDE.md and its path-scoped rules; read them, and the project's CI
  config, before acting: that is where its real gates and test traps are.
- Python: `/projectnb/liu-scc/philipp/.venv/bin/python` (or the project's own `.venv`).
- Findings files go where the caller says, by default in the findings dir
  `/projectnb/liu-scc/philipp/architect-setup-overlapping-claude-copilot-useage/.superpowers/findings/<YYYY-MM-DD>/`
  (persistent, gitignored). Never in the scratchpad: it is node-local and dies with the job.
- Scratch: the session scratchpad, under a folder named after you. Delete only files you
  created, by name.
- Output directories are read-only to you. Never create files under any `tests/` unless your
  task owns them. No tool's `--write` mode and no `cp` onto tracked files in a shared tree.
- Read past commits with `git show <commit>:<path>`; never `git stash` or `--work-tree`.
- Use `command grep` for absence claims (shell `grep` skips gitignored paths); count with a
  parser, not grep.
- Evidence is the command and its real output, or the artifact on disk; a clean exit with no
  artifact is not success, and a gate counts only after you have seen it fail.
- Unknown is its own typed state (an enum, never `bool | None`); list every consumer when you
  introduce one. A number from a brief or another report carries its n, column and artifact, and
  is unverified until you re-derive it.
- A tool that writes two reports may filter them differently (hmmsearch `--tblout` is gated at
  sequence level, `--domtblout` at domain level): say which report a number came from.
- Do not submit SGE jobs. Write the job spec (script, resources, expected artifact) into your
  report and stop.
- Run `git log -1 --format=%h` and `git status --porcelain` at the start and end of your work
  and report whether they moved.
