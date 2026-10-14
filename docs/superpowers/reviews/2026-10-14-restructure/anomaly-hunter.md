# anomaly-hunter findings — 2026-10-14 restructure review

Start: HEAD 076b0f8 (brief names ec42c36 as the spec commit; HEAD is already later), porcelain = 3 untracked review files only.
Scripts: scratchpad/anomaly-hunter/{m.py,dec.py,reg.py,sav.py}. Transcripts: ~/.claude/projects/-projectnb-liu-scc-philipp/ (13 main sessions with usage, 755 subagents).

### F1 [Important] The spec UNDERSTATES our share: "~122 KB ≈ 30k tokens" is ~41k tokens, and in a review seat it is ~80% of first-call context
Evidence: every subagent transcript records an `attachment.type=instructions` with the exact files injected. Across all 755 subagents that
attachment held 84.8k–121.7k bytes (rules grew over the period). OLS of first-call context on (instruction bytes, system-prompt bytes,
dispatch-prompt bytes) with per-agent-type intercepts, n=755, residual sd 2.8k:
  instructions 0.335 tokens/byte (= 2.99 bytes/token, not the spec's 4); seat intercepts 4.6k–7.0k; general-purpose intercept 28.1k.
Clean within-version cross-check: critic-reviewer on CC 2.1.280, rules 84,099 -> 94,819 bytes, first ctx 39,027 -> 43,412 (2.44 B/tok).
So today's 122.5 KB ≈ 41k tokens. Current anomaly-hunter seat (this run): first call 50,755 tokens, of which ~41k is our text.
Main session today: 99,996 first-call, ~41% ours; the rest is system prompt + tools (23.4k cached prefix) + skill/agent/MCP listings.
Why it matters: §2's headline and §5.1's "32 KB ≈ 8k tokens" both use 4 B/token; 32 KB is ~10.7k tokens. The *direction* favours the
spec (bigger saving than claimed, ~30k per seat rather than ~20-25k), but every token figure in §2/§4/§5.1/§6 is off by ~1/3 and
`context_budget.py` must not convert bytes at /4. Proposed change: state bytes as the budget unit, or calibrate tokens/byte from this
regression; rerun §2 row 3.
Branch A/B: A = regression confounded by time (plugins/agent bodies grew alongside rules) — the within-version pair (2.44 B/tok) argues
against A inflating it; B = the tokenizer is simply denser on this markdown (paths, backticks, numbers). Test: one count_tokens API call
on verification.md settles it.

### F2 [Important] MEMORY.md IS loaded into subagents here — spec §3.10 ("main session only, not in subagents") is false for this workspace
Evidence: all 755/755 subagent transcripts' instructions attachment lists exactly
('CLAUDE.md','CLAUDE.md','MEMORY.md','scc.md','subagent-dispatch.md','verification.md'); this seat's own context contains MEMORY.md
verbatim (14,597 escaped bytes). Why it matters: §5.1 table says "Memory index | main session only"; seat budget and
the "omitClaudeMd drops what?" question must include memory (14 KB ≈ 4.7k tokens per seat). Either the docs describe a different
CC version (2.1.299 here) or the docs are wrong; whichever, the spec must be based on the transcript, not the doc. Test whether
`omitClaudeMd: true` also drops MEMORY.md and the rules: one seat run with it, then read its instructions attachment — the transcript
records the answer directly (this also settles the brief's unverified omitClaudeMd claim with no reasoning required).

### F3 [Important — premise] Cost is not dominated by the first-call baseline in MAIN sessions; it is dominated by accumulated context
Evidence (all main sessions, 12,095 deduped calls; cost units = 1.25·cache_write + 0.1·cache_read + 5·output, Opus ratios):
  cache_read 74% of main cost, cache_write 18%, output 8%. Mean context per main call = 489k tokens.
  Calls by context size: >500k = 5,840 calls carrying 69% of main cost; <100k = 230 calls, 0.6%.
  Simulated cut of 30k from every call (0.1x on cache hits, 1.25x on rebuilds): main -5.6% cost; subagents -20.5%.
  Subagents total 923M cost units vs main 801M; subagent first calls have cache_read=0 in the median (each seat pays 1.25x on its
  whole ~50k baseline, 2,098 rebuild calls in 39,062).
Why it matters: §1's "fraction of the token cost" is achievable for SEATS (where our text is ~80% of their start and they are short,
median 41 calls), not for the main session, where a 30k cut is ~5% because each call already carries ~490k. The bigger main-session lever
— compaction/session-splitting policy, or handing long work to seats — is not in the spec at all. Proposed change: §6 realistic target
should state per-arena savings (seats ~20%, main ~5%) and add a main-session context-length policy as an approach row.

### F4 [Important] The seat redesign targets ~21% of subagent spend; general-purpose dispatches are 79% and get none of §5.4
Evidence (755 subagents, meta.json agentType, cost units as F3): general-purpose 0.790 of subagent cost (411 agents, 27,006 calls);
all named review seats combined 0.21 (critic 0.085, domain 0.045, inventory 0.024, ...). Regression intercepts (F1): general-purpose
carries ~28k tokens of non-instruction baseline vs 4.6k–7.0k for seats — ~23k of tool schemas/listings from an unrestricted tool set.
The spec's subagent range "49.6k–72.5k" mixes these two populations: the top of it is general-purpose, the bottom seats.
Why it matters: §5.4's "~20-25k per seat" is real per seat but the spend is in implementers/general workers, which keep loading
CLAUDE.md+core (no omitClaudeMd) and the full tool list. Proposed: add a row for general-purpose/implementer dispatches — a named
`implementer` agent with a `tools:` allowlist would remove most of the ~23k intercept, which is the single largest per-agent
lever measured here and is absent from the spec.

### F5 [Important — premise] "Over-verification" (Opus 5 docs) is imported without in-workspace evidence, and the spec cuts where no waste is measured while adding where waste IS recorded
Observation: `command grep -il "over-verif|wasted|redundant"` over memory/*.md and .claude/context/learnings.md finds no record of verification
as a cost problem. What IS recorded:
 - verification that fired and prevented defects: the stop rule ("the only thing that caught an error before publication", subagent-dispatch.md
   W2 section); the contradiction slot (5 false claims 2026-08-29, 14 in W14); the findings-file rule (3-for-3 deliverables saved);
   memory feedback_keep_going_means_run_the_cycle ("dispatched reviews were the single highest-yield activity"; Tasks 8-13 without review shipped defects).
 - verification that did NOT pay: memory feedback_external_check_beats_more_gates — "four gates, three test files, six review seats" over one
   project; none could go red because a number was wrong; one external script found what all of them missed.
 - the generic layer is near free: the Stop hook produced output on 23 of 1,587 stop events (1.4%) across all main transcripts
   (`hookErrors` non-empty in `stop_hook_summary` records).
Third state the spec does not name: checks that are neither GENERIC (Opus-5 duplicates) nor PROVEN (fired after a real failure) — i.e.
self-consistency layers (more gates, more seats) whose yield is unmeasured and, in the one measured case, ~zero. That is where an
over-verification cost actually lives in this workspace. The spec drops the cheap generic line (§3.1) but keeps all 11 seats and ADDS a
12th (lean-critic) and a `completion-check` skill with vulture/mutmut/diff-cover — more self-consistency instruments.
Discriminating test: for the last N wave-end reviews under docs/superpowers/reviews and project review dirs, tabulate findings per seat that
were (a) acted on and (b) unique to that seat. Branch A (premise wrong for us): every seat has unique acted-on findings → keep all, the
generic cut is cosmetic. Branch B (premise right, misapplied): some seats have ~0 unique acted-on findings → those, not the CLAUDE.md
line, are the over-verification to cut, and lean-critic should not be added without the same measurement.

### F6 [Important — premise] The workspace's own "rule existed and was not followed" incidents are mostly NOT length/burial failures
Classified from the rule files' own records (subagent-dispatch.md, verification.md):
 1. caller-owns-qsub (subagent-dispatch.md ~l.18, l.39): rule stated 3x and quoted VERBATIM in the brief; violated twice. Cause: structural (agent cannot finish in-turn). Not length.
 2. findings-file-first (l.657-664): controller missed it because it "sits mid-paragraph" — BURIAL. Supports the premise. But the same rule given
    explicitly in a dispatch was still ignored once (144k tokens) — cause: agent reads brief and starts investigating; fixed by "literal first action".
 3. three-state collapse (verification.md): 5 instances, 2 "by agents whose briefs quoted the convention". Cause: prose convention cannot cross a
    boundary; fix was types. Not length.
 4. explicit-path commit (l.~150): "Both agents had read the explicit-path rule; one ... got the flag order wrong." Cause: execution detail. Not length.
 5. W2 six wrong citations "every one the controller's" + "Watch for the asymmetry" (verification.md end): rule applied outward, not to self. Not length.
 6. TC-NC rule wrong twice: the RULE CONTENT was the failure. Not length.
Tally: 1 of 6 is the failure mode the spec's premise names; 3 of 6 were fixed by MECHANISM (caller submits, types, `git show --stat` check).
Why it matters: §1 promises "rules Claude actually follows because they are no longer buried"; on this record, slimming fixes ~1/6 and
moving rules into description-matched skills converts the one burial failure (a line missed inside a LOADED file) into a worse one (a whole
file not loaded). Proposed change: make §5.5 (hooks/mechanism) the primary adherence lever and state slimming's goal as cost, not adherence;
add the 6 incidents to §9.2 evals (each has a grep-able expected behaviour already).

### F7 [Important] The weird number: main first-call context grew 78.5k -> 100.0k in four weeks, and under half of that is our text; the newest growth is MCP connectors the spec does not list
Evidence (main transcripts, first assistant `usage`, deduped by message id): 2026-09-17 78,545; 09-24 77,603; 09-29 92,379; 10-07 91,074/93,076;
10-14 99,996. Our instruction bytes over the same span: ~84 KB -> 125.9 KB (attachment `instructions`) ≈ +14k tokens at 3 B/tok.
Last week alone (10-07 -> 10-14, +8.9k tokens): `instructions` +1.3 KB; `deferred_tools_delta` 5,360 -> 16,066 B; `mcp_instructions_delta`
2,157 -> 6,203 B (claude.ai alphaXiv / bioRxiv / Claude Docs / Undermind connectors). Today's non-our-text attachments: skill_listing 24.7 KB
(anthropic-skills entries alone 10.3 KB), deferred_tools 16.1 KB, agent_listing 7.5 KB, mcp_instructions 6.2 KB, superpowers SessionStart
inject 3.7 KB ("<EXTREMELY_IMPORTANT>" — the exact emphasis style §5.7 bans in our files), plus a 23.4k cached tool/system prefix.
Second oddity: in both main transcripts checked, deferred_tools / agent_listing / mcp_instructions deltas are recorded TWICE before the first
call. Byte-sum reconstruction of the 10-14 first call fits 100k better with the duplicates counted (~98k) than without (~89k); not conclusive at
an uncertain bytes/token.
Branch A: transcript logging artefact, the duplicates are not sent — then the growth is just connectors. Branch B: they are sent twice —
then ~10k tokens/session is a harness duplication that no amount of rule slimming touches. Test: start one session with the MCP connectors
disabled and one enabled, diff first-call usage against the delta byte size (×1 vs ×2).
Why it matters: §2's table attributes the baseline to our files + plugins and omits connectors/deferred tools entirely; §6 target
"main first-call −20k" can be eaten by one week of connector growth. `context_budget.py` (§5.6) sums only OUR bytes, so it cannot see the
fastest-growing component. Proposed: budget script reads the transcript `attachment` sizes (they are all recorded) rather than re-deriving
from source files; add connectors to §2 and to the owner-recommendation list in §5.9.

F2 addendum: the docs DO say what the spec says — code.claude.com/docs/en/memory: "The main conversation's auto memory isn't loaded into
subagents; the exception is a fork". Observed behaviour on CC 2.1.270–2.1.299 contradicts the docs in 755/755 subagents. So this is a
doc/behaviour mismatch, which means every load-behaviour premise in §3.8/§3.10 (incl. omitClaudeMd scope) must be settled from a transcript's
`instructions` attachment, not from the docs. Upgrade suggestion: make "read the instructions attachment of one seat run" the acceptance
test for §5.4 before any seat is migrated.

## Close
End: HEAD 076b0f8, porcelain unchanged (3 untracked review files). HEAD did not move during this review; it was already past the brief's ec42c36 at start.
Strongest unasked objection: the spec optimises the 5% lever in the main session (baseline) and ignores the 69% lever (calls at >500k
context; mean main-call context 489k). See F3.
Brief wrong: (a) "measured baseline accepted" — numbers are fine, the token conversion (4 B/tok) and "memory main-only" interpretation are not (F1, F2);
(b) brief cites spec commit ec42c36, HEAD is 076b0f8; (c) subagent range 49.6k–72.5k pools seats and general-purpose (F4).
Most want to be true: deferred-tool/MCP deltas are sent twice per session (F7 branch B) — test: connectors on/off, diff first-call usage.
