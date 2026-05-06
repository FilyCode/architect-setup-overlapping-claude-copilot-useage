# Token Efficiency

## Model Routing
- Low complexity (edits, summaries, lookups) → low-cost model
- Medium complexity (implementation, debugging, review) → balanced model
- High complexity (architecture, security, cross-file redesign) → high-capability model

Escalate when: context grows large, ambiguity is unresolved, task spans multiple coupled files, or architectural/security reasoning is needed.

## Context Hygiene
- Load only files required for the current step — prefer focused reads.
- Workspace state lives in `.github/` and root docs; project state in `projects/<project>/phases/`; session state in memory.
- Keep always-on instruction files short; link to detail docs rather than embedding them.
- Validate after meaningful edit groups, not after every micro-change.

## Response Style
- Keep responses concise; reuse context rather than restating it.
- Compress long outputs when the full detail is not needed.
- Batch related changes in one pass.
