---
name: rtk
description: Token-reduction CLI proxy. Filters and compresses Bash command output before it reaches the LLM context. Active via PreToolUse hook in ~/.claude/settings.json.
---

rtk is always active via the PreToolUse Bash hook — no manual invocation needed.

Check savings: `rtk gain`
Re-initialize for Claude Code: `rtk init -g`
Edit global filters: `~/.config/rtk/filters.toml`

Binary installed at: `~/.local/bin/rtk` (in PATH via .path_hook.sh)
