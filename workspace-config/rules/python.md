---
paths:
  - "**/*.py"
---

# Python

Standard conventions (PEP 8, type hints, specific exception types, logging over silent
failure) are assumed — this file covers only what differs here.

- Interpreters: workspace venv `/projectnb/liu-scc/philipp/.venv/bin/python`;
  `software/local/bin/python3` for the standalone build. There is no system Python to rely on.
- No sudo. Installs go to a project `.venv` or `~/.local` — never system-wide.
- Adding a field to a dataclass that has hand-maintained checkpoint serialization
  (`to_checkpoint_dict` / `from_checkpoint_dict` or equivalent) means the field must
  round-trip. Test the downstream consequence after deserialize, not just that the raw
  value survived. This gap has recurred repeatedly.
- Never run the test suite on the login node. See `.claude/rules/scc.md`.
