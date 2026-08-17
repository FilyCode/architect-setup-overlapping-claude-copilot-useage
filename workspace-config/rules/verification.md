# Verify the artifact, not the narrative

Before claiming anything is done, fixed, passing, or unaffected: check the thing itself.
Re-deriving the expected behaviour from corrected code is not evidence that the corrected
code ran. Every failure below actually happened in this workspace.

**The shapes this takes**

- An output file predates the fix, or was never regenerated. Check mtimes against the fix,
  or rerun and diff — do not reason about which outputs "should be unaffected".
- A clean exit code with no artifact. A tool that catches its own errors exits 0 having
  produced nothing. Check the expected file exists.
- A comment or docstring describes a change the code below it never received. After
  changing behaviour, grep the actual invocation line, not the prose around it.
- A plan's own example code carries the bug. Re-derive maths, library behaviour and
  adapter signatures from real current source — especially against any claim of the form
  "this is exact", "this mirrors the existing pattern", or "this always holds".
- A field survives the forward path but is dropped by checkpoint serialization, so only
  resumed runs are wrong, silently. Test the round-trip's downstream consequence.
- A cached column or stored flag is trusted as current. Re-check against the live source
  before reporting something as missing or needing manual work.
- A check that cannot fail, because it matches the wrong field. A docstring stating what a
  check does is not evidence the check works. Test it against a real case that should trip it.

**Before overwriting** a canonical-named output with a `--redo`-style regeneration, archive
the previous version first. Do not rely on git as an implicit safety net for output
directories that are mostly gitignored.

**Reporting.** State what was run and what it returned. If tests fail, say so with the
output. If a step was skipped, say that. When something is verified, say it plainly.
