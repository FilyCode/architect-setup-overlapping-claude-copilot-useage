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
- A test that fails *on the fix* — the inverse of the bullet above, and it does fail, on the
  correct repair, because it asserts the defect as the expected behaviour.
  `test_plm_backend_revision_override` asserted that a 15-character non-SHA revision is
  *accepted*, pinning the defeat of a version pin. When a fix turns an existing test red, ask
  whether the test was asserting the bug before assuming the fix is wrong. Three instances
  surfaced on 2026-08-27, one in a file no task owned — per-task review cannot find those, only
  a full-suite run after the fix.
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
- An isolation run credited with more than it executed. Isolating a diff to find *whose* failures
  these are is valid **attribution** and invalid **clearance** — the two need different runs, and
  the second always costs a full suite. On 2026-08-29 an isolation over the five *failing* files
  correctly attributed 9 failures to one agent, and was then quoted as "the other agent's work is
  clean"; that run never executed the other agent's own new test file, which held 2 of its 3 real
  failures. Second half of the same rule: **a `git worktree` is not the main checkout.** Tests
  keying on CWD, an env lock, or on-disk state fail there for reasons unrelated to the diff — the
  same day, a worktree isolation reported 5 failures of which 2 reproduced on a clean worktree
  with *no diff applied*. Run a clean-worktree baseline before believing any worktree failure, and
  read the **skip count**, not only the FAILED lines: 23-vs-12 skipped was the only visible tell
  that the environment differed.
- A green mocked test over a code path that cannot reach its service at all. Mocked transport
  asserts what the code does with a response it was handed; it cannot observe that no socket
  ever opens. On 2026-08-29 an ID-mapping path had a full mocked suite passing while every real
  call died in the TLS handshake — and behind that, once the handshake was fixed, every call
  returned HTTP 400 for a second, independent reason. Two stacked defects, neither reachable by
  any mock, in a path whose paging bug had been "fixed" with mocked tests 43 minutes earlier. For
  an adapter that talks to an external service, evidence is **one live call showing the real
  response**; the regression test then asserts the *construction* (that the session is built
  with the right policy), because that is the part that silently regressed and the part a test
  can actually hold.
- A claim written into multiple locations gets its scope qualifier updated in only one of them.
  This is asymmetric in practice: a strengthening edit naturally recruits the author to hunt down
  every place the old, weaker claim lived, but an edit that *undercuts* an existing claim gets
  written once and the other locations are never revisited because nothing there looks wrong, only
  unsupported. When a finding undercuts an existing claim, grep for that claim's other homes
  before considering the fix committed.

- A three-state value collapsed back to two at a boundary its author did not own. This is
  the single most repeated defect in this workspace: **five instances in one wave**
  (2026-09-01), two of them in code written during that wave *to fix* the class, by agents
  whose briefs quoted the convention. Unknown became `False` and manufactured a novelty flag;
  became "index unavailable" with no flag; became **`unanimous`, the strongest state**; became
  a prediction failure; became `[]`, identical to a genuine empty result. **A three-state
  value must be typed, not conventional** — introduce it as a distinct type or explicit enum,
  never a `bool | None` guarded by a comment, because `bool()`, `or False`, `.get(k, False)`
  and any truthiness test erases the third state silently. **At introduction, enumerate every
  consumer** with `command grep` across `src/`, tests, renderers and exporters, and list them
  in the commit message: four of those five collapses were in a consumer the introducing
  change never looked at.
- **A check that compares a derived quantity between two populations read through the SAME code
  path, with no liveness assertion.** Rename the field and BOTH sides go to zero; the comparison
  then passes vacuously, forever, and nothing reddens. Three instances in one wave (2026-09-21),
  including an implementer discovering its **own** synthetic tests were vacuous because a fixture
  package name never resolved — caught only because one of them *passed on the unfixed code*. The
  repair is one line: assert the quantity is non-zero on at least one side before comparing. Prove
  it by removing the guard and watching the check pass anyway.
- **Where a record carries both a generated field and a hand-written one, the hand-written one holds
  ALL the decay risk and needs MORE verification, not less.** Stated best by the agent who missed it:
  *"a `reach:` value is regenerated on every `--write` and cannot drift; a `no-impl` reason is prose
  nothing re-checks."* It had been sizing verification effort by how **visible** a claim was rather
  than how **load-bearing**. The same error produced its earlier miss — it verified a baseline's
  *counts* were untouched (they were) and never read its *prose*, which the preceding commit had
  just falsified.
