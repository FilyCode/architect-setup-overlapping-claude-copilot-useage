# Documentation System (hot/cold registers) Implementation Plan

> **STATUS 2026-11-26: SUPERSEDED before Task 1.** Owner redirected (2026-11-26): one canonical format for ALL projects, converted once, built for EnzymeFinder and BileAcidDB (1-4 more years); rollout MeMES -> BAD -> EF; format (md file per item vs database vs hybrid) pending a research wave (`.superpowers/findings/2026-11-26/doc-research/format-research-investigator.md`, `bench/`). Critique findings that carry over to the redesign: `.superpowers/findings/2026-11-26/plan-critique/{inventory,critic,domain,lean}.md`.

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** one documentation convention for every project: registers that hold only open items in short rows, history out of the live view, a short PROJECT_STATE index, and a gate that keeps it so. Piloted on SenC-SelD-GNcheck with a before/after measurement.

**Serves:** the owner's aim (2026-11-26 message): "we need good documentation but also something that is manageable, maintainable, and readable ... a system that is optimal for you but potentially still readable by me if needed and fits all the projects"; and the 2026-11-18 audit aim quoted in `2026-11-18-doc-convention.md` ("docs always get stale and so often need to be rewritten and checked and updated").

**Architecture:** a stdlib-only tool `tools/docsys.py` in the config repo (subcommands `check`, `archive`, `rotate`, `measure`) driven by a per-project `docs/docsys.json` that names the project's registers, logs and caps. Projects call it by absolute path from their gate script. The SenC migration is a separate, partly judgment-based wave run in a SenC session after its current wave closes.

**Tech Stack:** Python 3.13 stdlib (workspace venv `/projectnb/liu-scc/philipp/.venv/bin/python`), pytest, markdown.

**Spec:** `.superpowers/findings/2026-11-26/doc-research/PROPOSAL.md` (owner-approved 2026-11-26, DECISION-035(3)). Evidence: `inventory-investigator.md`, `best-practice-investigator.md`, `probes/doc_reads.json` in the same directory. Extends `docs/superpowers/plans/2026-11-18-doc-convention.md` (DECISION-032(2)); its Phase 1 D1/D2 were never done and are folded in here (D1 as Task 5; D2 stays as written there, out of scope).

