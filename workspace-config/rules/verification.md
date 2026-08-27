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
- A claim written into multiple locations gets its scope qualifier updated in only one of them.
  This is asymmetric in practice: a strengthening edit naturally recruits the author to hunt down
  every place the old, weaker claim lived, but an edit that *undercuts* an existing claim gets
  written once and the other locations are never revisited because nothing there looks wrong, only
  unsupported. When a finding undercuts an existing claim, grep for that claim's other homes
  before considering the fix committed.

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

**Before overwriting** a canonical-named output with a `--redo`-style regeneration, archive
the previous version first. Do not rely on git as an implicit safety net for output
directories that are mostly gitignored.

**Reporting.** State what was run and what it returned. If tests fail, say so with the
output. If a step was skipped, say that. When something is verified, say it plainly.
