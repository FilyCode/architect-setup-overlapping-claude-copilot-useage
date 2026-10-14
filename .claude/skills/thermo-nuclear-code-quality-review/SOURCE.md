Vendored verbatim from https://github.com/cursor/plugins (thermos/skills/thermo-nuclear-code-quality-review) at commit 1e5c90a4b6f249917bd21fe361b3a2a7deb741b8 on 2026-10-14. MIT, see LICENSE. Do not edit here; local adaptations go in the lean-critic agent.

One local change (2026-10-14, plan Task 18): removed `disable-model-invocation: true` from SKILL.md,
because a flagged skill cannot be preloaded into the lean-critic seat and was silently skipped
(agent-seat-review F1). Re-apply this when updating from upstream.
