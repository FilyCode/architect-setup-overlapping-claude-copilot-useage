# verification-patterns: worked incidents

The rules are in [../SKILL.md](../SKILL.md); this file keeps the incidents behind them.

Contents:
- Published zeros (MeMES_OvoA_search 2026-11-09)
- W14 plan tests and claims (2026-09-06)
- Fixes that broke something else (W2b-1 2026-09-23)
- Isolation runs and mocked tests (2026-08-29)
- Other incidents

## Published zeros (MeMES_OvoA_search 2026-11-09)

Both halves of the published-zero rule are one wave's errors (R-119, R-122). A "0 of 1,940,695
proteins" was really 0 of 87,564 molybdopterin carriers, where the other arm's rate predicts 2.28
and P(0) = 0.102: an ordinary draw written up as a corroborating negative. And "the undecided
families are a column, not a unit" was published in a findings file and a commit message without
running the count with those families removed: they were supplying units through a `clan.get(n) or n`
fallback, and 11.5% of the fusion census depended on them.

## W14 plan tests and claims (2026-09-06)

W14 shipped ~15 tests inside its plan. Four were defective, and every implementer treated them as
requirements:
- one never exercised the state it existed to protect, the `UNMEASURED` branch of a three-state
  value (collapsing that state left all four given tests green);
- one asserted a branch that never executes (`if "ef_ec_confidence" in text:`, a column never
  emitted by design);
- one used a fixture that could not trip its own check;
- two could not run in CI, silently depending on a machine-local reference map that
  `tests/conftest.py` forces off.

The "drafts" line was absent from the W14 briefs; implementers who applied the make-it-fail rule
anyway found the defects. The convenient-fixture rule's embarrassing worked instance: a plan step
whose purpose was to verify that appending columns does not break a downstream parser probed an
11-column row, the plan's fixture had 8 and the real artifact 6; appending onto the short row put
the new columns where the parser reads `full_sseq`/`qlen`/`slen`, and every row was dropped.

Six plan claims reached implementers unexecuted, all checkable in seconds:

| Claimed | Actual |
|---|---|
| `idx.known(module)` validates a module name | `resolve()` is a prefix walk, so any dotted name under the package resolves; use `name in idx.states` |
| `align --input/--output` | positional `FASTA` plus `--project-dir` |
| `run_self_test` | the function is `selftest` |
| `load_entries()` returns a list | a tuple, and takes a required `methods_dir` |
| "122 rows" in `CAPABILITY_STATUS.md` | 112; the scanner counted a legend and a roadmap table |
| `M1:668` | `M1-open-findings-inventory.md:676`; no `M1.md` exists |

Every W14 rule violation by the controlling session was against its own assertions.

## Fixes that broke something else (W2b-1 2026-09-23)

Three rows closed `FIXED-VERIFIED`, each red-proven on its own parent, and all three broke something
else: a batch loop that lost every sibling's result (a `[]`-on-failure fallback changed to raise,
copied from a single-item sibling), an escalation that turned a tolerated degradation into a run
failure, and a transaction boundary that defeated an earlier concurrency fix and lost a stage's
records on a hard kill. `command grep -rn "sleep.call_count" tests/` returned 4 hits where the
author had looked at 1; `command grep -rn "with ProjectDB(" tests/ src/` found the F-21 race test.
For a while two tests asserted contradictory sleep counts (2 and 1) for the same call.

A RED proof via `git show <commit>:<path>` plus `PYTHONPATH` reported 3 passed against a broken
blob: the editable install's `conftest.py` re-inserts `src/` ahead of `PYTHONPATH`. The test file
copied outside the repo gave `1 failed, 2 passed`, `assert [] == ['Q2']`.

## Isolation runs and mocked tests (2026-08-29)

An isolation over five failing files correctly attributed 9 failures to one agent and was then
quoted as "the other agent's work is clean"; it never ran that agent's new test file, which held 2
of its 3 real failures. A worktree isolation reported 5 failures, 2 of which reproduced on a clean
worktree with no diff; 23-vs-12 skipped was the only visible tell.

An ID-mapping path had a full mocked suite passing while every real call died in the TLS handshake,
and once that was fixed every call returned HTTP 400 for an independent reason, 43 minutes after
its paging bug was "fixed" with mocked tests.

## Other incidents

- `test_plm_backend_revision_override` asserted that a 15-character non-SHA revision is accepted,
  pinning the defeat of a version pin; three such tests surfaced 2026-08-27, one in a file no task owned.
- 2026-09-01: a signal reported dark from a code comment, then "live, so scores move", was
  measured live and unable to change any score (a `max`-folded group). The same day "no boundary
  was touched" was offered as a safety property while score semantics changed.
- `test_fusion_is_monotone_in_each_signal_value` swept one signal 0.00→1.00 beside another in the
  same `max` fold: one distinct score over 101 steps, and a constant satisfies `>= previous`.
- 2026-09-01: an AST import graph over 196 modules found 53 modules / 14,704 lines unreachable,
  several documented "Implemented + unit-tested".
- 2026-09-05: a structure stage held 69 accessions, was offered 10 after an upstream regex, and
  reported `{missing: 0, ..., resolved: 10}`; `"invalid_accession"` was in 0 of 227 artifacts.
- W2 (2026-09-21): three wrong counts by the controller (57-vs-55, 19-vs-18 rows; 8-vs-29 scripts
  from unresolved `$PROJ`/`PYTHON_BIN=` indirection), each caught by the implementer.
- `FIXES.md` said "Generated from `ROW_ASSIGNMENTS.tsv`"; no generator wrote it; it read `59 closed
  / 40 to fix` against a live `185 / 17`, and three readers walked past it.
- A CI comment said the job ran Python 3.13 to justify a report-only type ratchet; it runs 3.11.13.
- A newly live threshold shipped as 0.45 (a published cut for a binary question) where the code
  used 0.40; four tier tests (0.75, 0.50, 0.30, 0.60) had none in `[0.40, 0.45)`.