- **When you correct a false statement, check what was DECIDED on it.** A false premise that
  supported a decision means the decision is now unjustified-as-written, and that belongs in the
  record rather than buried under the correction. A CI comment asserted the job ran Python 3.13 and
  used that to justify making a type-check ratchet report-only instead of gating; the job runs
  3.11.13, the same version CI pins. Correcting the sentence exposed that the gating decision rests
  on nothing — which is now a visible open question instead of a settled one.
- **Four shape gates cannot detect decay.** A gate that validates a record's *shape* — row count,
  enum membership, non-empty reason — can never go red when its *content* stops being true: a
  parked item whose blocker was resolved, a superseded item whose named replacement was itself
  deleted. At least one gate must **dereference a claim**. This objection reshaped a wave's largest
  deliverable from four shape checks into five of which three dereference, and all three were then
  watched failing against a mutated copy of the real artifact.
- A claim that a signal is live, or dark, argued from wiring rather than measured. **Firing is
  not moving.** On 2026-09-01 a controller reported "no shipped score moves" from a code
  comment, a reviewer corrected it to "the signal is live, so scores move", and the
  measurement showed it was live *and algebraically incapable of changing any score* — it sat
  in a `max`-folded group where its own upper bound could never beat a co-member. Three
  parties reasoned about connectivity; none probed behaviour. The cheap probe is the value's
  **own upper bound**: if the output does not move there, the signal cannot move it anywhere.
- A boundary held constant while the thing producing it changed meaning, with no version stamp
  on the output. **Stability of the scale is not stability of the meaning** — it is what makes
  old and new artifacts incomparable *while looking comparable*. If a score's inputs, grouping
  or semantics change, bump a version that travels with every artifact carrying it and refuse
  to resume across a mismatch. "No boundary was touched" was offered as this workspace's
  safety property on 2026-09-01 and was precisely the hazard.
- A test made vacuous by a change that never edited it. `test_fusion_is_monotone_in_each_signal_value`
  swept one signal 0.00→1.00 beside another; once a grouping change put both in the same
  `max` fold, the sweep produced **exactly one distinct score across all 101 steps**, and a
  constant satisfies `>= previous` unconditionally. **A change to how inputs combine
  invalidates every test that probes one input in isolation** — after such a change, re-derive
  what each affected test actually varies. A sensitivity or monotonicity test whose swept
  variable no longer reaches the output stays green and says nothing.
- **A capability claimed as "implemented" with no call path.** This workspace requires that a
  *number* trace to a committed script and an output artifact; it did not require that a
  *capability claim* trace to a call path, and on 2026-09-01 an AST import graph over all 196
  modules found **53 modules / 14,704 lines — a third of the package, all but two with
  dedicated tests — unreachable from any real run**, several of them documented as
  "Implemented + unit-tested". Before writing "implemented" in any status document, name the
  entry point, the config flag and the artifact it consumes. **"It has tests" is not
  reachability.** Prefer generating the column: a ~60-line import-graph script produces it and
  CI can fail when a claimed row and measured reachability disagree.

**`rtk` is now an allowlist: only `cat` is filtered. Everything else runs raw.** rtk's
PreToolUse hook used to rewrite `cmd` into `rtk cmd` for 53 command families. rtk subcommands
parse their own flags, so a collision changed the *answer*, not just the formatting, always in
the reassuring direction. Reproduced on 0.39.0, all silent, all exit 0: `grep -v`/`-vn`/`-nv`
returned the **matching** lines instead of the non-matching ones; `grep -h` printed a usage
banner and zero matches; `grep -l 5 a b` swallowed `5` as `--max-len` and searched for `a`;
`diff` turned exit 1 into exit 0, inverting `diff a b && …`; `git log` silently injected
`--no-merges`, dropping the merge *and backfilling the count* so the output looked complete;
`find`/`tree` omitted every hidden **and** gitignored path while reporting their own total as
complete (raw `find . -name '*.md'` = 41 hits in the config repo, `rtk find` = 24, header `24F`).

The reason for going all the way to an allowlist rather than blocking those shapes is
measurement, not caution. From rtk's own usage DB (`~/.local/share/rtk/history.db`, 36,449
commands): **median saving per call is 0 tokens**, 61% of calls saved nothing, 82% saved under
100, and the ten largest calls account for **91%** of all lifetime savings. `rtk find`'s entire
1136.9M was a single `find / -name '*'`; its other 770 calls saved 0.1M combined. `rtk grep`
saved 12.0M across 6,954 calls — 0.6% — while being the largest corruption source. The real
wins were two pathological commands (`find /`, `cat` on a multi-GB database), which want
*bounding* (`-maxdepth`, `| head -n N`), not compression. So routine filtering was paying
approximately nothing in exchange for a live false-negative surface.

