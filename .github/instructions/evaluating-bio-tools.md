# Bioinformatics Tool Evaluation

When asked to evaluate, select, or integrate a new bioinformatics tool adapter (Phases 6–14):
Apply the workflow from `projects/EnzymeFinder/.claude/skills/evaluating-bio-tools/SKILL.md`.

Trigger phrases: "evaluate tool", "add adapter", "new backend", "bioinformatics tool", "tool selection", "integrate HHblits", "integrate MMseqs2", "integrate Foldseek", "new search backend"

Key rules:
- Answer 4 questions first: replaces/new? SCC available? license? DB size?
- If DB > 5 GB: stop and flag to Architect before implementation.
- All adapters must implement: search()/fetch(), cache hook, HTTPAdapter+Retry, unit tests.
- Get Architect approval via integration brief before starting implementation.
- Full 40+ tool table: read `evaluating-bio-tools/tool-ecosystem-table.md` only when needed.
