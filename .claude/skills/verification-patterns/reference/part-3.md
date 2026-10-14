# verification-patterns — reference part 3

<!-- BEGIN MOVED TEXT (verbatim; do not edit — source: docs/history/rules-2026-10-14) -->
<!-- from verification.md:346 -->
- **Making a no-op live is a behaviour change, and must not also move its default.** A parameter
  stored on `self` and never read was correctly wired into the function that should have used it —
  and shipped with its own default (`0.45`) rather than the constant that function already used
  (`0.40`). Every input in `[0.40, 0.45)` silently changed category under **default** construction:
  no flag, no changelog, identical field names and schema. No caller anywhere passed the parameter,
  so the change reached the only production path and benefited nobody. **When you make a dead knob
  live, default it to the value the code was already using**, and say in the commit that default
  output is unchanged. If the two numbers genuinely should differ, that is a decision with a
  citation, not a hygiene fix. Worse here: the number adopted was a *published threshold for a
  different question* (a binary soluble/insoluble call, not a three-way tier cut), so the fix also
  silently redefined what the output categories meant.

<!-- from verification.md:358 -->
- **A boundary test that does not probe the disputed interval cannot fail.** The suite had four
  tier-boundary tests — 0.75, 0.50, 0.30, 0.60 — and **none in `[0.40, 0.45)`**, the only interval
  where the old and new thresholds disagree. They all stayed green across a boundary move. This is
  the convenient-fixture rule landing specifically on boundary tests, where it is least excusable:
  a boundary test's entire job is the interval around the boundary, so **parametrise it on both
  sides of every constant it names**, and when a constant changes, re-derive which tests can still
  distinguish the old value from the new one.

**An absence is only as good as the instrument's headroom IN THAT STRATUM, and a textbook
premise may not close an anomaly.** These are one rule because they are one failure: the
project measures "not detected", the literature says "must be present", and the gap gets
resolved by assertion in whichever direction is convenient. SenC-SelD hit this **three times
and diagnosed it fresh each time**, never recognising it as a class:

<!-- from verification.md:497 -->
**Reporting.** State what was run and what it returned. If tests fail, say so with the
output. If a step was skipped, say that. When something is verified, say it plainly.

<!-- from verification.md:500 -->
## A plan's own tests and fixtures are suspects, not specifications

W14 (2026-09-06) shipped ~15 tests inside its plan document. **Four were defective**, and every
implementer treated them as requirements because that is what a brief looks like:

<!-- from verification.md:505 -->
- one never exercised the state it existed to protect — the `UNMEASURED` branch of a three-state
  value. Proven by collapsing that state and watching all four given tests stay green;
<!-- from verification.md:507 -->
- one asserted a branch that never executes (`if "ef_ec_confidence" in text:` where the column is
  never emitted by design), so its assertion never ran;
<!-- from verification.md:509 -->
- one used a fixture that could not trip its own check;
<!-- from verification.md:510 -->
- two could not run in CI at all, because they silently depended on a machine-local reference map
  that `tests/conftest.py` forces off.

<!-- from verification.md:513 -->
**So: tests arriving in a brief are drafts.** Every dispatch that hands an implementer test code
says so, in one line: *"the tests in your brief are drafts — prove each can fail before trusting
it, and report any that cannot."* In W14 that instruction was absent, and the defects were found
by implementers who applied the make-it-fail rule anyway. Do not rely on that.

<!-- from verification.md:518 -->
**The convenient-fixture rule now has a worked instance, and it is embarrassing enough to keep.**
This file already says a positive control built from a convenient fixture proves nothing. W14's
plan contained a step whose *entire purpose* was to verify that appending columns does not break
a downstream parser — and it missed, because the probe used an 11-column row while the plan's own
fixture used 8 and the real artifact turned out to be **6**. Appending onto a short row put the new
columns where the parser reads `full_sseq`/`qlen`/`slen`, and it **silently dropped every row**.
The step written to prevent picking the easy fixture picked the easy fixture.

**Corollary: for any format, parser or schema work, the first fixture is a real artifact,
downsampled — never a hand-typed row.** A hand-typed row encodes what the author believes the
format is. The real file is what the format is. Find one with `command find` (output directories
are usually gitignored, so the shell `grep`/`find` wrappers will not see them).

<!-- from verification.md:531 -->
## Execute the plan's own claims before Task 1

Every factual claim a plan makes about the codebase is either executed before dispatch or labelled
`UNVERIFIED`. W14 shipped six that were not, and each reached an implementer verbatim:

| Claimed | Actual |
|---|---|
| `idx.known(module)` validates a module name | `resolve()` is a **prefix walk**, so any dotted name under the package resolves — `enzymefinder.totally.made.up.module` returns `known=True, state=cli`. The docstring prescribes `name in idx.states` for document-supplied names |
| `align --input/--output` | positional `FASTA` plus `--project-dir` |
| `run_self_test` | the function is `selftest` |
| `load_entries()` returns a list | returns a tuple, and takes a required `methods_dir` |
| "122 rows" in `CAPABILITY_STATUS.md` | 112 capability rows; the scanner counted a legend table and a roadmap table as capabilities |
| `M1:668` | the quote is at `M1-open-findings-inventory.md:676`, and no file named `M1.md` exists |

All six were mechanically checkable in seconds. The cheap mechanism is a **plan preflight**: extract
every symbol, path and figure the plan cites, assert each resolves, and run any code block the plan
tells an implementer to copy. The alternative is what happened — the plan's code is first executed
by the implementer of the task that copies it, by which time it is in the repo.

<!-- from verification.md:550 -->
**Watch for the asymmetry.** These rules are applied reliably *outward* — to dispatches, to
reviewers, to gates someone else must pass — and unreliably to the author's own assertions. Every
W14 rule violation by the controlling session was of the second kind.

