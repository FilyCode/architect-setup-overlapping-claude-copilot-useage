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

The rules below are the original workspace text, moved verbatim.
