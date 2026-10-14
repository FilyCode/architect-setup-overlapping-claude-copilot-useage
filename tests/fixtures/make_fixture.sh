#!/bin/bash
# Usage: make_fixture.sh <real-subagent.jsonl> <out-dir>
# Keeps the first 60 lines; replaces every string longer than 40 chars with x's of equal length.
set -euo pipefail
src="$1"; out="$2"; mkdir -p "$out/sub"
head -n 60 "$src" | jq -c 'walk(if type == "string" and (length > 40) then ("x" * length) else . end)' \
  > "$out/sub/agent-fixture.jsonl"
cp "${src%.jsonl}.meta.json" "$out/sub/agent-fixture.meta.json"
