# Phase0 P7: review seat yield (started 2026-10-14)

Scripts: /scratch/8090063.1.y/claude-768026/p7/{dedup.py,yield.py,uniq.py} (output res.json). Run 2026-10-14.

## Scope actually found
- Sources searched: architect-setup .../docs/superpowers/reviews/, projects/*/docs/superpowers/reviews/, projects/*/.superpowers/ (command find). 11,184 files, of which 669 .md; after dropping non-review docs and de-duplicating by md5 (the Bile_acid_database scratch_task10 holds 12 mirror copies of the same audit), 64 distinct files, 49 of them seat-attributable. ALL seat findings files are in ONE project, Bile_acid_database (.superpowers/sdd, 3 waves: 2026-09-24 census plan incl. audit_wave/ + review/ + harvest-audit mirror, 2026-10-09 wave B, 2026-10-11 wave C). MqnE has 4 retrospective review files (no seat names, not parsed). EnzymeFinder, SenC-SelD, EanB, CaMES, K4-K26 have no seat findings files in these paths.
- The 4 files in 2026-10-14-restructure/ are this restructure's own seat outputs and were excluded.

## Patterns used (validated by eye on 3 files)
Finding = markdown heading `^#{2,4} [SEV] [Finding] <ID>` where ID = `F1`, `D-1`, `C3`, `E1`, `D-W1-1`, `I-4`, `PD2`, `P1`. Severity = BLOCKING/IMPORTANT/MINOR/CRITICAL(->Blocking) in the heading, else "unrated" (informational, "no defect", UNPROBED). Headings containing "addendum" skipped; ids deduped within file.
Validation: critic-findings.md (review/) parsed 4 = F1..F4 (headings at lines 5,11,31,34; "Observation" and "Verified OK" correctly skipped); domain-findings.md (audit_wave/) parsed 7 = F1..F7; wave-B critique-domain.md parsed 13 = D-1..D-13 (18 `## ` headings, rest are answers/objection/minor-block). Misses: files with bullet-style or table-style findings parse 0 (see UNCLASSIFIED).
The user-specified patterns (`### F`, `- **F<n>`) matched nothing; the real format is `## F<n>`.

