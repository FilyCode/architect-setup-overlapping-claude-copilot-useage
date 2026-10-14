# alignment-officer findings (scope truth: spec vs owner ask) 2026-10-14
Start HEAD 076b0f8; status: only untracked seat findings files. Spec 296 lines read in full.

## Owner-ask trace (area 1)
| Owner ask | Class | Evidence |
|---|---|---|
| Reduce token use majorly, aggressive budget | Delivered (design) | spec 5.1 (<=32 KB, stretch 24 KB), 5.6 script |
| Rules -> skills | Delivered (design) | 5.3 seven skills |
| Slim documents | Partial | 5.8 touches MEMORY.md, history; DECISIONS/ARCHITECTURE are NOT auto-loaded (no @import; CLAUDE.md:22 only names them) so nothing to slim for tokens; agent bodies (49 KB) untouched, see F4 |
| Change personas | Partial | 5.4 changes frontmatter for all, prompt substance for 2 of 11; see F4 |
| How/when things are loaded | Delivered | 3.8-3.10, 5.1 layer table |
| How to formulate (check what style works best) | Partial | 5.7 is derived from Anthropic docs; 9.2 evals test triggers, not wording variants. No test of which phrasing is followed better |
| Combine/summarize parts | Substituted | 1: "kept unless the wave shows a merge is safe" - the wave is now; no merge proposed or refuted; see F4 |
| Humanizers / desktop doc skills | Partial | 5.9 recommends, from descriptions only (5.9 header: synced, recommendations only); science-writing-edit not inspected |
| Codex loop worth it | Delivered (deferred with reason) | 8 "no subscription" - not a worth-it analysis, but written disposition exists |
| Karpathy behaviour skills/md | MISSING | `command grep -in karpathy` on spec: 0 hits. No disposition. See F1 |
| Ponytail as persona checking plan, later code | Partial | F2 |
| pstack + thermo-nuclear -> debloat persona | Delivered | lean-critic 5.4:165, vendored skill 5.8 |
| More verification tools to find unfinished/non-working code | Partial | completion-check 5.3:139 real, but F3 |
| Code modernization plugin | Explicitly deferred, no reason | 8 "code-modernization usage" - one phrase, no why |

### F1 [Important] Karpathy behaviour skills/md: no disposition anywhere
Evidence: `command grep -in karpathy spec` = no matches. Owner asked it earlier this session. This is exactly silent shrinkage (absent from spec, and from "out of scope" 8).
Fix: add a line in 5.3/5.7/8: adopt (and where, e.g. core.md lines or a skill) / reject with reason. Note it also bears on 5.7 (a behaviour-md is a competing always-loaded file against the budget).

### F2 [Important] Ponytail "persona checking the plan and later the code" is only partly delivered, and the plan half contradicts the host agent
Evidence: spec 5.4:159 puts the ladder (need? exists? stdlib?) into inventory-auditor. inventory-auditor.md Constraints: "You don't judge whether the plan or wave *should* do the thing at all, or whether it's proportionate - that's alignment-officer's and pragmatism-officer's axis ... Yours is strictly: does it already exist". The ladder's first rung ("need?") is the forbidden question; the spec changes the table cell but not the Constraint, so the agent is self-contradictory. Code half: lean-critic "may call /ponytail-review" (5.4:165) - optional, and ponytail is default-off (5.5:183), so by default the code-stage check does not run. No seat is "ponytail"; the owner asked for a persona.
Fix: decide explicitly - either a plan-stage seat (or pragmatism-officer at plan stage, which already owns proportionality) carries the ladder, and rewrite inventory-auditor Constraints accordingly; and make the code-stage ponytail call mandatory in lean-critic or state it is optional by decision.

### F3 [Important] completion-check depends on tools not installed; "non-working code" has no executing check
Evidence: `command -v vulture mutmut diff-cover` = nothing; find under .venv/software/EnzymeFinder .venv: only ruff exists. Spec 5.3:139 lists vulture, mutmut, diff-cover as if available; no install step, no home (quota/software rule). Also listed checks (stub scan, reachability, vulture, diff-cover) find unfinished/dead code; nothing runs the entrypoint / a smoke command to find code that does not work (mutmut on changed modules is the only dynamic one and is slow, not a qsub-safe fast gate).
Fix: add install task (to software/, per CLAUDE.md) or drop tools the owner will not have; add a "run the entry point on a fixture" step; say which are fast gates (per-task, 5.4:167) vs wave-close.

