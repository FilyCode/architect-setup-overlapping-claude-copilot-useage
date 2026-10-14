# Agent seat review (2026-10-14) — findings appended as confirmed

Start state: HEAD 3db1f65; porcelain = 4 untracked review files (incl. this one). Patch applied to a scratch copy only (exit 0, 11 seats patched).
Frontmatter fields confirmed in the 2.1.300 binary's agent field list: name, description, prompt, tools, disallowedTools, model, effort, permissionMode, mcpServers, hooks, maxTurns, autoCompactWindow, skills, initialPrompt, memory(user|project|local), background, omitClaudeMd, isolation; `color` appears in the plugin-agent key list.

## F1 [Blocking] lean-critic preloads a skill that cannot be preloaded
- File: workspace-config/agents/lean-critic.md, `skills: [thermo-nuclear-code-quality-review, verification-patterns]`.
- Evidence: .claude/skills/thermo-nuclear-code-quality-review/SKILL.md frontmatter has `disable-model-invocation: true`; settled fact: such skills are silently skipped on preload. The body says "Apply the thermo-nuclear rubric you were given" -> the seat runs with no rubric and no error. The `Skill` tool in its list cannot load it either (same flag).
- Fix: either drop `disable-model-invocation` from that skill (it is only a reviewer rubric; user-only invocation buys nothing), or copy the rubric into the agent body / a preloadable `debloat-rubric` skill. Then remove `Skill` from tools unless /ponytail-review is really wanted (ponytail-review IS model-invocable; plugin enabled in ~/.claude/settings.json).

## F2 [Important] implementer preloads the CALLER's skill (dispatch-brief), ~15 KB
- File: implementer.md `skills: [dispatch-brief, verification-patterns, completion-check]`.
- Evidence: build_skills.py --out scratch: dispatch-brief/SKILL.md 14,998 B, verification-patterns/SKILL.md 14,373 B, completion-check 1,574 B => ~31 KB (~8k tokens) preloaded per implementer. dispatch-brief's headings are all controller-side ("Never dispatch wait-and-report", "A dispatch's factual claims become code", "Contradiction slot", "Reviewers write findings down") — guidance on WRITING briefs, not executing them.
- Fix: drop dispatch-brief; the 4 lines the implementer needs from it (stop rule, contradiction slot, job-spec handoff, git show --stat recovery) go in the agent body (done in the proposed implementer.md below).

## F3 [Important] implementer: "Run pytest only inside an SGE job ($JOB_ID set)" is ambiguous here and probably wrong as phrased
- Evidence: this very session has JOB_ID=8090063 on host scc-yf3 (a compute node; scratchpad path /scratch/8090063.1.y/...). So inside an interactive qrsh/OnDemand session the implementer WILL see $JOB_ID and run the full pytest, which the wave rules reserve for wave close with a quiet tree; on the login node it can run nothing and must hand back a job spec even for one test file.
- Fix: state the scope, not the host: "Run only your task's own test file(s) and the linter on changed paths. Never the full suite (that is the caller's, at wave close, on a quiet tree). If $JOB_ID is unset (login node) and the tests take >15 s, put the job spec in your report instead."

## F4 [Blocking for the seat's purpose] Nothing routes SDD dispatches to `implementer`; superpowers' template names general-purpose
- Evidence: superpowers 6.4.1 skills/subagent-driven-development/implementer-prompt.md opens `Subagent (general-purpose):`. `command grep -rln implementer` over workspace-config/, skill-headers/: only core.md:33 ("Dispatching an implementer or a review seat -> skill dispatch-brief") and dispatch-brief.md, whose header never says `subagent_type: implementer` (plan line 1019 says dispatch-brief WILL use it, "Task 13", but skill-headers/dispatch-brief.md has no such text). general-purpose = 81.2% of subagent context tokens (spec §2, n=411 of 757) — the lever only pays if the controller actually selects the seat.
- Fix: add to skill-headers/dispatch-brief.md (header, not moved text): "SDD implementer tasks: `subagent_type: implementer`, never general-purpose. Default sonnet (frontmatter). Pass `model: opus` when the task crosses >2 modules, changes a contract/transaction boundary/exception type, or the previous attempt came back BLOCKED or wrong. The SDD template's 'run the full suite before committing' and 'ask questions' lines do not apply: the implementer runs its own tests only and cannot ask mid-run." Then measure: re-run tools/measure_context.py after one wave and check the general-purpose share fell.

