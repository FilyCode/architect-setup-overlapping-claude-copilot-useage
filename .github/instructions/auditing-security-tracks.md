# Phase 5 Security Audit Tracks

When asked to run security audits, CodeQL, subprocess audit, or Phase 5 tracks:
Apply the workflow from `projects/EnzymeFinder/.claude/skills/auditing-security-tracks/SKILL.md`.

Trigger phrases: "security audit", "codeql", "subprocess audit", "phase 5 track", "T1", "T2", "T3", "T4", "T5", "T6"

Key rules:
- T1 (CodeQL) is BLOCKING — must PASS before T2–T6 can gate.
- T2–T6 can run in parallel after T1 passes.
- CodeQL binary: `/usr3/graduate/phitro/bin/codeql`
- Log all findings to `/memories/session/review.md` with severity tags.
- Fix CRITICAL/HIGH before proceeding; defer MEDIUM/LOW with documented decision.