### F4 [Important] Persona change is mostly frontmatter; overlaps unresolved; "combine" ask unanswered
Evidence: agent bodies total 48,769 B (wc -c); 5.4 "Change" column: "-" for 6 of 11, a path swap for critic-reviewer, one addition for inventory-auditor, one for docs-sync. Descriptions alone are 3,753 chars (~940 tokens) in every main session (awk on description: lines) - not in 2 baseline.
Unresolved overlaps:
 - critic-reviewer item 7 (simplicity/reuse; text says it exists because the seat lacks Skill tool) vs new lean-critic vs inventory-auditor "exists/reuse" vs ponytail ladder: four seats ask "does it need to exist/already exist". With preload (5.4) the stated reason for item 7 disappears; spec neither deletes item 7 nor says it stays.
 - alignment-officer vs docs-sync: both check status surfaces vs docs (alignment-officer prompt step 4 "status surfaces agree"; docs-sync "governance docs match work"). Spec keeps both, no boundary sentence.
 - alignment-officer gets verification-patterns preloaded (5.4:157) though its job is scope truth, not shapes; costs tokens contrary to the aim.
 - critic-reviewer item 5 (docs-sync reminder, cites subagent-dispatch.md) duplicates what wave-review will do.
 - Stale references that moving rules will break: critic-reviewer.md:36 `.claude/rules/verification.md`; :69 subagent-dispatch.md; pragmatism-officer.md:48; scc-monitor.md:52 scc.md; anomaly-hunter.md:58 verification.md and :92-95 a verbatim rtk block. Spec says "remove rtk lore everywhere" and "points at skills" for critic-reviewer only.
 - Largest bodies (security-specialist 8.2 KB, anomaly-hunter 7.0 KB, domain-reviewer 5.7 KB) get no slimming; they load only when dispatched but then in every dispatch.
Why it matters: 1 says the 10 (really 11: anomaly-hunter uncounted; 5.4 table lists 11) seats stay "unless the wave shows a merge is safe" - this review wave is where that is decided, so the spec defers the owner's ask to the thing reviewing it.
Fix: add a persona subsection: per-seat keep/merge/slim decision, one boundary sentence per overlapping pair, list of agent-file edits (references), word budget for agent bodies. Correct "10 existing seats" to 11.

