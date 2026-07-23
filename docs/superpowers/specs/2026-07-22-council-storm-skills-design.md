# Council + STORM skills — design

Two new Claude Code skills for the shared workspace: `council` (fast multi-persona decision stress-test) and `storm` (deep multi-perspective research with citations). Built from scratch rather than adopted — checked real repos first (`ngmeyer/council-review`, 15★, fixed non-swappable personas; `kunjan-p/storm-skill`, `sageraii/storm-research-skill`, `hadufer/claude-storm`, all 0-4★, unproven). Neither fit closely enough to depend on; `ngmeyer/council-review`'s peer-review/chairman-synthesis orchestration pattern is reused as a reference, not a dependency.

Both are explicit-invocation only — neither should auto-fire on ordinary questions or decisions. They are multi-round, multi-search skills; casual auto-triggering would be expensive and unwanted (this was an explicit design constraint from the start: "not use them all the time").

## Location

Both skills live in the shared config repo, git-tracked, workspace-wide:
- `architect-setup-overlapping-claude-copilot-useage/.claude/skills/council/SKILL.md`
- `architect-setup-overlapping-claude-copilot-useage/.claude/skills/storm/SKILL.md`

Same tier as `caveman`, `rtk`, `ccusage`, `planning-with-files` — custom-built, not plugin-marketplace-installed (no marketplace exists for either).

## Council

**Trigger:** explicit only — e.g. "run this through council," "get a council verdict on X." Not for routine questions.

**Roster:** 4-7 personas total.
- **Critic** (fixed) — stress-tests for failure modes, hidden risks, edge cases.
- **Chairman** (fixed) — does not debate; only synthesizes the final verdict from the other personas' output plus peer review.
- **2-5 dynamic personas** — generated per decision, named for relevance to the actual question (e.g. Security/Maintainability/Timeline for a code architecture call; Cost/Risk/Stakeholder-Impact for a project-direction call).

**Orchestration flow:**
1. Frame the question neutrally — state the actual decision, stakes, and known constraints.
2. Generate 2-5 dynamic personas relevant to this specific decision (plus fixed Critic).
3. Parallel round: every persona (Critic + dynamic) states a position independently — Position / Evidence / Risk, ~150-250 words each.
4. Anonymous peer review: each persona's position is critiqued by the others without attribution — surfaces blind spots and weak reasoning without personas simply defending their own prior statement.
5. Chairman synthesis: weighs all positions and peer-review feedback, produces the verdict — confidence level, direct contradictions between personas, points of consensus, "what you lose" if the recommendation is taken, and a concrete next step.

**Edge case:** if the question doesn't support at least 2 genuinely distinct dynamic personas (i.e., it's not actually a multi-angle decision), the skill says so and answers directly instead of manufacturing personas to hit a roster size.

**Output:** full verdict written to `docs/council/<topic-slug>-<date>.md` in the **active project** (decisions are project-specific, not shared-repo-wide). Chat response is a short pointer only: verdict headline, confidence, 2-3 key bullets, file path — not the full report duplicated in chat (avoids ~2x token cost of generating the same content twice).

## STORM

**Trigger:** explicit only — e.g. "do a STORM pass on X," "run STORM research on this topic."

**Roster:** fixed 6, proven in the 2026-07-22 selenocysteine-synthesis dry run:
1. Practitioner (operational/hands-on angle)
2. Academic (theoretical/mechanistic angle)
3. Skeptic (critical/failure-mode angle)
4. Economist (market/resource/ROI angle)
5. Historian (evolutionary/timeline angle)
6. Fund Giver / Politician (public-importance/funding-case angle)

Plus an **optional 7th custom persona** the caller can specify for a domain-specific angle not covered by the fixed 6.

**Orchestration flow:**
- **Phase 1 — independent analysis:** for each persona, run 2-3 targeted web searches grounded in that persona's lens; produce Core Lens / Critical Evidence / Unique Insight per persona.
- **Phase 2 — synthesis:** Direct Contradictions (where personas' conclusions actively conflict), Unified Consensus (what all personas agree on independently), Blind Spots (questions no persona addressed).

**Edge case:** sparse or obscure topics — note the evidence gap explicitly in Phase 2 blind spots rather than fabricating citations or evidence to fill a persona's slot.

**Output:** full report written to `docs/research/<topic-slug>-<date>.md` in the active project. Chat response: topic, personas used, 3-line executive summary, file path — same file-only-for-full-content rule as Council.

## Shared mechanics

- Both skills produce long-form output — the file-only-for-full-content / summary-in-chat rule applies to both, resolving the token-doubling concern raised during design (writing full content to both chat and a file costs roughly 2x, since the file-write tool call carries the full content as a parameter).
- Output directories (`docs/council/`, `docs/research/`) live per-project, created on first use if absent.
- Neither skill has unit tests in the conventional sense (prompt-engineering artifacts, not code). Validation = dry-run against a real topic/decision and manually check output quality against the shape defined here. `skill-creator`'s eval/benchmark mode (installed 2026-07-21 via the `example-skills` plugin) is available for more rigorous testing later if wanted, but is not required to consider these skills done.

## Out of scope (deliberately not building)

- Persona customization beyond the documented fixed+dynamic (Council) and fixed 6+1 (STORM) shapes — no general-purpose "arbitrary persona list" API.
- Any UI/dashboard for browsing past Council/STORM outputs — they're plain markdown files, discoverable via normal file search.
- Integration with the `.claude/context/learnings.md` promotion log — Council/STORM outputs are research/decision artifacts, not recurring-mistake patterns; no reason to route them through that mechanism.
