# Owner actions — setup restructure (2026-10-14)

Things only the owner can do (account-side, or blocked for the session). Each says why.

1. **Restore the three parked plugins** (uninstalled by mistake; `parked-extensions.md` records
   them as disabled-but-installed for instant re-enable; the auto-mode classifier blocked the
   session from doing it):
   ```
   ! for p in example-skills@anthropic-agent-skills research-skills@claude-code-skills planning-with-files@planning-with-files; do claude plugin install $p --scope user && claude plugin disable $p --scope user; done
   ```
2. **Account-synced writing plugins** (managed in the desktop app / claude.ai, not from here):
   - Disable `humanize-kit`. It targets AI-detector evasion, which conflicts with journals'
     AI-use disclosure policies, and it adds a SessionStart hook.
   - In `writing-skills`, keep `plain-language`, `orwells-rules`, `google-dev-docs`; disable the
     character voices (bob-ross, jack-sparrow, paddington, shrek, ted-lasso, winnie-the-pooh,
     yoda, scott-adams). Together the 17 descriptions cost ≈ 1k tokens in every session.
   - `bio-research`: keep only if the nf-core / scvi skills get used; its PubMed and bioRxiv
     connectors duplicate ones already connected.
   - Paper workflow: `science-writing-edit` (yours) → `humanizer` as a de-AI checklist pass →
     diff numbers and citations against the original before submitting.
3. **Q3 — `pr-review-toolkit`** costs ≈ 2,035 tokens per session (CLI estimate; six agent
   descriptions with long examples). `completion-check` now carries the silent-failure check
   (stub scan flags broad `except` that returns empty). Decide: keep the plugin for
   `/review-pr` and its specialist agents, or disable it.
4. **Q5 — connectors (Phase 0 P5, not run).** Main first-call context grew 78.5k → 100k in four
   weeks; most of the growth is claude.ai connector attachments (deferred tools 5.4 → 16.1 KB,
   MCP instructions 2.2 → 6.2 KB). To test whether they are sent twice: start one session with
   unused connectors disabled in claude.ai settings, then run
   `.venv/bin/python architect-setup-overlapping-claude-copilot-useage/tools/measure_context.py --since <today>`
   and compare the main first-call median. Disable connectors you do not use either way.
5. **Not ours, noticed in passing:** SGE job 8054899 (`roadseg_au`) has been in `Eqw` since
   2026-10-13.
