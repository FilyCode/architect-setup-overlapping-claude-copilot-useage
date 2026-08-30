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
  **The round-trip lands in the SAME task that adds the field — or the punt is made safe.**
  Observed five times (MA-45, MA-46, MA-101, MA-114, and again 2026-08-29). The MA-101 case is
  the instructive one, and it cuts both ways: the punt was explicit, documented in an inline
  comment, and correct under `subagent-dispatch.md`'s "Concurrent dispatches need declared file
  ownership" — and the gap was then caught about two hours later, in the same session, by the
  round-trip discipline above, before anything shipped in a bad state. So this is **not** a
  licence to override file ownership. If the serializer lives in a file another task owns,
  re-sequence the plan so one task covers both edits; that is the resolution the ownership rule
  already requires, not an exception to it. Where re-sequencing genuinely is not possible, a
  punt is acceptable only if it ships with a regression test that **fails until the serializer
  is updated** and names the exact file and task that must update it. The silent punt is what
  recurs, not the punt itself.
  What the missing field actually cost: `bridge_max_coverage` defaulted to NaN on reload, and
  an unguarded `>= 0.8` against NaN is `False`, so a bridge classified `domain_mediated` came
  back `weak` after any checkpoint reload — a wrong answer, not a crash.
- Never run the test suite on the login node. See `.claude/rules/scc.md`.
