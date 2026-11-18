# Skill consolidation (2026-11-18)

**Goal:** the six process skills (verification-patterns, dispatch-brief, plan-critique,
wave-review, scientific-evidence, running-sge-jobs) each become one curated text: no "header +
verbatim moved text" layering, nothing a later line supersedes, load-bearing rules first, every
SKILL.md body ≤ 12,288 bytes, and a test that fails when any skill is over its ceiling or missing.
**Serves:** the owner's audit aim (2026-11-08 and 2026-11-18 requests): "more efficient, less error
prone and more token efficient, while keeping or increasing quality".
**Owner rulings (AskUserQuestion 2026-11-18):** "Skill size" → full review wave; "Six or four" →
all six, keep `tools/build_skills.py` dormant; "Review depth" → 7 seats + coverage script.
**Out of scope:** agent files (except retro-officer's target path), core.md, hooks.
**Critique:** `.superpowers/findings/2026-11-18/plan-critique/` (inventory, lean, critic, domain,
pragmatism: 30 FIX-NOW rows applied here; ids in brackets).

## Calibration

- Sizes at 36f2a5e (`wc -c`): header / SKILL.md+references: dispatch-brief 5,384 / 32,348;
  plan-critique 4,658 / 19,534; verification-patterns 3,517 / 35,170; wave-review 4,701 / 16,498;
  scientific-evidence 1,401 / 10,958; running-sge-jobs 2,683 / 7,888. `context_budget.py` bodies
  of the first four: 16,797 / 15,925 / 16,097 / 16,061 (ceiling 15,360). Non-skill OVER is
  reported separately (MEMORY.md 6,654 of 6,656) [C4, C12].
- Why it grew: each retro integration appends a header line; build_skills.py and
  `test_every_skill_body_is_verbatim` freeze the moved text, so nothing old is merged or deleted.
  Reference parts were read 11 times in a month (`.superpowers/findings/2026-11-08/workspace-audit/skill_scan.log`).
- Platform fact [D1]: after compaction Claude Code keeps only the first 5,000 tokens of each
  invoked skill (quoted in `plan-critique/domain.md` D1, code.claude.com/docs skills page); the four
  measure ~5,000-6,000 tokens on invocation (n=20, `probes/domain/skill_tokens.py`), ~3.3 B/token.
  12,288 B ≈ 3,700 tokens, so a curated body survives compaction whole. Anthropic skill guidance:
  concise SKILL.md, detail in referenced files with a contents list (domain.md D1/D3 quotes).
- Readers: `skills:` preload in implementer, critic-reviewer, investigator, lean-critic
  (verification-patterns); anomaly-hunter, domain-reviewer, figure-auditor (scientific-evidence);
  scc-monitor (running-sge-jobs). Invocations since 2026-10-14: dispatch-brief 172, plan-critique
  69, wave-review 66, running-sge-jobs 56, scientific-evidence 17.
- Cited headings that must survive by name [F3]: dispatch-brief "Concurrent dispatches need
  declared file ownership" (`rules/python.md:21`); plan-critique's escalation section (`core.md`
  rule 8; `verification-patterns/SKILL.md:46`; heading now at plan-critique `SKILL.md:209`).
- Retirement: DECISION-026 made the verbatim move deliberate; DECISION-030 item 5 added
  provenance sidecars. This plan supersedes both parts; traceability = git history + the
  disposition map + rule-map.tsv (kept as history) [F5, C11].
- Vision: the process layer only. Realistic target: six bodies ≤ 12,288 B, every old rule with a
  checked disposition, no eval scenario collapsing. Standard: Anthropic skill-authoring guidance;
  our existing `evals/` before/after harness (2026-10-14) is the behavioural check [D2].
  Thresholds: 12,288 B = 80% of our own ceiling (declared), fits the 5,000-token compaction limit.

## Tasks

**Staging [C9].** All edits happen in a git worktree on branch `skill-consolidation`
(`.worktrees/skill-consolidation`, not reached by the `~/.claude/skills` links). One swap (merge)
commit after owner sign-off; rollback = revert of that merge.

**E0 eval before arm [D2].** Submit before T2: `qsub -v ARM=consol-before,K=5,EVAL_OUT=<repo>/evals/runs/consol-before evals/run_evals.sh`
(h_rt 06:00:00, 1 slot); artifact 10x5 jsonl + `grade.py <dir> --out`.

