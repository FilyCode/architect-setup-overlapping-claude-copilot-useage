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
- A gate that passes because it never exercises the path in use. A regression check ran the
  statistic on the *production* artifacts and passed, while the new code path it was meant to
  protect produced a null result for every input. When you add a code path, assume the existing
  gate does not cover it, and add a positive control on the new path specifically.
- A parser validated against a fixture its own author wrote. The fixture encodes the same
  misunderstanding as the parser, so it passes a dry run and fails on first real input.
  Validate against a real artifact, or state plainly that it is unvalidated.
- Two artifacts compared positionally when their row order is not guaranteed. Align on a
  unique key first. An unstable sort on a tied key is itself a reproducibility bug even when
  every value is correct — row order that changes between runs is not reproducible output.
- A check that cannot fail, because it matches the wrong field. A docstring stating what a
  check does is not evidence the check works. Test it against a real case that should trip it.
- A named metric appears in a governance doc as evidence without three basic checks having been
  done: quote its defining formula from the code and state in one sentence what it physically
  measures; compute it on the control/negative arm too (if both arms saturate, the metric cannot
  support the comparison at that setting — that, not "the window/threshold was too wide," is the
  real lesson); and state the physical state of the modelled system (e.g. holo/apo, ligands present,
  which cofactors) and whether it matches the claim being made. All three are needed — each
  catches a different failure, and none substitutes for another.
- **Positive-control corollary:** if a positive control scores below a candidate on the same
  metric, the metric is suspect, not the control. A yardstick that fails on a case it should have
  passed easily is broken before it says anything about the harder case.
- A number that supports or closes a claim in a governance doc (decisions/findings/summary/status
  files) traces only to chat-report or ledger prose, never to a committed script + output
  artifact. Plausibility is not provenance — a wrong number survives review precisely because it
  looks right; require it to resolve to something on disk before it is cited as evidence.
- Report-generating code contains a hardcoded numeric literal in its prose output, rather than
  formatting a value computed from data. This is the mechanism, not just a symptom — a literal
  sitting in a template is exactly how a fabricated statistic gets produced and then gets cited as
  if it were computed.
- Two populations/rates/groups get compared without first listing every axis they could differ on
  (taxonomy, detection method, window or distance scale, copy number, annotation quality,
  sampling) and stating which were matched and which were not. Fixing only the one axis you were
  told about just relocates the confound to the next one.
- A claim written into multiple locations gets its scope qualifier updated in only one of them.
  This is asymmetric in practice: a strengthening edit naturally recruits the author to hunt down
  every place the old, weaker claim lived, but an edit that *undercuts* an existing claim gets
  written once and the other locations are never revisited because nothing there looks wrong, only
  unsupported. When a finding undercuts an existing claim, grep for that claim's other homes
  before considering the fix committed.

**Before overwriting** a canonical-named output with a `--redo`-style regeneration, archive
the previous version first. Do not rely on git as an implicit safety net for output
directories that are mostly gitignored.

**Reporting.** State what was run and what it returned. If tests fail, say so with the
output. If a step was skipped, say that. When something is verified, say it plainly.
