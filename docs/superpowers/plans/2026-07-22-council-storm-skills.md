# Council + STORM Skills Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build two new Claude Code skills — `council` (fast multi-persona decision stress-test) and `storm` (deep multi-perspective cited research) — in the shared config repo, and validate each with one real dry run.

**Architecture:** Both are pure prompt-engineering skills (a `SKILL.md` file each, no supporting code) living in `architect-setup-overlapping-claude-copilot-useage/.claude/skills/`, same tier as the existing `caveman`/`rtk`/`ccusage`/`planning-with-files` skills. No plugin marketplace involved — these are hand-authored, not adopted from a third party (see spec for why: the closest existing repos were either too small/unproven or had non-swappable personas).

**Tech Stack:** Markdown (`SKILL.md` frontmatter + instructions), no code, no dependencies.

## Global Constraints

- Both skills are **explicit-invocation only** — must not self-trigger on routine questions or decisions. This must be stated plainly in each skill's `description` frontmatter field, since that field is what the model uses to decide whether to fire.
- Full-length output (Council verdict, STORM report) is written **to a file only**. Chat gets a short summary + file path — never the full content duplicated in chat (this was an explicit design decision to avoid ~2x token cost of generating the same long content twice).
- Council roster: **Critic + Chairman fixed**, 2-5 dynamic personas generated per decision, 4-7 total. Chairman never debates, only synthesizes.
- STORM roster: **fixed 6** (Practitioner, Academic, Skeptic, Economist, Historian, Fund Giver/Politician), plus an optional 7th custom persona per call.
- Council output path: `docs/council/<topic-slug>-<date>.md` in the **active project** (not the shared repo).
- STORM output path: `docs/research/<topic-slug>-<date>.md` in the **active project** (not the shared repo).
- No unit tests are possible (these are instruction files, not code) — validation is a real dry run checked against the shape defined in the spec (`docs/superpowers/specs/2026-07-22-council-storm-skills-design.md`), not automated assertions.

---

### Task 1: Council skill

**Files:**
- Create: `architect-setup-overlapping-claude-copilot-useage/.claude/skills/council/SKILL.md`

**Interfaces:**
- Produces: a skill triggered by explicit user invocation (e.g. "run this through council"). Writes output to `docs/council/<topic-slug>-<date>.md` in whatever project is active at invocation time. No other task depends on this file's internals.

- [ ] **Step 1: Write the skill file**

```markdown
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
```

- [ ] **Step 2: Verify the file was written correctly**

Run: `cat architect-setup-overlapping-claude-copilot-useage/.claude/skills/council/SKILL.md | head -5`
Expected: shows the `---`/`name: council`/`description:`/`---` frontmatter block, confirming valid SKILL.md structure.

- [ ] **Step 3: Dry-run validation on a real decision**

Invoke the skill (new Claude Code session, since skills are discovered at session start) with this real, currently-undecided question from the workspace: *"Should we adopt K-Dense-AI/scientific-agent-skills (31k★, 148 skills) now, or keep deferring it?"*

Check the output against the spec:
- At least 2 dynamic personas were generated (not manufactured to hit a count) — if the topic didn't support 2, the skill should have said so and answered directly instead. Confirm which happened.
- `docs/council/` was created under `/projectnb/liu-scc/philipp/` (the active project for this workspace-tooling decision) if it didn't exist.
- A file matching `docs/council/*k-dense*-2026-07-*.md` (exact slug may vary) exists and contains all of Steps 1-6 (framing, positions, peer review, chairman synthesis) — not just a summary.
- The chat response was short: headline, confidence, 2-3 bullets, file path — and did **not** repeat the full report.

Expected: file exists with full content, chat response is short. If chat repeated the full report, fix Step 7 of the skill instructions and re-run.

- [ ] **Step 4: Commit**

```bash
cd architect-setup-overlapping-claude-copilot-useage
git add .claude/skills/council/SKILL.md
git commit -m "Add council skill: multi-persona decision stress-test"
```

---

### Task 2: STORM skill

**Files:**
- Create: `architect-setup-overlapping-claude-copilot-useage/.claude/skills/storm/SKILL.md`

**Interfaces:**
- Produces: a skill triggered by explicit user invocation (e.g. "do a STORM pass on X"). Writes output to `docs/research/<topic-slug>-<date>.md` in whatever project is active at invocation time. Independent of Task 1 — no shared state.

- [ ] **Step 1: Write the skill file**

```markdown
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
- **Critical Evidence:** the concrete data/examples backing this view (cite what the search actually returned, don't invent).
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
```

- [ ] **Step 2: Verify the file was written correctly**

Run: `cat architect-setup-overlapping-claude-copilot-useage/.claude/skills/storm/SKILL.md | head -5`
Expected: shows the `---`/`name: storm`/`description:`/`---` frontmatter block, confirming valid SKILL.md structure.

- [ ] **Step 3: Dry-run validation on a real topic**

Invoke the skill (new Claude Code session) with this real topic the K4-K26 project actually needs a funding-case answer for: *"Why does phosphonotripeptide (K4-K26) natural product BGC discovery matter to the general public and funders?"*

Check the output against the spec:
- All 6 fixed personas ran (no 7th unless one was explicitly requested).
- Each persona's Phase 1 entry has Core Lens / Critical Evidence / Unique Insight, with evidence traceable to an actual search result (not fabricated) — or an explicit "thin evidence" note if a persona's searches came up sparse.
- Phase 2 has all three sections: Direct Contradictions, Unified Consensus, Blind Spots.
- `docs/research/` was created under `/projectnb/liu-scc/philipp/projects/K4-K26/` if it didn't exist.
- A file matching `docs/research/*phosphonotripeptide*-2026-07-*.md` (exact slug may vary) exists with the full report.
- The chat response was short: topic, personas used, 3-line summary, file path — and did **not** repeat the full report.

Expected: file exists with full content, chat response is short. If chat repeated the full report, fix Step 4 of the skill instructions and re-run.

- [ ] **Step 4: Commit**

```bash
cd architect-setup-overlapping-claude-copilot-useage
git add .claude/skills/storm/SKILL.md
git commit -m "Add storm skill: 6-persona cited research with funder angle"
```

---

## Self-Review

**Spec coverage:** Council (roster, orchestration flow, edge case, output rule) — Task 1. STORM (roster, orchestration flow, edge case, output rule) — Task 2. Shared file-only-output rule — stated in Global Constraints and both skill files' Step 7/4. Location decision (shared repo, not plugin) — reflected in file paths. "Out of scope" items from the spec (persona-customization API, UI/dashboard, learnings.md integration) — correctly have no task, since they're explicitly not being built.

**Placeholder scan:** no TBD/TODO; both skill files are complete, copy-pasteable content, not summaries of what they should contain.

**Type consistency:** N/A (no code, no function signatures) — checked instead for consistent terminology across both files and the spec: "Critic"/"Chairman" (Council) and the exact 6 persona names (STORM) match the spec verbatim in both skill files.
