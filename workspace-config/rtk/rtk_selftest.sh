#!/bin/bash
# rtk_selftest.sh — regression harness for rtk's Bash-hook rewrites.
#
# POLICY UNDER TEST: allowlist. Only `cat` is rewritten (to `rtk read`); everything else runs
# raw. Rationale is in ~/.config/rtk/config.toml and .claude/rules/verification.md; the short
# version is that the usage DB shows a median saving of 0 tokens per call, with 91% of all
# lifetime savings coming from the 10 largest calls (chiefly one `find / -name '*'`).
#
# WHAT IT CHECKS
#   Layer 1  the hook's rewrite DECISION: only cat is allowed through   (rtk hook check)
#   Layer 2  the BEHAVIOUR of excluded commands, vs the absolute native binary
#   Layer 3  `rtk read` fidelity — the one adapter the allowlist still depends on
#   Layer 4  known rtk defects we cannot configure away, asserted so a fix/regression shows up
#
# Layer 2 asks the REAL hook what it would run and executes exactly that. An earlier version
# just ran `grep -v` and compared to a hardcoded string, which was vacuous: inside a bash script
# the PreToolUse hook does not apply and Claude Code's `grep` shim is not exported, so it tested
# /usr/bin/grep against its own fixture and could never fail.
#
# Deliberate deviation from shell.md's `set -euo pipefail`: this is a test harness, so `set -e`
# would abort on the first failing check instead of reporting all of them, and `pipefail` would
# trip the intentional `| wc -l` counts. Failures are counted and returned as the exit status.
#
# Usage: bash software/bin/rtk_selftest.sh        (exit 0 = all pass)
#        bash software/bin/rtk_selftest.sh -v     (also print rtk gain, to watch savings drift)

set -u
V=${1:-}
pass=0; fail=0
CFG="${XDG_CONFIG_HOME:-$HOME/.config}/rtk/config.toml"
GREP=/usr/bin/grep; DIFF=/usr/bin/diff; CAT=/usr/bin/cat; GIT=$(command -v git)

ok()  { pass=$((pass+1)); printf '  ok    %s\n' "$1"; }
bad() { fail=$((fail+1)); printf '  FAIL  %s\n' "$1"; }

effective_cmd() { # what Claude Code would actually run, from the real hook's JSON
  local out
  out=$(printf '%s' "$1" | python3 -c 'import json,sys
print(json.dumps({"tool_name":"Bash","tool_input":{"command":sys.stdin.read()}}))' \
        | rtk hook claude 2>/dev/null)
  [ -z "$out" ] && { printf '%s' "$1"; return; }
  printf '%s' "$out" | python3 -c 'import json,sys
try: print(json.load(sys.stdin)["hookSpecificOutput"]["updatedInput"]["command"])
except Exception: sys.exit(1)' 2>/dev/null || printf '%s' "$1"
}

echo "== rtk $(rtk --version 2>&1 | awk '{print $2}')  config: $([ -e "$CFG" ] && echo present || echo MISSING) =="
[ -e "$CFG" ] || bad "config.toml missing — exclude_commands empty, NOTHING excluded"
# An unparseable config silently restores zero exclusions with no warning, so prove rtk actually
# parsed our patterns rather than trusting that the file exists. (This exact failure happened:
# a "..." basic string containing \s is invalid TOML and wiped every exclusion.)
if rtk config 2>/dev/null | $GREP -q "\^cat"; then
  ok "config parsed by rtk (allowlist patterns present in effective config)"
else
  bad "rtk did NOT parse the exclusion patterns — invalid TOML? every command is being rewritten"
fi

# --- Layer 1: only `cat` may be rewritten ----------------------------------------------------
chk() { # chk "<cmd>" EXCLUDED|REWRITTEN
  local got act
  got=$(rtk hook check "$1" 2>&1)
  case "$got" in "No rewrite"*) act=EXCLUDED ;; *) act=REWRITTEN ;; esac
  if [ "$act" = "$2" ]; then ok "$2  $1"; else bad "$1 -> got $act, want $2 ($got)"; fi
}

echo "-- layer 1a: everything except cat must run RAW --"
for c in "grep x f" "grep -v x f" "grep -vn x f" "grep -h x f" "grep -l 5 a b" "grep -rn x ." \
         "rg x" "rg -v x" \
         "find . -name '*.py'" "find .claude -name '*.md'" \
         "diff a b" "tree ." "ls -la" "wc -l f" \
         "git status" "git diff" "git log -1" "git -C /r log --oneline" "git --no-pager log -1" \
         "git commit -m x" "git push" "git show HEAD" \
         "pytest tests/" "ruff check ." "mypy ." "make" "ps aux" "du -sh ." "curl http://x" \
         "npm run b" "docker ps" "cargo build" "rsync -av a b" "gh pr list"; do
  chk "$c" EXCLUDED
done

echo "-- layer 1b: the allowlist — cat only --"
for c in "cat f.txt" "cat -n f.txt" "cat /a/b.txt"; do chk "$c" REWRITTEN; done

# --- Layer 2: excluded commands must behave exactly like the native binary --------------------
echo "-- layer 2: excluded commands vs NATIVE binary (stdout + exit code) --"
T=$(mktemp -d) || exit 1
trap 'rm -rf "$T"' EXIT
printf 'threshold = 0.85\nmode = strict\n' > "$T/cfg.txt"
printf 'alpha\nbeta\n' > "$T/a.txt"
printf 'alpha\nBETA\n' > "$T/b.txt"
printf 'v 5\nv 7\n'    > "$T/n1.txt"
printf 'x 5\n'         > "$T/n2.txt"

