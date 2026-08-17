---
paths:
  - "projects/EnzymeFinder/**"
---

# Navigating the EnzymeFinder codebase

188 files, ~59,600 lines. Reading broadly to find something is the main avoidable token
cost in this project. Locate first, then read only what you located.

## Order of preference

1. **Know the symbol name** → use code intelligence (go-to-definition / find-references).
   Exact, always current, no rebuild.
2. **Know roughly what you want but not where** → `graphify query`. Returns `file:line`
   candidates from the knowledge graph.
3. **Know the file** → read it directly. Do not route a known path through the graph.

## Using graphify

```bash
cd /projectnb/liu-scc/philipp/projects/EnzymeFinder
/projectnb/liu-scc/philipp/.venv/bin/python -m graphify query "confidence tier assignment" --budget 800
/projectnb/liu-scc/philipp/.venv/bin/python -m graphify path "BlastAdapter" "HitRecord"
```

**Read the output as a candidate list, not as an answer.** BFS from a 17.8k-node graph
converges on high-degree hubs, so roughly the same dozen nodes (`HitRecord`,
`SearchPipelineConfig`, `SimpleFileCache`, `RunMetadata`, `StageOrchestrator`,
`HttpNCBIClient`) appear in almost every result regardless of the question. Ignore them
unless they are actually the subject. The topic-specific hits are the ones that matter.

Always pass `--budget` (default 2000 tokens is more than most questions need).
`explain` matches node names fuzzily and often lands on a test or rationale node —
prefer `query` unless you have an exact node ID.

**Never read `graphify-out/GRAPH_REPORT.md`** — it is ~463 KB. It is a human artifact,
not a lookup path. Same for `graph.json` (17.5 MB).

## Freshness

A `post-commit` hook rebuilds the graph, and rebuilds cost zero tokens (static extraction,
no LLM). To confirm currency, compare the `HEAD:` line in `GRAPH_REPORT.md`'s header
against `git rev-parse --short HEAD`. Manual rebuild: `graphify update .`

The hook lives in `.git/hooks/`, which is not version-controlled — re-running
`graphify hook install` regenerates a broken version whose interpreter detection misses
the venv. If the graph stops updating, check that first.

## MCP vs CLI

The `graphify-enzymefinder` MCP server loads `graph.json` into memory once per session and
never re-reads it, so after any rebuild its counts are stale until the session restarts.
**Use the CLI for queries.** Reserve the MCP tools for `graph_stats`, `god_nodes` and
`get_community`, and never treat its numbers as a freshness check.