## F5 [Important] implementer report format conflicts with the SDD controller's status contract
- Evidence: implementer-prompt.md requires a REPORT_FILE plus a <15-line reply with `**Status:** DONE | DONE_WITH_CONCERNS | BLOCKED | NEEDS_CONTEXT`, commits, one-line test summary, and TDD RED/GREEN evidence. implementer.md's Report section has none of: Status vocabulary, report file, RED evidence. Two contracts in one context = the agent picks one; the controller parses the other.
- Fix: implementer.md adopts the SDD vocabulary and adds the workspace extras (brief-was-wrong, HEAD moved, job spec). See proposed file.

## F6 [Important] implementer has no "failing test first" step, no RED evidence, no blast-radius grep
- Evidence: implementer.md "How you work" goes read -> drafts -> change -> tests -> commit. verification-patterns preloaded but the loop never requires RED before GREEN, nor the `command grep tests/ src/` blast-radius check that verification.md requires before FIXED-VERIFIED (3 casualties in W2b-1).
- Fix: in proposed loop, steps 3 and 6.

## F7 [Important] Review seats other than anomaly-hunter/domain-reviewer carry no findings-file-first line in their own system prompt
- Evidence (patched copies): `command grep -ci "findings file"` = 0 for critic-reviewer, alignment-officer, docs-sync, inventory-auditor, figure-auditor, security-specialist, lean-critic. critic-reviewer is the seat with BOTH recorded empty-hand turn-outs (162,646 and 162,630 tokens). The rule says state it as the literal first action, not advice inside a brief; the agent body is the only place that holds for every dispatch.
- Fix: one line in every review seat body, top of file: "First action, before reading the brief: create the findings file the brief names (or `<scratchpad>/<your-name>/findings.md` if none) and append each finding as you confirm it." Seats with no Write tool create it via Bash heredoc — say so.

## F8 [Important] Six seats have no maxTurns
- Evidence: patched frontmatter: alignment-officer, docs-sync, inventory-auditor, pragmatism-officer, research-scout, scc-monitor have no `maxTurns`. maxTurns is a supported field (binary agent key list).
- Fix: alignment-officer 30, docs-sync 25, inventory-auditor 35, pragmatism-officer 20, research-scout 25, scc-monitor 15 (table below). Each paired with F7 so a turn-out still leaves a deliverable.

## F9 [Minor] `memory: project` silently grants Write/Edit to "read-only" seats
- Evidence: alignment-officer, pragmatism-officer, scc-monitor frontmatter `tools: Read, Grep, Glob, Bash`, yet the live agent listing in this session shows them as "Read, Grep, Glob, Bash, Write, Edit" (memory auto-adds file tools). .claude/agent-memory/ holds only alignment-officer (last write 2026-08-29) and pragmatism-officer (2026-09-29); scc-monitor has never written memory.
- Fix: drop `memory: project` from scc-monitor (unused). Keep it on the other two only if their notes are still read; otherwise drop. Least privilege is mostly nominal anyway while Bash is present, so this is Minor. Minor-triage test: does any stated conclusion change? No.

## F10 [Important] Debloat has five overlapping paths; lean-critic as specified is the weakest of them
- Evidence: critic-reviewer checklist item 7 (simplicity/reuse), pragmatism-officer's new ladder (plan stage), lean-critic (diff stage), thermo-nuclear skill (user-only), /ponytail-review (model-invocable, plugin enabled), plus built-in /simplify and /code-review. lean-critic's rubric is the one that does not load (F1), and its "may run /ponytail-review and fold its cuts" doubles review cost inside one seat.
- Fix: keep lean-critic only with a working rubric (F1); drop `Skill` and the ponytail clause; keep it out of the default roster (spec already says so). Re-decide after it has a seat-yield row.

