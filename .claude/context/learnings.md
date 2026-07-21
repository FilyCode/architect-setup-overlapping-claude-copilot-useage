# Learnings Log

Cross-project patterns promoted here once proven — not a dumping ground for one-off mistakes. Promotion bar: the same pattern recurs 3+ times across 2+ distinct tasks/projects. Below that bar, a pattern stays in personal session memory; above it, it belongs here so every project (and any agent working from this repo) inherits the fix instead of re-learning it.

Each entry: what recurred, why it happened, how to apply the fix. Delete or rewrite entries that turn out wrong — this file is a working tool, not an audit trail.

## SCC login-node process reaper kills long-running commands silently

**Recurred:** lost full pytest runs on the login node multiple times before the pattern was written down (EnzymeFinder).

**Why:** the SCC login node kills any process over ~30s CPU with no error message — looks like the command just never finished.

**Fix:** never run `pytest` or any process >~15s directly on the login node; always route through `qsub`. Full procedure: `.claude/context/runbook.md`.
