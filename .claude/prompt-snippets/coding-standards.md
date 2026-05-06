# Coding Standards

## Python
- Follow PEP 8; use type hints; keep modules small and focused.
- Catch specific exceptions; use logging instead of silent failure.
- Validate inputs early and fail fast at system boundaries.

## R
- Follow tidyverse style; use snake_case.

## Shell
- Use strict mode (`set -euo pipefail`) and explicit variable names.
- Use `#!/bin/bash -l` for scripts that need `module load`.

## General
- Prefer built-in libraries unless a dependency is clearly justified.
- Write tests before submission for new logic.
- Profile before optimizing.
