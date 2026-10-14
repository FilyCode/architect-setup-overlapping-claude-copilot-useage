# critic-reviewer findings — 2026-10-14 restructure spec (feasibility / technical claims)

Start: HEAD 076b0f8 (brief says spec at ec42c36), porcelain = 3 untracked review files only.

### F1 [Blocking] core rule 6 "Concurrent implementers run in `isolation: worktree`" is infeasible as stated
Evidence:
- code.claude.com/docs/en/worktrees ("Choose the base branch"): subagent worktrees "branch from your repository's default branch unless `worktree.baseRef` is set to `\"head\"`"; default `"fresh"` = remote default branch. sub-agents doc, `isolation` row: "branched by default from your default branch rather than the parent session's `HEAD`". The spec sets no `worktree.baseRef`. An implementer dispatched mid-wave on a feature branch would start from `main` and not see the wave's earlier commits.
- Worktrees "require a git repository". `git -C /projectnb/liu-scc/philipp rev-parse` -> "fatal: not a git repository". Main sessions run from the workspace root (transcripts live under `-projectnb-liu-scc-philipp`); the git repos are `projects/*/` subdirectories (10 found). The spec does not say which repository a root-launched session's subagent worktree would be made from, and nothing shows it works.
- A worktree is "a fresh checkout ... checks out only tracked files" — no `.venv`, no gitignored `results/`/data. EnzymeFinder tests and evidence that depend on gitignored artifacts or the editable install would behave differently there. verification.md already records "a `git worktree` is not the main checkout" (5 failures, 2 of them pure environment).
- The worktree's commits sit on a `worktree-*` branch. The spec defines no merge-back step and no owner for it.
Why it matters: this one sentence replaces the whole shared-index hazard section (stash / `--work-tree` / bare commit / `commit -- paths`). If it cannot run, that protection is gone and nothing replaces it.
Proposed change: either (a) keep the shared-tree rules (explicit-path commit + `git show --stat` + recovery recipe) as the default, or (b) make worktree isolation conditional: set `worktree.baseRef: "head"`, launch from inside the project repo, add `.worktreeinclude` for the venv/data, and add a merge-back step owned by the caller. Then verify with one real dispatch before relying on it. Pick (a) unless (b) has been demonstrated.

### F2 [Important] lean-critic cannot preload `thermo-nuclear-code-quality-review`; it would be dropped silently
Evidence: `/projectnb/liu-scc/philipp/.claude/skills/thermo-nuclear-code-quality-review/SKILL.md` frontmatter has `disable-model-invocation: true`. The sub-agents doc says: "You can't preload skills that set `disable-model-invocation: true` ... If a listed skill is missing or disabled ... Claude Code skips it and logs a warning to the debug log." The spec (§5.3) says the skill is kept "verbatim", and §5.4 lists it as a preload for lean-critic.
Why it matters: the new seat's main instrument would be missing. Nothing in the session would say so; the warning goes only to the debug log. This is the "gate that never exercises its path" shape.
Proposed change: either remove `disable-model-invocation` from the vendored copy (record it as a deliberate deviation in `SOURCE.md`; the description then costs about 1,536 chars or less every session), or have lean-critic's body Read the file at a fixed path. Add an acceptance check that each seat's preloads actually appear in a real seat transcript.

### F3 [Important] process skills invoked "by a core rule" must be model-invocable, so they are not free, and the spec does not budget for them
Evidence: skills doc, context table: `disable-model-invocation: true` gives "Description not in context" and "Claude can invoke: Not on its own". So a zero-cost skill cannot be reached by a core.md line that tells Claude to run `/wave-review` or `/plan-critique` or to "build the brief with `dispatch-brief`". Each model-invocable description costs up to 1,536 chars (listing truncation) "on every turn". Today 6 of the 7 workspace skills are `disable-model-invocation: true` (only `caveman` is not).
Why it matters: the seven new skills add roughly 7 × 0.3–1.5 KB to always-on context. That is not in the projected saving, and §5.1's 32 KB target counts only L0+L1+memory. §5.6 counts skill descriptions while §5.1/§9.3 do not: two definitions of the same budget.
Proposed change: state an invocation mode per new skill. Process skills (`dispatch-brief`, `wave-review`, `plan-critique`) and the preloaded ones (`verification-patterns`, `scientific-evidence`, `running-sge-jobs`, `completion-check`) must be model-invocable. Preloading requires it, so every one of the seven is. Define one budget that includes their descriptions.

