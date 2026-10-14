# core.md review (prompt-engineering seat), 2026-10-14
Seat: prompt-engineering / agent-harness. Start: HEAD f0d3e90; porcelain: core.md untracked (`?? workspace-config/rules/core.md`), phase0-p7-seat-yield.md untracked, 4 __pycache__ dirs.

Mechanism note that several findings below depend on (verified in tools/build_skills.py:4-5, 63): a row
mapped `core:N` is copied into NO skill. Its whole old span (item line up to the next item) survives
only in docs/history/. So anything core.md compressed out of a core-mapped span is no longer live text
anywhere, not "covered by a skill".

### F1 [Important] core 5 dropped the login-node exception and points at no skill; the SGE skill has no trigger in core 8
Old scc.md:13-18 (span mapped core:5): "Never run `pytest` or any long process on the login node...
Safe on the login node (<15s): syntax/import checks, a single tiny test file." Core 5: "Run pytest and
anything long only inside an SGE job (`$JOB_ID` set)." (a) The exemption for a single tiny test file
is gone from all live text (span is core-mapped, so not in running-sge-jobs). (b) Measured: this very
session runs inside SGE job 8090063 on scc-yf3 with NSLOTS=1 (`echo $JOB_ID` = 8090063), and
bash_guard.py:156-157 allows pytest whenever JOB_ID is set. So for the usual OnDemand/qrsh session
core 5 is vacuously satisfied and reads as permission to run the full suite in the 1-slot interactive
job, while the old SGE/dispatch text (subagent-dispatch.md:574 "Reserve the full suite (and `qsub`)
for wave close") routes the full suite through qsub. (c) The spec draft (design.md §5.2 item 5) ended
with "Details: `running-sge-jobs`"; core.md lost that pointer, and item 8 lists no trigger for
running-sge-jobs, so resource defaults (-P liu-scc, mem_per_core, h_rt, NCBI_EMAIL, appended logs)
depend entirely on description matching.
Replacement:
"5. The login node kills anything over ~30 s CPU with no error. There, run only syntax/import checks
   or one tiny test file; route pytest suites and long work through `qsub` (`$JOB_ID` set means you
   are already on a compute node; still submit the full suite as its own job). The caller owns every
   `qsub`: a subagent writes a job spec and stops; the caller waits in one backgrounded loop with a
   deadline and verifies the output artifact, not the exit status. Writing, submitting or waiting on
   a job → skill `running-sge-jobs`."

### F2 [Important] core 7 widens the `--write` ban to every agent, and narrows the output-directory rule to reviewers only
Old subagent-dispatch.md:728-737: "tell **reviewers** that any tool with a `--write` flag is off-limits
in a shared worktree". Old :604 (environment block, "Every dispatch carries", :593): "Read output
directories; never modify, move or delete them." Core 7: "Output directories are read-only to
reviewers. ... No tool's `--write` mode and no `cp` onto tracked files in a shared tree."
(a) New, stronger claim: implementers and the controller are now forbidden `--write`, which is the
only way to regenerate a generated doc — contradicting verification-patterns' own "correct the
generator, not the narrative" and the reach-column regeneration. A literal-following Opus/Sonnet will
hand-edit the generated file instead (the exact defect class). (b) Lost scope: implementers were
covered by the output-directory rule; now only reviewers are. The W14 incident (:598-602) that
motivated it was a review agent, but the rule was deliberately put in every dispatch.
Replacement:
"7. Put scratch in the session scratchpad, in a folder named for the agent. Delete only files you
   created, by name. Leave existing files in output directories alone unless your task is to
   regenerate them; they are usually gitignored and unrecoverable. Create files under `tests/` only
   when your task is to write tests. Reviewers run generators to stdout or into scratch, never with
   `--write`, and never `cp` over a tracked file."

### F3 [Important] core 1 "A gate counts only after you have seen it fail" is broader than any old text
Old dispatch template item 11 (subagent-dispatch.md:695): "When the work under review is a guard, a
gate or a check: verify it by REMOVING it and confirming the test fails". Old scope = a guard/check
being added or relied on as new evidence. Core 1 is unconditional: read literally, an existing CI
suite, ruff, or a pre-existing test never "counts" until each is made to fail, and "an exit code ...
is not [evidence]" makes `pytest` exit 0 non-evidence. Models resolve such over-broad absolutes by
ignoring them, which costs the rule exactly where it matters (new tests/guards). Also lost: the
trigger "Before claiming anything is done, fixed, passing, or unaffected" (verification.md:3) — the
word "unaffected" is the one that names the stale-output failure.
Replacement:
"1. Before saying done, fixed, passing or unaffected, check the artifact on disk: its contents, and its
   mtime against your change. An exit code alone is not evidence; a tool that catches its own errors
   exits 0 with nothing written. A test, guard or check you add is evidence only after you have seen
   it fail without your change."

### F4 [Important] core 8 lost the "known-heavy problem" escalation trigger and the external-ID habit
Spec draft §5.2 item 8: "third failed fix or a known-heavy problem → escalation". Old
subagent-dispatch.md:500 (mapped plan-critique): "Known-heavy problem, before any
attempt ... Trigger this immediately, don't spend the 3 attempts first just to 'earn' the escalation."
Core 8 keeps only "after a third failed fix", which teaches the model to spend three attempts first —
the opposite of the old rule. Separately old :353-359 (core-mapped, so in no skill): "Make it a
standing habit to resolve any external ID (PDB/accession/etc.) that a pipeline returns repeatedly" —
the cheapest premise check this workspace has (memory: top structural hit = the query's own
structure). Core 8 keeps only the project-start check; the recurring-ID habit is now in no live text.
Replacement lines:
"- Before Task 1 of an architectural plan, after a third failed fix, or as soon as a problem matches
   one that has eaten time before → `plan-critique`."
"- A new project or a reframing → one external premise check on the target itself. An external ID
   (PDB, accession) that a pipeline keeps returning → resolve it once."

### F5 [Important] Quiet-tree rule for evidence jobs is skill-only, but core 5 sends every session to qsub
Old subagent-dispatch.md:576-590 (→ wave-review): "`#$ -cwd` runs against the LIVE tree ... make no
commits and run no agents until it returns." MEMORY.md feedback_no_commits_during_evidence_jobs
records a voided pytest batch. Core 5 tells any session to submit pytest via qsub and core 6 tells it
to commit; wave-review loads only at wave end. Session that gets it wrong: an ordinary single-task
session that submits the suite mid-task and keeps committing — it never reaches wave-review.
Proposed addition to core 6: "A queued or running job reads the live tree: record HEAD at submission
and commit nothing until it returns."

### F6 [Important] core 10 instructs the model to do things only the user can do; it is new text
No old row maps to core:10 (rule-map.tsv has no `core:10`, `core:9`, `core:11` or `core:4` rows;
`command grep -c 'core:4' rule-map.tsv` = 0). /clear and /compact are user slash commands; the model
cannot clear its own context or choose a compaction instruction. Always-loaded text the model cannot
act on is either ignored or turned into chat nagging ("you may want to /clear"). "hand long
investigations to a seat" also cuts against old :3-49 (subagent context is expensive to reload; "If
the wait is the entire reason for dispatch, don't dispatch at all") and the 2-3 concurrency cap.
Fails the selection test as model-facing text. Replacement: move the first two clauses to the user-
facing context_nudge hook (which exists for exactly this, hooks/context_nudge.py) and keep in core:
"10. Hand a long, self-contained investigation to a seat when its result can be returned as a short
    report; do the work in this session when you would need the intermediate output anyway."

### F7 [Important] core 4/9/10/11 have no source rows, so the traceability checker cannot see them
rule-map.tsv destinations used: core:1,2,3,5,6,7,8 only. Core 4 condenses :91 and :95 (both mapped to
dispatch-brief), core 9's last sentence condenses :50 (dispatch-brief), core 11 comes from
workspace-config/CLAUDE.md:22-24 which is not in the map at all. A future edit to core 4 has no
history row to be read beside, which is the "rewrite read old-beside-new" safeguard the spec (§4)
depends on. Fix: add `core:N` as a secondary destination column (or a second row) for 91, 95, 50 and
a `CLAUDE.md` file entry for the governance lines.

### F8 [Important] core 6 prescribes the commit form that steals unstaged edits, and its own check cannot see the theft
Old subagent-dispatch.md:74-75: "a bare `git commit` sweeps another agent's **staged** files, and
`git commit -- <paths>` sweeps their **unstaged** ones." MEMORY feedback_concurrent_agents_share_git_index:
"Neither form is universally safe — pick by which hazard is present." Core 6: "Commit with explicit
paths, then run `git show --stat` and confirm only your files are in it." (b) Lost condition: the
pathspec form commits the whole working-tree content of the path, including a concurrent agent's
edits to the same file (state `MM`), and `git show --stat` then lists only "your" file, so the
confirmation passes on exactly the hazard-2 case. The recovery recipe and "stage untracked files by
name, never `git add <dir>/`" (old subagent-dispatch.md:206, → dispatch-brief) are also skill-only, but an
implementer with omitClaudeMd never sees core anyway; the controller is the one who needs this.
Replacement:
"6. Before committing, read `git status --porcelain` for your paths. Stage your files by name, then
   `git commit` with no pathspec if nothing else is staged; if a path shows `MM`, someone else is
   editing it — stop and ask. After the commit, `git show --stat` must list only your files. Read past
   commits with `git show <commit>:<path>`."

### F9 [Important] item-8 triggers collide with superpowers and one fires on almost every coding turn
Measured descriptions (superpowers 6.4.1 cache): requesting-code-review "Use when completing tasks,
implementing major features, or before merging"; verification-before-completion "Use when about to
claim work is complete, fixed, or passing"; subagent-driven-development "executing implementation
plans with independent tasks". Ours (skill-headers/): wave-review "at the end of a wave, before
finishing a branch"; verification-patterns "when implementing or reviewing a fix, a test, a gate or a
generated document"; dispatch-brief "when dispatching an implementer or a review seat".
- wave-review vs requesting-code-review / finishing-a-development-branch: "before finishing a branch" is
  superpowers' own trigger. The old text set the boundary explicitly (subagent-dispatch.md:219-220:
  "This does not replace superpowers' `requesting-code-review` for smaller, ad hoc checks"); neither
  core 8 nor the wave-review description carries it, and using-superpowers tells the model to invoke
  every plausibly-matching skill, so both fire and run two review procedures.
