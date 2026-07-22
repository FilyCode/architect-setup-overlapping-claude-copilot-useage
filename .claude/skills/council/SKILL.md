---
name: council
description: Multi-persona decision stress-test — Critic + Chairman (fixed) plus 2-5 dynamic personas debate a decision, peer-review each other anonymously, and get synthesized into a verdict. Use only on explicit invocation ("run this through council", "get a council verdict on X") for genuinely multi-angle decisions — not for routine questions. Full report goes to docs/council/<topic-slug>-<date>.md in the active project; chat gets a short summary only.
---

# Council

Explicit-invocation only. Don't self-trigger on ordinary questions — this is a multi-round, multi-persona process meant for decisions with genuine competing angles (architecture choices, project-direction calls, high-stakes tradeoffs).

## Step 1: Frame the question

State the actual decision, the stakes, and known constraints in 2-4 sentences. This framing is shown to every persona so they argue from the same starting point.

## Step 2: Check the decision actually supports a council

Identify 2-5 genuinely distinct angles this decision turns on (not generic categories — angles specific to this decision). If you can't find at least 2 distinct angles, stop here: say so, and answer the question directly instead of manufacturing personas to hit a roster size.

## Step 3: Generate the roster

- **Critic** (fixed) — stress-tests for failure modes, hidden risks, edge cases.
- **Chairman** (fixed) — does not debate; synthesizes only, in Step 6.
- **2-5 dynamic personas** — named for the angles identified in Step 2 (e.g., for a code-architecture decision: Security, Maintainability, Performance; for a project-direction call: Cost, Risk, Stakeholder-Impact).

## Step 4: Parallel positions

For Critic + each dynamic persona (not Chairman), write an independent position: Position / Evidence / Risk, ~150-250 words. Each persona argues only its own angle — don't let one persona pre-empt another's point.

## Step 5: Anonymous peer review

Without attribution, have each position critiqued by the others: what does it miss, where is the reasoning weak, what blind spot does it have. This step exists so personas don't just defend their own prior statement — critique the position, not the (unnamed) author.

## Step 6: Chairman synthesis

The Chairman (not one of the debating personas) weighs every position plus the peer-review critiques and produces the verdict:
- **Confidence:** high / medium / low, with one line why.
- **Direct contradictions:** where personas' positions actively conflict, not just differ in emphasis.
- **Consensus:** what every persona agrees on despite different angles.
- **What you lose:** the real cost of taking the recommendation.
- **Next step:** one concrete action.

## Step 7: Write the output

1. Create `docs/council/` in the active project if it doesn't exist.
2. Write the full verdict (all of Steps 1-6, not just the Chairman's summary) to `docs/council/<topic-slug>-<date>.md` — slug the question to kebab-case, date as YYYY-MM-DD.
3. In chat, reply with **only**: the verdict headline, confidence level, 2-3 key bullets from the synthesis, and the file path. Do not repeat the full report in chat — the file already has it, and duplicating a long report in both places costs roughly double the tokens for identical content.