### F4 [Important] `CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS=3` exists, but it does not replace the memory prose
Evidence: sub-agents doc: the default is 20, it needs v2.1.217+, and when the limit is hit "spawning another with the Agent tool fails with `Concurrent subagent limit reached`, and the error tells Claude not to retry". `/subtask` forks "take a slot but aren't blocked", and resuming a finished subagent "takes a slot without checking it". The memory file `feedback_subagent_dispatch.md` § "Concurrency cap" says the cap is **2** on the smaller account and **3** on the larger one, "not a fixed universal number", and limits it to the *shape* "one slow job + one companion".
Why it matters: (a) A hard 3 in user `settings.json` is wrong whenever the 2-cap account is in use. (b) The limit fails instead of queueing, and Claude is told not to retry. A plan-critique wave of up to ~10 seats (subagent-dispatch.md) would then drop seats or have Claude do the work inline, unless the `wave-review`/`plan-critique` skills say "dispatch in batches of N". (c) The "shape" half of the rule cannot be expressed by an env var at all.
Proposed change: keep the env var as a backstop, set to the lower account's value or set per account. Keep one line on the batching and shape rule in `dispatch-brief`/`wave-review`. Do not delete the memory text on the grounds that the env var "replaces" it.

### F5 [Important] memory clean-up misses a memory entry that directly contradicts the rule being kept
Evidence: `feedback_subagent_dispatch.md` (same file, "Apply") tells dispatched agents to "poll synchronously with a real blocking loop (`while qstat -j <id> ...; do sleep 15; done`)". subagent-dispatch.md says the opposite: "the dispatching side submits every job ... the caller submits, waits". It also documents the `qstat -j` transient-exit failure, which that loop has. §5.8 only plans to fix the notification claim in that file.
Why it matters: §1's "zero lessons lost" goal has a mirror risk, keeping a contradicted lesson. Memory loads in the main session, and the docs say contradictory instructions get picked "arbitrarily".
Proposed change: §9.1 traceability should also cover memory topic files that restate a rule, and flag contradictions as well as duplicates.

### F6 [Important] the "login node" test should key on the SGE job environment, not the hostname; this session is not on a login node (the brief's claim is wrong)
Evidence: in this session, `hostname` returns `scc-yf3`, with `JOB_ID=8090063 QUEUE=y NSLOTS=1 SGE_O_HOST=scc1 TMPDIR=/scratch/8090063.1.y`. Claude itself runs inside an SGE job on a compute node, which is why the scratchpad path is under `/scratch/<jobid>`. The real login nodes resolve as `scc1`, `scc2`, `scc4`, `geo`. A hostname allowlist is a brittle list that has to be kept up to date. "`$JOB_ID` unset" is the property that actually matters here, since the reaper applies outside a job. Hooks inherit the claude process environment.
Second half: inside a job with `NSLOTS=1`, a full suite still competes with the session for the same single slot. "Not on a login node" does not mean "safe to run the suite"; scc.md's wave-close rule still says to run the suite through `qsub`.
Why it matters: (a) a hostname-keyed block gives false negatives on any login node not in the list, and maybe false positives if the pattern is a regex like `scc*`. (b) The brief and the scc.md wording ("this is a login node") are both stale for the current way sessions are run. The scc.md premise ("process reaper ... ~30s CPU") applies to `scc1/2/4/geo`, not to this host.
Proposed change: hook condition = `[ -z "$JOB_ID" ]` OR hostname in {scc1,scc2,scc4,geo,...}, and print the reason. Fix the brief template's "this is a login node" line. Test both ways on a real login node and inside a job.

