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

**CI and PR checks** (2026-11-01; owner approved):
1. A red check blocks the merge.
2. Lint and type errors are fixed first, before any further push.
3. Every failure gets a cause: a real bug is fixed in the PR; a test that passes only on SCC gets a
   skip marker for GitHub plus a register row; a flaky test gets at most one re-run, then quarantine
   plus a register row.
4. A check that did not run (out of minutes, blocked) is unknown, not passed. Run the cluster suite
   (`tools/scc_ci_status.py submit`) and cite its job id in the PR body.
5. Red main is reverted or fixed the same day, with no other pushes on top.
6. A third failed fix of the same check triggers the escalation section of plan-critique.

The rules below are the original workspace text, moved verbatim.
