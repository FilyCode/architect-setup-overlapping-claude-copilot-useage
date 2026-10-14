# Pragmatism-officer triage: 2026-10-14 setup restructure spec

Verdicts: FIX-IN-SPEC-NOW / PLAN-TASK / DEFER-DOCUMENTED / REJECT. Severity untouched (Blocking: critic:F1, domain:F2).
Seat abbreviations: critic, domain, anomaly, align (alignment-officer), inv (inventory-auditor).

1. Strategy: static baseline is ~5% of main cost; long-context calls dominate (anomaly:F3, domain:close, critic:close). FIX-IN-SPEC-NOW (honest scope + per-arena targets); owner Q1.
2. General-purpose dispatches carry most subagent spend; implementation-time lessons reach no preloaded seat (anomaly:F4, critic:F9). FIX-IN-SPEC-NOW (add named implementer agent row) + PLAN-TASK.
3. MEMORY.md reaches named subagents; omitClaudeMd effect on it unknown (domain:F1, anomaly:F2). FIX-IN-SPEC-NOW + Phase 0 probe.
4. Bytes/token is ~3, not 4 (anomaly:F1). FIX-IN-SPEC-NOW (budget unit = bytes).
5. Opus-5 guidance applied to sonnet/haiku seats at low effort (domain:F2 Blocking, domain:F5); over-verification unevidenced locally (anomaly:F5). FIX-IN-SPEC-NOW; yield tabulation PLAN-TASK; global effortLevel owner Q2.
6. Worktree isolation rule infeasible (critic:F1 Blocking). FIX-IN-SPEC-NOW option (a); REJECT option (b).
7. Preload feasibility, invocation modes, description cost, one budget definition (critic:F2, critic:F3, domain:F4 tail). FIX-IN-SPEC-NOW; probe Phase 0.
8. Skill compaction keeps only first ~5k tokens (domain:F4). FIX-IN-SPEC-NOW (per-skill cap, rules first); check in budget script PLAN-TASK.
9. Concurrency env var refuses rather than queues (critic:F4, domain:F3). FIX-IN-SPEC-NOW.
10. Hooks: matchers, JOB_ID key, subagent firing, corpus replay, versioned scripts, command-type only (critic:F6, critic:F7, domain:F8b, inv:F9, inv:F2b, inv:F5b). Constraints FIX-IN-SPEC-NOW; matcher table PLAN-TASK.
11. Budget script blind to agent descriptions, hooks, connectors, deferred tools, active account (critic:F12, anomaly:F7). FIX-IN-SPEC-NOW (measure_context = gate of record); REJECT sandbox-executing hooks.
12. Lesson placement: review template, rtk-embedded lessons, trigger orphans (critic:F8, critic:F10, align:F5). FIX-IN-SPEC-NOW; remainder via traceability script PLAN-TASK.
13. Traceability unit and 114 count (critic:F11, align:F6). FIX-IN-SPEC-NOW (drop number, unit includes top-level bullets).
14. Evals have no power (critic:F14, domain:F9; anomaly:F6 scenarios). FIX-IN-SPEC-NOW (design) + PLAN-TASK. Baseline captured before any change.
15. Skill collisions with superpowers; dispatch-brief too broad (domain:F7). FIX-IN-SPEC-NOW (narrow) + PLAN-TASK eval; fate of verification-before-completion DEFER.
16. Writing standard (domain:F6), mechanism-first framing (anomaly:F6). FIX-IN-SPEC-NOW (3 lines).
17. Seat env-block lines (domain:F8a). PLAN-TASK.
18. Dead pointers (critic:F13, align:F4, inv:F8). Live pointers PLAN-TASK; historical citations DEFER; REJECT stub files in rules/.
19. Memory contradictions (critic:F5). PLAN-TASK.
20. Karpathy (align:F1). FIX-IN-SPEC-NOW (disposition line).
21. Ponytail vs inventory-auditor constraint; lean-critic overlap (align:F2, inv:F7). FIX-IN-SPEC-NOW (decide).
22. completion-check tooling (align:F3, inv:F1, inv:F3, inv:F6). FIX-IN-SPEC-NOW (amend row) + PLAN-TASK; mutmut/diff-cover DEFER.
23. Persona overlaps, seat count, 12th seat (align:F4, anomaly:F5, inv:F9). PLAN-TASK; large-body slimming DEFER.
24. Existing assets (inv:F1, F4, F5, F6). Wire check_citations, reuse hook helpers PLAN-TASK; EF skill overlap DEFER.
25. DECISION-010 / cwd skill-load (inv:F2). FIX-IN-SPEC-NOW (cite) + Phase 0 probe.
26. DECISION-025 supersede (inv:F9). PLAN-TASK (approval needed).
27. Minors (domain:F10, F11, align:F7, F8, scc.md loop defect, workspace-audit prose). Fold into spec pass or PLAN-TASK.