### F7 [Important] the §5.5 block hooks as worded will block legitimate commands and miss real ones; specify the matcher, not the intent
Concrete false positives and false negatives (derived from the command shapes; no hook exists yet to execute):
- `git stash` block: blocks the read-only `git stash list` / `git stash show`, and stash in a repo with no concurrent agent. Misses `git -C <repo> stash`, `git --no-pager stash`. verification.md already records "match the command as invoked, not as idealised" (`git -C <dir> log`).
- `git --work-tree … checkout`: the documented hazard is real only when `GIT_DIR`/`GIT_INDEX_FILE` are not redirected (subagent-dispatch.md: "mutates the REAL index unless `GIT_DIR` is redirected too"). A naive match also blocks the safe redirected form. It must not match `git worktree add/list/remove` either; those are different subcommands but the same prefix.
- `rm -rf` under `projects/`: blocks routine `rm -rf .pytest_cache __pycache__ build/` and Claude Code's own leftover worktree removal. Misses `rm -fr`, `rm -r -f`, `\rm -rf` (scc.md recommends `\rm -f` because `rm` is aliased), `find … -delete`, and a relative `rm -rf results` whose cwd is inside `projects/`. A hook only sees the cwd via the input JSON `cwd` field.
- login-node `pytest`: blocks `qsub … pytest`, `grep pytest`, `echo … pytest` and heredoc job scripts that mention it. Misses `python -m pytest`, `uv run pytest`, `make test`, `tox`.
- `git commit` without `--` warn: by subagent-dispatch.md's own text, `git commit -- <paths>` sweeps another agent's unstaged changes in those paths. A warning that nudges toward `--` paths pushes toward the second hazard. The correct reminder is "then run `git show --stat`".
Why it matters: §7 promises that "each hook tested both ways" in near-miss form, but the near-misses listed above are the ones that need testing. A hook that blocks `git stash list` trains the agent to route around blocks, which the memory forbids.
Proposed change: in the spec, list per hook the exact regex/parser, the input fields it reads (`tool_input.command`, `cwd`), and three positive and three near-miss cases from the list above. Prefer a tokenising parser (`shlex`) over regex.

## Area 2: sampled placement check
Method: a Python regex for headings or bold-lead lines over the three files, `random.seed(20261014)`, 10 sampled. Results:

| # | Old item | Spec destination | Loads when needed? |
|---|---|---|---|
| 1 | sd:160 contradiction slot | dispatch-brief | yes, if Claude invokes dispatch-brief (core 8); see F9 on superpowers SDD dispatches |
| 2 | sd:191 declared file ownership | core 6 + dispatch-brief | yes |
| 3 | sd:604 output dirs read-only | core 7 | yes |
| 4 | sd:633 three-state at plan time | plan-critique | yes |
| 5 | sd:673 findings file before investigation | wave-review only | **MISS for ad hoc review dispatches** (F8) |
| 6 | ver:48 positive-control corollary | listed in scientific-evidence; general form belongs in verification-patterns too | **partial**: critic/alignment seats do not preload scientific-evidence |
| 7 | ver:223 convenient-fixture control | the text sits inside the rtk section; §5.5 says "remove rtk lore everywhere" | **at risk** (F10) |
| 8 | ver:287 three-state typed at introduction | core 2 | yes |
| 9 | ver:320 assert module path inside the pytest run (RED proof) | verification-patterns | **MISS at the moment needed**: the implementer doing the RED proof is a generic subagent with no preload (F9) |
| 10 | ver:383 instrument headroom before "absent" | core 3 + scientific-evidence | yes |

### F8 [Important] the review-dispatch template reaches wave-end reviews only; ad hoc review dispatches lose it
Evidence: subagent-dispatch.md:266 "Every review dispatch — wave-end or ad hoc — ends with ..."; the findings-file-first rule (sd:673, sd "Fourteenth") is likewise for every review dispatch. Spec §5.3 puts the review-dispatch template only in `wave-review`. `dispatch-brief`, the skill core rule 8 fires on "any dispatch", lists no review-template content.
Failure scenario: a mid-wave ad hoc `critic-reviewer` dispatch (like this one) is built from `dispatch-brief`. It carries no findings-file-first requirement, no objection slot and no HEAD-moves check. That is the exact 162k-token / one-sentence failure recorded twice.
Proposed change: move the review-dispatch template into `dispatch-brief` (a "if the dispatch is a review" section), and have `wave-review` reference it.

