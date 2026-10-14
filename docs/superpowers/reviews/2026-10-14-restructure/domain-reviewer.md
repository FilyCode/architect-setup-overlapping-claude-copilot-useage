# Domain review (LLM agent-harness / prompt-engineering role) — 2026-10-14 restructure

Start: HEAD 076b0f8; status = 3 untracked review files (critic, anomaly, domain). CLI 2.1.299.

### F1 [Important] Spec §3.10 / §5.1 "auto memory loads in the main session only, not subagents" is false on this install — every review seat in THIS wave received MEMORY.md
Evidence: first-message attachment of the critic-reviewer seat transcript
`~/.claude/projects/-projectnb-liu-scc-philipp/b989fe41-.../subagents/agent-a2c4b6ad281bb8ebf.jsonl` line 5,
parsed with a JSON walk (not grep):
```
User    ~/.claude/CLAUDE.md                     653 chars
Project /projectnb/liu-scc/philipp/CLAUDE.md   1569
Project .../rules/subagent-dispatch.md        56052
Project .../rules/verification.md             46782
Project .../rules/scc.md                       5534
AutoMem .../memory/MEMORY.md                  14469
```
Same `AutoMem` attachment in anomaly-hunter (agent-a9d7513e2f710d847) and this seat (agent-a2f02e3f933141eae);
all three are named, non-fork agents (`.meta.json` agentType critic-reviewer / anomaly-hunter / domain-reviewer,
spawnDepth 1). The docs (code.claude.com/docs/en/memory: "The main conversation's auto memory isn't loaded into
subagents"; sub-agents page says the same) are contradicted by the installed harness (2.1.299).
Why it matters: (a) the "Memory index — main session only" row in §5.1 is wrong, so MEMORY.md is ~3.6k tokens in
every seat, not 0; (b) it is a different attachment type (`AutoMem`, not `Project`/`User`), so whether
`omitClaudeMd: true` drops it is UNKNOWN — the per-seat saving projection (~20–25k) silently assumes either answer;
(c) MEMORY.md carries behavioural rules ("never route around a blocked permission", transient-vs-not-found) that
seats are currently receiving and the spec does not know they receive.
This is the spec trusting a doc over the harness — the exact move the workspace's own rules forbid.
Proposed change: §3.10 → "docs say main-only; measured: loaded into named subagents on 2.1.299". Before Task 1, run
one throwaway agent with `omitClaudeMd: true` and read its first-message `attachment.files` types (the same 10-line
parse above). `context_budget.py` must compute a SEAT budget (incl. AutoMem unless measured absent), not only main.

### F2 [Blocking] §3 reads Opus-5 guidance as model-general; the "drop generic verification" premise is reversed by Anthropic for the Sonnet 5.5 / Haiku 5.5 / low-effort seats the same spec creates
Evidence (WebFetch 2026-10-14, verbatim):
- prompting-claude-opus-5: "Claude Opus 5 verifies its own work without being told to ... remove them". Best-practices
  page, thinking section: "Ask Claude to self-check ... Claude Opus 5 is the exception" — i.e. self-check prompting is
  still the general recommendation; Opus 5 is the carve-out.
- prompting-claude-sonnet-5-5: "At `low`, it keeps its thinking short and can skip verifying a change" — and Anthropic
  ADDS a verification paragraph ("run a real check that exercises the change before reporting it done ... A
  syntax-only check, or a check command that failed to start, does not count").
- prompting-claude-haiku-5-5: "At `low` and `medium` effort, Claude Haiku 5.5 sometimes reports a code change as done
  without running a check" → same added paragraph; also "`low` ... more likely to skip a search, stop early, or skip a
  check"; "With a long coding-agent system prompt at `low` effort, it sometimes stops early".
- The spec (§3.1, §3.7) never cites the Opus 5.5, Sonnet 5.5 or Haiku 5.5 pages, although the workspace runs those
  models (this seat is claude-opus-5-5). Opus 5.5's page says Opus-5 prompts "remain a reasonable starting point" —
  so for opus seats §3.1 holds; for nothing else does it hold by citation.
Collision with §5.4: scc-monitor = haiku/low (its whole job is checking that a job really succeeded), research-scout
= sonnet/low, docs-sync = sonnet/low, and four more seats at sonnet/medium. These are exactly the model×effort cells
where Anthropic says verification gets skipped and early stopping rises.
What a reader would wrongly conclude: that removing generic verification text is safe workspace-wide. It is safe for
Opus seats and for the main session only if it runs Opus.
Answer to the dispatch's question "is the line drawable?": yes, with a mechanical test, but the line is per-model:
- SPECIFIC (keep everywhere): names a silent failure the model cannot infer from the repo or general knowledge —
  `qacct exit_status 0` from a tool that swallows errors; shell `grep` skipping gitignored paths; `hmmsearch --cut_tc`
  gating `--tblout` and `--domtblout` differently; `conftest.py` re-inserting `src/` so a RED proof runs the current
  tree. Litmus: *could a strong model with no access to this workspace have written this line?* If no, it is specific.
- GENERIC (drop on Opus, keep ONE line on Sonnet/Haiku seats): "verify before claiming done", "double-check".
- METHOD (keep, it is neither): "a gate counts only after you have seen it fail", "assert non-zero before comparing two
  arms read through one code path". Models verify by default; they do not mutation-test their own gates by default.
  Classifying these as "generic verification" is the main way the cut will lose real lessons — core.md item 1's second
  sentence is in this class and is correctly kept; its first sentence ("artifact, not exit code") is generic on Opus.
Proposed change: §3.1 add the per-model table above; §5.4 every sonnet/haiku seat body carries Anthropic's own
verification paragraph (adapted: "run the check / read the artifact before reporting"), and haiku/sonnet seats at
`low` move to `medium` unless an eval shows otherwise (see F5). Cite the 5.5 pages, not only Opus 5.

### F3 [Important] §5.5 `CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS=3` does not "replace the memory prose cap" — it changes a slowdown into a refused spawn that tells Claude not to retry
Evidence: code.claude.com/docs/en/sub-agents (WebFetch): "By default, when 20 subagents are running in a session,
spawning another with the Agent tool fails with `Concurrent subagent limit reached`, and the error tells Claude not to
retry. Spawning succeeds again when the running count drops below the limit." Also: "Sessions with ultracode active
are exempt".
Why it matters: plan-critique allows "up to ~10" seats and wave-review rosters run 5-7. With the cap at 3, a parallel
batch of 6 Agent calls returns 3 refusals carrying a do-not-retry instruction. The likely model behaviour is to report
three seats as "could not run" — a silently thinner wave that still reads as a full wave in the close-out. The prose
cap described *batching*; the env var implements *rejection*.
Proposed change: keep the env var, and keep one line in `wave-review`/`plan-critique`: "Launch at most 3 seats at
once; a `Concurrent subagent limit reached` reply means re-dispatch that seat when one finishes, not that it is
skipped. The close lists every seat as ran/not-ran." Add one of the §9.2 evals: a 6-seat wave must end with 6 reports.

### F4 [Important] Skill bodies are truncated to their first 5,000 tokens after compaction; the spec's only size limit (≤500 lines) does not protect the long main sessions this workspace runs
Evidence: code.claude.com/docs/en/skills (WebFetch): "Claude Code re-attaches the most recent invocation of each skill
after the summary, keeping the first 5,000 tokens of each. Re-attached skills share a combined budget of 25,000
tokens ... older skills can be dropped entirely". Main sessions here run 1,880-2,854 API calls (transcripts
7582cefc / 453ec45c, usage parse), i.e. they compact. `verification-patterns` and `scientific-evidence` are cut from
a 46.8 KB file; 500 lines of this workspace's ~95-char prose is ~47 KB ≈ 12k tokens, so after one compaction more
than half of such a skill silently disappears, and with `dispatch-brief` + `wave-review` + `plan-critique` +
`running-sge-jobs` invoked in one session, the 25k pool drops whole skills.
Also from the same page: invoked skill text "stays there across later turns ... write guidance that should apply
throughout a task as standing instructions rather than one-time steps" — relevant to §5.7.
Proposed change: §5.3/§5.7 add "skill body ≤ ~18 KB (~4.5k tokens); the rules a skill exists to enforce come first,
worked examples and `reference/` after"; `context_budget.py` checks per-skill bytes. Put the bio worked examples in
`reference/` files (loaded on demand, not re-attached), as §5.3 already does for scientific-evidence — extend that to
verification-patterns.
Also: none of the process skills may set `disable-model-invocation: true` (the docs recommend it for side-effect
workflows, an author may reach for it): it would stop core.md's "when" lines from invoking them AND blocks preloading.

### F5 [Important] §5.4 tiering is calibrated to Opus-5 effort semantics; three cells are wrong for the 5.5 models and one global setting is missed
Evidence (WebFetch, 5.5 prompting pages): Opus 5.5 "Start at `medium`, the default ... Claude Opus 5.5 at `medium`
matches or exceeds Claude Opus 5 at `high`"; "At a given level, Claude Opus 5.5 tends to think more per turn than
Claude Opus 5". Sonnet 5.5: "At `low` and `medium`, on long agentic tasks, it's more likely to stop and check in with
the user before it finishes"; it "sometimes answers from its training knowledge when a web search would catch details
that have changed". Haiku 5.5: "`medium` is the default. Start here for most work"; `low` "more likely to skip a
search, stop early, or skip a check". Live: `~/.claude/settings.json` `effortLevel: "high"` (python json parse);
agents currently: research-scout haiku/low, scc-monitor haiku (no effort), others no `effort` key.
Cell by cell:
- critic-reviewer opus/medium, figure-auditor opus/medium: right (Opus 5 page: review "accuracy holds at lower effort").
- domain-reviewer / anomaly-hunter / security-specialist opus/high: defensible, but note high on 5.5 is above Opus-5
  high; make anomaly-hunter+security high, domain-reviewer medium, and let the eval decide.
- scc-monitor haiku/low: wrong. Its job is "is this success real?" — the exact behaviour Haiku skips at low. → haiku/medium.
- research-scout sonnet/low: wrong for a search-and-synthesise seat → sonnet/medium plus Anthropic's search line
  ("Use the search tool to check specifics that may have changed ... even when you feel confident").
- docs-sync sonnet/low → sonnet/medium (checks against live files are its whole job).
- All sonnet seats run as background, non-interactive (this wave's `.meta.json`: `requestShape: background`,
  `requestNonInteractive: true`). A Sonnet "check-in" there is an end of turn with no report — the 162k-token
  one-sentence failure the old rules record. Put Anthropic's carry-through paragraph ("Keep working until everything
  the user asked for is done ... When the work ... is done and checked, stop and report") in every sonnet seat body.
- Missed: the main session's global `effortLevel: high` on Opus 5.5. Anthropic names effort, not prompt text, as the
  first lever for thinking/output tokens. The spec should at least name it as an owner decision.
Minor-triage not applicable (filed Important): the stated per-seat settings change.

### F6 [Important] §5.7 writing standard: right direction, but its "no numbers" rule and missing example rule will strip exactly the content that makes a domain lesson override the model's prior
What the standard gets right (keep, do not re-open): imperative one-rule bullets; "because <one clause>" (Anthropic's
own example: the reason lets Claude "generalize from the explanation"); no CAPS/CRITICAL (best-practices: "dial back
any aggressive language"); markdown headers + bullets for loaded files (memory docs: "Organized sections are easier
for Claude to follow than dense paragraphs"); caveman compression not used for instructions.
What is missing or wrong:
1. **Examples.** Anthropic: "Examples are one of the most reliable ways to steer"; "Positive examples ... tend to be
   more effective than instructions about what not to do"; wrap them in `<example>` tags "so Claude can distinguish
   them from instructions". The standard has no example rule, and its "no ... token counts or war stories" line will
   be applied to worked cases too. Distinguish: a NARRATIVE (who, when, what it cost) → history; a WORKED CASE (the
   numbers that show the failure's signature) → stays, ≤3 lines, in `<example>`. Domain lessons in particular need
   the number: "TC−NC is 0.1 for 36.1 % of Pfam" is what stops a model reading a 0.1-bit band as a weak model. Without
   it the rule is an assertion against the model's prior, and loses.
2. **Emphasis.** Code best-practices allows it precisely: "If Claude keeps skipping one instruction, add emphasis such
   as "IMPORTANT" to that line alone. If you emphasize many lines, none of them stands out." So: zero emphasis by
   default; one IMPORTANT in core.md, earned by an eval showing it is skipped — not chosen in advance.
3. **Ordering inside a skill** follows F4: rules first, examples next, reference/history links last, because only
   the first 5k tokens survive compaction.
4. **Trigger phrasing** (for descriptions): front-load the user-visible situation in the user's own words (qsub,
   `Eqw`, "job finished?", "absent in clade"), put trigger phrases in `when_to_use` (docs: "trigger phrases or example
   requests"), and end with a boundary clause naming the sibling skill ("Not for code-level checks — use
   verification-patterns"). Third person, as stated.
5. **Positive form** works for this workspace's negative knowledge only if the replacement names the positive
   evidence: "`qacct exit_status 0` is not success" → "prove success by the artifact on disk" loses the reason the
   exit code is wrong. Keep the "X is not evidence of Y — because" form when the model's prior is X.

Demonstration (scratch copies under `/scratch/.../scratchpad/domain-reviewer/{old,new}{1,2,3}.md`; bytes by `wc -c`):
| Old section | Old | New | Precision lost |
|---|---|---|---|
| scc.md "Waiting on a job without burning tokens" | 2,774 B / 33 lines | 1,022 B / 13 lines | sleep-interval tuning advice (low value). GAINED: the old file gives two loops, each half right — the `qstat -j` loop has the deadline but the transient-exit bug; the listing-form loop fixes that but has **no deadline**, and an `Eqw` job stays in `qstat -u` output forever, so it never exits. The rewrite merges them (`bash -n` OK). |
| verification.md "When a tool writes two reports..." | 2,677 B / 39 lines | 1,086 B / 6 lines | the 4-row damage table, kept as one clause ("losses grow with domain count") — had §5.7 been applied literally ("no token counts"), the signature would have been lost |
| subagent-dispatch.md "Concurrent dispatches need declared file ownership" | 1,527 B / 22 lines | 748 B / 5 lines | none found; the incident and "flag order" anecdote go to history |
Total 6,978 → 2,856 B (−59 %). The two history paths cited in the rewrites are hypothetical.
Rewrite of section 2, as it would ship:
## A tool's output formats can be filtered differently
- Before parsing a report, read the manual for that output format, not just the tool: summary vs detail files, `--tblout` vs `--domtblout`, and list vs get API endpoints can apply different filters, silently.
- Answer a membership question ("does this genome have the gene?") from the sequence-level report, and a coordinate question from the domain-level one.
  <example>`hmmsearch --cut_tc` applies the sequence trusted cutoff to `--tblout` and the domain cutoff to `--domtblout`. A divergent SelB hit (full sequence 268.3 vs TC 242.25; best single domain 216.1) passes the first and is absent from the second, with exit status ok. Losses grow with domain count: TIGR00475 (~4 domains) +7.1 %, TIGR00476 (1 domain) +0.</example>
- When two reports should agree, store their difference per run, with a third state "only one report produced: gap not measurable".
- Before reading a subgroup that sits just above a threshold as biology, re-run it through the other report. Background: `docs/history/2026-09-25-cut-tc-domtblout.md`.

Proposed change to §5.7: add items 1-5 above; replace "No dates, incident IDs, token counts or war stories" with
"No narratives in loaded text; a worked case of ≤3 lines that shows the failure's signature stays, in `<example>`".

### F7 [Important] §5.3 skill boundaries: the triggering risk is not the seven custom skills among themselves, it is collision with superpowers skills that fire at the same moments, under a router that says "1% chance ... ABSOLUTELY MUST"
Evidence: `superpowers/6.4.1/skills/using-superpowers/SKILL.md:10-16`:
"<EXTREMELY-IMPORTANT> If you think there is even a 1% chance a skill might apply ... you ABSOLUTELY MUST invoke
the skill. ... YOU DO NOT HAVE A CHOICE." Installed superpowers skills whose descriptions trigger at the same moment
as the proposed ones (`ls ~/.claude/plugins/cache/*/*/*/skills/`, frontmatter read):
| proposed | competes with (superpowers description) |
|---|---|
| verification-patterns / completion-check | verification-before-completion: "Use when about to claim work is complete, fixed, or passing" |
| dispatch-brief | dispatching-parallel-agents: "Use when facing 2+ independent tasks" |
| wave-review | requesting-code-review: "Use when completing tasks, implementing major features, or before merging" |
| plan-critique | writing-plans (self-review step) |
Consequence: at "done", a session plausibly loads verification-before-completion + verification-patterns +
completion-check — three skills, a few thousand tokens, and two of them say the same generic thing that §3.1 says to
delete. §3.1 counts verification-before-completion as one of four duplicate layers, then never decides its fate; the
§5.7 emphasis standard applies only to our files while the single loudest emphasised instruction in every session is
superpowers' router. That is the overtriggering mechanism §7 row 3 attributes to Opus being "proactive".
Verdict on the questions asked:
- Count: seven is about right. Fewer/larger loses to F4 (5k-token compaction cut) and to preloading precision;
  more/smaller multiplies descriptions in the listing and boundary clauses. The two knowledge skills
  (verification-patterns, scientific-evidence) overlap on "gates that cannot fail / positive controls / metric
  checks"; give each a boundary clause and put the shared three items in ONE of them.
- Preloading into seats: right trade. Seats are short-lived, non-interactive (`requestNonInteractive: true` in this
  wave's meta), their job IS the skill, and description-matching in a seat started with `omitClaudeMd` is the least
  observable path. Keep preloading; do not rely on in-seat invocation.
- Process skills (dispatch-brief, wave-review, plan-critique) should be invoked by core.md's "when" lines and should
  NOT also be description-matched: give them `user-invocable` default and a narrow description, and scope the
  dispatch-brief trigger to "dispatching an implementer or review seat" — Opus delegates readily (Explore, research),
  and "any dispatch" makes it load in nearly every session.
Proposed change: §5.3 add a "competes with" column and a decision per row (wrap, defer to superpowers, or disable the
superpowers skill); §9.2 add one eval: "claim done on a small fix" → count skills loaded (target ≤1).

### F8 [Important] The seats that get `omitClaudeMd` are the population that caused the recorded shared-tree incidents, and §5.4's environment block omits those rules
Evidence: docs (sub-agents, WebFetch): with `omitClaudeMd` the seat "loads only the managed policy files"; "If a rule
must [reach the subagent] ... restate it in the prompt". §5.4's env block lists: venv path, scratchpad, read-only
outputs, no files under `tests/`, `command grep`, job spec instead of qsub. Not listed, and each was a REVIEW-SEAT
incident per the live rules: `git --work-tree … checkout` staging a commit (subagent-dispatch.md, "fourth hazard",
"a review seat ran it"), `cp` after a generator `--write` reverting the controller's file ("Fifteenth"), deleting an
untracked `logs/` dir ("Scratch goes in the session scratchpad"), and the HEAD-moves start/end check ("Thirteenth").
§5.5 hooks cover stash / work-tree / rm -rf only if PreToolUse hooks fire on subagent Bash calls — plausible, not
verified in the spec; no hook covers `--write` generators or `cp` over tracked files.
Proposed change: the seat env block gains three lines: "Never run a tool's `--write` mode or `cp` onto a tracked
file — render into your scratch dir and diff there"; "Run `git log -1` and `git status --porcelain` at start and end
and report whether they moved"; "Read past commits only with `git show <c>:<path>`". §5.5: demonstrate each hook
firing inside a subagent, not only in the main session (§9.4).

### F9 [Important] §9.2 behavioural evals cannot establish "unchanged behaviour": 8 scenarios × 1 run on a stochastic model has no power, and the runner is unspecified for an SGE login node
Evidence: §9.2 "8 scenario prompts run headless before and after ... Each has a grep-able expected behaviour."
BRIEF: "Do not run `claude -p` sessions" on the login node; scc.md: >~30 s CPU is reaped. No repeat count, no
pass-rate threshold, no runner.
Why it matters: §9 is the only mitigation for approach B's named risk ("a lesson may not load when needed"). With one
run per arm, a lesson that now triggers 60 % of the time instead of 95 % passes the eval most of the time, and the
"before" arm is not a baseline either. A green 8/8 would then be quoted as "no lessons lost" — a self-consistency
gate presented as a held-out test, which the workspace's own sixteenth rule warns about.
Proposed change: each scenario run k≥5 times per arm (40 runs/arm, headless via `qsub`, low/medium effort to bound
cost), report per-scenario trigger rate with n, declare a pass as "after ≥ before − 1/k". Include two NEGATIVE
scenarios (an ordinary edit that must NOT load wave-review or scientific-evidence) — the overtrigger side of §7 row 3
is otherwise untested. Ship the eval spec as a qsub job spec; the caller submits.

### F10 [Minor] §3.6 cites one Anthropic source; the other says the opposite
Evidence: Opus 5 page: "ask it to report everything and filter in a separate pass"; Code best-practices,
"Add an adversarial review step": "Tell the reviewer to flag only gaps that affect correctness or the stated
requirements, and treat the rest as optional", motivated by "Chasing every finding leads to over-engineering".
Minor-triage: if correct, does a stated conclusion change? No — the workspace's report-all + pragmatism-officer
pattern satisfies both (report everything; the filter pass is where over-engineering is prevented). The spec should
cite both, because the second is the reason pragmatism-officer must run before fixes are commissioned.

### F11 [Minor] §5.9: the humanize-kit recommendation is right, and the reason is stronger than "not suited"
A tool whose purpose is AI-detector evasion conflicts with journal AI-use disclosure policies (the owner's papers are
Nature-family submissions per memory). For `humanizer`, attach the one specific check this workspace already knows:
after any rewrite pass, diff the set of numbers and citations before vs after (a 5-line script) — "preserves claims
and numbers" is a description, not a measurement.
Minor-triage: no stated conclusion changes; it strengthens §5.9's.

## What the spec gets right (do not re-open)
- §3.2-3.4 (no aggressive emphasis, explain why in one clause, positive form) match the cited docs.
- §3.5/3.8/3.9 claims checked against code.claude.com: `omitClaudeMd` drops user/project/local CLAUDE.md AND "project
  rules" (sub-agents page lists project rules inside the CLAUDE.md set), path rules still load on file touch, needs
  v2.1.271 (installed 2.1.299); `skills:` injects full content; skill listing loads name+description only.
- Moving procedures to skills and keeping "when" lines in core is exactly the docs' advice ("If an entry is a
  multi-step procedure ... move it to a skill"); hooks for must-happen-every-time rules likewise.
- Selection test in §5.2 is the docs' own ("Would removing this cause Claude to make mistakes?").
- Report-everything-then-triage (§3.6) is the right reviewer pattern for Opus.
- §2 always-loaded size: seat attachment parse gives 125,059 chars (CLAUDE.md×2 + 3 rules + MEMORY.md), consistent
  with the spec's ~122 KB.

## Strongest objection not asked about: the spec optimises the term that is ~5 % of the bill
Parsed `usage` (dedup by message id) for the two largest main transcripts:
453ec45c: 2,854 calls, cache-read 1,476.8M, cache-write 23.5M, output 3.4M; 7582cefc: 1,880 calls, 907.7M / 28.2M /
1.6M. First-call context 79.9k / 77.6k. Average context per call ≈ 517k / 483k — conversation growth, not rules.
30k tokens of always-loaded text × calls = 86M / 56M = 5.7 % / 6.0 % of tokens, ~4.2-4.4 % cost-weighted (list-price
ratios read .1, write 1.25, output 5; approximate). For the 40 largest subagent transcripts (median 172 calls,
median first call 69.9k), static text is a median ~9 % of cost-weighted tokens (range 4-33 %).
So approach B, executed perfectly, cuts roughly 4-5 % of a long main session and ~5-10 % of a long seat. The owner's
goal ("reduce token use majorly") is set by: context hygiene (`/clear` between tasks, deliberate `/compact`), number
and size of seats per wave, and effort (global `effortLevel: high` on Opus 5.5, whose default is medium and whose
medium ≈ Opus-5 high). None of these is in the spec. The restructure is still worth doing — for ADHERENCE, which is
the docs' actual argument for the 200-line limit — but §1 and §6 should say that its token win is single-digit
percent and name the levers that are not, or the owner will judge the restructure by a number it cannot move.
(Caveat: weights are list-price ratios, not the subscription meter; transcripts may under-record thinking tokens,
which would make output's share, and the effort lever, larger still.)

## Brief / spec items found wrong
- Spec §3.10, §5.1 "Memory index — main session only": false on this install (F1).
- Spec §3.1, §3.7: Opus-5 guidance generalised to Sonnet/Haiku 5.5 seats; the 5.5 pages say the opposite for
  verification at low effort (F2, F5).
- Spec §5.5: the concurrency env var refuses rather than queues (F3).
- Spec §3 "If many lines are emphasised, none stands out (best-practices)": that sentence is on code.claude.com
  best-practices, not the platform best-practices page the section otherwise cites; the platform page's CAPS passage is
  about Opus 4.5/4.6 tool/skill undertriggering. Citation location, no conclusion change.
- BRIEF unverified claim "skills: preload works when tools omits Skill": the docs neither say nor deny it ("This field
  controls which skills are preloaded, not which skills the subagent can access"). All 11 current agents omit `Skill`
  from `tools`. Resolve with the same throwaway-agent probe as F1 — one run answers both.
- Live scc.md defect surfaced by the rewrite (F6 row 1): the listing-form wait loop has no deadline and never exits
  for an `Eqw` job.
- Dispatch completeness: the dispatch named the Anthropic pages to read, which is the domain material for this seat;
  adequate.

End: HEAD 076b0f8 (unchanged); status unchanged apart from the review files (untracked).
