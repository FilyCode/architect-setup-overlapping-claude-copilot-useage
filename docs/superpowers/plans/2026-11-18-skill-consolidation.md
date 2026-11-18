# Skill consolidation (2026-11-18)

**Goal:** dispatch-brief, plan-critique, verification-patterns and wave-review each become one
curated text: no "header + verbatim moved text" layering, nothing a later line supersedes,
every SKILL.md body at or under 12,288 bytes (the ceiling is 15,360; the gap leaves room for
growth), and `tools/context_budget.py` exiting 0 and run by the test suite.
**Serves:** the owner's audit aim (2026-11-08 and 2026-11-18 requests): "more efficient, less error
prone and more token efficient, while keeping or increasing quality".
**Owner ruling:** 2026-11-18, AskUserQuestion "Skill size" → "full review wave".
**Out of scope:** scientific-evidence and running-sge-jobs (under budget); agent files; core.md.

## Calibration

- Sizes now (bytes, `wc -c`, 2026-11-18 at 36f2a5e): header / SKILL.md+references total:
  dispatch-brief 5,384 / 32,348; plan-critique 4,658 / 19,534; verification-patterns 3,517 /
  35,170; wave-review 4,701 / 16,498. `context_budget.py` bodies: 16,797 / 15,925 / 16,097 /
  16,061, all over 15,360.
- Why it grew: each retro integration appends a header line; the moved text is frozen verbatim by
  `tools/build_skills.py` and `tests/test_build_skills.py::test_every_skill_body_is_verbatim`, so
  nothing old is ever merged or deleted. Reference parts were read 11 times in a month (Skill/Read
  scan 2026-11-08, `.superpowers/findings/2026-11-08/workspace-audit/skill_scan.log`).
- Readers: `skills:` preload in implementer, critic-reviewer, investigator, lean-critic
  (verification-patterns), anomaly-hunter, domain-reviewer, figure-auditor (scientific-evidence,
  untouched); controller invocations dispatch-brief 172, plan-critique 69, wave-review 66 since
  2026-10-14.
- Independent check of "nothing lost": the alignment seat diffs every rule-map item and every
  retro proposal ticked "applied" against the new text (not the implementer's own map).
- Retirement check: `command grep -n "verbatim\|build_skills" workspace-config/DECISIONS.md`
  → DECISION-026 (2026-10-14 restructure) made the verbatim move deliberate for traceability;
  this plan supersedes that part and keeps traceability through git history plus a disposition map.

- Vision: serves the process layer only (the text every controller and seat reads). Not
  responsible for whether sessions obey it (behaviour), for core.md, or for agent files.
- Realistic target: 4 bodies ≤ 12,288 B with no rule lost; readers see one current statement per
  rule. Not a measured quality gain (no behavioural eval).
- Limits: the 15,360 B ceiling is ours (2026-10-14 spec §5.1), not a platform limit; Claude Code
  docs recommend concise skills with detail in referenced files (code.claude.com/docs, skills
  page — UNVERIFIED wording, fetch in preflight). Growth by appended lines is ours (retro process).
- Standard: the Anthropic skill-authoring guidance (SKILL.md concise, progressive disclosure via
  referenced files). Does it already do this? It describes the shape, not our content; the
  existing references/part-N split is a mechanical form of it that readers do not open.
- Thresholds: 12,288 B is a declared choice (80% of our ceiling), not derived.

## Tasks

**T0 (controller) inventory.** List consumers of `reference/part-N.md`, `provenance.tsv`,
`build_skills.py`, `rule_map.py`, `rule-map.tsv` (`command grep -rln`), and every skill name or
section title cited from agents, rules, hooks or other skills. Output into the ledger.

**T1 tooling (implementer).** `build_skills.py` stops generating the four curated skills (a
`CURATED` set; their `.claude/skills/<name>/` files become the source); tests updated so the
verbatim test covers only the two remaining built skills; new test
`tests/test_context_budget.py::test_real_tree_within_budget` runs `context_budget.check()` on the
real tree's skill bodies and fails on any OVER line (seen failing first on today's tree), added to
the existing `tests/test_context_budget.py` and limited to skills, because MEMORY.md and home paths
are node-local (inventory F2); provenance sidecars of the four skills removed. Rule-map stays as
history. `tests/test_agents.py:23,86-89` reads `skill-headers/{wave-review,plan-critique}.md`:
repoint it to the curated SKILL.md and see it fail on a SKILL.md without "lean-critic" (inventory
F2). `skill-headers/` files for the four skills are deleted; retro-officer's proposal format and
the workspace-audit skill name `.claude/skills/<name>/SKILL.md` as the target (inventory F3; agent
file edit, owner-approved scope of this plan).

**T2-T5 one implementer per skill (model: opus — contract: every session's process text).** Input:
current SKILL.md + references + header. Output: one SKILL.md (body ≤ 12,288 B) with this shape:
when to use (2-3 lines); the procedure or checklist; rules each in one or two sentences with a
short evidence tag (date/project/id, no story); for verification-patterns a catalogue table
(failure → check → evidence tag) with the long incident narratives cut. Optional one reference
file only for material a reader needs rarely (verification-patterns incident detail), listed with
when to open it. Plus a disposition map `docs/history/consolidation-2026-11/<skill>.tsv`: every
rule-map item and every header line → `kept <section>` | `merged into <section>` | `dropped:
<reason: superseded by X / duplicate of Y / obsolete because Z>`. No new rules; wording may change,
meaning may not. Headings cited from elsewhere survive by name (inventory F3): dispatch-brief
"Concurrent dispatches need declared file ownership" (`rules/python.md:21`); plan-critique's
"escalation section" (`core.md` rule 8, `verification-patterns/SKILL.md:46`); T0 lists the rest.

**T6 build and gates (controller).** `context_budget.py` exit 0; full config test suite as an SGE
job; `tools/link_user_scope.sh` links unchanged.

**T7 wave-end review (full roster, wave-review).** alignment-officer (every disposition row vs
the old text and every "applied" retro tick vs the new text), critic-reviewer (contradictions,
dangling references, a rule whose meaning changed), lean-critic, docs-sync (DECISIONS, CLAUDE.md,
rule-index, README pointers), inventory-auditor (references to removed parts), pragmatism-officer,
retro-officer. Fix round, then owner sign-off before push.

## Acceptance

- Four bodies ≤ 12,288 B; `context_budget.py` exit 0; new real-tree test seen red at 36f2a5e.
- Every rule-map item for the four skills and every header line has a disposition row; zero
  `dropped` rows without a reason; alignment seat finds no meaning change unflagged.
- DECISION-032 records the change (supersedes the verbatim part of DECISION-026).

## Known limitations

- No behavioural eval: whether sessions follow the curated text as well as the old is UNMEASURED.
  Trigger: next retro integration counts recurrences of the dropped-text classes.
