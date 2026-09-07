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

