# verification-patterns — reference part 2

<!-- BEGIN MOVED TEXT (verbatim; do not edit — source: docs/history/rules-2026-10-14) -->
<!-- from verification.md:142 -->
- A test made vacuous by a change that never edited it. `test_fusion_is_monotone_in_each_signal_value`
  swept one signal 0.00→1.00 beside another; once a grouping change put both in the same
  `max` fold, the sweep produced **exactly one distinct score across all 101 steps**, and a
  constant satisfies `>= previous` unconditionally. **A change to how inputs combine
  invalidates every test that probes one input in isolation** — after such a change, re-derive
  what each affected test actually varies. A sensitivity or monotonicity test whose swept
  variable no longer reaches the output stays green and says nothing.
<!-- from verification.md:149 -->
- **A capability claimed as "implemented" with no call path.** This workspace requires that a
  *number* trace to a committed script and an output artifact; it did not require that a
  *capability claim* trace to a call path, and on 2026-09-01 an AST import graph over all 196
  modules found **53 modules / 14,704 lines — a third of the package, all but two with
  dedicated tests — unreachable from any real run**, several of them documented as
  "Implemented + unit-tested". Before writing "implemented" in any status document, name the
  entry point, the config flag and the artifact it consumes. **"It has tests" is not
  reachability.** Prefer generating the column: a ~60-line import-graph script produces it and
  CI can fail when a claimed row and measured reachability disagree.

<!-- from verification.md:221 -->
- **Match the command as invoked, not as idealised.** `^git log\b` failed to cover
  `git -C <dir> log` and `git --no-pager log` — the spellings actually used in practice.
<!-- from verification.md:223 -->
- **A positive control built from a convenient fixture proves nothing.** The `-l` collision
  passed a `grep -l foo f` check while corrupting `grep -l 5 …`, because the safe and broken
  cases differ by the argument's *type*, not the flag. Pick the fixture that should trip the
  check, not the one that is easy to write.
<!-- from verification.md:227 -->
- **Check the aggregate's distribution before optimising for it.** "98.8% of tokens saved" was
  true and almost entirely irrelevant: it described two mistaken commands, not the workload. The
  median call saved nothing. A headline percentage with no percentiles behind it is not evidence
  about the common case.

<!-- from verification.md:247 -->
- The earlier line in this file that "every other command runs raw, so grep/find/diff/git output
  is trustworthy" is true *about rtk* and was being read as a blanket guarantee about grep. It is
  not one. Review dispatches quoting that line should add: *use `command grep` for absence checks.*
<!-- from verification.md:250 -->
- Before blaming the wrapper, check your own flags. A 0-vs-1 discrepancy that looked like the
  shell function turned out to be `-i` passed to one invocation and not the other. Compare with
  identical arguments first; the wrapper is a real hazard and also a convenient scapegoat.

<!-- from verification.md:254 -->
**Before overwriting** a canonical-named output with a `--redo`-style regeneration, archive
the previous version first. Do not rely on git as an implicit safety net for output
directories that are mostly gitignored.

<!-- from verification.md:258 -->
**A stage that filters its own input must report what it dropped.** An omission from a queue is
invisible to every downstream counter, because counters count what *arrived*. On 2026-09-05 a
structure stage held 69 UniProt accessions, was offered 10 after an upstream regex filtered the
rest, and reported
`gating_summary = {missing: 0, rejected_low_confidence: 0, resolved: 10, retry_exhausted: 0}`
with `terminal_failures: []` — **a clean total-success report over a population silently reduced
from 69 to 10**. The string the investigation expected to find (`"invalid_accession"`) appeared
in **0 of 227** run artifacts, because the rejection happened one stage earlier and produced no
error, no flag and no non-zero count anywhere. The defect lived three months. Same shape as "a
gate that passes because it never exercises the path in use", one level earlier: **report the
denominator you started with, not only the numerator you finished with.**

<!-- from verification.md:270 -->
**This binds the CONTROLLER'S OWN counts, not only reviewers' absence claims.** W2 (2026-09-21)
produced three wrong counts from one person in one wave, all the same error: counting state tokens
anywhere in a markdown file rather than inside its table rows (twice — 57-vs-55 dispositions, then
19-vs-18 rows), and pattern-matching venv paths rather than resolving `$PROJ`/`$REPO`/`PYTHON_BIN=`
shell indirection (8-vs-29 scripts, which inverted the conclusion). Each reached a dispatch brief.
Each was caught by the implementer who received it, not by the author. **If a count is going into a
brief, parse the structure it lives in** — table rows, import statements, AST nodes — and say which
you used.

<!-- from verification.md:279 -->
**Use `command grep` to find candidates, and a parser to count them.** `command grep` is right
for absence claims — the shell `grep` here silently skips gitignored paths — but a grep count
quoted as an enumeration is a confidently wrong number. Measured 2026-09-05:
`command grep -rlE "^\s*from .* import"` returned **102 test modules and 17 `src/` modules**;
a scope-aware AST walk over the same question returned **78 and 10**, because `^\s*` also
matches *function-local* imports, which were not exposed to the defect being counted. Grep finds
the candidates; an AST walk counts them.

<!-- from verification.md:298 -->
**A number in a comment is a claim and decays like one.** On 2026-09-05 a correct fix added
`inspect.getsource` to a hashing function, taking it from **30.7 µs to 6.64 ms** — a 200x
regression — while the comment beside it still read 30.7 µs. The fix was right; the comment
became false the moment it landed, and nothing noticed for the rest of the day. When a change
touches code whose cost or behaviour a nearby comment quantifies, **re-measure or delete the
number.** A stale figure in a comment is indistinguishable from a current one.