`cat` is kept because `rtk read` is the only adapter that is both verified faithful —
byte-identical to `/usr/bin/cat` across tabs, unicode, 5000-char lines and a missing trailing
newline — and carrying recurring value: five of the ten largest savings are `cat` on huge
database files, and it truncates those *with disclosure*.

Consequences to remember:

- **`head -N` and `tail -N` are still rewritten, and cannot be excluded.** This is an rtk bug:
  they bypass `exclude_commands` entirely — even an explicit `^head\b` fails, while `^[^c]`
  correctly excludes `ls` and `grep`. `head -20 f` becomes `rtk read --max-lines 20` and returns
  about half the lines asked for (disclosed as `[N more lines]`, so not silent). **Use
  `head -n 20` or `head -c 100`, which run raw.** `tail` is rewritten in both spellings — use
  `sed -n` or an `RTK_DISABLED=1` prefix when the exact tail matters.
- **An unparseable config silently restores zero exclusions, with no warning of any kind.** A
  `"…"` TOML *basic* string rejects `\s` as an invalid escape; that mistake was made while
  writing this config and wiped every exclusion while still looking present on disk. The
  patterns are single-quoted TOML *literal* strings, and the harness asserts that rtk actually
  parsed them rather than merely that the file exists.
- **No exit code from an rtk-wrapped command is evidence.**
- **Escape hatches:** `RTK_DISABLED=1 <cmd>` as a command *prefix* works and says so;
  `rtk proxy <cmd>` and `rtk run "<cmd>"` also bypass and were verified faithful. Setting
  `RTK_DISABLED` in the parent environment does *not* work. **A pipeline is NOT a bypass** —
  `grep foo f | sort` became `rtk grep foo f | sort`; only `find … | …` happened to decline.
  An earlier version of this section offered a pipeline as the safe escape hatch, which was
  wrong in the worst direction, since it was offered for exactly the cases that break.

Config: `~/.config/rtk/config.toml`, a **symlink into
`architect-setup-.../workspace-config/rtk/config.toml`** so it is version-controlled like these
rules. The hook itself is registered once, user-globally, in `~/.claude/settings.json`; there
are no project-level rtk hooks or configs, so this policy applies to every project.

Verified by `bash software/bin/rtk_selftest.sh`: **52/52** — 1 config-parse assertion, 34
must-run-raw, 3 allowlist, 8 executing the hook's own resolved command and requiring it to match
the *absolute native binary* on stdout and exit code, 4 asserting `rtk read` stays byte-identical
to `cat`, and 2 pinning the head/tail bug so a fix or a regression both surface. `rtk verify`
145/145. Falsifiable, and tested rather than assumed: emptying `exclude_commands` drives it to
FAIL=41, and an invalid-TOML config to FAIL=41 with the parse assertion firing by name.

Three lessons here generalise beyond rtk, all produced by review rounds *after* this section was
first written and believed complete:

- **Match the command as invoked, not as idealised.** `^git log\b` failed to cover
  `git -C <dir> log` and `git --no-pager log` — the spellings actually used in practice.
- **A positive control built from a convenient fixture proves nothing.** The `-l` collision
  passed a `grep -l foo f` check while corrupting `grep -l 5 …`, because the safe and broken
  cases differ by the argument's *type*, not the flag. Pick the fixture that should trip the
  check, not the one that is easy to write.
- **Check the aggregate's distribution before optimising for it.** "98.8% of tokens saved" was
  true and almost entirely irrelevant: it described two mistaken commands, not the workload. The
  median call saved nothing. A headline percentage with no percentiles behind it is not evidence
  about the common case.

**`grep` is a shell function here, and it silently skips gitignored paths.** Separate from rtk,
and `RTK_DISABLED=1` does **not** bypass it — that prefix only disables rtk's hook. `type grep`
shows a function re-dispatching to Claude Code's bundled ugrep with `--ignore-files`. Measured in
EnzymeFinder on 2026-08-30: `grep -rIl 'noisy-OR' --include='*.md' .` returns **14** files,
`command grep` with identical arguments returns **18**. The four dropped were gitignored —
`graphify-out/` and `.superpowers/sdd/` (whose own `.gitignore` is `*`) — and one of them was a
research report, so not a harmless omission.

