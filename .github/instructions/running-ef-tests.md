# EnzymeFinder Test Runner

When asked to run tests, pytest, the test suite, or validate EnzymeFinder code:
Apply the workflow from `projects/EnzymeFinder/.claude/skills/running-ef-tests/SKILL.md`.

Trigger phrases: "run tests", "pytest", "test suite", "run ef tests", "test runner", "validate tests"

Key rules:
- Python binary: `/projectnb/liu-scc/philipp/software/local/bin/python3`
- Set NCBI_EMAIL before running compliance tests or 20 tests will fail with ValueError.
- Expected baseline: 476 passing, 30 expected failures (no live NCBI), 10 skipped.
- After full suite passes: report count to running-quality-gates.
