---
name: verification-patterns
description: Catalogue of verification failures seen in this workspace — stale artifacts, gates that cannot fail, vacuous tests, counts taken with grep, fixes that are effective but unsafe, claims and docs that decay. Use when writing or reviewing a test, gate or check, or before claiming a fix works. Scientific absences and anomalies are in scientific-evidence.
---

# Verification patterns

Each entry is a failure that actually happened here, with the check that catches it. Before
claiming a fix works, find the entries that match what you changed and apply their checks. A
gate or guard is verified by removing it and watching its test fail.

**A zero from a join is accepted only with the pre-join count printed beside it** (R-20261030-4;
SenC and MeMES): a probe that prints a count and writes a verdict asserts the two agree, and a guard
that passes a 99.97%-broken join is not a guard.

**A published zero names the denominator that could have carried the signal, with the
rate-implied expectation and P(0) beside it; and "X is kept out of Y" is accepted only after one
run with X flipped shows Y unchanged** (R-119, R-122; MeMES_OvoA_search 2026-11-09). Both halves
are one wave's errors. A "0 of 1,940,695 proteins" was really 0 of 87,564 molybdopterin carriers,
where the other arm's rate predicts 2.28 and P(0) = 0.102 -- an ordinary draw written up as a
corroborating negative. And "the undecided families are a column, not a unit" was published in a
findings file and a commit message without once running the count with those families removed:
they were supplying units through a `clan.get(n) or n` fallback, and 11.5% of the fusion census
depended on them. Both were flattering, both were found by accident weeks or hours later, and
both cost one run to check at the time of writing.

After editing a helper or script that a test parses as text (ROOT lines, paths, log lines), run that test file before commit (R-20261105-B3; fe1b242).

**CI and PR checks** (2026-11-01; owner approved):
1. A red check blocks the merge.
2. Lint and type errors are fixed first, before any further push.
3. Every failure gets a cause: a real bug is fixed in the PR; a test that passes only on SCC gets a
   skip marker for GitHub plus a register row; a flaky test gets at most one re-run, then quarantine
   plus a register row.
4. Every EF PR needs `scc-tests` = success on its head SHA: the full suite does not run on GitHub for
   PRs, so run `tools/scc_ci_status.py submit` and cite its job id in the PR body. A new push needs a new
   submit. A GitHub check that did not run (out of minutes, blocked) is unknown, not passed. For
   `scc-tests`, `pending`, `error` and absent also mean unknown, not passed; only `success` counts.
   `scc_ci_status.py sweep` turns a stuck `pending` into `error`.
5. Red main is reverted or fixed the same day, with no other pushes on top.
6. A third failed fix of the same check triggers the escalation section of plan-critique.

The rules below are the original workspace text, moved verbatim.