## Calibration (re-derived 2026-11-26 at SenC HEAD `e1283ee`)
- SenC `docs/NEXT_TASKS.md`: 749,702 chars; 436 table rows holding 643,298 chars, 107,278 chars of prose; about 30 dated `## A-*` journal sections; the register is section `A-sexvicies` (line 1355), 375 `| D-n |` rows whose LAST column is OWNER, with status mixed in (`next-wave` 169, `closed` 56, `closed 2026-11-02 (DECISION-178)` 37, `controller` 35, ...). Status is not its own column.
- MeMES `docs/REGISTER.md`: clean `| ID | Item | Status | Note |` table, status words OPEN / CLOSED <date> / PARTLY CLOSED / MEASURED.
- EF `phases/W9-BACKLOG.md`: 1.45M chars, 1,081 rows, IDs bolded on purpose (`build_open_tasks.py --verify-live` keys on `| <ID> |`).
- SenC PROJECT_STATE.md 38,028 chars; reads across 1,708 transcripts since 2026-11-01: MeMES PROJECT_STATE 9 reads / 451k chars; registers rarely and partially read (doc_reads.json).
- Thresholds are declared, not derived: row cap 600 chars, PROJECT_STATE cap 8,000 chars. Both are
  dataset-specific choices for these repos (SenC median row ~1.4k; Claude Code memory docs "target
  under 200 lines" for always-loaded files, best-practice-investigator.md), revisited at Task 8.
- **Vision context:** the documentation layer of every project: what is open, what was decided,
  where the evidence is. NOT responsible for whether a row's science is right, nor for a premature
  "closed" typed into a row (a gate guarantees format, not truth; 2026-11-18 plan D5 caveat).
- **Realistic target:** SenC hot register + PROJECT_STATE readable in one read each (est. < 60k
  chars together, UNMEASURED until Task 6/7), no information lost (verbatim moves), and a gate that
  stops regrowth. Not: fewer errors in rows.
- **General limits vs ours:** no source measures agent accuracy on table vs per-item docs
  (best-practice-investigator.md CLOSING) — a field gap, hence the Task 6/8 read test. Everything
  else (heterogeneous SenC journal, status mixed into the OWNER column) is OURS.
- **Standard / does it already exist:** ADR superseded-by (Nygard), keepachangelog-style dated
  logs, generated blocks with `--check` (SenC 186, EF `build_open_tasks.py` + CI, MeMES
  `70_summary.py --check-docs`). EF's generated `phases/OPEN_TASKS.md` already gives EF an open-items
  view: the EF rollout (Task 8) must reuse it, not replace it.
- **Retirement check (2026-11-26):** `command grep` of SenC/MeMES/EF DECISIONS and FINDINGS for
  NEXT_TASKS/REGISTER/BACKLOG/PROJECT_STATE near withdrawn|retired|generat|archiv: no ruling against;
  supporting EF DECISIONS.md:1515 ("Every register field that can be derived is generated");
  SenC DECISIONS.md:2305 (claims in a file no generator rewrites). SenC DECISION-043 constrains
  (Global Constraints).

## Global Constraints
- Nothing is deleted: every moved text lands verbatim in an archive, log or item file, and git keeps the rest.
- Status is a typed state: `OPEN`, `CLOSED`, `PARTLY_CLOSED`, `UNKNOWN` (core rule 2); `UNKNOWN` is never treated as closed.
- Generated blocks use the SenC 186 splice convention: `<!-- BEGIN GENERATED: <name> -- rewritten by <script> -->` / `<!-- END GENERATED: <name> -->`, exactly one pair per name.
- Every writing subcommand has `--dry-run` printing the unified diff to stdout (no `--write` without it being explicit: default is dry-run; `--write` writes).
- The tool never edits a project's CLAUDE.md, DECISIONS or rules files.
- Exit codes: 0 clean, 1 violations, 2 config/usage error. Error messages say what the check does.
- SenC DECISION-043 ("extend existing generators, no new generator family") applies inside SenC: SenC's PROJECT_STATE counts block is rendered by extending `scripts/186_decisions_index.py`'s splice, not by a new SenC script; `docsys` is workspace tooling, which the plan-critique must confirm or overrule.

## Review Focus
1. A register row whose state cannot be parsed (SenC's OWNER column, prose status): must come out `UNKNOWN` and stay in the hot file, never archived. → Task 1 test `test_unparseable_status_is_unknown_and_not_archived`.
2. Running `archive --write` twice: second run is a no-op (idempotent), archive rows not duplicated. → Task 3 `test_archive_is_idempotent`.
3. A register table interrupted by prose or a second table in the same file (SenC has ~30): only the configured table (by heading) is touched; bytes outside it unchanged. → Task 1 `test_only_configured_table_is_parsed`, Task 3 `test_bytes_outside_register_unchanged`.
4. Pipes inside backticks or escaped `\|` in a cell must not split the cell. → Task 1 `test_escaped_pipe_does_not_split_cell`.
5. A project with legacy violations must be able to adopt the gate before migrating: `check --baseline <file>` fails only on NEW violations (ratchet). → Task 2 `test_baseline_ratchet_fails_only_new_rows`.

---

### Task 1: register parser and typed status

**Files:**
- Create: `tools/docsys.py`
- Test: `tests/test_docsys.py`

**Interfaces:**
- Produces: `class State(Enum): OPEN, CLOSED, PARTLY_CLOSED, UNKNOWN`; `@dataclass Row(id: str, cells: list[str], line_no: int, raw: str, state: State)`; `parse_register(text: str, heading: str, id_col: str, status_col: str | None, status_re: dict[str, str]) -> list[Row]`; `load_config(repo: Path) -> dict` reading `docs/docsys.json`.
- Config schema (`docs/docsys.json`): `{"registers": [{"file": str, "heading": str, "id_col": str, "status_col": str|null, "status_re": {"CLOSED": regex, "PARTLY_CLOSED": regex, "OPEN": regex}, "row_cap": 600, "archive_dir": "docs/archive"}], "logs": [{"file": str, "section_re": regex, "log_dir": "docs/log"}], "state_file": "PROJECT_STATE.md", "state_cap": 8000, "generated_checks": [str]}`.

- [ ] **Step 1: tests** — `test_parses_memes_style_table` (header `| ID | Item | Status | Note |`, rows `CLOSED 2026-10-29 — ...` → CLOSED, `**PARTLY CLOSED 2026-10-30**` → PARTLY_CLOSED, `OPEN, live lead` → OPEN; markdown bold stripped before matching); `test_unparseable_status_is_unknown_and_not_archived` (`status_col` = OWNER cell `controller` → UNKNOWN); `test_only_configured_table_is_parsed` (file with two tables, heading selects the second); `test_escaped_pipe_does_not_split_cell` (cell containing `` `a|b` `` and `a \| b` stays one cell); `test_missing_heading_is_config_error` (raises `SystemExit(2)` naming the heading).
- [ ] **Step 2:** run `pytest tests/test_docsys.py -q` → FAIL (module missing).
- [ ] **Step 3:** implement the signatures above by EXTENDING, not re-writing: move `tools/wave_stats.py:_cells` and `_register_rows` (lines 146, 150) into `docsys.py` and have `wave_stats` import them (its tests must stay green); add the escaped-pipe split `(?<!\\)\|` (as in MeMES `scripts/38_register_words.py`) and backtick-span protection. Status matching order CLOSED, PARTLY_CLOSED, OPEN, else UNKNOWN (precedent: EF `count_deferred_registers.py` CLOSED/AMBIGUOUS/OPEN); `status_col: null` means the last column. Inventory: `.superpowers/findings/2026-11-26/plan-critique/inventory.md`.
- [ ] **Step 4:** run → PASS; also parse the real MeMES `docs/REGISTER.md` read-only and paste the state counts (n per State).
- [ ] **Step 5:** commit `tools/docsys.py tests/test_docsys.py`.

### Task 2: `docsys check` (caps, closed-in-hot, generated freshness, ratchet)

**Files:** Modify `tools/docsys.py`; Test `tests/test_docsys.py`.
**Interfaces:** Consumes Task 1. Produces `check(repo: Path, baseline: Path | None) -> list[Violation]`; `@dataclass Violation(kind: str, file: str, id: str | None, detail: str)` with kinds `row_over_cap`, `closed_in_hot`, `state_over_cap`, `generated_stale`, `generated_not_run`; CLI `docsys.py check --repo <path> [--baseline <json>] [--write-baseline <json>]`.

- [ ] **Step 1: tests** — `test_row_over_cap` (601-char row → `row_over_cap`, 600 → none); `test_closed_row_in_hot_file` (CLOSED row → `closed_in_hot`; PARTLY_CLOSED and UNKNOWN → none); `test_state_file_cap` (8,001 chars → violation, 8,000 → none); `test_generated_check_failure_reported` (config `generated_checks: ["false"]` → `generated_stale`; `["true"]` → none; missing executable → `generated_not_run`, a distinct state); `test_baseline_ratchet_fails_only_new_rows` (baseline lists row ids D-1, D-2 over cap; a new over-cap D-3 fails, D-1 does not; baseline keyed by (kind, file, id)).
- [ ] **Step 2:** run → FAIL. **Step 3:** implement (ratchet pattern: EF `scripts/check_size_ratchet.py`; decided: docsys fails only on NEW violations and prints paid-down entries as `baseline_stale` info, exit 0, so the owner shrinks the baseline with `--write-baseline`); generated checks run via `subprocess.run(cmd, shell=False, cwd=repo, timeout=120)` from a list split with `shlex.split`. **Step 4:** run → PASS; run `check --repo` on MeMES read-only and paste the violation counts per kind (this is the MeMES "before" number; do not write a baseline there).
- [ ] **Step 5:** commit.

### Task 3: `docsys archive` (closed rows to monthly archive)

**Files:** Modify `tools/docsys.py`; Test `tests/test_docsys.py`.
**Interfaces:** Produces `archive(repo: Path, write: bool, today: date) -> str` (returns unified diff); CLI `docsys.py archive --repo <path> [--write]`. Archive file: `<archive_dir>/<register-file-stem>-<YYYY-MM>.md` where YYYY-MM is the month of the archive run; header = register heading + table header copied; rows appended verbatim.

- [ ] **Step 1: tests** — `test_closed_rows_move_verbatim` (CLOSED row bytes appear unchanged in archive, gone from hot); `test_archive_is_idempotent`; `test_bytes_outside_register_unchanged` (hash of text before heading and after the table equal); `test_dry_run_writes_nothing` (mtimes unchanged); `test_partly_and_unknown_stay`.
- [ ] **Step 2-4:** FAIL → implement → PASS.
- [ ] **Step 5:** commit.

### Task 4: `docsys rotate` (dated log sections to monthly files) and `docsys measure`

**Files:** Modify `tools/docsys.py`; Test `tests/test_docsys.py`.
**Interfaces:** Produces `rotate(repo: Path, write: bool, today: date) -> str`: for each `logs` entry, `##` sections whose heading matches `section_re` with a `YYYY-MM-DD` date in a month before `today`'s move verbatim, in order, to `<log_dir>/<YYYY-MM>.md`; undated sections stay and are listed on stderr. `measure(repo: Path) -> dict` → `{file: {"chars": int, "rows": int, "rows_by_state": {State: int}, "max_row": int}}` for registers, logs, state file; CLI prints JSON.

- [ ] **Step 1: tests** — `test_old_month_sections_move_in_order`; `test_current_month_stays`; `test_undated_section_stays_and_is_reported`; `test_rotate_idempotent`; `test_measure_counts` (fixture with known chars and states).
- [ ] **Step 2-4:** FAIL → implement → PASS.
- [ ] **Step 5:** commit. Then run the full config-repo suite via qsub (`.superpowers/findings/2026-11-26/setup-round3/suite.qsub` pattern) and paste the pass count.

### Task 5: convention text and wiring (config repo)

**Files:**
- Create: `.claude/context/doc-convention.md` (not auto-loaded; ≤ 4,000 chars)
- Modify: `.claude/skills/wave-review/SKILL.md` (one line: docs-sync runs `docsys.py check` where the project has `docs/docsys.json`; "gate not run" is its own output state) — body must stay ≤ 12,288 B (`tests/test_context_budget.py`).
- Test: `tests/test_context_budget.py` (existing, must stay green).

- [ ] **Step 1:** write the convention: the doc classes (generated / append-only / register / log / prose), the row rule (id | state | one-line what | evidence path | trigger; ≤ 600 chars; a correction replaces the cell and the commit message names the row id), item files `docs/items/<id>.md` (current state first, dated log below) only when a row needs more, PROJECT_STATE as an index ≤ 8,000 chars, decisions append-only with `Superseded by DECISION-n`, monthly logs, the `docsys.json` schema with one worked example (MeMES REGISTER).
- [ ] **Step 2:** add the wave-review line; run `pytest tests/test_context_budget.py -q` → PASS.
- [ ] **Step 3:** commit. Owner approval for the skill edit: DECISION-035(3).

### Task 6: SenC before-arm measurement and read test (read-only on SenC)

**Files:** Create in SenC findings: `.superpowers/findings/<date>/doc-pilot/before.json`, `read-test-questions.md`, `read-test-before.md`.
- [ ] **Step 1:** write SenC's draft `docs/docsys.json` in the findings dir (NOT in the SenC tree yet): register = `docs/NEXT_TASKS.md` heading `## A-sexvicies...`, `id_col` `#`, `status_col` null; logs = `docs/NEXT_TASKS.md` `## A-` sections, `docs/STATUS.md`, `docs/FINDINGS.md`. Run `docsys.py measure` against it → `before.json`. Paste n rows by state; expect many `UNKNOWN` (OWNER column).
- [ ] **Step 2:** rows touched per wave for the last 4 SenC retro-log waves: `git log --numstat` on NEXT_TASKS / PROJECT_STATE between the waves' commits → `before.json`.
- [ ] **Step 3:** freeze 10 questions answerable from the register and PROJECT_STATE (e.g. "what are the open PI decisions", "what triggers D-37"), each with its expected answer and source row, written BEFORE migration; an investigator answers them from the current files (tokens used + correctness) → `read-test-before.md`.

### Task 7: SenC migration wave (in a SenC session after its current wave closes; live tree)

Judgment-based; dispatched per sub-step with dispatch-brief, file ownership declared.
**Files (SenC repo):** Create `docs/docsys.json`, `docs/REGISTER.md`, `docs/archive/`, `docs/log/`, `docs/items/`, `.claude/rules/docs.md` (path-scoped, `paths: docs/**`, points at the convention); Modify `docs/NEXT_TASKS.md` (becomes a pointer stub or is retired — owner rule in DECISIONS), `PROJECT_STATE.md`, `scripts/135_gates.sh` (call `docsys.py check --baseline docs/docsys-baseline.json`), `CLAUDE.md` (register pointer, owner-approved via DECISION-035).
- [ ] **7a register:** move the A-sexvicies table to `docs/REGISTER.md` with columns `| ID | State | Item | Evidence | Trigger | Owner |`. State per row is assigned by an implementer from the existing last-column word and the row text; rows it cannot type stay `UNKNOWN` and are listed for the controller. Every row over 600 chars: full old cell verbatim → `docs/items/<id>.md`; the row gets a ≤ 600-char current-state line. A domain-reviewer checks 20 random shortened rows against their item files (no claim changed, hedges kept). Then `archive --write`.
- [ ] **7b journal:** `rotate --write` moves the dated `## A-*` sections of NEXT_TASKS to `docs/log/2026-10.md` / `2026-11.md`; undated sections listed and placed by the controller.
- [ ] **7c PROJECT_STATE:** rewrite as an index ≤ 8,000 chars (aim, phase/wave, next step, pointers, PI decisions open); overflow text verbatim to `docs/log/<month>.md`. No generated counts block in the pilot: `186_decisions_index.py` hard-codes DECISIONS.md and one marker pair, so a block would be a refactor (inventory); `docsys measure` prints the counts on demand. Revisit at Task 8.
- [ ] **7d gate:** write `docs/docsys-baseline.json` from `check --write-baseline` AFTER 7a-7c, wire 135_gates.sh; seen RED once by adding a 601-char test row in a scratch copy.
- [ ] **7e:** SenC DECISIONS entry (what, why, alternatives, reference: PROPOSAL.md, revisit trigger: Task 8 numbers).

### Task 8: after-arm and rollout decision

- [ ] **Step 1:** after the next 4 SenC waves (the 2026-11-18 plan's S4 arms): `measure` → `after.json`; rows touched per wave; the frozen 10 questions answered from the new files → `read-test-after.md`.
- [ ] **Rollout constraints found by the inventory:** MeMES `scripts/70_summary.py:_register_entries` counts PARTLY CLOSED as closed while `38`/`39` exclude it, and `archive` would make archived R-ids look dead to `38` and change `register.rows` in `--check-docs` — the MeMES rollout updates those three scripts first. EF status lives in the ID cell (trailing `*`, bold FIXED/RESOLVED): EF uses `build_open_tasks.py:parse_w9` as its parser, configured in `docsys.json` as `"parser": "ef_w9"`, not `status_re`.
- [ ] **Step 2:** report before vs after with n per metric to the owner via AskUserQuestion: roll out to EnzymeFinder (needs its `--verify-live` row-prefix rule respected: IDs stay bolded) and MeMES, adjust caps, or stop. No preset threshold (owner ruling 2026-11-18 carries over).
