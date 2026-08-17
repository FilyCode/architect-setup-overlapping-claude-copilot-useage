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
