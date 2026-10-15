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

## Policy: allowlist — only `cat` is filtered

Since 2026-08-25 the hook rewrites **only `cat`** (to `rtk read`). Every other command runs
raw. This was a measurement call, not caution: rtk's own usage DB (36,449 commands) shows a
**median saving of 0 tokens per call**, 82% of calls under 100, and the ten largest calls
accounting for 91% of all lifetime savings — `rtk find`'s entire 1136.9M was one
`find / -name '*'`. Routine filtering bought ~nothing while carrying a live false-negative
surface.

What it used to do, all verified on 0.39.0, all silent, all exit 0: `grep -v`/`-vn`/`-nv`
returned MATCHING lines instead of non-matching; `grep -h` printed a usage banner; `grep -l 5 a b`
swallowed `5` as `--max-len`; `diff` turned exit 1 into 0; `git log` injected `--no-merges` and
backfilled the count; `find`/`tree` dropped every hidden and gitignored path while reporting
their total as complete.

`cat` stays because `rtk read` is the only adapter verified byte-identical to `/usr/bin/cat`
(tabs, unicode, 5000-char lines, missing trailing newline) *and* carrying real recurring value —
five of the ten biggest savings are `cat` on huge database files, truncated with disclosure.

Still true:

- **`head -N`/`tail -N` are rewritten anyway and cannot be excluded** — an rtk bug; even an
  explicit `^head\b` fails. `head -20` returns ~10 lines. Use **`head -n 20`** or `head -c 100`,
  which run raw. `tail` is rewritten in both forms.
- **An unparseable config silently disables every exclusion** with no warning. Patterns are
  single-quoted TOML *literal* strings; `"…"` basic strings reject `\s`.
- **A pipeline is NOT a bypass.** The working escape hatch is the `RTK_DISABLED=1` command
  prefix, or `rtk proxy <cmd>` / `rtk run "<cmd>"`.
- **No exit code from an rtk-wrapped command is evidence.**

Config `~/.config/rtk/config.toml` is a symlink into `workspace-config/rtk/config.toml`, so it
is version-controlled. The hook lives once in `~/.claude/settings.json`, so this applies to all
projects.

```bash
bash software/bin/rtk_selftest.sh      # 52 checks; run after any rtk upgrade or config edit
rtk hook check "<cmd>"                 # would this command be rewritten?
```
