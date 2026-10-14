---
name: completion-check
description: Finds unfinished or non-working code — stub scan, unused-code lint, import-graph reachability, and running the changed entry point on a real fixture. Use when asked whether work is finished or actually runs, or via /completion-check. Correctness review of logic is critic-reviewer's job.
---

# Completion check

Scripts live in this skill's directory (`scripts/`); run them, do not read them.

## Run, in this order
1. `python3 <skill dir>/scripts/stub_scan.py <changed files or package dir>` — every hit is either finished
   or reported as unfinished with a reason.
2. `ruff check --select F401,F811,F841,ARG <changed paths>` — unused imports, redefinitions,
   dead assignments and arguments. A dead variable can mean a feature that silently does nothing.
3. `python3 <skill dir>/scripts/reach.py --repo <repo root> --package <name>` (src layout; wraps EnzymeFinder's audit_reachability.py) — modules unreachable from any
   entry point. "It has tests" is not reachability.
4. Run the changed entry point on a real, downsampled input (never a hand-typed row) and check
   that the expected artifact exists and is non-empty. Inside an SGE job only, for anything
   heavier than a few seconds.
5. Silent failures: for every `except` in the diff, does the caller learn that it failed?
   A fallback that returns an empty result must be distinguishable from a genuine empty result.

## Report
List each check, the command, and its result. "Finished" requires all five; otherwise say
which check failed and what is unfinished.