**T0 inventory (controller).** Consumers of `reference/part-N.md`, `provenance.tsv`,
`build_skills.py`, `rule_map.py`, `rule-map.tsv`; every heading cited from agents, rules, hooks,
skills; open or deferred retro rows whose target is `skill-headers/<name>.md` [F3]. Into the ledger.

**T1 tooling (implementer).**
- `context_budget.py`: extract `skill_violations(paths)`; new test in the existing
  `tests/test_context_budget.py` calls it on `REPO/.claude/skills/*/SKILL.md`, asserts all six
  names found and body > 0, then no OVER, and prints bytes per skill against 12,288 [C1, C2, C4];
  seen failing with one skill dir renamed and on today's tree.
- `tools/skill_coverage.py`: builds the disposition skeleton
  `docs/history/consolidation-2026-11/<skill>.tsv` from rule-map.tsv items and header sentences
  pinned at 36f2a5e (`git show 36f2a5e:skill-headers/<s>.md`, sentence units); the implementer fills
  only the disposition column (`kept <section>` | `merged into <section>` | `dropped: <reason>`).
  `--check` exits 1 on a missing row, a `kept` row whose key tokens are absent from the named
  section, a named section that does not exist, or a `dropped` row without a reason; it prints
  dropped counts per skill [C3, L2a/b, C10]. Seen failing on a planted bad TSV.
- `tests/test_agents.py:23,86-89` repointed from `skill-headers/` to SKILL.md; seen failing on a
  SKILL.md without "lean-critic ... always" [F2]. `CLAUDE.md:26` wording updated.
- build_skills.py stays on disk, no longer run for any skill (owner: dormant); its tests still build
  into tmp_path and pass. Provenance sidecars removed. `skill-headers/` kept as history (read-only).
- retro-officer and workspace-audit name `.claude/skills/<name>/SKILL.md` as the proposal target.

**T2-T7 one implementer per skill (model: opus — contract: every session's process text).** Order:
T2 verification-patterns first (4 agents preload it), proving `skill_coverage.py --check` on it
before T3-T7 (dispatch-brief, plan-critique, wave-review, scientific-evidence, running-sge-jobs)
[L10]. Shape: when to use (2-3 lines); procedure or checklist; rules ordered by consequence, each
one or two sentences with a short evidence tag; nothing load-bearing past ~4,000 tokens [D1];
optional reference file with a contents list for rarely-needed detail [D3]. No new rules; wording
may change, meaning may not. Brief carries lean's cut-candidate pointers [L4/A1]. DONE: the
`--check` output and bytes.

**T8 build and gates (controller).** `skill_violations` exit 0 at ≤ 12,288 per skill; non-skill
OVER reported separately; relative links in each new SKILL.md resolve; `test_link_user_scope`;
full config test suite as an SGE job.

**T9 wave-end review (7 seats, wave-review).** alignment-officer reads `merged` and `dropped` rows
(the script covers `kept`) and every "applied" retro tick vs the new text; critic-reviewer;
lean-critic; docs-sync (DECISIONS, CLAUDE.md, rule-index, README); inventory-auditor; pragmatism;
retro-officer, which also re-targets the T0 retro rows. Fix round.

**T10 owner sign-off and swap.** The question lists dropped rows per skill and body + reference
bytes; on yes, merge; E1 after arm `ARM=consol-after` on the merged tree; DECISION-032.

## Acceptance

- `skill_violations` prints six bodies ≤ 12,288 B; `skill_coverage.py --check` exit 0 on all six;
  both seen red first.
- Eval: no scenario falls by ≥ 3 of 5 between arms; a fall of 2 goes to the alignment seat; a
  fall of 3 reverts the swap.
- DECISION-032 records the change.

## Known limitations

- "No meaning change" for `merged` rows is a reader judgement (alignment seat); the script checks
  presence, not meaning.
- Eval [A2]: 10 scenarios, K=5, default model only; detects collapse of a rule, not erosion.
  Deferred: 3-5 scenarios from merged/dropped rows and a 5-brief replay; trigger = any scenario
  down ≥ 2 of 5 or a merged row flagged as meaning-changing.
- Seats on other models (sonnet, haiku) not tested [A3]; trigger = a retro row showing such a seat
  ignoring a curated rule.
