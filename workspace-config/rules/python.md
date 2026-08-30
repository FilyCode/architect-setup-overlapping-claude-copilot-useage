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
  **The round-trip lands in the SAME task that adds the field.** If the serializer lives in a
  file another task owns, that is a *sequencing error in the plan* — raise it and re-sequence;
  it is not something to punt. Observed five times (MA-45, MA-46, MA-101, MA-114, and again
  2026-08-29). The MA-101 case is the instructive one: the punt was explicit, documented, and
  locally correct under the file-ownership rule — which is precisely why the round-trip rule
  above failed to prevent it. When these two rules collide, ownership must yield or the plan
  must change; a field that does not round-trip is a live defect, while a task boundary is a
  convenience. The MA-101 field (`bridge_max_coverage`) sat unserialized for a week and
  silently defaulted to NaN, and an unguarded `>= 0.8` against NaN is `False`, so a bridge
  classified `domain_mediated` came back `weak` after any checkpoint reload — a wrong answer,
  not a crash.
- Never run the test suite on the login node. See `.claude/rules/scc.md`.
