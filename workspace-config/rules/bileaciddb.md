---
paths:
  - "projects/Bile_acid_database/**"
---

# BileAcidDB

Standing quality bar, stated directly by the user as a persistent goal for this project —
it applies on top of whatever any individual wave's plan says.

**Comprehensive over minimal.** Capture all available information from every source, not
just what the current task needs. Where a harvest or enrichment script can choose between
a narrow fetch and a fuller one — extra fields, extra endpoints, extra metadata — take the
fuller one unless it breaks a schema or time budget. Persist raw payloads for provenance.

**Production-grade, not throwaway.** Code should hold up beyond the current dataset size
and the dev environment: idempotency, real error handling, evidence records, portable paths.

**Scoping down is a flag, not a decision.** When a task takes the minimum-viable path — a
table without a `raw_payload_json` column, a skipped optional API field, error handling
that would break at larger scale — raise it as a follow-up task or migration. Do not
silently accept it because the task passed.