Scope it correctly rather than over-reacting: `src/` and `tests/` are tracked, so ordinary
code-absence claims are unaffected. What breaks is any absence check that *should* include an
ignored path — `.superpowers/` ledgers and briefs, `graphify-out/`, `results/` where ignored,
`__pycache__`. **Use `command grep` for any "no matches anywhere" claim**, and say which you used.

Two cautions learned the same day, in the same five minutes:

- The earlier line in this file that "every other command runs raw, so grep/find/diff/git output
  is trustworthy" is true *about rtk* and was being read as a blanket guarantee about grep. It is
  not one. Review dispatches quoting that line should add: *use `command grep` for absence checks.*
- Before blaming the wrapper, check your own flags. A 0-vs-1 discrepancy that looked like the
  shell function turned out to be `-i` passed to one invocation and not the other. Compare with
  identical arguments first; the wrapper is a real hazard and also a convenient scapegoat.

**Before overwriting** a canonical-named output with a `--redo`-style regeneration, archive
the previous version first. Do not rely on git as an implicit safety net for output
directories that are mostly gitignored.

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

**This binds the CONTROLLER'S OWN counts, not only reviewers' absence claims.** W2 (2026-09-21)
produced three wrong counts from one person in one wave, all the same error: counting state tokens
anywhere in a markdown file rather than inside its table rows (twice — 57-vs-55 dispositions, then
19-vs-18 rows), and pattern-matching venv paths rather than resolving `$PROJ`/`$REPO`/`PYTHON_BIN=`
shell indirection (8-vs-29 scripts, which inverted the conclusion). Each reached a dispatch brief.
Each was caught by the implementer who received it, not by the author. **If a count is going into a
brief, parse the structure it lives in** — table rows, import statements, AST nodes — and say which
you used.

**Use `command grep` to find candidates, and a parser to count them.** `command grep` is right
for absence claims — the shell `grep` here silently skips gitignored paths — but a grep count
quoted as an enumeration is a confidently wrong number. Measured 2026-09-05:
`command grep -rlE "^\s*from .* import"` returned **102 test modules and 17 `src/` modules**;
a scope-aware AST walk over the same question returned **78 and 10**, because `^\s*` also
matches *function-local* imports, which were not exposed to the defect being counted. Grep finds
the candidates; an AST walk counts them.

**A three-state value is typed at introduction, not repaired at review.** The existing rule
above is right and is being followed *after* the fact. One 2026-09-05 wave produced roughly
eight fresh instances — `evidence_index`, `neighborhood_consensus`, `confidence_stage_status`,
`clean_extrapolated` (twice, on two independent paths), `identity_margin` written as `NaN` and
recovered by convention, `vote_breakdown` collapsed by `dict(getattr(..., {}) or {})`, and a
resolution state — **several of them in code written during that wave to fix the class**. What
is new is not the rule but the evidence that it must be enforced at *review* time: ask of every
new value whether it can be unknown, and if it can, require the type to say so and the
introducing commit to list every consumer. `subagent-dispatch.md`'s "Three-state is a plan-time
checklist item, not a review-time catch" asks the same question one stage earlier, at plan time.

**A number in a comment is a claim and decays like one.** On 2026-09-05 a correct fix added
`inspect.getsource` to a hashing function, taking it from **30.7 µs to 6.64 ms** — a 200x
regression — while the comment beside it still read 30.7 µs. The fix was right; the comment
became false the moment it landed, and nothing noticed for the rest of the day. When a change
touches code whose cost or behaviour a nearby comment quantifies, **re-measure or delete the
number.** A stale figure in a comment is indistinguishable from a current one.

- **A fix copied from a sibling module, without opening the sibling's CALLER.** The pattern transfers; the call site's shape may not. On 2026-09-23 a fallback that returned `[]` on four failure classes — indistinguishable from a genuine empty result — was correctly changed to raise, modelled on a sibling adapter that already raised. The precedent was real and correctly cited. But the sibling's call site is **single-item**, so raising there loses nothing, while the target's is a **batch loop with no handler**: one item's failure then discarded every other item's result. The conflation was removed and instantly recreated one level up, because the batch path could not express "this one failed, the rest are fine". **A change from returning a value to raising is a contract change** — `command grep` every consumer, exactly as this file already requires for a three-state value, and check whether the new failure can escape further than the old one could.

