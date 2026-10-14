---
paths:
  - "projects/**"
---

# Finding code in a project

Locate first, then read only what you located. Pick the tool by the question:

| Question | Tool |
|---|---|
| Where is symbol X defined, who calls it, what type is it | LSP tool (pyright): go-to-definition, find-references, hover. Exact and current; the first call in a session takes about a minute to index. |
| Where does this string, flag, column name or message appear | Grep tool (ripgrep). Use `command grep` when gitignored paths (`.superpowers/`, `results/`, `graphify-out/`) must be included. |
| Which files deal with a topic, when you do not know the names | Explore agent with `model: haiku`. |
| How does X connect to Y across modules (EnzymeFinder only) | graphify, below. |
| You know the file | Read it, with offset/limit for large files. |

## graphify (EnzymeFinder)

The graph covers `src/` and `scripts/` only (`.graphifyignore`; about 6.6k nodes). Tests,
docs and phases are not in it, so it cannot answer questions about them.

```bash
cd /projectnb/liu-scc/philipp/projects/EnzymeFinder
/projectnb/liu-scc/philipp/.venv/bin/python -m graphify query "confidence tier assignment" --budget 400
/projectnb/liu-scc/philipp/.venv/bin/python -m graphify path "BlastAdapter" "HitRecord"
```

- `query` takes topic keywords, not an exact symbol name; for a symbol use the LSP tool.
- Treat the output as candidates. Generic nodes (`str`, `Enum`, `from_dict()`) appear in
  most results; skip them.
- Always pass `--budget`. Never read `graphify-out/GRAPH_REPORT.md` or `graph.json`.
- A `post-commit` hook rebuilds the graph in the background (about 15 s, no LLM calls; log
  `~/.cache/graphify-rebuild.log`). `graphify hook install` regenerates a hook that misses
  the workspace venv; if the graph stops updating, check the hook first.
- Use the CLI, not the `graphify-enzymefinder` MCP server: the server loads `graph.json`
  once per session and goes stale after a rebuild.
