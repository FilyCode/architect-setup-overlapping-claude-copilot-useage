---
paths:
  - "**/*.sh"
  - "**/*.bash"
---

# Shell scripts

- `set -euo pipefail` at the top.
- `#!/bin/bash -l` (login shell) whenever the script calls `module load` — a plain
  `#!/bin/bash` will not have the module system available and fails obscurely.
- SGE directives belong in the header: `-P liu-scc`, `-l h_rt=`, `-l mem_per_core=`,
  `-pe omp <N>` for parallel. See `.claude/rules/scc.md` for the value envelopes.
- Bake an output-artifact check into any job script that calls a tool which can swallow
  its own errors, so a silent no-op surfaces as a real job failure instead of `exit 0`.
- Quote variable expansions. Use explicit names, not `$1`/`$2`, past the first few lines.