### F5 [Important] Rule-trigger orphans: three "when" lines in the old rules have no home in core item 8
Method: script cov.py (scratchpad/alignment-officer) listed headings/bold-leads/top bullets of the 3 rules (186 items) with zero keyword overlap with spec 5.2-5.8; hand-triaged. Keyword heuristic is crude (spec 5.3 compresses sources to phrases), so most hits are covered (calibration -> plan-critique, escalation wave -> plan-critique, scc defaults/log/verify -> running-sge-jobs, shapes -> verification-patterns, 'firing is not moving', version-stamp, reachability -> completion-check/verification-patterns by grouping). Genuine orphans (no named destination in 5.2/5.3/5.5/5.8):
 1. Release/publication gate: dispatch security-specialist before public release/paper (subagent-dispatch.md "Release/publication gate"). Spec lists the seat (5.4) but no trigger anywhere. Core item 8 has only 3 gates.
 2. Brainstorming: research-scout for non-trivial design decisions; `command grep` .superpowers/ for prior work before research; one external premise check (PDB/PubMed lookup on the target itself) at project start and any reframing. No destination.
 3. Plan-writing: dispatch inventory-auditor before the task list is locked and feed it into the plan before critique. Spec only has the seat's table row; no skill (plan-critique source list 5.3:135 omits it) and no core "when".
 4. Escalate to a research/review wave at 3+ failed fixes / known-heavy problem: listed only as "escalation wave" inside plan-critique, but the trigger fires during debugging, not planning - a skill about plan critique will not be loaded then. Core 8 does not name it.
 5. "Self-verification is not independent review" (don't skip reviewers for doc-only corrections): not listed in wave-review sources; given spec 3.1 pushes the other way, this deserves an explicit keep/drop.
 6. "Wave has no negative control: say so in wave close; carry a standing held-out evaluation row" (sixteenth item): not named; spec 9.2 evals partly echo but are for the restructure, not the rule.
 7. verification.md "Reporting." and "Watch for the asymmetry" (author's own assertions): "deleted: default behaviour" candidates, but need an explicit disposition, not silence.
 8. "When you correct a false statement, check what was DECIDED on it" and "Making a no-op live must not move its default": belong to verification-patterns group "claims that decay"/"fixes" but not obviously; traceability script (9.1) must map them.
9.1's script covers this by design if built as stated; the finding is that 5.2/5.3 as drafted do not yet carry 1-4, which are triggers (cannot be recovered by description-matching a skill that is not loaded). Not Minor: Risk table row 1 states "core keeps the 'when' lines" but core item 8 keeps only three.
Fix: extend core item 8 to the five trigger lines (plan-writing inventory, brainstorming/premise check, publication gate, escalation, wave-end) each <=1 line, or add a `workflow-gates` skill and say so.

### F6 [Minor-to-Important] Premise: "114 headings" and unit definition
My extraction (headings + bold-lead + top-level bullets) gave 87 / 76 / 23 = 186 items vs spec 63/42/9 = 114. Different heuristic, so not a contradiction, but 9.1 acceptance is only as strong as its unit: bullets such as the verification shapes list and the many scc bullets (cores/mem/h_rt defaults, NCBI_EMAIL, bash -l) are individually load-bearing. Spec 9.1 concedes shapes are outside the count. Does a conclusion change? Yes: 9.1 "every section maps" would pass while ~70 bullets are unmapped. State the unit as items, include top-level bullets.

### F7 [Minor] Documents: DECISIONS.md (44,648 B) and ARCHITECTURE.md (6,406 B) are not auto-loaded
Evidence: no @import; CLAUDE.md:22 and rules only mention by name. So the owner's "slim documents" does not apply to tokens there; only readers (inventory-auditor, docs-sync) pay. Spec correctly leaves them. Memory: MEMORY.md 85 lines/14.1 KB, 68 topic files 296 KB lazy - 5.1 "<=60 entries" is stated but 5.8 lists no compression plan beyond one sentence; the 25 entries marked project_* are not scoped. Project CLAUDE.md files (38 KB for 6 projects, out of scope 8) are the likely place an owner sees "bloat" when working in a project: the active project EnzymeFinder keeps its CLAUDE.md at projects/EnzymeFinder/.claude/CLAUDE.md (1,366 B) - small, fine. MqnE 12.6 KB and K4-K26 10.4 KB are the large ones. Does a conclusion change? No (out-of-scope is stated). Minor.

### F8 [Minor] "Pre-existing statements the spec gets wrong"
 - 1: "the 10 existing seats" - there are 11 files in .claude/agents (anomaly-hunter included); repo CLAUDE.md also says 10 and is stale; spec 5.8 corrects only the rules sentence.
 - 5.3 `workspace-audit` "gains the budget check" and "upstream-drift check": listed in 5.3/5.8 but not in a Tasks list - spec has no task list, so ownership of these edits is unassigned.

End HEAD 076b0f8; status unchanged (untracked findings files only).

## Close
Strongest unasked objection: the spec's "zero lessons lost" (6) is certified by a section-level traceability script (9.1) whose unit excludes bullets, while the real regression risk is TRIGGER loss: a lesson in a skill fires only if something loads the skill, and the five process triggers (F5) are not in core. The eval set (9.2, 8 scenarios) cannot cover ~186 items, so "unchanged behaviour" is asserted from ~8 samples.
Brief/spec errors: spec 1 and repo CLAUDE.md say 10 seats; there are 11. Brief says "114" is a heuristic count: my heuristic gives 186 items (F6). Brief's claim that other seats' files sit "next to yours" is true; I did not duplicate them.