- verification-patterns: "implementing ... a fix" matches nearly every coding task, so either it loads
  every turn (defeating the 20 KB budget; its moved text is split across reference parts) or the model
  learns to skip it. It also fires at the wrong moment relative to verification-before-completion
  (that one fires at the claim; ours should fire when a test/guard/generated doc is being WRITTEN).
- dispatch-brief vs subagent-driven-development: SDD ships its own implementer/reviewer prompt
  templates; nothing says ours augments rather than replaces them, so a model picks one.
Replacement core 8 lines:
"- Dispatching an implementer or review seat, including from subagent-driven-development → also load
   `dispatch-brief` and add its required lines to that skill's template."
"- End of a wave (several tasks landed) → `wave-review`; a single task's review stays
   `requesting-code-review`. Self-verification is not independent review."
"- Writing a new test, guard, gate or generator, or reviewing one → `verification-patterns`."
and in the wave-review description replace "before finishing a branch" with "before finishing a branch
that carried several tasks (a single-task branch uses requesting-code-review)".

### F10 [Important] the always-loaded rule file itself is outside the governance list
Core 11 / old CLAUDE.md:22-24 list ARCHITECTURE.md, DECISIONS.md, CLAUDE.md, PROJECT_STATE.md. The
restructure moves the always-loaded instructions out of CLAUDE.md into rules/core.md and the skill
bodies; neither is named. A docs-sync or implementer seat told to "fix drift" can now edit the text
every session obeys without approval, which the old arrangement prevented for the file that held it.
If correct, behaviour changes (an unapproved edit becomes permitted), so not Minor.
Replacement: "11. Changes to `ARCHITECTURE.md`, `DECISIONS.md`, `PROJECT_STATE.md`, any `CLAUDE.md`,
    `.claude/rules/`, `.claude/skills/` and `.claude/agents/`, and any push, GitHub issue or CI change,
    need the owner's explicit approval."

