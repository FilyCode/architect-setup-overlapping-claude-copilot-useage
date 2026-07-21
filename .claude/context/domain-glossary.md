# Domain Glossary

Terms shared across projects in this workspace. Project-specific terminology belongs in `projects/<project>/`, not here.

- **SCC** — Boston University Shared Computing Cluster. This workspace runs under project allocation `liu-scc`.
- **SGE** — Sun Grid Engine, the SCC's job scheduler. Jobs submitted with `qsub`, monitored with `qstat`/`qacct`.
- **WP** — Work Package. Unit of scoped, trackable project work (see EnzymeFinder phase docs for the pattern).
- **Phase** — A named stage of a project's roadmap (e.g. `P13b`), tracked with a status from `PLANNED | READY | IN_PROGRESS | COMPLETE | DEPLOYED | ARCHIVED`.
- **PLANS.md** — In-repo plan registry per project; the discoverable pointer to approved plans (external `~/.claude/plans/` files are the content source, PLANS.md indexes them).
- **Governance files** — `ARCHITECTURE.md`, `DECISIONS.md`, `CLAUDE.md`, `AGENTS.md`. Require explicit user approval before modification (see `agent-gates.md`).
