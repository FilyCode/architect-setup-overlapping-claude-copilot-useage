---
name: wave-review
description: Runs the wave-end review in this workspace — which seats to dispatch for this kind of wave, in batches under the concurrency cap, with pragmatism triage last and a ran/not-ran list. Use at the end of a multi-task wave or when asked for /wave-review. For a quick ad hoc review of one change use superpowers requesting-code-review or /code-review instead. Seat briefs come from dispatch-brief.
effort: high
---

# Wave-end review

Roster by wave type: critic-reviewer always; alignment-officer and docs-sync when a plan or
phase doc exists; domain-reviewer for domain work; anomaly-hunter when the wave produced a new
measurement (skip on pure bug-fix or doc-only waves); inventory-auditor when the wave added
capability; lean-critic only on request; pragmatism-officer last, once findings exist; then
retro-officer, always, as the final step: give it the ledger path, the findings (files or
reports), the commit range per repo and the main transcript path
(`~/.claude/projects/<project>/<session id>.jsonl`). It appends one entry to
`docs/retros/retro-log.md` in the config repo.

Dispatch in batches under the concurrency cap (2 on the smaller account, 3 on the larger). A
spawn refused at the cap is not queued: re-dispatch it when a slot frees. The close lists every
seat as ran or not-ran, with the reason. Copy seat findings into the repo before the session
ends: the scratchpad is node-local and dies with the job. When the wave's evidence is only self-consistency, say
so in the close and keep a standing row for one held-out evaluation.

The rules below are the original workspace text, moved verbatim.
