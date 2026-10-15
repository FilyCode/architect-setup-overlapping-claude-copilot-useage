# Project setup audit, 2026-10-14

Two read-only investigator seats audited every project's Claude Code setup against the
restructured workspace (core.md + skills; project CLAUDE.md holds durable project facts only).
Their findings files stayed empty (the reports came back as messages), so this file records the
reports' findings and what was done with each. Owner approved groups 1-3 the same day.

## graphify beyond EnzymeFinder: declined

Measured, non-test Python files importing another file of the same project:
EnzymeFinder 207 of 354 (841 import lines); SenC-SelD-GNcheck 89 of 168; EanB 57 of 98 (100
edges); Bile_acid_database 30 of 65; CaMES 31 of 107; MqnE 18 of 56; K4-K26 15 of 69. With at
most ~100 edges, grep answers "who uses X"; a graph adds hooks and hub noise.

## Findings and dispositions

| Project | Finding (evidence) | Done |
|---|---|---|
| EnzymeFinder | AGENTS.md stale Copilot file (dead link, 5,800-test baseline) | archived to docs/history, deleted |
| EnzymeFinder | running-ef-tests: baseline "476 passing", runs pytest directly | points at run_pytest_qsub.sh and PROJECT_STATE |
| EnzymeFinder | submitting-scc-jobs duplicates running-sge-jobs | retired, archived |
| EnzymeFinder | phase-era skills auto-invocable | owner: manual-only (3 skills) |
| EnzymeFinder | .claude/CLAUDE.md has no verify commands | Verify section |
| EnzymeFinder | `make test` runs pytest on any node | prints the qsub command, exits 1 |
| EnzymeFinder | PROJECT_STATE.md 2,408 lines | 59; rest archived; census surface added, baseline kept at 94 |
| Bile_acid_database | two CLAUDE.md files overlap; rtk and Copilot pointers | merged into one, stale sections dropped |
| Bile_acid_database | 2,068 untracked logs; planning-with-files leftovers at root | `logs/*.log` ignored; files moved to docs/history |
| Bile_acid_database | no CI tests | owner: secret scan only for now; more checks later |
| SenC-SelD-GNcheck | no CLAUDE.md; STATUS.md stale; no PROJECT_STATE | CLAUDE.md, PROJECT_STATE.md (4 UNKNOWNs), STATUS superseded header, secret scan |
| TBI | no CLAUDE.md; settings backup | 16-line CLAUDE.md, secret scan, backup removed |
| GeroprotectorSigs-mapping | worktree of the shared montilab repo, no CLAUDE.md | local CLAUDE.local.md only (excluded), nothing committed |
| EanB_homologue_search | Copilot section + stale copilot-instructions.md; hook claim nothing backs | removed |
| EanB_homologue_search | MSA files 13-18 MB tracked; canonical CSVs gitignored | open: waits for the owner of the uncommitted .gitignore edit |
| K4-K26 | 99_full_pytest_qsub.sh cds into a nonexistent worktree | fixed to project root |
| K4-K26 | CLAUDE.md narration, incomplete pipeline table | 123→69; strains to docs/strains.md |
| MqnE_cofactor_finding | CLAUDE.md ~125 of 162 lines status narration | 40 lines, premise correction kept as a rule |
| MqnE_cofactor_finding | 32 tracked files >10 MB; PROJECT_STATE 469 lines | untracked (owner: AF3 outputs are rerunnable); state 53 lines |
| CaMES_homologue_search | PROJECT_STATE stale ("A6 in progress") | rewritten from qacct + commits; 5 UNKNOWNs |
| CaMES_homologue_search | .git 4.4 GB, interrupted pack; `Bash(find:*)` allow | gc → 86 MiB pack (unreachable objects); find/cd allows removed |
| CaMES_homologue_search | results/a6_detection_floor/ 310 MB untracked | owner: ignored |
| Sulfotrans | dormant; rtk pointer; duplicate .claude/CLAUDE.md | 17-line dormant CLAUDE.md; duplicate deleted |

## Objections the seats raised

- A file-quality audit measures instruction hygiene, not whether a line changes behaviour;
  deleted "narration" may have been guard text. Mitigation: removed text is archived verbatim,
  and guard conclusions (MqnE premise correction) were kept as one-line rules.
- Most drift (interpreter paths, SGE notes, tool lists) is workspace-level text repeated per
  project. The standard applied: project files hold project facts and point at skills.
