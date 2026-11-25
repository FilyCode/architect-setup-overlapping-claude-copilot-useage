---
name: verification-patterns
description: Catalogue of verification failures seen in this workspace — stale artifacts, gates that cannot fail, vacuous tests, counts taken with grep, fixes that are effective but unsafe, claims and docs that decay. Use when writing or reviewing a test, gate or check, or before claiming a fix works. Scientific absences and anomalies are in scientific-evidence.
---

# Verification patterns

Use when writing or reviewing a test, gate or check, or before claiming a fix works. Each entry is
a failure that actually happened here, with the check that catches it: find the entries that match
what you changed and apply their checks. Worked incidents: [reference/incidents.md](reference/incidents.md).

## Procedure

1. Prove each gate, guard or test you rely on can fail.
2. Check the artifact, not the exit code: it exists, is non-empty, is newer than the fix.
3. On a contract change, run the blast-radius grep before calling the fix verified.
4. Every count, zero or percentage carries its denominator; a count read from a directory or glob
   is printed beside the number of tasks that should have produced it (an unexplained multiple is a stop).
5. Report what was run and what it returned.

## Gates and tests that cannot fail

- **A gate or guard is verified by removing it and watching its test fail.** A docstring stating
  what a check does is not evidence: a check that matches the wrong field cannot fail.
- **A liveness or "unit ran" predicate also needs a positive control:** the value it accepts is one
  only the unit's own output can produce (never a column default, an empty result or a zero), else it
  is typed ROWS-ONLY and prints no "ok" (EnzymeFinder WF1a: 801 false / 0 true accepted as live).
- **A check that compares a derived quantity between two populations read through the same code
  path** passes vacuously once a rename zeroes both sides: assert non-zero on one side first (2026-09-21).
- **A gate that passes because it never exercises the path in use:** when you add a code path, add a
  positive control on that path; the regression check on production artifacts does not cover it.
- **A control's expected outcome is published or declared in source before any score is read,
  never assumed;** a POSITIVE call first gets its population pass-rate and one published positive
  and negative.
- **A boundary test that does not probe the disputed interval cannot fail.** Parametrise both sides
  of every constant it names; when a constant changes, re-derive which tests tell old from new.
- **A test made vacuous by a change that never edited it:** a change to how inputs combine
  invalidates tests probing one input alone (`test_fusion_is_monotone_in_each_signal_value`).
- **Four shape gates cannot detect decay.** A gate that validates only shape (row count, enum,
  reason) stays green when content goes false; one gate must dereference a claim.
- **A gate that knows the answer and does not print it is half a gate.** Order offenders by
  actionability, break truncation down by state (`... and 77 more (77 SEEDED)`) (`report_ownership`).
- **Match the command as invoked, not as idealised:** `^git log\b` missed `git -C <dir> log`.

## Zeros, counts and denominators

- **A zero from a join is accepted only with the pre-join count printed beside it** (R-20261030-4;
  SenC and MeMES). A probe that prints a count and writes a verdict asserts the two agree; a guard
  that passes a 99.97%-broken join is not a guard.
- **A scan's zero (secrets, leaks) names the input scanned and whether the producer ever held the
  secret;** if it never did, the zero is "not exposed", not "clean".
- **A published zero names the denominator that could have carried the signal, with the
  rate-implied expectation and P(0) beside it; "X is kept out of Y" is accepted only after one run
  with X flipped shows Y unchanged** (R-119, R-122; MeMES_OvoA_search 2026-11-09). Both errors
  were flattering, found by accident, and cost one run to check at the time of writing.
- **A stage that filters its own input must report what it dropped:** an omission is invisible to
  counters that count what arrived. Report the denominator you started with (2026-09-05: 69 → 10).
- **Use `command grep` to find candidates, and a parser to count them:** shell `grep` skips
  gitignored paths, and a grep count is not an enumeration (2026-09-05: grep 102/17, AST 78/10).
- **This binds the controller's own counts, not only reviewers' absence claims:** a count for a
  brief comes from parsing its structure (table rows, AST nodes), and says which (W2 2026-09-21).
- **Check the aggregate's distribution before optimising for it:** a headline percentage with no
  percentiles says nothing about the common case ("98.8% saved"; median zero).
- **Two populations compared** only after listing every axis they could differ on (taxonomy,
  detection, window, copy number, annotation, sampling) and which were matched; fixing only the one
  axis you were told about relocates the confound.
- **A named metric that appears in a governance doc as evidence needs three checks:** its formula
  quoted from code and what it physically measures; its value on the control arm (both saturate =
  no comparison); the modelled system's physical state (holo/apo, ligands) vs the claim. All three:
  none substitutes for another.
- **Positive-control corollary:** if a positive control scores below a candidate on the same
  metric, the metric is suspect, not the control.

## CI and PR checks

Owner approved, 2026-11-01:
1. A red check blocks the merge.
2. Lint and type errors are fixed first, before any further push.
3. Every failure gets a cause: a real bug is fixed in the PR; a test that passes only on SCC gets a
   skip marker for GitHub plus a register row; a flaky test gets at most one re-run, then quarantine
   plus a register row.
4. Every EF PR needs `scc-tests` = success on its head SHA (the full suite does not run on GitHub
   for PRs): run `tools/scc_ci_status.py submit` and cite its job id in the PR body. A new push needs
   a new submit. A GitHub check that did not run (out of minutes, blocked) is unknown, not passed;
   for `scc-tests`, `pending`, `error` and absent are unknown too, only `success` counts.
   `scc_ci_status.py sweep` turns a stuck `pending` into `error`.
