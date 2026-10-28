---
name: plan-critique
description: Reviews an architectural plan before Task 1 — Calibration block and its hard gate, plan preflight that executes the plan's claims, critique-wave sizing, three-state check, and the escalation wave after repeated failed fixes. Use before starting an approved plan, when asked for /plan-critique, or after a third failed fix. Not for review of finished work (wave-review).
effort: high
---

# Plan critique

Order: Calibration block present and self-fact-checked → preflight (run the plan's code blocks
and resolve every path, symbol and figure it cites; EnzymeFinder has
`projects/EnzymeFinder/scripts/check_citations.py` for citations) → inventory-auditor → critique
wave (minimum 3 seats, batched under the concurrency cap; lean-critic, always, is one of
them: which tasks, files and abstractions the plan can drop or reuse) → pragmatism-officer → fix the plan
before Task 1. Ask of every new check: what is its third state, and how does it say so?

**Correction (2026-10-28, owner-approved):** the Calibration section below says "~35% identity really is the
field-wide ceiling for reliable annotation transfer (Zallot 2019)". That is wrong as stated. ~35% is EFI-EST's SSN
edge-drawing threshold; Zallot 2019 states the transfer sentence without a citation of its own, and the same paper's
worked example needs ~58% identity to separate isofunctional clusters. Do not quote it as a field-wide transfer
limit; cite a project's own low-identity measurements instead. Source:
`projects/EnzymeFinder/docs/superpowers/specs/2026-09-06-instrument-not-readout-design.md:271-290`. The MA-104
half of that sentence (a fixable 37.5% edge loss of ours) stands, and is still the point of the Calibration block.

The rules below are the original workspace text, moved verbatim.