## F11 [Minor] security-specialist maxTurns 25 for a 148-line checklist on opus/high
- Evidence: patched file 148 lines, the longest seat; maxTurns 25 is the lowest budget among opus seats (critic 40, domain/anomaly 45, figure 35). Zero recorded runs (seat-yield table), so no measured turn-out yet.
- Fix: 40, plus F7's findings-file line. Minor-triage: changes no stated conclusion.

## F12 [Important] No lean named seat exists for ad hoc investigation; this dispatch itself is the evidence
- Evidence: general-purpose = 81.2% of subagent context tokens (spec §2, n=411/757), baseline ≈28k tokens of non-ours schema vs 4.6-7.0k for named seats. Built-in Explore (binary: `omitClaudeMd:!0`, `model:"inherit"` capped at opus, Edit/Write disallowed) is lean but is a LOCATOR ("reads excerpts... doesn't review or audit") and runs at the parent's model (opus here) unless overridden per dispatch. Ad hoc audits like this one ("check our agent setup", run as a generic agent carrying all rules + MEMORY.md) fit no named seat: research-scout is web-only and brainstorming-scoped, critic-reviewer reviews a diff.
- Fix: add `investigator` (sonnet/medium, omitClaudeMd, tools Read Grep Glob Bash WebFetch WebSearch, maxTurns 40, findings-file-first, report = ranked findings with evidence + "what I could not verify"). Keep Explore for "where is X" with `model: haiku` per dispatch. Route in core.md: "ad hoc investigation/audit -> investigator; locate code -> Explore; general-purpose only when the task needs tools no seat has."

