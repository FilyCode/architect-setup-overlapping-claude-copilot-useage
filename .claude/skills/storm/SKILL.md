---
name: storm
description: Deep multi-perspective research — 6 fixed personas (Practitioner, Academic, Skeptic, Economist, Historian, Fund Giver/Politician) each run grounded web searches and produce Core Lens/Critical Evidence/Unique Insight, then get synthesized into contradictions/consensus/blind-spots. Use only on explicit invocation ("do a STORM pass on X", "run STORM research on this topic") for topics that need citation-grounded, many-angle research — not for quick lookups. Full report goes to docs/research/<topic-slug>-<date>.md in the active project; chat gets a short summary only.
---

# STORM

Explicit-invocation only. This is a multi-search, multi-persona research process — don't self-trigger on quick factual lookups or questions answerable from one search.

## Step 1: Confirm the topic and personas

State the topic in one sentence. Roster is the fixed 6 below, plus an optional 7th custom persona if the caller specified a domain-specific angle not covered by the fixed 6.

1. **Practitioner** — operational/hands-on angle: real-world execution, bottlenecks, workflows.
2. **Academic** — theoretical/mechanistic angle: foundational principles, structural frameworks.
3. **Skeptic** — critical angle: edge cases, failure modes, misconceptions.
4. **Economist** — market/resource angle: cost, ROI, resource allocation, incentives.
5. **Historian** — evolutionary angle: timeline, precedents, how the paradigm got here.
6. **Fund Giver / Politician** — public-importance angle: why this matters broadly, what problem it solves that's worth funding.
7. **(optional custom)** — only if the caller named a specific extra angle for this topic.

## Step 2: Phase 1 — independent analysis per persona

For each persona: run 2-3 web searches grounded in that persona's specific lens (not generic searches — phrase each query for that persona's angle, e.g. Skeptic searches for failure/misconception evidence, Economist searches for market/cost data). Produce, per persona:
- **Core Lens:** that persona's specific interpretation of the topic.
- **Critical Evidence:** the concrete data/examples backing this view (cite what the search actually returned, don't invent). Before citing a source for a specific quote or claim, confirm the claim actually appears in that specific source — not just that the source is real and topically related; a true fact attributed to the wrong URL is still a citation error.
- **Unique Insight:** a conclusion non-obvious from any other persona's angle.

If a persona's searches turn up thin (obscure/sparse topic), say so for that persona rather than padding with weak or fabricated evidence — this gap becomes a Phase 2 blind spot instead.

## Step 3: Phase 2 — synthesis

After all personas are done:
- **Direct Contradictions:** where two or more personas' conclusions actively conflict (not just differ in framing) — name which personas and why.
- **Unified Consensus:** what every persona's independent analysis agrees on despite the different angles.
- **Blind Spots:** questions no persona's analysis addressed, including any evidence gaps flagged in Step 2.

## Step 4: Write the output

1. Create `docs/research/` in the active project if it doesn't exist.
2. Write the full report (all personas' Phase 1 analysis + full Phase 2 synthesis) to `docs/research/<topic-slug>-<date>.md` — slug the topic to kebab-case, date as YYYY-MM-DD.
3. In chat, reply with **only**: the topic, which personas were used (noting the 7th if present), a 3-line executive summary, and the file path. Do not repeat the full report in chat.
