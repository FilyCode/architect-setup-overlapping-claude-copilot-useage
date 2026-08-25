---
name: rtk
description: Token-reduction CLI proxy that filters and compresses Bash output before it reaches context. Applied automatically via a PreToolUse hook — invoke this skill only to check savings, reconfigure filters, or troubleshoot.
disable-model-invocation: true
---

# rtk

rtk is always active through the `PreToolUse` Bash hook in `~/.claude/settings.json`
(`rtk hook claude`). Commands are rewritten transparently — no manual invocation needed
and no action required for it to work.

## Commands

```bash
rtk gain              # token savings analytics
rtk gain --history    # per-command usage history with savings
rtk discover          # analyze Claude Code history for missed opportunities
rtk proxy <cmd>       # run a command raw, unfiltered (debugging)
rtk init -g           # re-initialize for Claude Code
```

Binary: `~/.local/bin/rtk` (on PATH via `.path_hook.sh`). Global filters:
`~/.config/rtk/filters.toml`.

## Troubleshooting

```bash
rtk --version   # expect: rtk X.Y.Z
which rtk       # expect: /usr3/graduate/phitro/.local/bin/rtk
rtk gain        # must not be "command not found"
```

**Name collision:** if `rtk gain` fails but `rtk --version` works, a different tool named
`rtk` (reachingforthejack/rtk, "Rust Type Kit") is shadowing it on PATH. Check `which -a rtk`.

## False negatives (read this before trusting an empty result)

rtk rewrites `cmd` into `rtk cmd`, and rtk subcommands parse their own flags, so a collision
changes the **answer**, not just the formatting — always toward a reassuring "no matches" /
exit 0. Verified on 0.39.0 and now excluded via `[hooks] exclude_commands`:

- `grep -v`/`-vn`/`-nv` returned the **matching** lines instead of the non-matching ones;
  `grep -h`/`-hn` printed rtk's usage banner and zero matches.
- `grep -l N …` — `-l`/`-m`/`-t` are value-taking rtk options (`--max-len`/`--max`/
  `--file-type`) that swallow the next token. `grep -l 5 a.txt b.txt` → `0 matches for 'a.txt'`.
  Data-dependent: a word pattern falls back to raw, so `grep -l foo f` looks fine.
- `diff` on differing files returned exit **0** instead of 1, inverting `diff a b && …`.
- `git log` silently injects `--no-merges` — the merge commit is dropped *and the count
  backfilled*, so the output looks complete and a `--no-ff` merge reads as a fast-forward.

Because three separate collision classes turned up in grep alone, the policy is not an
enumeration: **any flagged `grep`/`rg` runs raw**; bare `grep PAT F` keeps its compaction.

**Not fixed — `rtk find`/`rtk tree` cannot prove absence.** They silently omit hidden *and*
gitignored paths and misreport their own total (in the config repo: raw 41 hits, rtk 24, header
says `24F`). The config only excludes `find` when the query text names a dot path, which is the
wrong axis — the blindness depends on where the hits are. `find` stays rewritten because it is
~58% of all savings.

Also still true:

- **Pipelines ARE rewritten** (`grep foo f | sort` → `rtk grep foo f | sort`). A pipeline is
  *not* an escape hatch.
- **The working escape hatch is the `RTK_DISABLED=1` command prefix**, or `rtk proxy <cmd>` /
  `rtk run "<cmd>"`. Setting `RTK_DISABLED` in the parent env does nothing.
- **No exit code from an rtk-wrapped command is evidence.**
- `head -20 f` returns ~10 lines (discloses `[N more lines]`); `head -n 20` is not rewritten.

Config is `~/.config/rtk/config.toml`, a symlink into `workspace-config/rtk/config.toml` so it
is version-controlled — if it goes missing, rtk rewrites everything again with no warning.

```bash
bash software/bin/rtk_selftest.sh      # 55 checks; run after any rtk upgrade or config edit
rtk hook check "<cmd>"                 # would this command be rewritten?
```
