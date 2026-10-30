#!/usr/bin/env bash
# Move Claude Code session transcripts (~/.claude/projects, incl. auto-memory) off the 10 GB home
# quota and leave a symlink in their place. Run only with every Claude session closed: it refuses
# while any file there changed in the last 10 minutes. The old copy is kept as
# projects.moved-<date> until you delete it yourself.
# Usage: tools/move_transcripts.sh [dest]   (default /projectnb/liu-scc/philipp/software/claude-projects)
set -euo pipefail
SRC="${CLAUDE_USER_DIR:-$HOME/.claude}/projects"
DEST="${1:-/projectnb/liu-scc/philipp/software/claude-projects}"

if [ -L "$SRC" ]; then echo "already a link: $SRC -> $(readlink "$SRC")"; exit 0; fi
recent=$(find "$SRC" -mmin -10 -type f -print -quit)
if [ -n "$recent" ]; then echo "refusing: $recent changed in the last 10 min; close every Claude session first"; exit 1; fi

mkdir -p "$DEST"
rsync -a "$SRC"/ "$DEST"/
listing() { (cd "$1" && find . -type f -printf '%P %s\n' | sort); }
if ! diff <(listing "$SRC") <(listing "$DEST") >/dev/null; then
  echo "copy differs from source (names or sizes); nothing moved"; exit 1
fi
old="$SRC.moved-$(date +%Y%m%d-%H%M)"
mv "$SRC" "$old"
ln -s "$DEST" "$SRC"
echo "moved $(find "$DEST" -type f | wc -l) files to $DEST; old copy at $old"
echo "after one session starts fine, delete it: rm -r '$old'"
