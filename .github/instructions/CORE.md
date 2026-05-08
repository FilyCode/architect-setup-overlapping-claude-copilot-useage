# CORE.md — Shared rules for all tools (Copilot and Claude Code)

## Response Format

IMPORTANT: Lead with the answer. Context and rationale follow, not precede.
IMPORTANT: No preamble, filler affirmations, or trailing summaries of work just done.

- Use prose when content is continuous reasoning. Use a list only when items are genuinely parallel and enumerable.
- When the request is ambiguous, state the assumption made and proceed. Do not stop to ask.
- Distinguish facts from inferences: "X is Y" (known) vs. "X appears to be Y" (inferred) vs. "unclear whether X" (genuine uncertainty).
- Short factual queries: 1–3 sentences. Technical tasks: working output first, explanation after if needed.

## Conduct

- Cite file paths when referencing project state or making decisions.

IMPORTANT: Do NOT edit governance files (ARCHITECTURE.md, DECISIONS.md, CLAUDE.md, AGENTS.md) without explicit user approval.

- English only in all files, comments, and responses.
- Track token usage and warn when approaching practical limits.

## Token Efficiency

- Load only files required for the current step.
- Keep always-on instruction files short; link to detail docs rather than embedding them.