### F9 [Important] the lessons needed at implementation time are preloaded only into reviewers
Evidence: §5.4 preloads `verification-patterns` into critic-reviewer, lean-critic and alignment-officer only. Implementers are `general-purpose` / superpowers `subagent-driven-development` workers. They have no frontmatter we control, so they get core.md plus whatever description-matching picks. Lessons whose moment is implementation: RED proof inside pytest (ver:320), blast-radius grep before `FIXED-VERIFIED`, a dead knob's default must equal the old value, a boundary test on both sides of the constant, the first fixture being a real artifact. superpowers SDD builds its own implementer prompt, so core rule 8 ("build the brief with `dispatch-brief`") competes with that skill's template.
Why it matters: today these lessons are always on, so implementers had them. After the change they arrive only at review time, which turns prevention into detection. §6's "zero lessons lost" is met on paper and missed in practice.
Proposed change: either a thin custom `implementer` agent with `skills: [verification-patterns]`, or a `dispatch-brief` line telling implementers to invoke `verification-patterns`. Add one implementer scenario to the §9.2 evals that checks for the RED-proof module-path line.

### F10 [Important] "remove rtk lore everywhere" would delete three general lessons that live inside the rtk section
Evidence: verification.md:218-230, "Three lessons here generalise beyond rtk": match the command as invoked (`git -C`, `--no-pager`); a positive control from a convenient fixture proves nothing; check an aggregate's distribution before optimising for it. The third underpins the spec's own byte/4 savings projection.
Proposed change: §9.1 traceability must map these three to `verification-patterns` explicitly, and §5.5's wording should become "remove rtk-specific lore". The first lesson also applies directly to the new hooks (F7).

### F11 [Minor] the "114 items" count does not reproduce under an equally reasonable heuristic
Evidence: my regex (`^#{1,6} ` or optional `- ` plus a `**bold**` lead) gives subagent-dispatch 73, verification 43, scc 9 = **125**, against the spec's 63/42/9 = 114. The difference is in subagent-dispatch.md's bold-lead bullets.
Minor-triage: does any spec conclusion change? No. §9.1 already defers the unit to the mapping script. It is Minor provided the spec drops the number or labels it with its regex.

