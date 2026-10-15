# Workspace root clutter (spec §5.6)

**Done 2026-10-15 (owner approved):** scratch deleted; `outputs/`, `memories/`, `.mcp.json`, the
stray `14F 14D:` file (an old `sigma-baseline.mjs`) and the task13 worktree's re-rendered figures
moved to `archives/root-clutter-2026-10-15/`; the CaMES task13 worktree removed. List as found:

Measured 2026-10-15 in `/projectnb/liu-scc/philipp` (`ls -la`, `du -sh --apparent-size`), before the
cleanup.

| Path | Size | Last modified | What it is | Suggestion |
|---|---|---|---|---|
| `tmp/` | 641 MB | 2026-09-27 | ad hoc temporary output | review, then archive or delete |
| `.figure-verify-worktrees/task13-verify-worktree` | 223 MB | 2026-09-02 | registered git worktree of CaMES_homologue_search (detached at 6e5b883) | `git -C projects/CaMES_homologue_search worktree remove` if the figure check is done |
| `scratch_agents/` | 146 MB | 2026-09-21 | old agent scratch | delete |
| `scratch_j2/` | 930 KB | 2026-09-02 | old scratch | delete |
| `tmp_t4review_2278912/` | 802 KB | 2026-08-21 | review scratch | delete |
| `.tmp_ggi_review/`, `.tmp_review_task2/`, `.t4_review_tmp/` | 21–134 KB | 2026-08/09 | review scratch | delete |
| `.scratch_backup_test_wave6.py.bak` | 5 KB | 2026-09-14 | stray backup | delete |
| `scratch-worktrees/` | empty | 2026-09-16 | empty | delete |
| `.pytest_cache/` | 607 KB | 2026-04-15 | pytest cache at a non-project root | delete |
| `14F 14D:` | 21 KB | 2026-05-15 | file with an accidental name (likely a redirected command's output) | read, then delete |
| `outputs/` | 103 KB | 2026-05-15 | early EnzymeFinder run outputs (`c4-e2e`, `real-e2e`, …) | move into the project or archive |
| `memories/session` | 17 KB | 2026-05-19 | pre-auto-memory notes | archive |
| `.mcp.json` | 426 B | 2026-05-23 | defines `graphify-enzymefinder`, disabled everywhere | delete, or keep for the graph-stats tools |

Not clutter: `archives/` (deliberate backups, 1.6 GB), `databases/` (37 GB, shared reference
data), `bin/`, `general/` (SGE templates), `docs/`, `software/`, `.venv`, `.local` (symlink into
`software/`), `.path_hook.sh` (sourced from `~/.bashrc`), `.vscode/`, the root symlinks into the
config repo.