<!-- from verification.md:305 -->
- **A fix copied from a sibling module, without opening the sibling's CALLER.** The pattern transfers; the call site's shape may not. On 2026-09-23 a fallback that returned `[]` on four failure classes — indistinguishable from a genuine empty result — was correctly changed to raise, modelled on a sibling adapter that already raised. The precedent was real and correctly cited. But the sibling's call site is **single-item**, so raising there loses nothing, while the target's is a **batch loop with no handler**: one item's failure then discarded every other item's result. The conflation was removed and instantly recreated one level up, because the batch path could not express "this one failed, the rest are fine". **A change from returning a value to raising is a contract change** — `command grep` every consumer, exactly as this file already requires for a three-state value, and check whether the new failure can escape further than the old one could.

<!-- from verification.md:307 -->
- **RED-confirmed proves a fix is EFFECTIVE; it says nothing about whether it is SAFE.** Both halves of a wave's evidence are needed and only one was being collected. W2b-1 (2026-09-23) closed three rows `FIXED-VERIFIED`, each with its own new test proven red on its own fix's parent commit, and **all three broke something else** — a batch loop that lost every sibling's result, an escalation that turned a tolerated degradation into a run failure, and a transaction boundary that silently defeated an earlier concurrency fix *and* lost a whole stage's records on a hard kill. None of the three was visible to the per-task gates, because per-task gates run the task's own tests.
  The two greps that would have caught all three cost seconds: `command grep -rn "sleep.call_count" tests/` returned **4** hits where the fix's author had looked at 1; `command grep -rn "with ProjectDB(" tests/ src/` found the single test that opens two concurrent contexts, which is the F-21 race test. So: **if a fix changes timing, a transaction boundary, an exception type, a return contract, or an arity, `command grep` `tests/` AND `src/` for existing consumers before writing `FIXED-VERIFIED`** — and say in the ledger row which grep you ran and how many hits it returned. A row that names no blast-radius grep is `FIXED-UNVERIFIED`.
  Corollary, observed in the same wave: for a while the repo held **two tests asserting contradictory contracts for the same call** (sleep counts of 2 and 1 on identical adapter config), because the new test was added without reconciling the old one. When a blast-radius grep finds an existing assertion, the fix is not done until that assertion is either corrected *with a comment naming this finding* or deleted as superseded — leaving both is how a suite goes red at wave close instead of at the task.
  Second corollary: **an over-specified assertion is a latent blast-radius failure.** Two of the three casualties asserted an exact `sleep.call_count` where the contract they guarded was only *"still retries with backoff"*. Assert the contract, not the incidental number, or the next correct fix in that path turns the test red for no reason.

<!-- from verification.md:312 -->
- **A RED proof run from inside `tests/` can silently execute the CURRENT tree, not the blob.** The
  standard recipe — `git show <commit>:<path>` into scratch, point `PYTHONPATH` at it, re-run the
  test — is right, and on 2026-09-23 it reported **3 passed** against a pre-fix blob that was
  provably broken. The project is an editable install with a `src/` layout, and the repo's own
  `conftest.py` re-inserts `src/` ahead of `PYTHONPATH`, so pytest imported the fixed module while
  a plain `python -c` in the same shell correctly resolved the scratch copy. That discrepancy is
  the only reason it was caught. Copying the test file **outside the repo** and running it there
  gave the real answer: `1 failed, 2 passed`, `assert [] == ['Q2']`.
  **So: assert the module path inside the test run, not outside it.** One line —
  `import m; print(m.__file__, hasattr(m, "<symbol the fix introduced>"))` executed *by pytest* —
  distinguishes a real RED proof from a green one taken on the tree you were trying to exclude.
  Same family as "a `git worktree` is not the main checkout" and "an isolation run credited with
  more than it executed": the harness silently differed from the thing under test, and only a
  direct check of what actually loaded could say so.

<!-- from verification.md:327 -->
- **A document that CLAIMS to be generated, and is not, decays faster than one that admits it is
  hand-written.** `FIXES.md` opened with *"Generated from `ROW_ASSIGNMENTS.tsv` and `git log`, not
  hand-maintained."* No generator wrote it; the commands at the bottom were a manual recipe. Its
  standing block then sat at `59 closed / 40 to fix / 208 rows` against a live `185 / 17` — and
  **three separate readers walked past it**, because "generated" reads as "self-updating" and
  switches off the instinct to check. The false claim was the mechanism, not a detail beside it.
  So: a doc is generated only if a script writes it and something runs that script. Otherwise say
  *"hand-maintained, and the numbers below are a snapshot"*, and where a genuinely generated
  sibling exists, name it so the distinction is visible rather than assumed.

<!-- from verification.md:337 -->
- **A gate that knows the answer and does not print it is half a gate.** `report_ownership`
  reported `UNASSIGNED 1` and did not say which row, because it listed offenders alphabetically
  and capped the list at 40 — so the single actionable defect sat behind 116 `SEEDED` rows that
  are the expected resting state, and never reached the screen. A human reviewer found what the
  gate had already computed. **Order any offender listing by actionability, not alphabetically,
  and break the truncation notice down by state** (`... and 77 more (77 SEEDED)`), so a reader can
  tell whether the hidden remainder is benign. Prove it the usual way: re-introduce the defect and
  confirm the id now prints.

