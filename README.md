# Shared Claude/Copilot Config

This repository contains the workspace-shared instruction layer for Claude Code and GitHub Copilot.

## What belongs here

- `CLAUDE.md` for shared routing and workspace-wide rules
- `.github/copilot-instructions.md` for Copilot entry points
- `.github/instructions/` for compact shared rules
- `.claude/settings.json` for shared Claude CLI settings

## What does not belong here

- Project-specific architecture or sprint state
- One-off work notes that should live in the active project docs
- EnzymeFinder-only rules unless they are explicitly marked as project overrides

## Use

Sync this repository into the workspace with `git subtree` and keep the root `CLAUDE.md` aligned with it.
