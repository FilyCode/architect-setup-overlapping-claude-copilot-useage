# Documentation convention + SenC pilot (2026-11-18)

**Goal:** status docs stop drifting from their source: counts and tables a script can derive are
generated between markers with a `--check` gate, each fact has one home, and cited paths, scripts
and flags are checked to exist. Pilot in SenC-SelD-GNcheck (staged), then the owner decides rollout.
**Serves:** the owner's audit aim (2026-11-18): docs "always get stale and so often need to be
rewritten and checked and updated"; and "more efficient, less error prone and more token
efficient, while keeping or increasing quality" (2026-11-08).
**Owner rulings (AskUserQuestion 2026-11-18):** "Doc program" → convention + SenC pilot; "SenC
pilot" → staged, S2 + S4 first; "Rollout bar" → no preset threshold: "lets just wait for next
review and then check the result and then lets decide what to do".
**Order:** D3 runs after the skill-consolidation plan's T10 swap (both edit wave-review) [F3, L8].
**Critique:** `.superpowers/findings/2026-11-18/plan-critique/` (rows applied; ids in brackets).

## Calibration (evidence: `.superpowers/findings/2026-11-18/workspace-audit/`)

- Churn since 2026-10-04 (`investigator-doc-churn.md`; two rows re-derived by the controller):
  SenC `docs/NEXT_TASKS.md` 205 commits, 1,885 lines, hand-maintained ("Not a generated file",
  line 3), ungated; EF `phases/W9-BACKLOG.md` 172; BileAcidDB open-items plan 139; MeMES
  `docs/REGISTER.md` 118. PROJECT_STATE is rewritten in place in the four big repos (24-92% of
  changed lines deleted). DECISIONS files are append-only (3-4%).
- Existing generators/checks [F1, L9]: EF `phases/OPEN_TASKS.md` generated + CI; EF
  `scripts/check_citations.py` checks backticked paths and `--flag` attribution (EF-hardcoded,
  report-only; flags never fail [C6]); SenC `183_survey_map.py --check`, `186_decisions_index.py
  --check` (the only BEGIN/END splice), `105_doc_preflight.py` (dangling `results/*` citations,
  `135_gates.sh:62`); MeMES `70_summary.py --check-docs`. EF `build_open_tasks.py --verify-live` is
  a staleness probe, not a reference checker.
- Retirement: SenC DECISIONS has no ruling against generating NEXT_TASKS or PROJECT_STATE
  (`command grep -nE -i "NEXT_TASKS.*generat|PROJECT_STATE.*generat" docs/DECISIONS.md`: 0 hits).
  Supporting: SenC DECISIONS.md:2305 (a claim lived in CLAUDE.md "outside every check ... no
  generator rewrites"). Constraining: SenC DECISION-043 (`DECISIONS.md:430`) "extend existing
  generators rather than add a fourth/new one" [F5].
- What this does NOT fix [D5]: a generated block guarantees block == register, not register ==
  world. A premature "closed" typed into the register renders faithfully and `--check` stays
  green, so the pilot does not address R-20261109-3 ("closed" before review, 5 failures).
- External practice (`investigator-doc-best-practice.md`, `plan-critique/domain.md`): one home per
  fact; generated blocks + `--check`; reference checking (outdated code references in docs:
  arXiv 2212.01479 primary [D6]); append-only decisions; keep always-loaded files short (Claude
  Code memory docs; arXiv 2602.11988: context files add > 20% cost) — hence no doc map in CLAUDE.md
  [D4, L5]. Agents follow stale instruction files (arXiv 2610.30571, preprint) — the reason for D2.
- Vision: the documentation layer. Not responsible for prose truth or the science.
- Thresholds: declared, none derived.

## Phase 1 — workspace

**D1 convention [D4, L5, F6].** Template `.claude/context/doc-convention.md` (config repo, not
auto-loaded): four doc classes — generated (marker text names script and gate), append-only,
register (single home of status), prose (hand-written; no counts the generator owns). In the pilot
only: one path-scoped rule `.claude/rules/docs.md` in SenC (owner approval) pointing at
`docs/GATES.md` for gate names. Other projects get theirs at their rollout wave.
**D2 reference check [F1, L6, C5, C6].** No move to the config repo (EF CI imports the script).
EF `scripts/check_citations.py` gains `--repo-root` and a prefix list, through an EF PR with its
governance test updated. Run from SenC at wave end, report-only. Before any gate use: measure n
references and n unresolved on SenC HEAD; gate only with a ratchet baseline or 0 unresolved; flag
attribution stays report-only. The allowlist never exempts CLAUDE.md or `.claude/rules`.
**D3 wave end [C13, L8].** One line in the curated wave-review (after the consolidation T10 swap):
docs-sync runs `check_citations.py --repo-root` and the project's gate script; "gate not run" is a
distinct output state.

## Phase 2 — SenC pilot, staged (in a SenC session after its current wave closes; live tree)

**S2 generated status [C7, F5].** Copy `186_decisions_index.py`'s BEGIN/END splice and `--check`
(DECISION-043: extend, not a new generator family) to render NEXT_TASKS' status summary from the
committed rows of the A-sexvicies table (input named in the marker). Only values derived from those
rows go inside the markers; "last commits" and "last gate run" stay outside. `--check` in
`135_gates.sh`. Status words in the register are not enforced (unenforced; see D5).
**S4 measure [C8, D5].** Arms declared now: before = the 4 SenC retro-log entries preceding the
pilot commit; after = the next 4. Per arm: hand-edit hunks in regions that stay hand-written in both
arms, docs-sync drift findings, and a truth sample of 10 random register rows whose evidence cell is
re-derived. n and spread printed.
**S1, S3 conditional:** the register move (S1) and the PROJECT_STATE shrink (S3) only if the
owner, reading S4 at the next review, says so.

## Phase 3 — rollout

Owner decides after reading S4 (no preset threshold). Candidates: MeMES, BileAcidDB, EnzymeFinder.

## Acceptance

Phase 1: D2's measurement table (n refs, n unresolved) on SenC HEAD; EF PR green with its
governance test; D3 line present. Phase 2: S2 `--check` seen failing on a hand-edited count inside
the markers and passing on a committed tree; S4 table recorded with n.

## Known limitations

- Prose truth and register truth are unchecked by any mechanism; review seats and S4's truth
  sample are the only checks.
- [A4] The R-20261109-3 commit-msg hook (reject "closed" in DECISIONS or a commit subject unless
  the roster close line exists) is not built. Trigger: S4 truth sample finds a closed row without a
  re-derivable evidence cell, or a sixth "closed before review" retro line. Owner: SenC session.
- S4 has n = 4 waves per arm, and D3 changes the docs-sync instrument between arms (domain
  objection); drift-finding counts are compared with that caveat.
