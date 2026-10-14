# dispatch-brief — reference part 3

<!-- BEGIN MOVED TEXT (verbatim; do not edit — source: docs/history/rules-2026-10-14) -->
<!-- from subagent-dispatch.md:728 -->
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

<!-- from subagent-dispatch.md:751 -->
**Twelfth item, and it belongs with the contradiction slot: say that your own summary is lossy, and point at the source.** A brief compresses each row's evidence into a line or a table cell. That compression drops exactly the load-bearing clause you did not know was load-bearing. In W2b-1 (2026-09-23) an implementer refused two rows **correctly**, and both refusals were only possible because it read the full per-row record instead of the controller's table: one row's fix site was a different file entirely, and another was blocked on a separate open finding — neither fact survived the compression. The line costs nothing: *"the table above is a compression of <source>; read the full row there before trusting it, and report any place the compression is wrong."* The same wave's headline count had already moved twice for the same reason — a per-group summary quoted as a per-row enumeration — so this is one failure mode wearing two hats, at two altitudes.

