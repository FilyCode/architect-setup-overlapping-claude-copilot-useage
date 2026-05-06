# Unified Claude Code and GitHub Copilot Instructions

Shared canonical instruction set for Claude Code in the terminal and GitHub Copilot in VS Code across all projects under `projects/`.

**Owner**: Philipp Trollmann  
**Scope**: Workspace-wide and project-agnostic; project-specific overrides live in `projects/<project>/.claude/CLAUDE.md`

## Core Behaviors

### Code Quality and Best Practices

- Python: follow PEP 8, use type hints, and keep modules small.
- R: follow tidyverse style and use snake_case.
- Shell: use strict mode and explicit variables.
- Documentation: explain purpose, arguments, return values, and side effects when needed.

### Error Handling

- Catch specific exceptions.
- Use logging instead of silent failure.
- Validate inputs early and fail fast.

### Testing and Validation

- Prefer tests before submission for new logic.
- Validate SCC jobs with post-run diagnostics.
- Use mock data before hitting production APIs.

### Performance and Efficiency

- Profile before optimizing.
- Prefer built-in libraries unless a dependency is justified.
- Set conservative runtime and memory limits for SCC work.

## Token Efficiency

- Keep responses concise.
- Reuse context instead of restating it.
- Compress long outputs when needed.
- Load only the files required for the current step.

## Tool Approval

### Globally Approved

- ccusage
- rtk
- caveman
- planning-with-files

### Project-Specific

- superpowers: enforce TDD for project-specific adapter work.
- graphify: build a codebase knowledge graph when useful.

### Explicitly Excluded

- everything-claude-code
- GSD
- ruflo
- claude-mem

## Memory and Session State

- Session memory lives in `/memories/session/`.
- Project memory lives in `projects/<project>/docs/` and `projects/<project>/phases/`.
- Keep workspace-wide rules here and in `.github/`.

## Gate Decisions and Handoffs

- Ask before changing global governance files or project scope.
- Validate behavior after meaningful edit groups.
- Follow the plan, implement, review, gate, then commit handoff path.

## SCC Integration

- Use `qsub` with explicit resource limits.
- Use `qstat` for live checks and `qacct` for completed jobs.
- Treat permission errors, account mismatches, and OOMs as blockers to report clearly.