same_as_native() { # "<native cmd>" "<as-typed>" "<label>"
  local nout nrc eff eout erc
  nout=$(eval "$1" 2>&1); nrc=$?
  eff=$(effective_cmd "$2"); eout=$(eval "$eff" 2>&1); erc=$?
  if [ "$nout" = "$eout" ] && [ "$nrc" -eq "$erc" ]; then ok "$3 (native==effective, rc=$nrc)"
  else bad "$3 -> differs. effective=[$eff] rc native=$nrc eff=$erc"; fi
}

same_as_native "$GREP -v threshold $T/cfg.txt"  "grep -v threshold $T/cfg.txt"  "grep -v (was: inverted)"
same_as_native "$GREP -vn threshold $T/cfg.txt" "grep -vn threshold $T/cfg.txt" "grep -vn (was: inverted)"
same_as_native "$GREP -h threshold $T/cfg.txt"  "grep -h threshold $T/cfg.txt"  "grep -h (was: usage banner)"
same_as_native "$GREP -l 5 $T/n1.txt $T/n2.txt" "grep -l 5 $T/n1.txt $T/n2.txt" "grep -l NUMERIC (was: value swallow)"
same_as_native "$GREP -rn threshold $T"         "grep -rn threshold $T"         "grep -rn (plain search)"
same_as_native "$DIFF $T/a.txt $T/b.txt"        "diff $T/a.txt $T/b.txt"        "diff (was: exit 1 -> 0)"

if [ -n "$GIT" ]; then
  ( cd "$T" && $GIT init -q m && cd m \
    && $GIT -c user.email=t@t -c user.name=t commit -q --allow-empty -m base \
    && $GIT checkout -q -b side \
    && $GIT -c user.email=t@t -c user.name=t commit -q --allow-empty -m side \
    && $GIT checkout -q - \
    && $GIT -c user.email=t@t -c user.name=t commit -q --allow-empty -m main2 \
    && $GIT -c user.email=t@t -c user.name=t merge -q --no-ff -m MERGE-COMMIT side ) >/dev/null 2>&1
  if $GIT -C "$T/m" rev-list --merges --count HEAD 2>/dev/null | $GREP -q '^[1-9]'; then
    same_as_native "$GIT -C $T/m log --oneline -5" "git -C $T/m log --oneline -5" \
                   "git log (was: silent --no-merges)"
  else
    printf '  skip  git log merge check — could not build a merge commit\n'
  fi
fi
# find is now excluded, so it must be complete — including hidden and gitignored hits, the two
# classes rtk find silently dropped.
mkdir -p "$T/h/.hidden"; touch "$T/h/.hidden/needle.py" "$T/h/plain_needle.py" 2>/dev/null
mkdir -p "$T/h/plain"; touch "$T/h/plain/needle.py"
same_as_native "/usr/bin/find $T/h -name '*needle*' | sort" "find $T/h -name '*needle*' | sort" \
               "find sees hidden paths again"

# --- Layer 3: rtk read fidelity — the allowlist's single dependency ---------------------------
echo "-- layer 3: rtk read must be byte-identical to cat (the one adapter we still trust) --"
printf 'a\tb\n  spaced  \nunicode: \xce\xb1\xce\xb2\xce\xb3\nno-trailing-newline' > "$T/mixed.txt"
seq 1 300 | sed 's/^/line /' > "$T/long.txt"
python3 -c "open('$T/wide.txt','w').write('x'*5000+'\n'+'y'*200+'\n')"
printf 'only line, no newline' > "$T/nonl.txt"
for f in mixed.txt long.txt wide.txt nonl.txt; do
  a=$($CAT "$T/$f" | md5sum | cut -d' ' -f1)
  b=$(rtk read "$T/$f" 2>/dev/null | md5sum | cut -d' ' -f1)
  if [ "$a" = "$b" ]; then ok "rtk read == cat for $f"
  else bad "rtk read CORRUPTS $f — the allowlist's only remaining adapter is no longer faithful"; fi
done

# --- Layer 4: rtk defects that cannot be configured away -------------------------------------
echo "-- layer 4: known rtk bugs (asserted so a fix or regression is visible) --"
# head/tail bypass exclude_commands entirely: even an explicit '^head\b' does not stop them,
# while '^[^c]' correctly excludes ls and grep. So `head -N` still becomes `rtk read --max-lines`,
# which under-delivers (head -20 returns ~10 lines, disclosed as "[N more lines]").
# Workaround, and why the rules say to prefer it: `head -n 20` and `head -c 100` run raw.
if [ "$(rtk hook check 'head -20 f' 2>&1)" = "No rewrite for: head -20 f" ]; then
  ok "head -N is now excludable — rtk fixed it; simplify the rules and drop the -n workaround"
else
  ok "head -N still bypasses exclude_commands (known rtk bug) — prefer 'head -n N'"
fi
if [ "$(rtk hook check 'head -n 20 f' 2>&1)" = "No rewrite for: head -n 20 f" ]; then
  ok "the 'head -n N' workaround still runs raw"
else
  bad "'head -n N' is now rewritten too — the documented workaround is dead, update the rules"
fi

if [ -n "$V" ]; then
  echo "-- savings (allowlist baseline: median 0 tok/call; pre-change lifetime 1976.0M) --"
  rtk gain 2>&1 | sed -n '1,10p'
fi

echo
echo "PASS=$pass FAIL=$fail"
[ "$fail" -eq 0 ]
