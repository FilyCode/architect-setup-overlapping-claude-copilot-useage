#!/bin/bash
# Recreate the user-scope links into this repo (DECISION-026): core.md, every seat, the process
# skills and the hooks, under ~/.claude (or $CLAUDE_USER_DIR). Idempotent; never replaces a real
# file or directory — it reports it and exits 1. Path-scoped rules and the root CLAUDE.md stay
# linked at the workspace root.
set -u
REPO=$(cd "$(dirname "$0")/.." && pwd -P)
DEST=${CLAUDE_USER_DIR:-$HOME/.claude}
SKILLS="dispatch-brief wave-review plan-critique verification-patterns scientific-evidence
running-sge-jobs completion-check thermo-nuclear-code-quality-review"
rc=0

link() {  # link <target> <link path>
  local target=$1 path=$2
  mkdir -p "$(dirname "$path")"
  if [ -L "$path" ]; then
    [ "$(readlink "$path")" = "$target" ] && return
    ln -sfn "$target" "$path"
  elif [ -e "$path" ]; then
    echo "not a link, left alone: $path" >&2; rc=1; return
  else
    ln -s "$target" "$path"
  fi
  echo "linked $path"
}

link "$REPO/workspace-config/rules/core.md" "$DEST/rules/core.md"
for f in "$REPO"/workspace-config/agents/*.md; do link "$f" "$DEST/agents/$(basename "$f")"; done
for s in $SKILLS; do link "$REPO/.claude/skills/$s" "$DEST/skills/$s"; done
for h in bash_guard.py context_nudge.py large-change-check.py; do
  link "$REPO/workspace-config/hooks/$h" "$DEST/hooks/$h"
done
exit $rc
