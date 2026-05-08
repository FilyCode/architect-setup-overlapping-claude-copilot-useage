# SCC Job Submission

When asked about qsub, SCC submission, tier-2 rerun, array jobs, or SCC job monitoring:
Apply the workflow from `projects/EnzymeFinder/.claude/skills/submitting-scc-jobs/SKILL.md`.

Trigger phrases: "submit scc", "qsub", "tier-2 rerun", "submit job", "scc submission", "array job"

Key rules:

- Always verify NCBI_EMAIL is set in env before constructing qsub command (never hardcode it).
- Use the phase wrapper script (e.g. `bash run_tier2_test.sh`) when it exists; otherwise apply the pattern from the skill.
- Exit 137 = OOM; exit 1 = env/import error; 429 in logs = rate limit.
- After exit 0: invoke running-quality-gates.
