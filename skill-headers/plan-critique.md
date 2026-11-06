---
name: plan-critique
description: Reviews an architectural plan before Task 1 — Calibration block and its hard gate, plan preflight that executes the plan's claims, critique-wave sizing, three-state check, and the escalation wave after repeated failed fixes. Use before starting an approved plan, when asked for /plan-critique, or after a third failed fix. Not for review of finished work (wave-review).
effort: high
---

# Plan critique

Order: Calibration block present and self-fact-checked → **retirement check** (below) → preflight
(run the plan's code blocks
and resolve every path, symbol and figure it cites; EnzymeFinder has
`projects/EnzymeFinder/scripts/check_citations.py` for citations) → inventory-auditor → critique
wave (minimum 3 seats, batched under the concurrency cap; lean-critic, always, is one of
them: which tasks, files and abstractions the plan can drop or reuse) → pragmatism-officer → fix the plan
before Task 1. Ask of every new check: what is its third state, and how does it say so?

Exit: every "run X before/at T" in the critique's required changes is copied into the plan as a numbered task row before the plan is marked ready; the controller greps the critique for it.
Calibration: a plan whose acceptance is a count of self-agreement names one independent check (a different tool, or hand-picked cases) in the task row.
A forced-failure (or other negative-path) acceptance gets a miniature reachability run (stub chain, seconds) as a task row before the real run.
A sequential multi-step mutation (rename, swap, ledger) lists the state after each step's failure and the test covering it.

**Retirement check (R-20261103-1, owner-approved 2026-11-03). One grep, and it blocks Task 1.**
For every set the plan proposes to analyse, `command grep` the project's `DECISIONS.md` and
`FINDINGS.md` for that set's **defining marker and its cut value**, together with
`withdrawn|retired|sister`. Paste the hits into the Calibration block. **Any hit blocks Task 1**
until the plan says why the set is still worth measuring.

Why it exists: on 2026-11-03 a MeMES_OvoA_search wave spent **6 of its 11 commits** measuring a
93-protein stratum that `D-014` had retired on 2026-10-22 as a sister family — 51 of the 93 carried
the marker (Trm112/PF03966) that put it outside the target family, and the decision sat at
`DECISIONS.md:115` the whole time. A five-seat plan-critique ran before Task 1 and **none of its
five findings files mentions D-014**: the seats reviewed how the plan measured, never whether the
thing being measured had already been set aside. Preflight executes a plan's claims; it does not
ask whether the question was already answered. This is that question, and it costs one command.

Note the companion failure, which this check does not cover: that plan pre-registered its headline
sentence and also permitted superseding it "with reason", and the controller did exactly that and
published the wrong conclusion through eleven green gates. **A pre-registration with a
write-a-paragraph escape hatch is not a constraint.** If a plan pre-registers a sentence, state
what evidence — not what reasoning — may overturn it.

**Correction (2026-10-28, owner-approved):** the Calibration section below says "~35% identity really is the
field-wide ceiling for reliable annotation transfer (Zallot 2019)". That is wrong as stated. ~35% is EFI-EST's SSN
edge-drawing threshold; Zallot 2019 states the transfer sentence without a citation of its own, and the same paper's
worked example needs ~58% identity to separate isofunctional clusters. Do not quote it as a field-wide transfer
limit; cite a project's own low-identity measurements instead. Source:
`projects/EnzymeFinder/docs/superpowers/specs/2026-09-06-instrument-not-readout-design.md:271-290`. The MA-104
half of that sentence (a fixable 37.5% edge loss of ours) stands, and is still the point of the Calibration block.

The rules below are the original workspace text, moved verbatim.
