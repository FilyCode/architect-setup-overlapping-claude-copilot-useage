# Cache Performance Analysis

When asked about cache hit rate, cache metrics, TTL analysis, or cold vs warm latency:
Apply the workflow from `projects/EnzymeFinder/.claude/skills/analyzing-cache-performance/SKILL.md`.

Trigger phrases: "cache performance", "hit rate", "cache metrics", "ttl analysis", "cold vs warm", "cache analysis"

Key rules:
- Metrics file: `projects/EnzymeFinder/outputs/metrics.log` (JSONL format).
- hit_rate < 30% → TTL expired or cache key changed.
- hit_rate > 80% → consider shorter TTL for UniProt freshness.
- P4-MVP target speedup: ≥ 1.5× cold vs warm.
- If hit_rate < 50% after Tier-2 warm run → escalate to Architect.
