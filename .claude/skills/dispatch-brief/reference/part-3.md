# dispatch-brief — reference part 3

Old file names in the moved text are retired: `subagent-dispatch.md` is now the skills
`dispatch-brief`, `wave-review` and `plan-critique`; `verification.md` is `verification-patterns`
and `scientific-evidence`; `scc.md` is `running-sge-jobs`.

<!-- BEGIN MOVED TEXT (verbatim; do not edit — source: docs/history/rules-2026-10-14) -->
**Thirteenth: NEVER tell a reviewer the tree is clean. Tell it to check, at both ends.** A W2b-1
review dispatch (2026-09-23) carried the line *"the working tree is clean and HEAD is frozen at
`56993903`; no files are concurrently modified."* It was true when written and false within
minutes — the controller kept committing review fixes while six seats ran. The domain seat
objected that this is **the single paragraph most likely to manufacture a wrong finding, because
it tells a reviewer not to look**, and it is right: a reviewer that believes the tree is frozen
files drift findings against text already corrected. Replace it with the opposite instruction:
*"HEAD moves during this review. Run `git log -1` and `git status --porcelain` at the START and at
the END of your work and say whether they moved."* Two of that wave's best corrections came from
one seat doing this unprompted, and a second seat caught a figure that had shifted under it
mid-review. No rule required it; now one does.

**Fourteenth: a findings file must be created BEFORE investigation, and the evidence is now
three-for-three.** Already stated above as item 1, and W2b-1 supplied the cleanest demonstration
yet: seat 1 hit its 40-turn limit having delivered **no report at all** — and its findings file
held 125 lines with three confirmed findings, two of them against commits made within the hour,
one of which (CI red at committed HEAD) was Blocking. Nothing was lost. Prior instances lost
162,630 and 144,164 tokens respectively to the same turn limit, one having been told to append as
it went and never creating the file. **State it as the agent's literal first action, before it
reads the brief**, not as advice inside the brief — an agent that reads the brief first has
already started investigating.

**Fifteenth: `cp` after a `--write` is a fifth shared-worktree hazard.** The four recorded ones are
a bare `git commit`, `git commit -- <paths>`, `git stash push -- <paths>` and
`git --work-tree=<dir> checkout`. Add: a reviewer that runs a **generator** in `--write` mode to
inspect a diff, then restores the file by hand. In W2b-1 a seat did exactly this, disclosed it
unprompted, and its `cp` silently reverted a newer version the controller had written minutes
earlier — caught only because a gate went red for a reason that made no sense. Nothing was lost
because the artifact was generated. Two fixes, both cheap: **give every generator a `--stdout`
mode and say so in `--help`** (that one already printed to stdout with no flags — it simply was
not discoverable), and **tell reviewers that any tool with a `--write` flag is off-limits in a
shared worktree; render to your scratch directory and diff there.**

**Sixteenth, and it is structural rather than procedural: a review wave has no negative control,
and cannot supply one.** Every seat in a wave-end review asks some version of *"does the code do
what it says?"* — correctness, scope, inventory, drift, even domain plausibility. **None asks
"does the system do its job?"** W2b-1's domain seat raised this unprompted and it is the sharpest
objection the wave produced: three of its six findings were in **dark modules whose scientific
claims had been wrong for months precisely because nothing ever ran them against data**. Worse,
the appearance is actively misleading — six adversarial seats and a green suite read as validation
to anyone later quoting the status docs. So: when a wave's evidence standard is entirely
self-consistency (`live: path.py:LINE now reads X`), **say so explicitly in the wave's close**, and
carry a standing row for one held-out evaluation with a stated denominator and a trivial baseline.
A review wave that cannot be embarrassed by data has not been tested by data.

**Twelfth item, and it belongs with the contradiction slot: say that your own summary is lossy, and point at the source.** A brief compresses each row's evidence into a line or a table cell. That compression drops exactly the load-bearing clause you did not know was load-bearing. In W2b-1 (2026-09-23) an implementer refused two rows **correctly**, and both refusals were only possible because it read the full per-row record instead of the controller's table: one row's fix site was a different file entirely, and another was blocked on a separate open finding — neither fact survived the compression. The line costs nothing: *"the table above is a compression of <source>; read the full row there before trusting it, and report any place the compression is wrong."* The same wave's headline count had already moved twice for the same reason — a per-group summary quoted as a per-row enumeration — so this is one failure mode wearing two hats, at two altitudes.

