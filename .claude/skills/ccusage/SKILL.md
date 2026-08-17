---
name: ccusage
description: Check Claude Code token usage and cost by day. Run when user asks about usage, spend, or token consumption.
user-invocable: true
disable-model-invocation: true
---

Run `npx ccusage@latest daily` to show token usage and cost grouped by date.
For weekly summary: `npx ccusage@latest weekly`
For session breakdown: `npx ccusage@latest session`

Requires Node.js (module load nodejs/20.12.2 on BU SCC). Reads ~/.claude/projects/*.jsonl offline.
