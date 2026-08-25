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

**The `rtk` filter itself can manufacture a false negative.** rtk's PreToolUse hook rewrites
`cmd` into `rtk cmd`, and rtk subcommands parse their own flags — so a collision changes the
*answer*, not just the formatting, and always in the reassuring direction. All of the following
were reproduced on rtk 0.39.0 (2026-08-25) and are now excluded from rewriting; they are listed
because the *shapes* generalise, not because these particular commands still bite:

- `grep -v` / `-vn` / `-nv` returned the **matching** lines instead of the non-matching ones —
  rtk ate `-v` as its own verbosity flag. `grep -h` / `-hn` printed rtk's usage banner and zero
  matches. Both exit 0.
- `grep -l N PAT F` — `-l`, `-m` and `-t` are **value-taking** rtk options (`--max-len`,
  `--max`, `--file-type`), so they swallow the following token. `grep -l 5 a.txt b.txt` returned
  `0 matches for 'a.txt'` rc=1 where raw grep listed both files rc=0. This one is
  **data-dependent**: a word pattern makes the int parse fail and rtk falls back to raw, so
  `grep -l foo f` looks perfectly fine. No regex over the flag can see that difference.
- `diff A B` on differing files kept the correct content but returned **exit 0** instead of 1,
  inverting any `diff a b && …` or `if diff …` gate.
- `git log` silently injects `--no-merges`. Output is byte-identical to `git log --no-merges`:
  the merge commit is dropped **and the count is backfilled** with an older commit, so `-4`
  returns four lines and looks complete while a `--no-ff` merge reads as a fast-forward. Merges
  are dropped anywhere in history, not only at HEAD.

Because three distinct collision classes turned up in `grep` alone — each after the previous
list looked complete — the policy is no longer an enumeration: **any flagged `grep`/`rg` runs
raw**, and bare `grep PAT F` keeps its compaction. The adversary is a third-party argument
parser on its own release cadence, and the cost of over-excluding is correct-but-verbose output.

**`rtk find` and `rtk tree` cannot prove absence. This one is not fixed.** They silently omit
hidden paths *and* gitignored paths, and misreport their own total count as if it were complete.
Measured in the config repo: raw `find . -name '*.md'` returns **41** hits, `rtk find` returns
**24**, and its header says `24F`. A gitignored `results/` directory disappears the same way —
which collides directly with this file's own rule about checking mostly-gitignored output
directories on disk. There is no flag to include either class.

The config excludes `find` only when the *query text* names a dot path. **That is the wrong
axis and does not solve the class**: the blindness depends on where the hits are, not how the
query is spelled, so a plain `find . -name '*.py'` is still rewritten and still blind. `find` is
left rewritten because it is ~58% of all token savings. So: never conclude a file does not exist
from `rtk find`. Use `rtk proxy find …`, or `rtk grep` (verified clean on both hidden and
gitignored paths), or `RTK_DISABLED=1 find …`.

Config: `~/.config/rtk/config.toml`, a **symlink into
`architect-setup-.../workspace-config/rtk/config.toml`** so it is version-controlled like the
rules themselves. It did not exist at all before 2026-08-25, so `exclude_commands` was empty and
nothing was ever excluded. If it goes missing, rtk reverts to rewriting everything with **no
warning of any kind** — which is why it is not left loose in a quota-capped home directory.

Verified by `bash software/bin/rtk_selftest.sh`: **55/55** — 40 rewrite-decision checks, 12 that
execute the hook's own resolved command and require it to match the *absolute native binary* on
both stdout and exit code, and 3 asserting the residuals above. `rtk verify` 145/145. The
harness is falsifiable, and that was tested rather than assumed: emptying `exclude_commands`
drives it to FAIL=38, exit 1.

Standing caveats that no config can fix:

- **Pipelines ARE rewritten.** `grep foo f | sort` becomes `rtk grep foo f | sort`; the same for
  `cat`, `ls`, `diff`, `wc`. Only `find … | …` happens to decline. An earlier version of this
  section offered a pipeline as a safe escape hatch — that was **wrong**, and wrong in the worst
  direction, since it was offered for exactly the cases that break.
- **The escape hatch that does work is the `RTK_DISABLED=1` command prefix.** `RTK_DISABLED=1
  grep -vn foo f` makes the hook decline with an explicit message. Setting `RTK_DISABLED` in the
  parent environment does *not* work — that was the form tested when this file previously, and
  incorrectly, claimed the variable was ignored outright. `rtk proxy <cmd>` and `rtk run "<cmd>"`
  also bypass the filter and were verified faithful to the native binary.
- **No exit code from an rtk-wrapped command is evidence.** rtk preserves some (`grep` no-match
  still returns 1) and destroys others.
- **`head -N file` under-delivers.** It rewrites to `rtk read --max-lines N` and returns about
  half the requested lines (`head -20` gave 10, `head -5` gave 2). It does append
  `[N more lines]`, so this is disclosed rather than silent, but it does not say that lines you
  explicitly asked for were withheld. `head -n 20` and `head -c 100` are not rewritten at all.
- **A structurally odd result means suspect the filter before the data** — a usage banner where
  matches belonged, an implausible "identical", a header count that disagrees with the listing
  under it.
- **Not audited for content fidelity:** `rtk pytest`, `rtk git diff`, `rtk git stash show`,
  `rtk ls`. (`rtk read` was checked and is faithful — md5-identical to `cat`.)

Two lessons here generalise beyond rtk, and both were produced by review rounds *after* this
section was first written and believed complete:

- **Match the command as invoked, not as idealised.** `^git log\b` failed to cover
  `git -C <dir> log` and `git --no-pager log` — the spellings actually used in practice.
- **A positive control built from a convenient fixture proves nothing.** The `-l` collision
  passed a `grep -l foo f` check while corrupting `grep -l 5 …`, because the safe and broken
  cases differ by the argument's *type*, not the flag. Pick the fixture that should trip the
  check, not the one that is easy to write.

**Before overwriting** a canonical-named output with a `--redo`-style regeneration, archive
the previous version first. Do not rely on git as an implicit safety net for output
directories that are mostly gitignored.

**Reporting.** State what was run and what it returned. If tests fail, say so with the
output. If a step was skipped, say that. When something is verified, say it plainly.