### F11 [Minor] core 9's first two sentences are default Claude Code behaviour
Selection test (spec §5.2): "is it not default model behaviour?" "Deliver what was asked. Change only
what the task needs and match the surrounding style" restates the Claude Code system prompt's own
scope guidance; no old rule and no incident in the history carries it. Minor-triage: if correct, does
any conclusion or behaviour change? No behaviour changes; only ~150 bytes of budget. Keep the two
workspace-specific clauses: "Report unrelated dead code instead of deleting it. A fix that belongs in
a file you do not own becomes a dispatched task, not a comment."

### F12 [Minor] core 3 / core 1 lost "say which you used"
Old verification.md:243 "Use `command grep` for any 'no matches anywhere' claim, and say which you
used"; :271 "parse the structure it lives in ... and say which you used." Core 3 keeps the rule, drops
the disclosure. Minor-triage: does a conclusion change? No conclusion changes, but a reader of a report
can no longer audit an absence claim; cheap to restore: append "and say which tool you used."

## What core.md gets right (do not reopen)
- Core 2 keeps the load-bearing parts of verification.md:287-297 (typed, not conventional; list every
  consumer) and names the concrete anti-pattern (`bool | None`).
- Core 3 keeps both halves of the grep lesson (command grep for absence, a parser for counts) in one line.
- Core 4 adds "its artifact" to n+column, which matches subagent-dispatch.md:100 ("State the artifact,
  the column, and the arm") — correct, though it dropped "the arm".
- Core 5's "caller owns every qsub; subagent writes a job spec and stops" is the right structural form
  of the most expensive lesson in the old file, and it is stated positively.
- Section headers group by situation; prose is calm (one "Never", no capitals or bold) — consistent
  with Anthropic's guidance for 4.x/5.x models that overreact to aggressive emphasis.

## Strongest objection not asked about
The equivalence check this seat ran (old text beside new line) is the same kind of self-consistency
check the old file warns about (subagent-dispatch.md "Sixteenth"). Whether core.md + skills makes a
session BEHAVE as well as the 125 KB did is only testable by the evals harness (evals/, 9 scenarios),
and the decisive failures above (F1 vacuous $JOB_ID, F2 --write, F8 MM commit, F9 double-firing
skills) are all behaviours none of 9 scenarios is likely to probe unless written for them. Add one
scenario per Important here before old files retire; otherwise "evals pass" will read as "nothing lost".

## Brief errors
- "The rows whose destination is `core:<n>` are the ones core.md line n must carry": core 4, 9, 10, 11
  have no rows; core 4/9 condense rows mapped to skills, 10 is new, 11 is from CLAUDE.md (unmapped).
- "Everything else ... moves verbatim into skills": the full spans of core-mapped rows (e.g.
  scc.md:13-18 login-node exception, subagent-dispatch.md:353-359 external-ID habit, :326-338 security
  detail) move nowhere live; they exist only in docs/history.
- Aside (not core): scc.md's "`rm` is aliased to `rm -i` and will hang with no stdin" did not reproduce
  in the Bash tool today: alias active (`type rm`), but `rm <file>` deleted the file with exit 0.

End: HEAD 8765166 (moved from f0d3e90); porcelain now also shows ` M evals/run_evals.sh` and
`?? tests/test_run_evals.py` (not mine).