- **RED-confirmed proves a fix is EFFECTIVE; it says nothing about whether it is SAFE.** Both halves of a wave's evidence are needed and only one was being collected. W2b-1 (2026-09-23) closed three rows `FIXED-VERIFIED`, each with its own new test proven red on its own fix's parent commit, and **all three broke something else** — a batch loop that lost every sibling's result, an escalation that turned a tolerated degradation into a run failure, and a transaction boundary that silently defeated an earlier concurrency fix *and* lost a whole stage's records on a hard kill. None of the three was visible to the per-task gates, because per-task gates run the task's own tests.
  The two greps that would have caught all three cost seconds: `command grep -rn "sleep.call_count" tests/` returned **4** hits where the fix's author had looked at 1; `command grep -rn "with ProjectDB(" tests/ src/` found the single test that opens two concurrent contexts, which is the F-21 race test. So: **if a fix changes timing, a transaction boundary, an exception type, a return contract, or an arity, `command grep` `tests/` AND `src/` for existing consumers before writing `FIXED-VERIFIED`** — and say in the ledger row which grep you ran and how many hits it returned. A row that names no blast-radius grep is `FIXED-UNVERIFIED`.
  Corollary, observed in the same wave: for a while the repo held **two tests asserting contradictory contracts for the same call** (sleep counts of 2 and 1 on identical adapter config), because the new test was added without reconciling the old one. When a blast-radius grep finds an existing assertion, the fix is not done until that assertion is either corrected *with a comment naming this finding* or deleted as superseded — leaving both is how a suite goes red at wave close instead of at the task.
  Second corollary: **an over-specified assertion is a latent blast-radius failure.** Two of the three casualties asserted an exact `sleep.call_count` where the contract they guarded was only *"still retries with backoff"*. Assert the contract, not the incidental number, or the next correct fix in that path turns the test red for no reason.

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

- **A document that CLAIMS to be generated, and is not, decays faster than one that admits it is
  hand-written.** `FIXES.md` opened with *"Generated from `ROW_ASSIGNMENTS.tsv` and `git log`, not
  hand-maintained."* No generator wrote it; the commands at the bottom were a manual recipe. Its
  standing block then sat at `59 closed / 40 to fix / 208 rows` against a live `185 / 17` — and
  **three separate readers walked past it**, because "generated" reads as "self-updating" and
  switches off the instinct to check. The false claim was the mechanism, not a detail beside it.
  So: a doc is generated only if a script writes it and something runs that script. Otherwise say
  *"hand-maintained, and the numbers below are a snapshot"*, and where a genuinely generated
  sibling exists, name it so the distinction is visible rather than assumed.

- **A gate that knows the answer and does not print it is half a gate.** `report_ownership`
  reported `UNASSIGNED 1` and did not say which row, because it listed offenders alphabetically
  and capped the list at 40 — so the single actionable defect sat behind 116 `SEEDED` rows that
  are the expected resting state, and never reached the screen. A human reviewer found what the
  gate had already computed. **Order any offender listing by actionability, not alphabetically,
  and break the truncation notice down by state** (`... and 77 more (77 SEEDED)`), so a reader can
  tell whether the hidden remainder is benign. Prove it the usual way: re-introduce the defect and
  confirm the id now prints.

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

- `selD` is itself a selenoprotein, so its in-frame UGA defeats gene calling — 66 of 73
  genomes called SelD-negative carried a near-full-length unannotated *selD* in their DNA;
- `TIGR00475` (SelB) sits a median **32.6 bits** over its trusted cutoff in Actinomycetota
  against **209** in Pseudomonadota, and Actinomycetota SelA+/SelB− is **46.7%** of the
  published orphan count;
- `RF01852` (tRNA-Sec) declares **TC 47.00 against NC 46.90** — a **0.1-bit** discrimination
  band — and Campylobacterota's surviving calls cluster **3.2 bits** over the gate against
  31.0 for Pseudomonadota.

Each was read as biology before it was read as instrumentation. So:

- **Before writing "X is absent in C", measure where the instrument sits in C.** Report the
  margin between C's surviving calls and the cutoff beside the same margin elsewhere. A clade
  whose calls pile onto the gate cannot support an absence claim, and the pile-up is itself
  reportable. Check the model's own declared **discrimination band** too — for an
  HMM or CM that is **`TC - NC`**, the gap between its lowest-scoring curated member
  and its highest-scoring known non-member. **It is NOT `GA` vs `TC`**: those are
  routinely equal (23 of 23 models in the project that produced this rule), so an
  equality there means nothing. Measured in that project: `RF01852` has a 0.1-bit
  band (0.2% of TC) and did fail a whole phylum; `TIGR00475` has 13.25 bits, which
  is unremarkable — and its apparent "floor" turned out to be a collection bug
  instead. Recorded because the author of this rule wrote the `GA == TC` version
  first, into a rule file and an agent, on a constant the same project had already
  documented as universal.
