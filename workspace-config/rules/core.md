# Core rules

Detail and history for every line: `architect-setup-overlapping-claude-copilot-useage/docs/history/rule-index.md`.

## Evidence
1. Before you say done, fixed, passing or unaffected, show the evidence: the command and its real
   output, and the artifact on disk with an mtime after your change. A clean exit with no artifact
   is not success. A guard or gate you add or review counts only after you have seen it fail.
2. Unknown is its own typed state — an enum or a dedicated type, never `bool | None`. When you
   introduce one, list every consumer (`command grep` across src, tests, renderers, exporters).
3. For absence claims use `command grep` — the shell `grep` here skips gitignored paths. Count
   with a parser (table rows, AST nodes), not with grep. An absence is only as good as the
   instrument's headroom in that stratum.
4. A relayed number carries its n, its column and its artifact. A number from a plan or a
   subagent report is unverified until you re-derive it.

## SGE and shared trees
5. The interactive session runs in a 1-slot SGE job; anything heavier than a syntax check or one
   small test file goes to its own `qsub` job (never run long work on a login node). The caller
   owns every `qsub`: a subagent writes a job spec and stops; the caller waits in one
   backgrounded loop with a deadline and verifies the output artifact, not the exit status. A job
   reads the live tree: make no commits there until it returns. Details: skill `running-sge-jobs`.
6. In a tree other agents use, stage only your files by name, check that
   `git diff --cached --name-only` lists only them, then `git commit` without a pathspec
   (`git commit -- <paths>` sweeps another agent's unstaged edits to those paths), then run
   `git show --stat`. Read past commits with `git show <commit>:<path>`.
7. Put scratch in the session scratchpad, in a folder named for the agent. Delete only files you
   created, by name. Dispatched agents treat output directories as read-only and never create
   files under `tests/` outside their own task. Reviewers run no tool's `--write` mode and no
   `cp` onto tracked files; render to scratch and diff there.

## When to load which process
8. - Dispatching an implementer or a review seat → skill `dispatch-brief`. Code goes to
     `implementer`, ad hoc questions to `investigator`, never to general-purpose.
   - Before Task 1 of an architectural plan → `plan-critique`. A known-heavy problem (before any
     attempt) or a third failed fix → the escalation section of `plan-critique`.
   - End of a wave → `wave-review`. Self-verification is not independent review.
   - Writing or reviewing a test, gate or check, or claiming a fix works → `verification-patterns`.
   - A result that says absent, surprising or settled → `scientific-evidence`.
   - Writing, submitting or waiting on an SGE job → `running-sge-jobs`.
   - A release or publication → dispatch security-specialist.
   - A new project or a reframing → one external premise check on the target itself; resolve any
     external ID a pipeline keeps returning; before any research dispatch, `command grep`
     `.superpowers/` for prior work.

## Scope and context
9. A fix that belongs in a file you do not own becomes a dispatched task, not a comment. Report
   unrelated dead code instead of deleting it.
10. When context is large or the next task is unrelated, suggest `/compact <what to keep>` or
    `/clear` to the user. Delegate only large, independent investigations; a subagent re-reads
    its whole context on every resume.

## Governance
11. `ARCHITECTURE.md`, `DECISIONS.md`, any `CLAUDE.md`, `PROJECT_STATE.md`, the files under
    `.claude/rules/`, `.claude/agents/` and `.claude/skills/`, pushes, GitHub issues and CI
    changes need the owner's explicit approval.

## Quality bar and known limitations
12. Code must work and be reproducible (pinned inputs, recorded versions, seeded or
    deterministic), clean, lean, documented, findable and easy to maintain. It need not be
    optimal on the first pass, because the surrounding design is often not settled yet: get it
    running correctly first; perfect and optimize it later.
13. Every known limitation, weakness, shortcut or optimization opportunity becomes a tracked
    row in the project's register. That covers ones you introduce, accept, defer or find. A row
    is never only a code comment, a ledger line or a free-text list. Each row states:
    - what the limitation is;
    - why it is acceptable now;
    - what triggers fixing it (scale, cost, a later phase);
    - its evidence (file:symbol, job id, report).
    A wave does not close with an unregistered one. The project's rule file names its
    register; the EnzymeFinder register is named in `enzymefinder.md`.