5. Red main is reverted or fixed the same day, with no other pushes on top.
6. A third failed fix of the same check triggers the escalation section of plan-critique.

## Fixes: effective is not safe

- **RED-confirmed proves a fix is effective; it says nothing about whether it is safe.** If a fix
  changes timing, a transaction boundary, an exception type, a return contract or an arity,
  `command grep` `tests/` and `src/` for consumers before `FIXED-VERIFIED` and name the grep and hit
  count; without one it is `FIXED-UNVERIFIED` (W2b-1 2026-09-23). Each old assertion found is
  corrected or deleted, never left contradicting; assert the contract, not `sleep.call_count`.
- **A fix copied from a sibling module needs the sibling's caller opened:** the pattern transfers,
  the call site may not. Return → raise is a contract change; check how far the failure escapes.
- **When a fix turns an existing test red, ask whether the test asserts the bug** (2026-08-27);
  ones in files no task owns surface only in a full-suite run after the fix.
- **A three-state value must be typed, not conventional:** an enum or type, never `bool | None`
  (`bool()`, `or False`, `.get(k, False)` erase the third state); at introduction `command grep` every
  consumer and list them in the commit (five collapses at a boundary, 2026-09-01).
- **Making a no-op live is a behaviour change, and must not also move its default:** default the
  newly read parameter to the value the code already used and say default output is unchanged; a
  different value is a cited decision (0.45 vs 0.40 re-tiered inputs).
- **A boundary held constant while the thing producing it changed meaning:** stability of the scale
  is not stability of the meaning. Bump a version carried by every artifact and refuse to resume
  across a mismatch (2026-09-01).
- **Firing is not moving:** whether a signal is live or dark is measured, not argued from wiring;
  probe the value's own upper bound (2026-09-01).
- **A RED proof run from inside `tests/` can silently execute the current tree, not the blob:**
  print `m.__file__` and the new symbol from inside pytest, or run outside the repo (2026-09-23).
- **An isolation run credited with more than it executed:** isolating attributes, never clears
  (that takes a full suite). A worktree is not the main checkout: baseline it, read the skip count.
- **Mocked transport cannot see that no socket opens:** an external-service adapter needs one live
  call showing the real response; the test asserts the construction (2026-08-29).
- **A field that survives the forward path but is dropped by checkpoint serialization** breaks only
  resumed runs: test the round-trip's downstream consequence.
- After editing a helper or script that a test parses as text (ROOT lines, paths, log lines), run
  that test file before commit (R-20261105-B3; fe1b242).

## Plans, briefs and fixtures

- **A plan's own tests and fixtures are suspects, not specifications.** Tests arriving in a brief are
  drafts: every dispatch that hands an implementer test code says "prove each can fail before
  trusting it, and report any that cannot" (W14 2026-09-06: 4 of ~15 defective).
- A plan's own example code carries the bug: re-derive maths, library behaviour and signatures from
  current source, especially against "this is exact" or "this mirrors the existing pattern".
- **A parser validated against a fixture its own author wrote** shares its misunderstanding: the
  first fixture is a real artifact, downsampled, never a hand-typed row; else say "unvalidated".
- **Execute the plan's own claims before Task 1:** check each symbol, path and figure and run each
  code block to copy, or label the claim `UNVERIFIED` (W14: six wrong claims).
- **Watch for the asymmetry:** these rules are applied reliably outward (dispatches, reviewers)
  and unreliably to the author's own assertions.

## Stale artifacts and outputs

- An output predates the fix or was never regenerated: check mtimes against the fix or rerun and
  diff; do not reason about which outputs "should be unaffected".
- A clean exit code with no artifact: a tool that catches its own errors exits 0; check the file.
- A cached column or stored flag trusted as current: re-check against the live source.
- Artifacts compared positionally when row order is not guaranteed: align on a unique key. An
  unstable sort on a tied key is itself a reproducibility bug.
- Before overwriting a canonical-named output with a `--redo`-style regeneration, archive the old one.
- Before blaming the wrapper, check your own flags: compare with identical arguments (0-vs-1 discrepancy: `-i`).

## Claims and documents that decay

- A number that supports or closes a claim in a governance doc (decisions, findings, summary,
  status) resolves to a committed script and output artifact, never prose.
- Report-generating code that contains a hardcoded numeric literal in its prose is how a fabricated
  statistic gets cited as computed: format the value computed from data.
- **A capability claimed as "implemented"** names its entry point, config flag and artifact; "it has
  tests" is not reachability (2026-09-01: 53 of 196 modules unreachable). Prefer generating the column.
- A claim written into multiple locations: when a finding undercuts it, grep its other homes and fix
  each scope qualifier.
- Where a record carries a generated and a hand-written field, the hand-written one holds the decay
  risk and needs more verification: size it by how load-bearing a claim is, not how visible.
- When you correct a false statement, check what was decided on it and record the decision as unjustified.
- A number in a comment is a claim: a change to the code it quantifies re-measures or deletes it
  (30.7 µs → 6.64 ms after a correct fix, 2026-09-05).
- A comment or docstring describes a change the code never received: grep the invocation line.
- A document that claims to be generated, and is not, decays fastest: it is generated only if a
  script writes it and something runs that script; otherwise label it a hand-maintained snapshot.

## Reporting

State what was run and what it returned. If tests fail, say so with the output. If a step was
skipped, say that. When something is verified, say it plainly.