## F13 [Important] omitClaudeMd also strips the PROJECT's CLAUDE.md, which is where a repo's gates and test traps live
- Evidence: binary description of omitClaudeMd: "Run this agent without the user, project and local CLAUDE.md instruction files". Six projects carry their own CLAUDE.md (Bile_acid_database, CaMES, EanB, K4-K26, MqnE, Sulfotrans; 38,455 B total). The rules require each dispatch to name "the repo's own test-environment traps" (conftest autouse fixtures, CI -k/-m filter); for an implementer with omitClaudeMd, the brief is now the ONLY carrier.
- Fix: implementer loop step 1 reads `projects/<name>/CLAUDE.md` (and the repo's CI config for its real lint/test commands) itself — a cheap Read, not 50k of workspace rules. Same line for critic-reviewer.

## F14 [Minor, UNVERIFIED] completion-check refers to `<skill dir>`; unclear a PRELOADED skill gets its base directory
- Evidence: binary contains the "Base directory for this skill: " prefix string for invoked skills; I did not verify it is emitted for `skills:` preloads. completion-check is also not yet linked into WS/.claude/skills (only REPO/.claude/skills/completion-check exists).
- Fix: give the absolute path in the agent body (done in proposed implementer.md), or verify with one `claude -p` probe after linking.

## Proposed implementer.md (complete)

````markdown
---
name: implementer
description: Implements one task from an approved plan — failing test first, minimal change, the repo's fast gates, a path-scoped commit, and a report with real command output. Use for every subagent-driven-development task and any scoped code change with named files, instead of general-purpose. Not for reviews (review seats), investigation (investigator) or web research (research-scout).
tools: Read, Edit, Write, Bash, Grep, Glob
model: sonnet
effort: medium
maxTurns: 60
omitClaudeMd: true
skills: [verification-patterns, completion-check]
---

You are a professional software engineer implementing exactly one task. The brief names the
files you own; touch nothing else. You do not dispatch subagents, you do not submit SGE jobs,
and nobody can answer a question mid-run: when you would ask, stop and report instead.

## Before you change anything
1. Run `git log -1 --format=%h` and `git status --porcelain`; note both.
2. Read the brief in full, then the project's own `CLAUDE.md` (e.g. `projects/<name>/CLAUDE.md`)
   and its CI config for the real lint/test commands and any conftest traps. Then read every
   file you will touch and the callers of anything whose contract you will change.
3. Check the brief's factual claims you depend on (paths, signatures, counts, line numbers)
   against the code. If one is wrong, do not reconcile toward the brief: if the task is still
   well-defined, proceed and record the error; if not, stop with NEEDS_CONTEXT.

## The loop
4. Write or adopt the failing test first. Tests handed to you in the brief are drafts: run
   each against the current code and confirm it fails for the reason it should (RED). A test
   that passes before your change cannot guard it — fix the test or report it.
5. Make the smallest change that turns it green. Follow neighbouring patterns. No speculative
   generality, no unrelated cleanup, no new files the brief did not ask for.
6. If the change alters timing, a transaction boundary, an exception type, a return contract
   or an arity: `command grep -rn <symbol> src/ tests/` for every consumer, fix or update each
   assertion that encoded the old contract, and give the hit count in your report.
7. Run the fast gates on changed paths only: the task's own test file(s), the repo's linter
   (`ruff check <paths>` unless the project says otherwise), and
   `python3 /projectnb/liu-scc/philipp/.claude/skills/completion-check/scripts/stub_scan.py <paths>`.
   Never the full suite: that belongs to the caller at wave close on a quiet tree. If your own
   tests need more than ~15 s and `$JOB_ID` is unset, write the job spec (below) and stop.
   Check every exit code outside a pipe.
8. Commit by name: `git add <file> <file>` (never a directory), `git commit -m "<msg>" -- <paths>`,
   then `git show --stat HEAD`. If anything not yours is in it: `git reset --soft HEAD~1`,
   `git reset -- <their files>`, re-commit path-scoped. Never `git stash`, `--work-tree`,
   `git add -A`, or a bare `git commit`.

## Stop and report (do not work around) when
- a permission is denied — report the exact command; never retry it another way;
- the fix belongs in a file you do not own — report it as a task with the file and the change;
- you need an SGE job — write the job spec: script, `-l h_rt`/cores/`mem_per_core`, the
  command, the artifact it must produce and how to check it; the caller submits;
- the task needs an architectural choice the plan did not make, or you have read many files
  without converging — BLOCKED, with what you tried.

## Environment
- Python: `/projectnb/liu-scc/philipp/.venv/bin/python` or the project's own `.venv`.
- Scratch: the session scratchpad, in a folder named `implementer-<task>`. Delete only files
  you created, by name; never `rm -rf` in the project tree.
- Output directories are read-only. Never create files under `tests/` except test files your
  task owns. No tool's `--write` mode and no `cp` onto tracked files.
- Read past commits with `git show <commit>:<path>`.
- `command grep` for any absence claim (shell `grep` skips gitignored paths).

## Report
Reply in under 20 lines:
- **Status:** DONE | DONE_WITH_CONCERNS | BLOCKED | NEEDS_CONTEXT
- Commit: short SHA + subject, and the `git show --stat` file list.
- RED: command and the failing line before the change. GREEN: command and its summary line
  (e.g. `5 passed`), lint result, stub-scan result. Real output, not paraphrase.
- Blast radius: the grep you ran and its hit count, or "no contract change".
- Brief errors: every claim in the brief you found wrong, with what is actually true.
- Not done / deviations, and why. Job spec if one is needed.
- HEAD and status at start vs end: moved or not.
If the brief names a report file, put the full detail there and keep this reply short.
````

Notes on the choices:
- sonnet/medium default; the caller escalates per dispatch with `model: opus` (Agent tool `model` overrides frontmatter) for cross-module/contract changes or after a BLOCKED/wrong attempt. Global effortLevel is already medium; `effort: medium` is stated so it survives a global change.
- No `isolation: worktree`: it would remove the shared-index hazards, but the workspace's editable installs point at the main checkout's `src/` and conftest re-inserts it, so tests in a worktree can silently import the main tree (verification.md, 2026-09-23 RED-proof incident). Reconsider only per-repo after a probe.
- No `Agent` in tools (cannot spawn reviewers), no web tools (the brief is the spec), no `Skill` (preloads do not need it).
- dispatch-brief dropped from preload (F2): ~15 KB of controller guidance.
- No `permissionMode`: permission changes are the owner's call; a denial is a stop condition.

## Proposed per-seat frontmatter (after patch + this review)

| Seat | model / effort | maxTurns | tools | skills | omitClaudeMd | memory | change vs patch |
|---|---|---|---|---|---|---|---|
| implementer | sonnet / medium (opus per dispatch) | 60 | Read Edit Write Bash Grep Glob | verification-patterns, completion-check | true | - | drop dispatch-brief; body above |
| investigator (new) | sonnet / medium | 40 | Read Grep Glob Bash WebFetch WebSearch | verification-patterns | true | - | new (F12) |
| critic-reviewer | opus / medium | 40 | Read Grep Glob Bash WebFetch | verification-patterns, completion-check | true | - | + findings-file-first, + read project CLAUDE.md |
| domain-reviewer | opus / high | 45 | Read Grep Glob Bash WebFetch | scientific-evidence | true | - | none |
| anomaly-hunter | opus / high | 45 | Read Grep Glob Bash WebFetch | scientific-evidence | true | - | none |
| alignment-officer | sonnet / medium | 30 | Read Grep Glob Bash | - | true | project (only if notes still read) | + maxTurns, + findings-file |
| docs-sync | sonnet / medium | 25 | Read Grep Glob Bash | - | true | - | + maxTurns, + findings-file |
| inventory-auditor | sonnet / medium | 35 | Read Grep Glob Bash | - | true | - | + maxTurns, + findings-file |
| pragmatism-officer | sonnet / medium | 20 | Read Grep Glob Bash | - | true | project | + maxTurns |
| lean-critic | sonnet / medium | 35 | Read Grep Glob Bash | thermo-nuclear (only after removing disable-model-invocation), verification-patterns | true | - | fix F1, drop Skill + ponytail |
| figure-auditor | opus / medium | 35 | Read Grep Glob Bash | scientific-evidence | true | - | + findings-file |
| security-specialist | opus / high | 40 | Read Grep Glob Bash WebFetch | - | true | - | 25 -> 40, + findings-file |
| research-scout | sonnet / medium | 25 | WebSearch WebFetch Read Grep Glob | - | true | - | + maxTurns |
| scc-monitor | haiku / medium | 15 | Bash Read Grep Glob | running-sge-jobs | true | drop (never used) | + maxTurns, drop memory |

## Strongest objection not asked about
Every seat is now `omitClaudeMd: true`, so the agent body and the brief are the only carriers of workspace knowledge — and the bodies now duplicate one Environment block 13 times (patch inserts it from the plan text). That is a generated-looking copy with no generator: when an env rule changes (e.g. the venv path, the JOB_ID rule in F3), 13 files drift independently, and nothing reddens. The patch script is a one-off. Either make `patch_agents_2026_10.py` (or build_skills.py) the standing generator for the env block with a check that all 13 copies match, or move the block into one tiny preloaded skill (`seat-environment`) that every seat lists.

## Brief errors
- "11 live seats" is correct: WS/.claude/agents holds 11 symlinks; implementer and lean-critic are unlinked.
- The brief implies the patch only touches frontmatter; it also inserts the Environment and keep-working blocks and the boundary lines into bodies.
- "skills ... built from skill-headers by build_skills.py": completion-check is NOT built by it (not in SKILLS, no header); it is a hand-made skill in REPO/.claude/skills/ and not yet linked into WS/.claude/skills.
- Implicit premise that seats are read-only by tool list: memory: project adds Write/Edit (F9).

End state: HEAD and porcelain recorded below at close.
End: HEAD moved 3db1f65 -> e31559e; porcelain now shows only this file untracked (the 3 other review files were committed).
