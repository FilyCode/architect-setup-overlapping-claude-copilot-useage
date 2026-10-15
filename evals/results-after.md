| scenario | pass | k |
|---|---|---|
| S1-qsub-owner | 2 | 5 |
| S2-findings-first | 2 | 5 |
| S3-third-state | 5 | 5 |
| S4-commit | 4 | 5 |
| S5-relayed-count | 4 | 5 |
| S6-absence | 5 | 5 |
| S7-batching | 2 | 5 |
| N1-small-edit | 5 | 5 |
| N2-small-done | 5 | 5 |
| S8-heavy-tests | 5 | 5 |

## What this eval does and does not show (wave-end review, 2026-10-14)

- It measures headless main sessions in plan mode (`--max-turns 8`), with `core.md` loaded and the
  superpowers SessionStart hook pushing skill use. It does not test seats, general-purpose
  subagents, sessions started inside a project (which do not load `core.md`), or implicit
  triggers. It is not evidence for retiring the old rule files; the retirement rests on the
  measured context cut (seat first call ≈ 50k → ≈ 12k tokens, n = 20 interactive seats) and the
  gap review in `docs/superpowers/reviews/2026-10-14-restructure/`.
- Relevant skill invoked in 5/5 after-arm runs of S1, S2, S5, S6, S7, S8 (0 Skill calls in the
  before arm). S3 and S4 pass from always-loaded `core.md`; the S4 gain is the new `core.md` rule 6,
  not a skills effect.
- Third state: runs that hit `--max-turns` (after: S1-2, S1-5, S5-1, all graded FAIL; before:
  S2-2 FAIL, S8-3 graded PASS). Without them: S1 2/3 vs 2/5, S5 4/4 vs 5/5.
- Grader limits: S4 after-arm run 2 is a correct answer graded FAIL (lowercase placeholder), so
  S4 is 5/5 in substance; S1 fails correct answers on wording; S2 fails on path length between
  "first action" and "findings" (substance 5/5 in both arms); S7's second check matches every run;
  S3's `must_not` names a field no run used; S8 is decided by plan mode. Arms also differ in tools,
  MCP connectors and plugins, so do not cite this eval's token delta.
