---
name: wave-review
description: Runs the wave-end review in this workspace — which seats to dispatch for this kind of wave, in batches under the concurrency cap, with pragmatism triage last and a ran/not-ran list. Use at the end of a multi-task wave or when asked for /wave-review. For a quick ad hoc review of one change use superpowers requesting-code-review or /code-review instead. Seat briefs come from dispatch-brief.
effort: high
---

# Wave-end review

Roster by wave type: critic-reviewer always; alignment-officer and docs-sync when a plan or
phase doc exists; domain-reviewer for domain work; anomaly-hunter when the wave produced a new
measurement (skip on pure bug-fix or doc-only waves); inventory-auditor when the wave added
capability; lean-critic, always, on the wave's diff (it preloads ponytail); pragmatism-officer last, once findings exist; then
retro-officer, always, as the final step: give it the ledger path, the findings (files or
reports), the commit range per repo and the main transcript path
(`~/.claude/projects/<project>/<session id>.jsonl`). It appends one entry to
`docs/retros/retro-log.md` in the config repo.

Dispatch in batches under the concurrency cap (2 on the smaller account, 3 on the larger),
science seats first (domain-reviewer, anomaly-hunter), then critic-reviewer and
alignment-officer, then docs-sync, inventory-auditor and lean-critic, so governance text is
drafted after the findings it must not contradict. The review is pinned to one commit (its HEAD is named in the close); commits after it, such as features the owner adds at review, get a short second critic pass before merge. A
spawn refused at the cap is not queued: re-dispatch it when a slot frees. The close lists every
seat as ran or not-ran, with the reason. Findings files go in the findings dir (`.superpowers/findings/<date>/` in the config repo,
persistent), never the scratchpad, which dies with the job. A seat is not "ran" until its
findings file has its closing section (`command grep -q '^## CLOSING' <file>`); if a seat put
findings only in its message, re-run it; only as a last resort write them into its file, marked controller-written, before closing. When the wave's evidence is only self-consistency, say
so in the close and keep a standing row for one held-out evaluation. A branch that is not merged,
or whose full suite could not run, carries the line "MERGE GATE: full suite on the merge commit,
job spec written" in its ledger and plan status, with the job spec's path; the wave is not marked
closed without that line. Nothing that says built, verified, merged, closed, answered or resolved
(status docs, findings, commit subjects) is written or pushed before the roster has run and the close
line exists, or it is marked DRAFT; "push at wave end" means after that line, and a /compact
keep-line says "push after review close" (R-20261030-1/-9: SenC and MeMES pushed claims hours before
the review, one headline later retracted). A post-refresh test failure recorded
in a handoff becomes a ledger item with an owner and the next refresh as its gate, never only a note.
A CI check that is red with no job log (minutes exhausted) is recorded as not run; the PR carries
the local equivalent's command and output.

**Aim check, after the retro.** Before any new wave or fix round, dispatch `aim-keeper` with the
project path, the wave's Goal line and commit range, and the next step on the table (say whether
the owner or Claude proposed it). Put its owner question to the owner with AskUserQuestion
(core rule 15) and record the answer in the ledger. The `aim_nudge` hook reminds at retro
dispatch and at the third fix round.

The rules below are the original workspace text, moved verbatim.