- **A general score depression is a mechanism, not a verdict.** Campylobacterota scores lower
  on *every* selenium model (SelA 0.88, SelD 0.81, SelB 0.65 of Pseudomonadota's median). That
  makes "the cutoff is failing this clade" plausible; it does not make it true. Test it against
  a **within-clade true-negative control** — same composition, pathway genuinely absent — and
  be ready for the control to be noisy: in that probe the negative arm produced a hit in
  **40/40** genomes and 4 of them cleared GA, so "a sub-threshold hit exists" proved nothing.
  What discriminated was a *relational* measure the negatives could not fake (the Sec model
  outscoring the generic tRNA model at the same locus: 16/16 in the test arm, **0/80** in
  controls).
- **When known biology says a thing must be present and the data says absent, write BOTH
  branches down before choosing.** Branch A, the instrument is failing — then name how, measure
  it, and the failure mode is a finding in its own right. Branch B, the premise does not hold
  here — then you have found something. A write-up naming only branch A has not done the work.
  The phrasing that marks the error is *"X must be true, therefore the measurement is wrong"*;
  it is usually right, which is exactly why it is invisible when it is not.
- **An instrument-driven absence and a real absence are different states and must be typed as
  such** — the same three-state discipline as everywhere else in this file, applied to the
  detector rather than to the value.

**Attack the results that CONFIRMED what you expected, not only the surprising ones.** Effort
is allocated by surprise, so confirming results are the least audited and the most likely to be
quietly wrong. Measured on 2026-09-25: a wave's own headline negative — "not one of 3,866 fusion
proteins carries Sec, and phylum does not explain it, P(0) = 1.3e-10" — **dissolved under finer
matching**, going 22.80 expected at phylum → 14.21 at class → 3.09 at order (p = 0.045) → **0.25
at family (p = 0.78)** → 0.00 at genus. The effect was where fusions *live*, not what fusions
*are*. Nobody asked, because the result was the one being hoped for. Take the wave's best result
and try to dissolve it: match at a finer stratum, swap the denominator, restrict instead of
stratify. State the power loss honestly when you do — comparator coverage fell 887 → 284 across
those ranks, so the fine strata lose power as well as confound, and "expected 0.00" is partly an
absence of comparator rather than a demonstrated absence of effect.

The seat that owns all of this is **`anomaly-hunter`** (`.claude/agents/anomaly-hunter.md`,
opus/45 turns), added 2026-09-25. Every other review seat is structurally biased toward closure
— `critic-reviewer` closes on "the code does what it says", `domain-reviewer` closes on "this is
plausible given what we know", and *plausible given what we know* is precisely the instrument
that buries a real result. Dispatch it at wave end alongside `domain-reviewer`, and before any
result is written down as settled.

**Reporting.** State what was run and what it returned. If tests fail, say so with the
output. If a step was skipped, say that. When something is verified, say it plainly.

## A plan's own tests and fixtures are suspects, not specifications

W14 (2026-09-06) shipped ~15 tests inside its plan document. **Four were defective**, and every
implementer treated them as requirements because that is what a brief looks like:

- one never exercised the state it existed to protect — the `UNMEASURED` branch of a three-state
  value. Proven by collapsing that state and watching all four given tests stay green;
- one asserted a branch that never executes (`if "ef_ec_confidence" in text:` where the column is
  never emitted by design), so its assertion never ran;
- one used a fixture that could not trip its own check;
- two could not run in CI at all, because they silently depended on a machine-local reference map
  that `tests/conftest.py` forces off.

**So: tests arriving in a brief are drafts.** Every dispatch that hands an implementer test code
says so, in one line: *"the tests in your brief are drafts — prove each can fail before trusting
it, and report any that cannot."* In W14 that instruction was absent, and the defects were found
by implementers who applied the make-it-fail rule anyway. Do not rely on that.

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

**Watch for the asymmetry.** These rules are applied reliably *outward* — to dispatches, to
reviewers, to gates someone else must pass — and unreliably to the author's own assertions. Every
W14 rule violation by the controlling session was of the second kind.