## Acted-on: what could and could not be measured
No FIXES.md / ROW_ASSIGNMENTS.tsv exists for Bile_acid_database (those are EnzymeFinder files, outside the findings sources). The only per-finding disposition record is the pragmatism-officer triage tables (5 files, 97 table rows mapped to finding ids, 37 rows unmappable). "acted-on" below = triage verdict is FIX NOW / FOLD / FN / FIX IN <pass> / ALREADY FIXED. This is a TRIAGE DECISION BY ANOTHER SEAT, not verified-fixed, and it is circular (pragmatism-officer's judgement scores the other seats). Commit-hash-next-to-id in progress.md/DECISIONS.md: only 5 seat-qualified mentions found, not usable.

## Table
| seat | review dirs (n) | findings (n) | Blocking | Important | Minor | unrated | triaged (n) | acted-on per triage verdict (n, % of triaged) | defer | reject | unique |
|---|---|---|---|---|---|---|---|---|---|---|---|
| critic-reviewer | 6 | 67 | 8 | 45 | 6 | 8 | 32 | 31 (97% of 32) | 0 | 1 | not measured |
| domain-reviewer | 6 | 65 | 15 | 42 | 2 | 6 | 22 | 20 (91% of 22) | 1 | 0 | not measured |
| anomaly-hunter | 3 | 18 | 5 | 12 | 1 | 0 | 12 | 12 (100% of 12) | 0 | 0 | not measured |
| alignment-officer | 1 | 0 parsed | - | - | - | - | 0 | not measured | - | - | not measured |
| docs-sync | 1 | 8 | 1 | 5 | 2 | 0 | 0 | not measured (n=0 triaged; the review/pragmatism-triage has no docs-sync row) | - | - | not measured |
| inventory-auditor | 5 | 7 | 1 | 0 | 2 | 4 | 4 | 0 (0% of 4) | 1 | 3 | not measured |
| pragmatism-officer | 5 | n/a (files verdicts, not findings; 134 table rows: 97 mapped, 37 not) | - | - | - | - | - | - | - | - | n/a |
| figure-auditor | 0 | no file found | | | | | | | | | |
| security-specialist | 0 | no file found | | | | | | | | | |
| research-scout | 0 | 1 prior-art survey (research_prior_art.md), no finding structure | | | | | | | | | |
| scc-monitor | 0 | no file found | | | | | | | | | |
| ad hoc/general-purpose | 4 | 32 | 9 | 18 | 5 | 0 | 27 | 24 (89% of 27) | 3 | 0 | not measured |

Counts are per distinct finding id per de-duplicated file (n=49 attributed files). Review-dir = containing directory (wave-B, wave-C, audit_wave, review, harvest-audit, scratch_task*). Seat attribution is by filename/header: critique-integrity (waves B,C) = anomaly-hunter per its own header; plan_critique_integrity/identity, external-findings, review_findings = ad hoc (header names no agent; "persona" seats); amendment_critique, plan_critique_feasibility = critic-reviewer per header.

## Unique
Not measured. Attempted: findings whose cited path:line also appears in another seat's file in the same wave. Only a subset is citable and it is the wrong subset: critic 47/60 citable (41 unique), domain 12/56 (6), anomaly 6/18 (2), docs-sync 5/8 (4), inventory 4/7... Domain and anomaly findings are about data rows, not code lines, so "no one cites this line" says nothing about whether another seat found the same defect. Reporting a number would be a guess.

## Could NOT classify
- alignment-findings.md: task-by-task delivery table, no finding ids (0 parsed). inventory.md (wave B 2 unrated, wave C 0), plan_inventory.md, scratch_ctrl/inventory_findings.md: prose sections, not ids.
- scratch_ctrl/adjudication_findings.md (domain seat), scratch_task9 rereview1/review_code_findings, scratch_task9b rev/findings.md: bullet/prose format, 0 parsed.
- research_prior_art.md (29 headings, all unrated; no seat named in header, may be research-scout or a general agent).
- controller_findings.md (9 findings) is the controller, not a seat; project findings.md/owner_decisions/parked_items are not reviews.
- 37 triage rows (objections, parked items, "PC1..PC9", W4 items, wave-B plan-triage bullets that name plan tasks B1..B6 not finding ids) could not be tied to a finding id; wave-B has no mappable triage at all, so its 30 findings are untriaged.
- Triage coverage is uneven: 134 triage-bearing rows cover audit_wave and review/ and wave-C but not wave-B, harvest critic/domain audit findings, or scratch task reviews; percentages are over the triaged subset only.
- Verdict classing is by regex on the verdict cell (act/defer/reject/other); 1 domain verdict fell in "other".
- figure-auditor, security-specialist, scc-monitor: zero invocations recorded in any searched file (grep of the 669 .md for the names: 0, 0, 0). Absence of files is not evidence they were never run, only that they left nothing in these paths.

## Strongest objection to using this table to decide which seats to keep
This is one database project, three waves, and the acted-on column is another seat's triage verdict, so it measures agreement with pragmatism-officer, not defect removal. It also cannot see a seat's value as a negative control: anomaly-hunter and domain-reviewer findings are about data and premises (and show the highest Blocking rates, 5/18 and 15/65 vs 8/67 for critic), but their effect shows up in changed headline numbers, not in a "fixed" mark. Seats with zero rows (security, figure, scc-monitor) are gate-type seats run rarely, so n=0 reflects dispatch frequency, not yield. No seat has a denominator of defects that escaped, so yield per seat cannot be compared to cost or to what the others would have caught anyway.

## Wrong or off in the prompt
- Heading pattern `### F`/`- **F<n>` is not the format used; real is `## F<n> SEVERITY`.
- Named ledgers FIXES.md / ROW_ASSIGNMENTS.tsv live only in EnzymeFinder (phases/ROW_ASSIGNMENTS.tsv), outside the listed findings sources, and EnzymeFinder has no seat findings files there, so they could not be joined.
- `/projectnb/.../projects/*/.superpowers/` holds ~11k files, mostly release data; a plain find+grep pipeline over it exceeds 2 minutes, so file lists were taken with find then filtered.
- The restructure review dir already contained other seats' files when I started; left untouched.
