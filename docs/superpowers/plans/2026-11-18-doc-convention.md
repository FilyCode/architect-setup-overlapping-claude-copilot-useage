# Documentation convention + SenC pilot (2026-11-18)

**Goal:** status and register docs stop being hand-rewritten: every count, status word and table
that a script can derive is generated with a `--check` gate, each fact has one home, and every
path/script/flag a doc cites is checked to exist. Pilot in SenC-SelD-GNcheck, then roll out.
**Serves:** the owner's audit aim (2026-11-18): docs "always get stale and so often need to be
rewritten and checked and updated"; and "more efficient, less error prone and more token
efficient, while keeping or increasing quality" (2026-11-08).
**Owner ruling:** 2026-11-18, AskUserQuestion "Doc program" → "Convention + SenC pilot".

## Calibration (evidence: `.superpowers/findings/2026-11-18/workspace-audit/`)

- Churn since 2026-10-04 (`investigator-doc-churn.md`, re-derived by the controller for two rows):
  SenC `docs/NEXT_TASKS.md` 205 commits, 1,885 lines, hand-maintained, ungated; EF
  `phases/W9-BACKLOG.md` 172; BileAcidDB open-items plan 139; MeMES `docs/REGISTER.md` 118,
  `FINDINGS.md` 110. PROJECT_STATE is rewritten in place in all four big repos (24-92% of changed
  lines are deletions; EF +208/-2,504). DECISIONS files are append-only (3-4% deletions).
- Only EF `phases/OPEN_TASKS.md` is generated and CI-checked. SenC `135_gates.sh` checks
  SURVEY_MAP and the decisions index only; MeMES `gates.sh --check-docs` checks numbers in FINDINGS
  and PROJECT_STATE but has no CI; BileAcidDB and the config repo check no Markdown.
- Retro log: 40 stale/drift lines; PROJECT_STATE the most named (6). "Closed before review" prose
  rule failed 5 times (R-20261109-3).
- External practice (`investigator-doc-best-practice.md`): one home per fact; generated blocks +
  `--check` (cog model); claim-dereferencing check (Tan et al. arXiv 2307.04291: ≥25% of top
  projects have an outdated code reference); append-only decisions; short CLAUDE.md (Claude Code
  memory docs; arXiv 2602.11988, 2610.30571 — preprints). Freshness dates and CODEOWNERS judged low
  fit (agents maintain these docs).
- Existing doc gates also include SenC `scripts/105_doc_preflight.py` (withdrawn claims in
  group-facing docs; NEXT_TASKS rows D-67, D-89 note its coverage gaps). SenC NEXT_TASKS line 3
  says "Not a generated file" — the pilot changes that convention for its status parts.
- Retirement check: SenC DECISIONS has no ruling against generating NEXT_TASKS or PROJECT_STATE
  (`command grep -n -i "NEXT_TASKS.*generat|PROJECT_STATE.*generat"`: 0 hits); config DECISIONS
  none either.
- Vision: the documentation layer of every project. Not responsible for prose truth, for the
  science, or for DECISIONS (already append-only and healthy).
- Realistic target: generated parts cannot drift (a `--check` fails); dangling references are found
  at wave end; status re-edit commits fall. Expected: fewer docs-sync drift findings; size of the
  fall UNMEASURED until S4.
- Limits: field-wide, no tool verifies that prose is true (Tan et al. check references only);
  everything else listed here (ungated status, many copies) is ours.
- Standard: cog-style generated blocks with `--check`; lychee for links. Does it already exist
  here? Yes in parts: EF OPEN_TASKS is generated+CI; SenC 183/186 and MeMES --check-docs are
  generated/checked; D0 inventories them before D2 builds anything.
- Thresholds: "≤ 60 lines" for PROJECT_STATE and "≤ 10-line doc map" are declared choices.
- Commit counts measure edits, not harm (churn seat's objection): the pilot measures drift
  findings and re-edit rate, not only commits.

## Phase 1 — workspace (config repo)

**D0 inventory (inventory-auditor):** EF `scripts/check_citations.py`, EF `build_open_tasks.py
--verify-live`, SenC `183`/`186 --check`, MeMES `70_summary.py --check-docs`: what each checks,
what is reusable workspace-wide.
**D1 doc map:** each project CLAUDE.md gets a ≤10-line "Doc map": file → class, one of
`generated (<script> --check, gate <name>)`, `append-only`, `register (single home of status)`,
`prose (hand-written, no counts or status words)`. Template in `.claude/context/doc-convention.md`
(not auto-loaded). Project CLAUDE.md edits need the owner's approval per project.
**D2 reference checker:** `tools/doc_refs.py <repo>`: backticked paths, script names and
`--flags` of named scripts in tracked .md must exist (offline, no network); generalised from
check_citations.py if D0 says it fits, else new and small. Exit 1 on a dangling reference; an
allowlist for historical docs (`docs/history/`, archives).
**D3 gates:** docs-sync runs `doc_refs.py` and every `--check` named in the doc map at wave end;
wave-review lists it; each project's gate script calls its own checks.

## Phase 2 — SenC pilot (run in a SenC session, after its current wave closes; that tree is live)

**S1** register single home: the A-sexvicies deferred table moves to a structured register
(one table, one row per item, a Status column with a fixed vocabulary); DONE/CORRECTED history
leaves the cells for an append-only history file.
**S2** generated status: a script renders NEXT_TASKS' status summary and the PROJECT_STATE status
block (counts by status, open items with triggers, last gate run, last commits) between
BEGIN/END GENERATED markers; `--check` in `135_gates.sh`. Status words (closed, resolved, done)
appear only in generated text or the register's Status column.
**S3** PROJECT_STATE hand-written part shrinks to a dated focus/next paragraph (≤ 60 lines total).
**S4** measure: for 4 waves before and after — commits per wave to NEXT_TASKS and PROJECT_STATE,
docs-sync drift findings per wave, retro stale/drift lines naming SenC docs.

## Phase 3 — rollout

MeMES (extend `--check-docs` to the REGISTER summary), BileAcidDB (open-items plan → register +
generated summary), EnzymeFinder (PROJECT_STATE status block from OPEN_TASKS generator). One
project per wave, each after its own current wave; skipped if S4 shows no reduction.

## Acceptance

Phase 1: doc_refs.py seen failing on a planted dangling path; doc maps in the 4 big repos
(owner-approved); docs-sync brief names the checks. Phase 2: S2's `--check` seen failing on a
hand-edited count; S4 table recorded with its n.

## Known limitations

- Prose truth (a sentence that is wrong but references existing things) is not checked by any
  mechanism here; review seats remain the only check.
- The two agent-behaviour studies are preprints on synthetic or SWE-bench tasks.