### F12 [Important] the §5.6 `context_budget.py` source list misses several measurable startup loads and cannot see others at all
Evidence (executed):
- **Agent descriptions** go into the Agent tool listing every session: the 11 workspace agents total 3,632 description chars (per-file 257–413). The new `lean-critic` adds more. pr-review-toolkit's ~2,035 tokens (spec §2) are also *agent* descriptions, yet §5.6 lists only "enabled skill descriptions".
- **SessionStart hook output**: superpowers `hooks/session-start` cats the whole `using-superpowers/SKILL.md` (3,192 bytes) plus a wrapper into context. It is computable only by running the hook or reading its script, not by summing description fields. humanize-kit (§5.9) adds another SessionStart hook.
- **Synced account plugins**: `~/.claude/plugins/synced/` holds **two** account directories (`00c1f97a…` empty, `cd950bbd…` with bio-research and 4 UUID plugins). The on-disk total depends on which account is logged in, so the script must pick the active one, or it double-counts or misses.
- **Not on disk at all**: the claude.ai MCP connector instructions (alphaXiv, bioRxiv, Claude Docs, Undermind; several KB of instruction text, visible in this very seat's context), deferred-tool names, the system prompt, built-in tool schemas, and the git-status snapshot.
Why it matters: a byte ceiling over a partial sum passes while the real first-call context grows, which is "a gate that never exercises the path in use". The spec's own baseline (77.6k–100k first-call) is ~3× its 30k "our text" figure, so most of the startup context is outside what the script counts.
Proposed change: make `measure_context.py` (transcript `usage` at first call) the gate of record, with the ceiling on it. Keep `context_budget.py` as an attribution tool that also counts agent descriptions, SessionStart hook output (by executing the hooks in a sandbox), and the active synced account. State plainly which components are unmeasurable from disk.

### F13 [Important] dissolving `verification.md` / `subagent-dispatch.md` leaves well over 100 files citing them by name; the spec has no redirect task
Evidence (`command grep -rlE "subagent-dispatch\.md|verification\.md|rules/scc\.md"`, excluding `/history/`): the matches are spread over many directories. The largest are EnzymeFinder `docs/superpowers/reports` (22), `plans` (16), `scripts` (14), SenC `docs/reviews` (11) and `scripts` (7), and EnzymeFinder `.claude/agent-memory/alignment-officer` (8). `projects/EanB_homologue_search/CLAUDE.md` cites them too. Script docstrings justify design choices by quoting named entries ("verification.md's 'four shape gates cannot detect decay'", `SenC…/131_headline_figures.py:11`). Inside this repo, 4 agent files reference them: critic-reviewer:36,69; anomaly-hunter:58; pragmatism-officer:48; scc-monitor:14,52. §5.4 only notes critic-reviewer's.
Why it matters: §8 places project repos out of scope, but these citations become dead pointers the day the files go. The EnzymeFinder alignment-officer agent memory is loaded by that seat and will tell it to check a file that no longer exists.
Proposed change: add a task that keeps `verification.md` and `subagent-dispatch.md` as **non-auto-loading** redirect indexes, with a `paths:` frontmatter or moved to `docs/history/` with the same names, mapping each old entry title to its new home (the §9.1 traceability table, rendered). Update all 4 agent files, not just one.

### F14 [Important] the §9.2 behavioural evals cannot detect the regression they exist for
Evidence: 8 scenarios, one headless run each before and after, with a grep-able pass/fail. Model behaviour is stochastic, so a lesson that fired 9/10 times before and 5/10 after passes one run in each arm with probability about 0.5. The design has no repetition, no stated n and no pass threshold. Spec §7 names these evals as *the* mitigation for the top risk ("a lesson exists in a skill but does not load when needed").
Ordering problem: the "before" runs must happen on the untouched config, i.e. before Task 1. Note too that `claude -p` sessions inherit the active account's synced plugins and connectors, so before and after must use the same account (F4, F12).
Proposed change: k ≥ 5 runs per scenario per arm (cheap at about 100k tokens each relative to the stakes), report x/k with the arm, and fix a pass rule such as "after ≥ before − 1". Add implementer-shaped scenarios (F9) and an ad hoc review dispatch (F8). Record the transcripts as artifacts.

## Verified, no finding
- `omitClaudeMd` drops unscoped project rules as well as CLAUDE.md files. Basis: sub-agents doc "What loads at startup", where the CLAUDE.md bullet includes "`~/.claude/CLAUDE.md`, project rules, `CLAUDE.local.md`" and "A subagent whose definition sets `omitClaudeMd` loads only the managed policy files". Path-scoped rules and subdirectory CLAUDE.md still load on file touch. Docs-verified, not executed.
- `skills:` preload works without `Skill` in `tools`. The docs say: "To preload Skills into context, use the `skills` field rather than listing `Skill` here". Caveat: a seat whose `tools:` omits `Skill` cannot invoke *unlisted* skills, e.g. lean-critic's "may call `/ponytail-review`" needs `Skill` in its tools.
- `CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS` and `CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH` exist (see F4 for the semantics).
- `disable-model-invocation: true` gives "Description not in context". It is zero-cost but neither model-invocable nor preloadable (F2, F3).
- Auto memory: first 200 lines / 25 KB, main session only, forks excepted. Matches the docs.
- §5.8's correction of this repo's CLAUDE.md ("no hook auto-injects any of them") is right. Unscoped rules load every session per the memory docs, and they are in this seat's own context.

## Close
- HEAD: start 076b0f8, end 076b0f8. Porcelain: only the 3 untracked review files, start and end. The spec is unchanged between ec42c36 and HEAD.
- Strongest objection not asked: the spec optimises startup bytes, but its own baseline says long sessions dominate cost (1.83B tokens over 3,714 calls). Saving 25k per call × 3,714 calls ≈ 93M ≈ **5.1%** of that session. The spec states no cost model (cache-read vs uncached input vs usage-limit accounting), so the projected "~22–25k" is an input to an objective it never defines. Measure the before/after against the quantity the owner pays in. Session length and compaction hygiene may matter more than core.md size.
- Brief errors: (1) "This is a login node": false; this seat runs in SGE job 8090063 on compute node `scc-yf3` (F6). (2) The spec commit is cited as `ec42c36` while HEAD is `076b0f8`; harmless, since the spec is unchanged. (3) The "114 items" figure does not reproduce under a comparable regex (125; F11).
