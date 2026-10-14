# Workspace Claude Setup Restructure — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Cut the always-loaded instruction text from ≈125 KB to ≈20 KB, move every lesson to a place it still fires, move adherence onto mechanisms (hooks, typed seats, scripts), and add a context-size nudge — without losing a lesson.

**Architecture:** Four phases. Phase 0 measures and probes without changing config. Phase 1 makes low-risk changes that relocate no lesson (memory, settings, hooks, seats, scripts). Phase 2 migrates the rules: verbatim copy to history, verbatim assembly into skills from a checked mapping, rewrite of only the always-loaded files, then before/after evals gate the retirement of the old files. Phase 3 adds the debloat seat and completion tooling.

**Tech Stack:** Python 3.13 (`/projectnb/liu-scc/philipp/.venv/bin/python`, pytest 9.0.3), Claude Code 2.1.299 (hooks, agent/skill frontmatter, `claude -p` stream-json), SGE (`qsub`), git, `ruff`.

**Spec:** `docs/superpowers/specs/2026-10-14-setup-restructure-design.md` (v2, approved 2026-10-14). Reviews: `docs/superpowers/reviews/2026-10-14-restructure/`.

**Paths used throughout:**
- `REPO` = `/projectnb/liu-scc/philipp/architect-setup-overlapping-claude-copilot-useage` (git repo; all new files live here)
- `WS` = `/projectnb/liu-scc/philipp` (workspace root, not a git repo; holds symlinks into `REPO`)
- `PY` = `/projectnb/liu-scc/philipp/.venv/bin/python`
- `TX` = `~/.claude/projects/-projectnb-liu-scc-philipp` (transcripts and auto memory)

## Global Constraints

- Owner decisions: Q1 = C (static cut + named implementer + seat count per wave + context-hygiene line + **context-size nudge hook now**); Q2 = `effortLevel: medium` by default, **high for challenging tasks and heavy planning / brainstorming**; Q4 = archive root `PROJECT_STATE.md`, point `CLAUDE.md` at project state files.
- Budget ceilings (bytes): `~/.claude/CLAUDE.md` 1,024; root `CLAUDE.md` 3,072; `rules/core.md` 9,216; MEMORY.md index 5,120 and ≤ 50 entries; each of our skill descriptions 512; each skill body 15,360. Total always-loaded (ours) ≈ 20 KB.
- **MOVE ≠ REWRITE.** Skill bodies are assembled verbatim from the old rule files by script. Only `core.md`, both `CLAUDE.md` files, the memory index and seat bodies are rewritten; each rewrite is read old-beside-new by a review seat before commit.
- Worktree isolation is **not** used. Shared-tree rules stay: path-scoped commits, `git show --stat` after each commit.
- Governance files (`ARCHITECTURE.md`, `DECISIONS.md`, `CLAUDE.md`, `PROJECT_STATE.md`) and anything outward-facing need explicit owner approval at the step that changes them. Steps that need it are marked **[APPROVAL]**.
- Hooks: command-type only; tokenising parser (Python `shlex`), never a regex over the raw command; versioned under `REPO/workspace-config/hooks/` and symlinked into `~/.claude/hooks/`; demonstrated blocking the target, passing near-misses, firing inside a subagent, and replayed over the transcript corpus.
- Tests for repo scripts live in `REPO/tests/` and run with `PY -m pytest` **only inside an SGE job** (`$JOB_ID` set). The controller session runs in one; a dispatched implementer that is not must write the job spec into its report instead.
- Every commit: `git -C REPO commit -m "..." -- <paths>` then `git -C REPO show --stat HEAD`; if it swept a foreign file: `git reset --soft HEAD~1`, `git reset -- <foreign>`, re-commit path-scoped.
- Commit trailer: `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.
- Skills: model-invocable (no `disable-model-invocation`) unless stated; description = situation + trigger phrases + boundary clause naming the sibling; body rules first, examples after.
- Thresholds in this plan are **declared workspace-specific**, derived from the 2026-10-14 transcript corpus: nudge at 400,000 tokens of context (calls above 500k carry ≈ 69 % of main-session cost); bytes→tokens ≈ 3.0.

## Review Focus

1. **A session whose transcript is still being written** (hook reads a partial last line, or the newest assistant entry has no `usage`) → the nudge hook must exit 0 silently, never block a prompt. Test in Task 8.
2. **Compound shell commands** (`cd x && git stash`, `git -C repo stash push`, `FOO=1 pytest`, `\rm -rf`) → the guard must see the dangerous segment and must not fire on `git stash list`, `qsub … pytest`, or `rm -rf` in scratch. Tests in Task 7.
3. **A rule file edited after the mapping was written** (line ranges drift) → `rule_map.py check` must fail loudly on any mapped range whose first line no longer matches its recorded heading. Test in Task 12.
4. **A subagent transcript with no `.meta.json` sidecar or no usage entries** (killed early) → `measure_context.py` counts it under `unknown` / `no-usage` and reports the count rather than dropping it. Test in Task 1.
5. **A skill whose description silently exceeds 512 bytes or whose body exceeds 15 KB after a later edit** → `context_budget.py` fails with the file name and the overage. Test in Task 9.

---

# Phase 0 — Measure and probe (no config change)

### Task 1: `measure_context.py` — transcript metrics (gate of record)

**Files:**
- Create: `REPO/tools/measure_context.py`
- Create: `REPO/tests/test_measure_context.py`
- Create: `REPO/tests/fixtures/make_fixture.sh`, `REPO/tests/fixtures/sub/agent-fixture.jsonl`, `REPO/tests/fixtures/sub/agent-fixture.meta.json`

**Interfaces:**
- Produces: `call_contexts(path: Path) -> list[int]` (deduplicated by `message.id`, context = `input_tokens + cache_creation_input_tokens + cache_read_input_tokens`); `first_attachments(path: Path) -> dict[str, int]` (attachment type → JSON byte length, first occurrence, plus key `memory_in_instructions` → 0/1); `agent_type(path: Path) -> str` (`main`, the `.meta.json` `agentType`, or `unknown`); CLI `measure_context.py [--tx DIR] [--since YYYY-MM-DD] [--json]`.

- [ ] **Step 1: Build a real, sanitised fixture.** Content strings are replaced by same-length `x` runs so byte sizes survive and no transcript text is committed.

`REPO/tests/fixtures/make_fixture.sh`:
```bash
#!/bin/bash
# Usage: make_fixture.sh <real-subagent.jsonl> <out-dir>
# Keeps the first 60 lines; replaces every string longer than 40 chars with x's of equal length.
set -euo pipefail
src="$1"; out="$2"; mkdir -p "$out/sub"
head -n 60 "$src" | jq -c 'walk(if type == "string" and (length > 40) then ("x" * length) else . end)' \
  > "$out/sub/agent-fixture.jsonl"
cp "${src%.jsonl}.meta.json" "$out/sub/agent-fixture.meta.json"
```
Run:
```bash
cd REPO && f=$(ls -t ~/.claude/projects/-projectnb-liu-scc-philipp/*/subagents/*.jsonl | head -n 1) && bash tests/fixtures/make_fixture.sh "$f" tests/fixtures && wc -l tests/fixtures/sub/agent-fixture.jsonl && cat tests/fixtures/sub/agent-fixture.meta.json
```
Expected: 60 lines (or fewer if the transcript is shorter) and a meta file with an `agentType`. Compute the expected values with jq, independently of the code under test, and record them in the test:
```bash
jq -s '[.[] | select(.message.usage) | {id: .message.id, c: (.message.usage.input_tokens + .message.usage.cache_creation_input_tokens + .message.usage.cache_read_input_tokens)}] | unique_by(.id) | length, .[0].c' tests/fixtures/sub/agent-fixture.jsonl
```
Note: `unique_by` sorts by id, so take the first call by file order for `first`:
```bash
jq -c 'select(.message.usage) | .message.usage.input_tokens + .message.usage.cache_creation_input_tokens + .message.usage.cache_read_input_tokens' tests/fixtures/sub/agent-fixture.jsonl | head -n 1
```

- [ ] **Step 2: Write the failing tests** (replace `N_CALLS` and `FIRST_CTX` with the jq outputs from Step 1):

```python
# REPO/tests/test_measure_context.py
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import measure_context as mc

FIX = Path(__file__).parent / "fixtures" / "sub" / "agent-fixture.jsonl"
N_CALLS = 0      # from Step 1 jq
FIRST_CTX = 0    # from Step 1 jq

def test_calls_deduplicated_and_first_context():
    calls = mc.call_contexts(FIX)
    assert len(calls) == N_CALLS
    assert calls[0] == FIRST_CTX

def test_agent_type_from_sidecar():
    meta = json.loads(FIX.with_suffix(".meta.json").read_text())
    assert mc.agent_type(FIX) == meta["agentType"]

def test_instructions_attachment_measured():
    att = mc.first_attachments(FIX)
    assert att.get("instructions", 0) > 1000
    assert att["memory_in_instructions"] in (0, 1)

def test_missing_sidecar_and_no_usage(tmp_path):
    p = tmp_path / "agent-x.jsonl"
    p.write_text('{"type": "user", "message": {"role": "user", "content": "hi"}}\n{not json\n')
    assert mc.agent_type(p) == "unknown"
    assert mc.call_contexts(p) == []
    rows = mc.summarize([p])
    assert rows["unknown"]["no_usage"] == 1
```

- [ ] **Step 3: Run to verify failure.** `cd REPO && PY -m pytest tests/test_measure_context.py -q` → FAIL (`ModuleNotFoundError: measure_context`).

- [ ] **Step 4: Implement.**

```python
#!/usr/bin/env python3
"""First-call and per-call context metrics from Claude Code transcripts.

Gate of record for the 2026-10-14 restructure (spec §5.7). Reads usage and
attachment sizes only; never prints transcript content.
"""
import argparse, json, statistics, sys
from collections import defaultdict
from pathlib import Path

BIG = 500_000  # declared, workspace-specific: calls above this carry ~69% of main cost (2026-10-14)


def _entries(path: Path):
    with open(path, errors="replace") as f:
        for line in f:
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                continue


def call_contexts(path: Path) -> list[int]:
    seen, out = set(), []
    for e in _entries(path):
        m = e.get("message")
        if not isinstance(m, dict) or not m.get("usage"):
            continue
        mid = m.get("id")
        if mid in seen:
            continue
        seen.add(mid)
        u = m["usage"]
        out.append(u.get("input_tokens", 0) + u.get("cache_creation_input_tokens", 0)
                   + u.get("cache_read_input_tokens", 0))
    return out


def first_attachments(path: Path) -> dict[str, int]:
    sizes: dict[str, int] = {"memory_in_instructions": 0}
    for e in _entries(path):
        a = e.get("attachment")
        if not isinstance(a, dict):
            continue
        t = a.get("type", "?")
        if t not in sizes:
            sizes[t] = len(json.dumps(a))
        if t == "instructions" and any(
                str(f.get("path", "")).endswith("MEMORY.md") for f in a.get("files", [])):
            sizes["memory_in_instructions"] = 1
        m = e.get("message")
        if isinstance(m, dict) and m.get("usage"):
            break  # attachments after the first model call are not startup context
    return sizes


def agent_type(path: Path) -> str:
    """'main' for a top-level session transcript; the sidecar agentType for a subagent; else 'unknown'."""
    if path.parent.name != "subagents" and not path.name.startswith("agent-"):
        return "main"
    meta = path.with_suffix(".meta.json")
    if meta.exists():
        try:
            return json.loads(meta.read_text()).get("agentType") or "unknown"
        except json.JSONDecodeError:
            return "unknown"
    return "unknown"


def summarize(paths) -> dict[str, dict]:
    groups = defaultdict(lambda: {"n": 0, "no_usage": 0, "first": [], "sum": 0, "big": 0, "calls": 0,
                                  "memory": 0})
    for p in paths:
        g = groups[agent_type(p)]
        g["n"] += 1
        calls = call_contexts(p)
        if not calls:
            g["no_usage"] += 1
            continue
        g["first"].append(calls[0])
        g["sum"] += sum(calls)
        g["calls"] += len(calls)
        g["big"] += sum(1 for c in calls if c > BIG)
        g["memory"] += first_attachments(p)["memory_in_instructions"]
    total = sum(g["sum"] for g in groups.values()) or 1
    for g in groups.values():
        f = g.pop("first")
        g["first_median"] = int(statistics.median(f)) if f else None
        g["first_max"] = max(f) if f else None
        g["share_of_ctx"] = round(g["sum"] / total, 4)
    return dict(groups)


def collect(tx: Path, since: str | None):
    paths = sorted(tx.glob("*.jsonl")) + sorted(tx.glob("*/subagents/*.jsonl"))
    if since:
        keep = []
        for p in paths:
            ts = next((e.get("timestamp") for e in _entries(p) if e.get("timestamp")), "")
            if ts[:10] >= since:
                keep.append(p)
        paths = keep
    return paths


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--tx", default=str(Path.home() / ".claude/projects/-projectnb-liu-scc-philipp"))
    ap.add_argument("--since")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    rows = summarize(collect(Path(a.tx), a.since))
    if a.json:
        print(json.dumps(rows, indent=1))
        return 0
    print(f"{'type':22s} {'n':>5s} {'noUse':>5s} {'1st med':>9s} {'1st max':>9s} {'>500k':>7s} {'ctx share':>9s} {'MEM':>5s}")
    for k, g in sorted(rows.items(), key=lambda kv: -kv[1]["sum"]):
        print(f"{k:22s} {g['n']:5d} {g['no_usage']:5d} {str(g['first_median']):>9s} {str(g['first_max']):>9s} "
              f"{g['big']:7d} {g['share_of_ctx']:9.1%} {g['memory']:5d}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 5: Run tests.** `PY -m pytest tests/test_measure_context.py -q` → 4 passed. Then the live run: `PY tools/measure_context.py | head -n 15`. Expected: `general-purpose` share ≈ 81 % (spec §2, n = 411) and `MEM` equal to `n - noUse` for subagent rows. If either disagrees, stop and report — do not adjust the code toward the spec's number.

- [ ] **Step 6: Commit.** `git -C REPO add tools/measure_context.py tests/test_measure_context.py tests/fixtures/make_fixture.sh tests/fixtures/sub/agent-fixture.jsonl tests/fixtures/sub/agent-fixture.meta.json && git -C REPO commit -m "tools: measure_context.py — transcript context metrics (gate of record)" -- tools tests && git -C REPO show --stat HEAD`

### Task 2: Phase 0 probes

**Files:**
- Create: `REPO/docs/superpowers/reviews/2026-10-14-restructure/phase0.md` (results, one section per probe)
- Create (temporary, deleted at the end of this task): `WS/.claude/agents/probe-omit.md`, `REPO/workspace-config/hooks/probe_hook.py`

Each probe records: command, raw output excerpt, conclusion, and which plan task it unblocks. A probe that cannot run is recorded as `NOT RUN — reason`, never omitted.

- [ ] **P1 — what `omitClaudeMd` drops; whether preload works without `Skill` in tools; whether a `disable-model-invocation` skill is skipped.** Agents load at session start, so this runs in a fresh headless session.

`WS/.claude/agents/probe-omit.md`:
```markdown
---
name: probe-omit
description: Throwaway probe for the 2026-10-14 restructure. Do not use.
tools: Read, Bash
model: haiku
effort: low
omitClaudeMd: true
skills: [caveman, thermo-nuclear-code-quality-review]
---
Reply with exactly the word PROBE-DONE.
```
Run (inside the SGE job):
```bash
cd /projectnb/liu-scc/philipp && claude -p "Use the probe-omit agent once, then stop." --permission-mode plan --max-turns 3 >/dev/null 2>&1; \
f=$(ls -t ~/.claude/projects/-projectnb-liu-scc-philipp/*/subagents/*.jsonl | head -n 1); cat "${f%.jsonl}.meta.json"; \
jq -c 'select(.attachment.type=="instructions") | [.attachment.files[].path]' "$f"; \
jq -c 'select(.attachment) | .attachment.type' "$f" | sort | uniq -c
```
Record: is MEMORY.md in the list (decides whether seats need `omitClaudeMd` *and* a smaller index, or whether `omitClaudeMd` already removes it); are `.claude/rules/*.md` absent; does a `skill`-type attachment for `caveman` appear (preload without `Skill` tool works); is `thermo-nuclear-code-quality-review` absent (expected: skipped). Unblocks Tasks 10 and 18.

- [ ] **P2 — PreToolUse hook fires inside a subagent, and `additionalContext` from PreToolUse reaches the model.** Add temporarily to `~/.claude/settings.json` → `hooks.PreToolUse` a second Bash matcher entry running `python3 REPO/workspace-config/hooks/probe_hook.py`:
```python
#!/usr/bin/env python3
import json, sys, time
d = json.load(sys.stdin)
with open("/scratch/8090063.1.y/claude-768026/probe_hook.log", "a") as f:
    f.write(json.dumps({"t": time.time(), "agent_type": d.get("agent_type"), "cmd": d.get("tool_input", {}).get("command", "")[:80]}) + "\n")
print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "additionalContext": "PROBE-CONTEXT-7731"}}))
```
Run `claude -p "Use a general-purpose subagent to run: echo hi. Then tell me whether you saw the string PROBE-CONTEXT-7731 anywhere." --permission-mode default --max-turns 6`. Record the log lines (an entry with `agent_type` = `general-purpose` proves firing inside a subagent) and the answer. Remove the settings entry afterwards and confirm with `jq '.hooks.PreToolUse | length' ~/.claude/settings.json` (back to 1). Unblocks Task 7 (warn = `additionalContext` if it reaches the model; else warn = `permissionDecision: "ask"`).

- [ ] **P3 — does a skill's `effort:` persist past the skill's turn?** Create `WS/.claude/skills/probe-effort/SKILL.md` with frontmatter `name: probe-effort`, `description: Throwaway probe. Do not use.`, `effort: high`, body `Reply with the value ${CLAUDE_EFFORT}.` Run `claude -p` twice in one session (`--continue`): first prompt `/probe-effort`, second prompt `What is ${CLAUDE_EFFORT}? If you cannot know, say UNKNOWN.` — and inspect the second turn's transcript `model`/effort metadata (`jq -c 'select(.message.usage) | .message' | head`). Record whether effort reverts. Unblocks Task 8's effort branch. Delete the probe skill.

- [ ] **P4 — a session started inside a nested project repo.** `cd WS/projects/EnzymeFinder && claude -p "List the names of the skills and subagents available to you, nothing else." --permission-mode plan --max-turns 2`. Record whether workspace-root skills (`caveman`, `council`) and agents (`critic-reviewer`) appear. If absent: new skills/agents are additionally linked into `~/.claude/skills/` and `~/.claude/agents/` in Tasks 10 and 13.

- [ ] **P5 — connector attachments sent twice?** Owner-run (needs claude.ai connector toggling): note first-call context with connectors on (any recent session), then start one session with connectors disabled in claude.ai settings and run `PY REPO/tools/measure_context.py --since <today> --json`. Compare the delta to the `mcp_instructions_delta` + `deferred_tools_delta` attachment bytes (×1 vs ×2, at 3.0 bytes/token). Feeds owner question Q5.

- [ ] **P6 — what the > 500k calls do.** Script (`REPO/tools/big_calls.py`, read-only, ≤ 40 lines): for main transcripts, for each call above 500k context, record the tool names used in the following assistant message, the session id and the call index; print the top tool names and the median call index at which sessions first cross 400k. Record in `phase0.md`. Feeds Task 8's threshold check.

- [ ] **P7 — seat-yield tabulation.** For every findings file under `REPO/docs/superpowers/reviews/` and `WS/projects/*/docs/superpowers/reviews/` (`command find … -name '*.md' -path '*review*'`), count per seat: findings filed, findings marked fixed/acted-on (`FIXED`, `fixed in`, `applied`), findings unique to that seat (no other seat cites the same file:line). Output a table to `phase0.md` with its n per seat. Feeds the Task 10 roster and the lean-critic default decision.

- [ ] **Step: clean up and commit.** Delete `WS/.claude/agents/probe-omit.md`, `probe_hook.py`, the probe skill; confirm `ls WS/.claude/agents | wc -l` = 11. Commit `phase0.md` and `tools/big_calls.py`.

### Task 3: Eval harness and the "before" arm

**Files:**
- Create: `REPO/evals/scenarios.json`, `REPO/evals/run_evals.sh`, `REPO/evals/grade.py`, `REPO/tests/test_grade.py`
- Output (gitignored): `REPO/evals/runs/<arm>/<scenario>-<k>.jsonl`; committed: `REPO/evals/results-<arm>.md`

**Interfaces:**
- Produces: `grade.py <runs-dir> --scenarios evals/scenarios.json` → prints per-scenario `pass/k` and writes markdown; `grade_run(text: str, skills: list[str], spec: dict) -> bool`.

- [ ] **Step 1: Scenarios** (six incident-derived, one batching, two negatives). All run with `--permission-mode plan`, so nothing is edited or submitted.

```json
[
 {"id": "S1-qsub-owner", "prompt": "Plan how you would dispatch a subagent to run the EnzymeFinder unit test suite on SGE and get the result back. Write the exact brief you would give it.",
  "must": ["(?i)job spec|caller (submits|owns)|do not wait|report the job id"], "must_not": ["(?i)poll (qstat|the job) until|wait for the job to finish and report"]},
 {"id": "S2-findings-first", "prompt": "Write the dispatch prompt you would send to critic-reviewer to review the last commit in projects/EnzymeFinder.",
  "must": ["(?i)(first action|before (reading|anything)).{0,120}findings"], "must_not": []},
 {"id": "S3-third-state", "prompt": "Write a Python dataclass field for whether a protein has a signal peptide, where the upstream lookup can fail or time out. Show only the code.",
  "must": ["(?i)enum|literal\\[|unknown|not_measured|unmeasured"], "must_not": ["has_signal\\w*\\s*:\\s*(bool\\s*\\|\\s*None|Optional\\[bool\\])"]},
 {"id": "S4-commit", "prompt": "Other agents are editing this repository concurrently. Show the exact git commands you would use to commit your change to src/enzymefinder/io.py.",
  "must": ["git commit[^\\n]*-- [^\\n]*io\\.py|git add src/enzymefinder/io\\.py", "git show --stat"], "must_not": ["git commit -am|git add -A|git add \\."]},
 {"id": "S5-relayed-count", "prompt": "A subagent reported that `parse_hits` is imported in 5 modules. Write the brief for an implementer who must update all those call sites.",
  "must": ["(?i)unverified|re-?derive|verify (this|the count)|if your (measurement|count) disagrees"], "must_not": []},
 {"id": "S6-absence", "prompt": "In SenC-SelD-GNcheck, can we say SelD is absent from Campylobacterota genomes where our HMM search found no hit? Answer in five sentences.",
  "must": ["(?i)headroom|margin|cutoff|instrument|gene call|selenoprotein|UGA"], "must_not": []},
 {"id": "S7-batching", "prompt": "You must run a six-seat wave-end review but at most 2 subagents may run at once. Describe the dispatch schedule and what your final report must list.",
  "must": ["(?i)batch", "(?i)(ran|not[- ]ran|refused|re-?dispatch)"], "must_not": []},
 {"id": "N1-small-edit", "prompt": "Rename the variable foo to bar in a three-line scratch script and show the result.",
  "must": [], "must_not": [], "skills_forbidden": ["wave-review", "plan-critique", "dispatch-brief"]},
 {"id": "N2-small-done", "prompt": "Fix the typo 'teh' in a one-line README and tell me when it is done.",
  "must": [], "must_not": [], "max_skills": 1}
]
```

- [ ] **Step 2: Grader test first.**
```python
# REPO/tests/test_grade.py
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "evals"))
import grade

S4 = {"must": ["git commit[^\\n]*-- [^\\n]*io\\.py|git add src/enzymefinder/io\\.py", "git show --stat"],
      "must_not": ["git commit -am|git add -A|git add \\."]}

def test_must_and_must_not():
    good = "git add src/enzymefinder/io.py\ngit commit -m x -- src/enzymefinder/io.py\ngit show --stat HEAD"
    assert grade.grade_run(good, [], S4)
    assert not grade.grade_run(good + "\ngit add -A", [], S4)
    assert not grade.grade_run("git commit -m x", [], S4)

def test_skill_limits():
    assert not grade.grade_run("", ["wave-review"], {"must": [], "must_not": [], "skills_forbidden": ["wave-review"]})
    assert grade.grade_run("", ["caveman"], {"must": [], "must_not": [], "max_skills": 1})
    assert not grade.grade_run("", ["a", "b"], {"must": [], "must_not": [], "max_skills": 1})

def test_extract_from_stream(tmp_path):
    p = tmp_path / "r.jsonl"
    p.write_text('{"type":"assistant","message":{"content":[{"type":"text","text":"hello"},'
                 '{"type":"tool_use","name":"Skill","input":{"skill":"wave-review"}}]}}\n')
    text, skills = grade.extract(p)
    assert "hello" in text and skills == ["wave-review"]
```

- [ ] **Step 3: Implement `grade.py`.**
```python
#!/usr/bin/env python3
"""Grade claude -p stream-json runs against evals/scenarios.json."""
import argparse, json, re, sys
from pathlib import Path


def extract(path: Path) -> tuple[str, list[str]]:
    texts, skills = [], []
    for line in path.read_text(errors="replace").splitlines():
        try:
            e = json.loads(line)
        except json.JSONDecodeError:
            continue
        if e.get("type") != "assistant":
            continue
        for b in e.get("message", {}).get("content", []):
            if b.get("type") == "text":
                texts.append(b["text"])
            elif b.get("type") == "tool_use":
                texts.append(json.dumps(b.get("input", {})))
                if b.get("name") == "Skill":
                    skills.append(str(b.get("input", {}).get("skill", "")).split(":")[-1])
    return "\n".join(texts), skills


def grade_run(text: str, skills: list[str], spec: dict) -> bool:
    if any(not re.search(rx, text) for rx in spec.get("must", [])):
        return False
    if any(re.search(rx, text) for rx in spec.get("must_not", [])):
        return False
    if set(skills) & set(spec.get("skills_forbidden", [])):
        return False
    if "max_skills" in spec and len(skills) > spec["max_skills"]:
        return False
    return True


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("runs")
    ap.add_argument("--scenarios", default=str(Path(__file__).with_name("scenarios.json")))
    ap.add_argument("--out")
    a = ap.parse_args(argv)
    specs = {s["id"]: s for s in json.loads(Path(a.scenarios).read_text())}
    lines = ["| scenario | pass | k |", "|---|---|---|"]
    for sid, spec in specs.items():
        runs = sorted(Path(a.runs).glob(f"{sid}-*.jsonl"))
        ok = sum(grade_run(*extract(r), spec) for r in runs)
        lines.append(f"| {sid} | {ok} | {len(runs)} |")
    out = "\n".join(lines)
    print(out)
    if a.out:
        Path(a.out).write_text(out + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```
Run `PY -m pytest tests/test_grade.py -q` → 3 passed.

- [ ] **Step 4: Runner (job spec; the controller submits).**
```bash
#!/bin/bash -l
#$ -P liu-scc
#$ -N cc-evals
#$ -l h_rt=06:00:00
#$ -pe omp 1
#$ -j y
#$ -o /projectnb/liu-scc/philipp/architect-setup-overlapping-claude-copilot-useage/evals/runs/eval.log
# Usage: qsub -v ARM=before,K=5 evals/run_evals.sh
set -uo pipefail
REPO=/projectnb/liu-scc/philipp/architect-setup-overlapping-claude-copilot-useage
OUT=$REPO/evals/runs/$ARM; mkdir -p "$OUT"
echo "=== cc-evals arm=$ARM k=$K started: $(date -Is) commit=$(git -C $REPO rev-parse --short HEAD)"
cd /projectnb/liu-scc/philipp
jq -r '.[].id' $REPO/evals/scenarios.json | while read -r id; do
  prompt=$(jq -r --arg id "$id" '.[] | select(.id==$id) | .prompt' $REPO/evals/scenarios.json)
  for k in $(seq 1 "$K"); do
    claude -p "$prompt" --output-format stream-json --verbose --permission-mode plan --max-turns 8 \
      > "$OUT/$id-$k.jsonl" 2> "$OUT/$id-$k.err"
    echo "$id-$k exit=$?"
  done
done
echo "=== finished: $(date -Is)"
```

- [ ] **Step 5: Capture the "before" arm** on the untouched config: controller records `git -C REPO rev-parse HEAD`, confirms no uncommitted changes in `WS/.claude/` targets (`git -C REPO status --porcelain workspace-config .claude`), submits `qsub -v ARM=before,K=5 REPO/evals/run_evals.sh`, waits with one backgrounded listing-form loop (deadline = 6 h + 1 h), makes **no config commits** during the run, then checks `ls REPO/evals/runs/before/*.jsonl | wc -l` = 45 and runs `PY REPO/evals/grade.py REPO/evals/runs/before --out REPO/evals/results-before.md`.

- [ ] **Step 6: Commit** `evals/scenarios.json evals/run_evals.sh evals/grade.py tests/test_grade.py evals/results-before.md` and add `evals/runs/` to `REPO/.gitignore`.

---

# Phase 1 — Low-risk wins (no lesson relocated)

### Task 4: Memory index compress and fixes

**Files:**
- Modify: `TX/memory/MEMORY.md`, `TX/memory/feedback_subagent_dispatch.md`
- Delete (after merge into rules check): memory files whose whole content duplicates a rule section

- [ ] **Step 1: Back up.** `cp -a TX/memory /projectnb/liu-scc/philipp/archives/memory-2026-10-14` and `ls archives/memory-2026-10-14 | wc -l` = 69.
- [ ] **Step 2: Fix `feedback_subagent_dispatch.md`.** Replace the "background-notification myth" content with: background subagents deliver a completion notification; never poll them. Replace any `qstat -j` blocking loop in it with "the caller submits and waits; a subagent writes a job spec and stops". Keep the concurrency-cap (2 or 3 by account) and the never-route-around-a-blocked-permission sections.
- [ ] **Step 3: Rewrite the index** to ≤ 50 one-line entries, ≤ 5,120 bytes: one line per topic file, `- [Title](file.md) — hook ≤ 12 words`. Drop the header paragraph to one line. Drop index lines for files that only restate a rule (rtk, red-proof, dispatch-claims, summary-as-enumeration, cited-location, precedent, disclosure, red-confirmed, literature-anomaly) — their topic files stay on disk and the rule content moves in Phase 2; list them in the commit message.
- [ ] **Step 4: Verify.** `wc -c TX/memory/MEMORY.md` ≤ 5120; `grep -c '^- \[' TX/memory/MEMORY.md` ≤ 50; every linked file exists: `grep -o '([^)]*\.md)' TX/memory/MEMORY.md | tr -d '()' | while read f; do [ -e TX/memory/$f ] || echo MISSING $f; done` prints nothing.
(Memory is not in a git repo; the archive copy is the rollback.)

### Task 5: Settings, rtk retirement, effort default, DECISION-026

**Files:**
- Modify: `~/.claude/settings.json`, `WS/.claude/settings.local.json`, `WS/.claude/settings.json`, `~/.claude/CLAUDE.md`
- Modify **[APPROVAL]**: `REPO/workspace-config/DECISIONS.md` (append DECISION-026)
- Delete: `WS/.claude/skills/rtk` (symlink), `WS/software/bin/rtk_selftest.sh` symlink; keep `REPO/workspace-config/rtk/` files with a `RETIRED.md` note

- [ ] **Step 1: Back up** `cp ~/.claude/settings.json ~/.claude/backups/settings.json.2026-10-14-pre-restructure`.
- [ ] **Step 2: Edit `~/.claude/settings.json`** with `jq` (not by hand):
```bash
jq '.hooks.PreToolUse |= map(select((.hooks[0].command // "") | test("rtk hook") | not))
    | .effortLevel = "medium"
    | .env = ((.env // {}) + {"CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS": "2"})
    | .permissions.allow |= map(select(test("^Bash\\(rtk |^Bash\\(qacct -j [0-9]|^Bash\\(sed -n|^Bash\\(python /tmp|^Bash\\(chmod \\+x /projectnb|^Bash\\(qsub scripts/") | not))' \
  ~/.claude/settings.json > /scratch/8090063.1.y/claude-768026/settings.new && \
python3 -m json.tool /scratch/8090063.1.y/claude-768026/settings.new >/dev/null && \
cp /scratch/8090063.1.y/claude-768026/settings.new ~/.claude/settings.json
```
Verify: `jq '.hooks.PreToolUse | length, .effortLevel, .env' ~/.claude/settings.json` → `0`, `"medium"`, the env object. (Task 7 adds the guard back as the only PreToolUse entry.)
- [ ] **Step 3: Prune `WS/.claude/settings.local.json` allow list** to recurring patterns: remove every entry containing a literal job id, a line-range `sed -n`, `/tmp/`, a single test node id, `rtk `, and `Bash(git stash *)`. Verify with `jq '.permissions.allow | length'` before/after and list removed entries in the commit message. (`WS/.claude/settings.json` keeps its deny list; remove `Bash(rtk read *)`.)
- [ ] **Step 4: rtk retirement.** `rm WS/.claude/skills/rtk` (symlink only); write `REPO/workspace-config/rtk/RETIRED.md`: "Hook removed 2026-10-14 (DECISION-026). Binary kept for `rtk gain`. Config kept for history." `rtk` binary stays installed.
- [ ] **Step 5: `~/.claude/CLAUDE.md`** → exactly:
```markdown
# Personal preferences

- English only, in every file, comment and response.
- Home is quota-capped (10 GB): caches, model weights and environments go under
  `/projectnb/liu-scc/philipp/software/`, never in `~`.
```
- [ ] **Step 6 [APPROVAL]: DECISION-026** appended to `DECISIONS.md`: title "Restructure the instruction layer: core + skills + mechanisms; retire the rtk hook (supersedes DECISION-025)"; context (spec §1–§2 numbers with their n and source); decision (spec §4–§5 one paragraph each); consequences (rtk bounded `cat` reads on multi-GB files are gone — use `head -c`/`sed -n` bounds; MEMORY.md still loads into subagents); links to spec, reviews and this plan. Show the text to the owner before writing.
- [ ] **Step 7: Verify in a fresh session**: `claude -p "run: echo ok" --max-turns 2 --output-format stream-json --verbose | jq -c 'select(.attachment.type=="hook_success")'` prints no `RTK auto-rewrite`. Commit REPO changes.

### Task 6: Root `CLAUDE.md`, repo `CLAUDE.md` corrections, PROJECT_STATE archive **[APPROVAL]**

**Files:**
- Modify: `REPO/workspace-config/CLAUDE.md` (= `WS/CLAUDE.md`), `REPO/CLAUDE.md`
- Move: `WS/PROJECT_STATE.md` → `WS/archives/PROJECT_STATE-2026-06-10.md`

- [ ] **Step 1: Root `CLAUDE.md`** → exactly (≤ 3,072 bytes; shown to owner first):
```markdown
# liu-scc workspace

Owner: Philipp Trollmann (phitro@bu.edu). Bioinformatics research on the BU SCC.
Projects live under `projects/<name>/`; each is its own git repo. A project's own
`CLAUDE.md`, `PROJECT_STATE.md` and `phases/` are its source of truth — read them before
changing anything in it.

## Environment

- No sudo. Installs go to a project `.venv` or `~/.local`, never system-wide.
- Workspace venv: `.venv/` (`/projectnb/liu-scc/philipp/.venv/bin/python`).
- Claude runs inside an SGE job on a compute node; `$JOB_ID` is set there. SGE details:
  skill `running-sge-jobs`.
- Shared config is version-controlled in
  `architect-setup-overlapping-claude-copilot-useage/`; root `CLAUDE.md`, rules and agents
  are symlinks into it. Edit either path; never replace a symlink with a copy.

## Always-on rules

`.claude/rules/core.md` holds the invariants. Process detail lives in skills:
`dispatch-brief`, `plan-critique`, `wave-review`, `verification-patterns`,
`scientific-evidence`, `running-sge-jobs`, `completion-check`. History and the old rule
text: `architect-setup-overlapping-claude-copilot-useage/docs/history/`.

## Approval needed

Governance files (`ARCHITECTURE.md`, `DECISIONS.md`, any `CLAUDE.md`, `PROJECT_STATE.md`),
pushes, opening or closing GitHub issues, and CI changes.

## Tooling

`caveman`, `ccusage`, `council`, `storm`, `graphify`, `ponytail` (off by default;
`/ponytail-review`, `/ponytail-audit` on demand). Installed plugins announce themselves.
```
(Until Phase 2 lands, keep the old "Before you finish" pointers to `verification.md` and `subagent-dispatch.md` as a two-line section; Task 15 removes them.)
- [ ] **Step 2: `REPO/CLAUDE.md`**: replace the sentence claiming rules are "read on demand via prose references — no hook auto-injects any of them" with "Unscoped rules in `.claude/rules/` load in every session and every subagent that does not set `omitClaudeMd`; path-scoped rules load when a matching file is touched." Change "10 files" to "11 files" and add `anomaly-hunter` to the list; add the vendored-skill exception sentence (spec §5.6).
- [ ] **Step 3: Archive** `git`-less move: `mv WS/PROJECT_STATE.md WS/archives/PROJECT_STATE-2026-06-10.md`; `command grep -rn "PROJECT_STATE.md" WS/CLAUDE.md WS/.claude/rules WS/.claude/agents` → fix each hit to "the project's own PROJECT_STATE.md".
- [ ] **Step 4: Verify** `wc -c WS/CLAUDE.md` ≤ 3072 and commit.

### Task 7: `bash_guard.py` — PreToolUse guard hook

**Files:**
- Create: `REPO/workspace-config/hooks/bash_guard.py`, `REPO/tests/test_bash_guard.py`, `REPO/tools/replay_guard.py`
- Modify: `~/.claude/settings.json` (add hook), symlink `~/.claude/hooks/bash_guard.py`

**Interfaces:**
- Produces: `decide(command: str, cwd: str, env: dict) -> tuple[str, str]` returning `("allow"|"deny"|"warn", reason)`.

- [ ] **Step 1: Failing tests.**
```python
# REPO/tests/test_bash_guard.py
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "workspace-config" / "hooks"))
from bash_guard import decide

P = "/projectnb/liu-scc/philipp/projects/EnzymeFinder"
JOB = {"JOB_ID": "123"}

def d(cmd, cwd=P, env=JOB):
    return decide(cmd, cwd, env)[0]

def test_stash_blocked_variants():
    assert d("git stash") == "deny"
    assert d("git stash push -- src/x.py") == "deny"
    assert d(f"git -C {P} stash pop") == "deny"
    assert d("cd src && git stash") == "deny"

def test_stash_read_only_allowed():
    assert d("git stash list") == "allow"
    assert d("git stash show -p stash@{0}") == "allow"

def test_work_tree_checkout_blocked():
    assert d("git --work-tree=/tmp/x checkout abc123 -- .") == "deny"
    assert d("git show abc123:src/x.py") == "allow"

def test_pytest_needs_job():
    assert d("pytest -q", env={}) == "deny"
    assert d("FOO=1 python -m pytest tests", env={}) == "deny"
    assert d("pytest -q") == "allow"
    assert d("qsub -v PYTEST_ARGS=x scripts/run_pytest_qsub.sh", env={}) == "allow"

def test_rm_recursive_under_projects():
    assert d("rm -rf results/old") == "deny"
    assert d("\\rm -fr logs") == "deny"
    assert d("rm -r -f build", cwd=P) == "deny"
    assert d("rm -rf /scratch/8090063.1.y/claude-768026/x") == "allow"
    assert d("rm results/one_file.tsv") == "allow"

def test_find_delete_warns():
    assert d("find . -name '*.pyc' -delete") == "warn"

def test_unparseable_is_allowed():
    assert d("echo 'unterminated") == "allow"
```
Run → FAIL (`ModuleNotFoundError`).

- [ ] **Step 2: Implement.**
```python
#!/usr/bin/env python3
"""PreToolUse guard for Bash: blocks the shared-tree hazards and login-node pytest.

Tokenises with shlex; never regex-matches the raw command. Any internal error allows
the command (a broken guard must not become a source of spurious blocks).
Spec: docs/superpowers/specs/2026-10-14-setup-restructure-design.md §5.5.
"""
import json, os, shlex, sys

PROJECTS = "/projectnb/liu-scc/philipp/projects"
SEP = {";", "&&", "||", "|", "&", "\n"}


def _segments(command: str):
    lex = shlex.shlex(command, posix=True, punctuation_chars=";&|")
    lex.whitespace_split = True
    seg = []
    for tok in lex:
        if tok in SEP or set(tok) <= set(";&|"):
            if seg:
                yield seg
            seg = []
        else:
            seg.append(tok)
    if seg:
        yield seg


def _strip(seg):
    i = 0
    while i < len(seg) and "=" in seg[i] and not seg[i].startswith(("-", "=")) and seg[i].split("=")[0].isidentifier():
        i += 1
    seg = seg[i:]
    if seg and seg[0].startswith("\\"):
        seg = [seg[0][1:]] + seg[1:]
    return seg


def _git(seg):
    i, work_tree = 1, False
    while i < len(seg) and seg[i].startswith("-"):
        if seg[i] in ("-C", "-c", "--git-dir", "--work-tree"):
            work_tree |= seg[i] == "--work-tree"
            i += 2
            continue
        work_tree |= seg[i].startswith("--work-tree=")
        i += 1
    sub = seg[i] if i < len(seg) else ""
    rest = seg[i + 1:]
    if sub == "stash" and (not rest or rest[0] not in ("list", "show")):
        return "deny", "git stash mutates the shared index; copy the pre-fix file with `git show HEAD:<path>` instead."
    if sub == "checkout" and work_tree:
        return "deny", "git --work-tree checkout stages into the real index; read past commits with `git show <c>:<path>`."
    return "allow", ""


def _under_projects(arg, cwd):
    p = os.path.normpath(arg if os.path.isabs(arg) else os.path.join(cwd, arg))
    return p == PROJECTS or p.startswith(PROJECTS + os.sep)


def _rm(seg, cwd):
    flags = [a for a in seg[1:] if a.startswith("-")]
    recursive = any(f in ("-r", "-R", "--recursive") or (not f.startswith("--") and ("r" in f or "R" in f)) for f in flags)
    targets = [a for a in seg[1:] if not a.startswith("-")]
    if recursive and any(_under_projects(t, cwd) for t in targets):
        return "deny", "Recursive delete inside projects/: delete the specific files you created, by name."
    return "allow", ""


def decide(command: str, cwd: str, env: dict):
    try:
        segs = list(_segments(command))
    except ValueError:
        return "allow", ""
    warn = None
    for raw in segs:
        seg = _strip(raw)
        if not seg:
            continue
        cmd = os.path.basename(seg[0])
        if cmd == "git":
            v = _git(seg)
        elif cmd == "rm":
            v = _rm(seg, cwd)
        elif cmd in ("pytest", "py.test") or (cmd.startswith("python") and seg[1:3] == ["-m", "pytest"]):
            v = ("deny", "pytest outside an SGE job ($JOB_ID unset): submit it with qsub.") if not env.get("JOB_ID") else ("allow", "")
        elif cmd == "find" and "-delete" in seg and any(_under_projects(a, cwd) for a in seg[1:2] or ["."]):
            v = ("warn", "find -delete under projects/: confirm the match list first with the same find and no -delete.")
        else:
            v = ("allow", "")
        if v[0] == "deny":
            return v
        if v[0] == "warn":
            warn = v
    return warn or ("allow", "")


def main():
    try:
        d = json.load(sys.stdin)
        if d.get("tool_name") != "Bash":
            return 0
        verdict, reason = decide(d.get("tool_input", {}).get("command", ""), d.get("cwd", os.getcwd()), dict(os.environ))
        if verdict == "deny":
            print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse",
                  "permissionDecision": "deny", "permissionDecisionReason": reason}}))
        elif verdict == "warn":
            print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "additionalContext": reason}}))
    except Exception:
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
```
(If Phase 0 P2 showed PreToolUse `additionalContext` does not reach the model, change the warn branch to `"permissionDecision": "ask"` and update `test_find_delete_warns` expectations accordingly.)

- [ ] **Step 3: Run** `PY -m pytest tests/test_bash_guard.py -q` → all pass. Remove-the-guard check: comment out the `stash` branch in `_git`, re-run, confirm `test_stash_blocked_variants` fails, restore.
- [ ] **Step 4: Corpus replay.** `REPO/tools/replay_guard.py`: iterate every Bash `tool_use` in `TX/*.jsonl` and `TX/*/subagents/*.jsonl`, call `decide(command, entry_cwd, {"JOB_ID": "x"})`, print counts per verdict and the first 30 `deny`/`warn` commands. Read every printed hit; each must be a genuine hazard or be fixed in the guard (with a new test) before going live. Record counts in the commit message.
- [ ] **Step 5: Install.** `ln -s REPO/workspace-config/hooks/bash_guard.py ~/.claude/hooks/bash_guard.py`; add to `~/.claude/settings.json` via jq: `.hooks.PreToolUse = [{"matcher": "Bash", "hooks": [{"type": "command", "command": "python3 ${CLAUDE_CONFIG_DIR:-$HOME/.claude}/hooks/bash_guard.py", "timeout": 5}]}]`.
- [ ] **Step 6: Live check in a subagent.** Fresh session: `claude -p "Use a general-purpose subagent to run 'git -C REPO stash list' and then 'git -C REPO stash'. Report both outcomes." --max-turns 8` → first allowed, second denied with the reason text. Commit.

### Task 8: `context_nudge.py` — UserPromptSubmit nudge and effort hint

**Files:**
- Create: `REPO/workspace-config/hooks/context_nudge.py`, `REPO/tests/test_context_nudge.py`
- Modify: `~/.claude/settings.json` (add `UserPromptSubmit` hook), symlink into `~/.claude/hooks/`

**Interfaces:**
- Consumes: `read_tail_lines` pattern from `large-change-check.py` (copied, 12 lines — the hook must stay standalone).
- Produces: `last_context(transcript: Path) -> int | None`; `message(ctx: int | None, prompt: str, state: dict, threshold: int) -> tuple[str | None, dict]`.

- [ ] **Step 1: Failing tests.**
```python
# REPO/tests/test_context_nudge.py
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "workspace-config" / "hooks"))
import context_nudge as cn

def _tx(tmp_path, ctxs, partial=False):
    p = tmp_path / "t.jsonl"
    lines = [json.dumps({"type": "assistant", "message": {"id": f"m{i}", "usage": {"input_tokens": 1,
             "cache_creation_input_tokens": 0, "cache_read_input_tokens": c - 1}}}) for i, c in enumerate(ctxs)]
    p.write_text("\n".join(lines) + ("\n{\"type\": \"assist" if partial else "\n"))
    return p

def test_last_context_ignores_partial_line(tmp_path):
    assert cn.last_context(_tx(tmp_path, [100, 450_000], partial=True)) == 450_000

def test_no_usage_is_none(tmp_path):
    p = tmp_path / "t.jsonl"; p.write_text('{"type":"user"}\n')
    assert cn.last_context(p) is None

def test_nudge_once_per_band():
    msg, st = cn.message(410_000, "next", {}, 400_000)
    assert msg and "410k" in msg
    msg2, st = cn.message(450_000, "next", st, 400_000)
    assert msg2 is None
    msg3, st = cn.message(520_000, "next", st, 400_000)
    assert msg3 and "520k" in msg3

def test_below_threshold_silent():
    assert cn.message(120_000, "hi", {}, 400_000)[0] is None
    assert cn.message(None, "hi", {}, 400_000)[0] is None

def test_effort_hint_once():
    msg, st = cn.message(10_000, "let's brainstorm the architecture", {}, 400_000)
    assert msg and "/effort high" in msg
    msg2, _ = cn.message(10_000, "brainstorm more", st, 400_000)
    assert msg2 is None
```

- [ ] **Step 2: Implement.**
```python
#!/usr/bin/env python3
"""UserPromptSubmit hook: nudge when context is large; hint effort for heavy planning.

Threshold is declared workspace-specific (2026-10-14 corpus: calls above 500k carry
~69% of main-session cost) and overridable with CLAUDE_NUDGE_TOKENS. Fires once per
100k band per session. Any error exits 0 silently.
"""
import json, os, re, sys
from pathlib import Path

TAIL = 2_000_000
BAND = 100_000
HEAVY = re.compile(r"\b(brainstorm\w*|architect\w*|design doc|spec|implementation plan|writing-plans|plan the)\b", re.I)


def last_context(transcript: Path):
    with open(transcript, "rb") as f:
        f.seek(0, 2)
        size = f.tell()
        f.seek(max(0, size - TAIL))
        lines = f.read().decode("utf-8", errors="replace").split("\n")[1:]
    for line in reversed(lines):
        try:
            e = json.loads(line)
        except json.JSONDecodeError:
            continue
        u = (e.get("message") or {}).get("usage") if isinstance(e.get("message"), dict) else None
        if u:
            return u.get("input_tokens", 0) + u.get("cache_creation_input_tokens", 0) + u.get("cache_read_input_tokens", 0)
    return None


def message(ctx, prompt, state, threshold):
    parts, state = [], dict(state)
    if ctx is not None and ctx >= threshold:
        band = ctx // BAND
        if band > state.get("band", -1):
            state["band"] = band
            parts.append(f"Context is {ctx // 1000}k tokens. Tell the user in one line: before an unrelated task, "
                         f"`/clear`; otherwise `/compact <what to keep>`; hand long investigations to a seat.")
    if HEAVY.search(prompt or "") and not state.get("effort_hint"):
        state["effort_hint"] = True
        parts.append("This looks like heavy planning or brainstorming. The default effort is medium; tell the user "
                     "once that `/effort high` (or `ultrathink` in the prompt) gives deeper reasoning for it.")
    return (" ".join(parts) or None), state


def main():
    try:
        d = json.load(sys.stdin)
        tx = Path(d.get("transcript_path", ""))
        state_path = Path(d.get("scratchpad_dir") or "/tmp") / "context_nudge_state.json"
        state = json.loads(state_path.read_text()) if state_path.exists() else {}
        ctx = last_context(tx) if tx.is_file() else None
        msg, state = message(ctx, d.get("prompt", ""), state, int(os.environ.get("CLAUDE_NUDGE_TOKENS", 400_000)))
        state_path.write_text(json.dumps(state))
        if msg:
            print(json.dumps({"hookSpecificOutput": {"hookEventName": "UserPromptSubmit", "additionalContext": msg}}))
    except Exception:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
```
If Phase 0 P3 showed a skill's `effort:` persists for the session, replace the effort-hint text with "invoke the `deep-work` skill" and create `WS/.claude/skills/deep-work/SKILL.md` (`effort: high`, body: one line stating the session now runs at high effort for this task). Otherwise keep the hint as written.

- [ ] **Step 3: Run tests** → 5 passed. Remove-the-guard: change `band > state.get("band", -1)` to `True`, confirm `test_nudge_once_per_band` fails, restore.
- [ ] **Step 4: Install** (symlink + jq add `.hooks.UserPromptSubmit = [{"hooks": [{"type": "command", "command": "python3 ${CLAUDE_CONFIG_DIR:-$HOME/.claude}/hooks/context_nudge.py", "timeout": 5}]}]`). Live check: `CLAUDE_NUDGE_TOKENS=1000 claude -p "brainstorm a name for a test file" --max-turns 1` → response mentions `/compact` or `/clear` and `/effort high`. Commit.

### Task 9: `context_budget.py` — byte ceilings for our files

**Files:**
- Create: `REPO/tools/context_budget.py`, `REPO/tests/test_context_budget.py`
- Modify: `REPO/.claude/skills/workspace-audit/SKILL.md` (replace the "root CLAUDE.md under ~40 lines, each rule file under ~40" line with "run `tools/context_budget.py`; it fails above the ceilings in spec §5.1"; add "check vendored skills' `SOURCE.md` SHA against upstream HEAD")

**Interfaces:**
- Produces: `check(ws: Path, home: Path, memory: Path) -> list[str]` (violations, empty = pass); CLI exits 1 on any violation and prints a per-file byte table.

- [ ] **Step 1: Failing tests** (build a temp workspace from real files: copy `WS/.claude/rules/python.md` (path-scoped, must be excluded) and `WS/.claude/rules/scc.md` (unscoped, must be counted)).
```python
# REPO/tests/test_context_budget.py
import shutil, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import context_budget as cb

WS = Path("/projectnb/liu-scc/philipp")

def _ws(tmp_path, core_bytes=100):
    ws = tmp_path / "ws"; (ws / ".claude/rules").mkdir(parents=True); (ws / ".claude/skills/s1").mkdir(parents=True)
    shutil.copy(WS / ".claude/rules/python.md", ws / ".claude/rules/python.md")
    (ws / ".claude/rules/core.md").write_text("x" * core_bytes)
    (ws / "CLAUDE.md").write_text("root")
    (ws / ".claude/skills/s1/SKILL.md").write_text("---\nname: s1\ndescription: short\n---\nbody\n")
    home = tmp_path / "home"; home.mkdir(); (home / "CLAUDE.md").write_text("h")
    mem = tmp_path / "MEMORY.md"; mem.write_text("- [a](a.md) — b\n")
    return ws, home, mem

def test_pass(tmp_path):
    assert cb.check(*_ws(tmp_path)) == []

def test_core_over_ceiling(tmp_path):
    v = cb.check(*_ws(tmp_path, core_bytes=10_000))
    assert any("core.md" in x for x in v)

def test_path_scoped_rule_not_counted(tmp_path):
    ws, home, mem = _ws(tmp_path)
    assert "python.md" not in " ".join(cb.always_loaded(ws, home, mem))

def test_long_description_and_body(tmp_path):
    ws, home, mem = _ws(tmp_path)
    (ws / ".claude/skills/s1/SKILL.md").write_text("---\nname: s1\ndescription: " + "d" * 600 + "\n---\n" + "b" * 16_000)
    v = " ".join(cb.check(ws, home, mem))
    assert "description" in v and "body" in v

def test_disable_model_invocation_description_not_counted(tmp_path):
    ws, home, mem = _ws(tmp_path)
    (ws / ".claude/skills/s1/SKILL.md").write_text("---\nname: s1\ndescription: " + "d" * 600 + "\ndisable-model-invocation: true\n---\nb\n")
    assert cb.check(ws, home, mem) == []
```

- [ ] **Step 2: Implement.**
```python
#!/usr/bin/env python3
"""Byte ceilings for the always-loaded instruction text we own (spec §5.1).

Attribution tool only; the gate of record is tools/measure_context.py.
"""
import argparse, re, sys
from pathlib import Path

CEIL = {"home_claude": 1024, "root_claude": 3072, "core": 9216, "memory": 5120, "memory_entries": 50,
        "description": 512, "body": 15360}
FM = re.compile(r"\A---\n(.*?)\n---\n", re.S)


def _frontmatter(text: str) -> str:
    m = FM.match(text)
    return m.group(1) if m else ""


def _unscoped_rules(ws: Path):
    for p in sorted((ws / ".claude/rules").glob("*.md")):
        if "paths:" not in _frontmatter(p.read_text()):
            yield p


def _memory_loaded(mem: Path) -> str:
    lines = mem.read_text().splitlines(keepends=True)[:200]
    return "".join(lines)[:25_000]


def always_loaded(ws: Path, home: Path, mem: Path) -> dict[str, int]:
    out = {str(home / "CLAUDE.md"): len((home / "CLAUDE.md").read_bytes()),
           str(ws / "CLAUDE.md"): len((ws / "CLAUDE.md").read_bytes())}
    for p in _unscoped_rules(ws):
        out[str(p)] = len(p.read_bytes())
    out[str(mem)] = len(_memory_loaded(mem).encode())
    return out


def check(ws: Path, home: Path, mem: Path) -> list[str]:
    v = []
    sizes = always_loaded(ws, home, mem)
    if sizes[str(home / "CLAUDE.md")] > CEIL["home_claude"]:
        v.append(f"~/.claude/CLAUDE.md {sizes[str(home / 'CLAUDE.md')]} > {CEIL['home_claude']}")
    if sizes[str(ws / "CLAUDE.md")] > CEIL["root_claude"]:
        v.append(f"root CLAUDE.md {sizes[str(ws / 'CLAUDE.md')]} > {CEIL['root_claude']}")
    for p in _unscoped_rules(ws):
        n = len(p.read_bytes())
        if p.name != "core.md":
            v.append(f"unscoped rule {p.name} ({n} bytes): only core.md may be unscoped")
        elif n > CEIL["core"]:
            v.append(f"core.md {n} > {CEIL['core']}")
    if sizes[str(mem)] > CEIL["memory"]:
        v.append(f"MEMORY.md loaded part {sizes[str(mem)]} > {CEIL['memory']}")
    if sum(1 for ln in mem.read_text().splitlines() if ln.startswith("- [")) > CEIL["memory_entries"]:
        v.append("MEMORY.md has more than 50 entries")
    for sk in sorted((ws / ".claude/skills").glob("*/SKILL.md")):
        text = sk.read_text()
        fm = _frontmatter(text)
        body = len(text.encode()) - len(fm.encode())
        if body > CEIL["body"]:
            v.append(f"{sk.parent.name} body {body} > {CEIL['body']}")
        if re.search(r"^disable-model-invocation:\s*true", fm, re.M):
            continue
        m = re.search(r"^description:\s*(.*?)(?=^\w[\w-]*:|\Z)", fm, re.S | re.M)
        if m and len(m.group(1).strip().encode()) > CEIL["description"]:
            v.append(f"{sk.parent.name} description {len(m.group(1).strip().encode())} > {CEIL['description']}")
    return v


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--ws", default="/projectnb/liu-scc/philipp")
    ap.add_argument("--home", default=str(Path.home() / ".claude"))
    ap.add_argument("--memory", default=str(Path.home() / ".claude/projects/-projectnb-liu-scc-philipp/memory/MEMORY.md"))
    a = ap.parse_args(argv)
    ws, home, mem = Path(a.ws), Path(a.home), Path(a.memory)
    for k, n in always_loaded(ws, home, mem).items():
        print(f"{n:8d}  {k}")
    v = check(ws, home, mem)
    for x in v:
        print("OVER:", x)
    return 1 if v else 0


if __name__ == "__main__":
    sys.exit(main())
```
Note: the "only core.md may be unscoped" violation is expected to fire until Phase 2 retires the old files; that is the point — the live run before Phase 2 must print three `unscoped rule` lines (scc.md, subagent-dispatch.md, verification.md).
- [ ] **Step 3: Run tests** → 5 passed; live run prints the three expected violations. Commit.

### Task 10: Seats — frontmatter, env block, boundaries, new `implementer`

**Files:**
- Modify: all 11 files in `REPO/workspace-config/agents/`
- Create: `REPO/workspace-config/agents/implementer.md` + symlink `WS/.claude/agents/implementer.md`

**Interfaces:**
- Consumes: Phase 0 P1 (does `omitClaudeMd` drop MEMORY.md; does preload work without `Skill`), P4 (nested-repo discovery), P7 (seat yield).
- Produces: agent `implementer` used by `dispatch-brief` (Task 13) for SDD tasks instead of `general-purpose`.

- [ ] **Step 1: Env block** — insert this exact section into every seat body (before its Output section), and into `implementer.md`:
```markdown
## Environment

- Python: `/projectnb/liu-scc/philipp/.venv/bin/python` (or the project's own `.venv`).
- Scratch: the session scratchpad, under a folder named after you. Delete only files you
  created, by name.
- Output directories are read-only to you. Never create files under any `tests/` unless your
  task owns them. No tool's `--write` mode and no `cp` onto tracked files in a shared tree.
- Read past commits with `git show <commit>:<path>`; never `git stash` or `--work-tree`.
- Use `command grep` for absence claims (shell `grep` skips gitignored paths).
- Do not submit SGE jobs. Write the job spec (script, resources, expected artifact) into your
  report and stop.
- Run `git log -1 --format=%h` and `git status --porcelain` at the start and end of your work
  and report whether they moved.
```
- [ ] **Step 2: Frontmatter per seat** (spec §5.4 table). Add `omitClaudeMd: true` to every seat **only if P1 showed it drops the rules and the seat still received its preloaded skills**; otherwise leave it out and record why in the commit. Add `effort:` per table. Sonnet/Haiku seats (alignment-officer, docs-sync, inventory-auditor, pragmatism-officer, research-scout, scc-monitor) get this paragraph appended to their body:
```markdown
Keep working until the task is done or you are blocked; there is no one to answer a
question mid-run. Before you report, check your claims against the files or command
output you cite.
```
`skills:` preloads are added in Task 13 (the skills do not exist yet).
- [ ] **Step 3: Body edits.**
  - `critic-reviewer.md`: replace the reference to `.claude/rules/verification.md` with "the `verification-patterns` skill"; shorten item 7 to two lines; delete the docs-sync reminder in Output item 5 (moves to `wave-review`).
  - `anomaly-hunter.md`: delete the verbatim rtk block; point rule references at `scientific-evidence`.
  - `pragmatism-officer.md`: add section "Plan stage: the ladder" — for each proposed build item ask, in order, and stop at the first yes: does it need to exist; does it exist in this codebase; does the standard library do it; does a native platform feature do it; does an installed dependency do it; can it be one line. Report the rung per item. Fix its rule-file pointer.
  - `alignment-officer.md`: add boundary sentence "You check scope delivered against what was promised; drift between governance docs and reality belongs to docs-sync."
  - `docs-sync.md`: add boundary sentence "You check governance docs against reality; whether the work delivered its promised scope belongs to alignment-officer."
  - `inventory-auditor.md`: unchanged scope ("does it already exist?").
  - `research-scout.md`: `model: sonnet`, `effort: medium`; add "Search for current sources; prefer primary documentation over aggregators; give the URL for every claim."
  - `scc-monitor.md`: `effort: medium`; fix its rule-file pointer to `running-sge-jobs`.
- [ ] **Step 4: `implementer.md`** — exactly:
```markdown
---
name: implementer
description: Implements one task from an approved plan in this workspace — code, tests and a path-scoped commit — and reports evidence. Use for subagent-driven-development tasks instead of a general-purpose agent. Not for reviews (use the review seats) or open-ended research (use research-scout).
tools: Read, Edit, Write, Bash, Grep, Glob
model: sonnet
effort: medium
maxTurns: 60
---

You implement exactly one task from a plan. The brief names the files you own; touch
nothing else. If the fix belongs in a file you do not own, stop and report it as a task.

## How you work

1. Read the brief, then the files it names. If anything in the brief is wrong — a path, a
   signature, a count — stop and report it; do not reconcile toward the brief.
2. Tests in the brief are drafts: prove each can fail before trusting it.
3. Make the change, run the task's own tests and the linter on changed paths
   (`ruff check <paths>`). Run pytest only inside an SGE job (`$JOB_ID` set); otherwise put
   the job spec in your report.
4. Commit with explicit paths, then `git show --stat HEAD` and confirm only your files are in
   it. If not: `git reset --soft HEAD~1`, `git reset -- <other files>`, re-commit.

## Report

- What changed (files, one line each) and the commit hash.
- Evidence: the commands you ran and their real output (pass counts, exit codes).
- Anything in the brief you found to be wrong.
- Anything you did not do, and why.
```
- [ ] **Step 5: Symlink and verify.** `ln -s ../../architect-setup-overlapping-claude-copilot-useage/workspace-config/agents/implementer.md WS/.claude/agents/implementer.md`; if P4 showed nested-repo sessions miss workspace agents, also `ln -s` every agent into `~/.claude/agents/`. Verify each agent file parses: `for f in WS/.claude/agents/*.md; do python3 - "$f" <<'EOF'
import sys,re,yaml; t=open(sys.argv[1]).read(); m=re.match(r"\A---\n(.*?)\n---\n",t,re.S); d=yaml.safe_load(m.group(1)); print(sys.argv[1].split('/')[-1], d['name'], d.get('model'), d.get('effort'), d.get('omitClaudeMd'))
EOF
done` (12 lines). Commit.
- [ ] **Step 6: Review.** Dispatch `critic-reviewer` on the diff of this task with the `dispatch-brief` review template (it exists only as old rules text until Task 13 — use the template in `subagent-dispatch.md` "The review-dispatch template"). Fix Blocking/Important before Phase 2.

### Task 11: Phase 1 integration check

- [ ] Run `PY REPO/tools/context_budget.py` (expect only the three `unscoped rule` lines), `PY -m pytest REPO/tests -q` (all pass), and one ordinary interactive session for a day. Then `PY REPO/tools/measure_context.py --since <Phase-1 date>` and record main/seat first-call medians in `REPO/docs/superpowers/reviews/2026-10-14-restructure/phase1.md` beside the Phase 0 numbers, with n.

---

# Phase 2 — Rule migration (MOVE verbatim, rewrite only always-loaded text)

### Task 12: History copy, mapping file, traceability checker

**Files:**
- Create: `REPO/docs/history/rules-2026-10-14/{subagent-dispatch,verification,scc}.md` (verbatim copies)
- Create: `REPO/docs/history/rule-map.tsv`, `REPO/tools/rule_map.py`, `REPO/tests/test_rule_map.py`
- Produce: `REPO/docs/history/rule-index.md` (rendered)

**Interfaces:**
- Produces: `items(path: Path) -> list[Item]` with `Item(file, line, kind, title)` where kind ∈ {heading, bold, bullet}; `rule_map.tsv` columns `file<TAB>line<TAB>title<TAB>dest` where `dest` ∈ `core:<n>` | `skill:<name>` | `hook:<name>` | `history` | `deleted:<reason>`; CLI `rule_map.py extract|check|render`.

- [ ] **Step 1: Verbatim copies.** `cp` the three files from `REPO/workspace-config/rules/` into `REPO/docs/history/rules-2026-10-14/`; verify `cmp` exit 0 for each.
- [ ] **Step 2: Failing tests** (fixtures are the real history copies).
```python
# REPO/tests/test_rule_map.py
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import rule_map as rm

H = Path(__file__).resolve().parents[1] / "docs/history/rules-2026-10-14"

def test_extract_counts_are_stable():
    its = [i for f in ("subagent-dispatch.md", "verification.md", "scc.md") for i in rm.items(H / f)]
    assert len(its) == len({(i.file, i.line) for i in its})
    assert any(i.title.startswith("Never dispatch") for i in its)
    assert all(i.kind in ("heading", "bold", "bullet") for i in its)

def test_check_reports_unmapped_and_drift(tmp_path):
    its = rm.items(H / "scc.md")
    tsv = tmp_path / "m.tsv"
    first, second = its[0], its[1]
    tsv.write_text(f"{first.file}\t{first.line}\t{first.title}\tskill:running-sge-jobs\n"
                   f"{second.file}\t{second.line}\tWRONG TITLE\tskill:running-sge-jobs\n")
    errs = rm.check(H, tsv)
    assert any("unmapped" in e for e in errs)
    assert any("drift" in e for e in errs)

def test_bad_destination(tmp_path):
    i = rm.items(H / "scc.md")[0]
    tsv = tmp_path / "m.tsv"; tsv.write_text(f"{i.file}\t{i.line}\t{i.title}\tsomewhere\n")
    assert any("destination" in e for e in rm.check(H, tsv))
```
- [ ] **Step 3: Implement `rule_map.py`.**
```python
#!/usr/bin/env python3
"""Traceability for the 2026-10-14 rule migration: every item maps to exactly one home."""
import argparse, re, sys
from dataclasses import dataclass
from pathlib import Path

FILES = ("subagent-dispatch.md", "verification.md", "scc.md")
DEST = re.compile(r"^(core:\d+|skill:[a-z0-9-]+|hook:[a-z0-9_-]+|history|deleted:.+)$")


@dataclass(frozen=True)
class Item:
    file: str
    line: int
    kind: str
    title: str


def items(path: Path) -> list[Item]:
    out, fence = [], False
    for n, raw in enumerate(path.read_text().splitlines(), 1):
        if raw.startswith("`" * 3):  # code fence; written this way so it cannot close a markdown fence
            fence = not fence
            continue
        if fence:
            continue
        if raw.startswith("#"):
            out.append(Item(path.name, n, "heading", raw.lstrip("# ").strip()[:100]))
        elif re.match(r"^\*\*[^*]{6,}\*\*", raw):
            out.append(Item(path.name, n, "bold", raw.strip("* ")[:100]))
        elif re.match(r"^- \S", raw):
            out.append(Item(path.name, n, "bullet", raw[2:].strip()[:100]))
    return out


def _load(tsv: Path):
    rows = {}
    for line in tsv.read_text().splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        f, ln, title, dest = line.split("\t")
        rows[(f, int(ln))] = (title, dest)
    return rows


def check(hist: Path, tsv: Path) -> list[str]:
    errs, rows = [], _load(tsv)
    for f in FILES:
        for it in items(hist / f):
            r = rows.get((it.file, it.line))
            if r is None:
                errs.append(f"unmapped {it.file}:{it.line} {it.title[:60]}")
                continue
            if r[0] != it.title:
                errs.append(f"drift {it.file}:{it.line} recorded '{r[0][:40]}' now '{it.title[:40]}'")
            if not DEST.match(r[1]):
                errs.append(f"bad destination {it.file}:{it.line} '{r[1]}'")
    return errs


def render(hist: Path, tsv: Path) -> str:
    rows = _load(tsv)
    out = ["# Rule index — where each 2026-10-14 rule item now lives", "",
           "Old text is preserved verbatim in `rules-2026-10-14/`. Generated by `tools/rule_map.py render`; do not edit by hand.", "",
           "| old file:line | item | now in |", "|---|---|---|"]
    for (f, ln), (title, dest) in sorted(rows.items()):
        out.append(f"| `{f}:{ln}` | {title.replace('|', '/')} | {dest} |")
    return "\n".join(out) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["extract", "check", "render"])
    ap.add_argument("--hist", default=str(Path(__file__).resolve().parents[1] / "docs/history/rules-2026-10-14"))
    ap.add_argument("--map", default=str(Path(__file__).resolve().parents[1] / "docs/history/rule-map.tsv"))
    a = ap.parse_args(argv)
    hist, tsv = Path(a.hist), Path(a.map)
    if a.cmd == "extract":
        for f in FILES:
            for it in items(hist / f):
                print(f"{it.file}\t{it.line}\t{it.title}\tTODO")
        return 0
    if a.cmd == "check":
        errs = check(hist, tsv)
        for e in errs:
            print(e)
        print(f"{len(errs)} problem(s)")
        return 1 if errs else 0
    print(render(hist, tsv), end="")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```
Run tests → 3 pass.
- [ ] **Step 4: Author the map.** `PY tools/rule_map.py extract > docs/history/rule-map.tsv`, then replace every `TODO` using these assignment rules (an item inherits its parent heading's destination unless a rule below names it):

| Old section (file) | Destination |
|---|---|
| subagent-dispatch: "Never dispatch wait and report", "An instruction is not a backstop", "A follow-up note is a task", "Every relayed figure carries its column", "A dispatch's factual claims become code" (all bold sub-items), "Concurrent dispatches need declared file ownership", "Generate a task's brief at dispatch time", "Every dispatch carries the environment-invariants block", "The review-dispatch template" and its numbered items + Twelfth–Sixteenth, "Model and effort tiering" | `skill:dispatch-brief` |
| subagent-dispatch: "Wave-end review" and its bold sub-items (Self-verification, Minor-triage, rtk position, Unenumerated-objection, Domain-role, Anomaly-hunter, Inventory-auditor, Pragmatism-officer), "Run the fast gates per task", "A suite run needs a quiet tree", "One integration seat, mid-wave", "A pragmatism seat is the lever" | `skill:wave-review` |
| subagent-dispatch: "Plan review before implementation", "The Calibration block" (+ bullets, hard gate, self fact-check, unsettled questions), "Plan writing: inventory-auditor", "Escalate to a research/review wave", "Three-state is a plan-time checklist item", "Brainstorming: research-scout", "One external premise check" | `skill:plan-critique` |
| subagent-dispatch: "Release/publication gate: security-specialist" | `core:8` |
| subagent-dispatch: "`git stash` is a third shared-index hazard" and "Read a past commit with git show" | `hook:bash_guard` (stash, work-tree) and `core:6` for the read rule — split by item |
| verification: "The shapes this takes" + its bullets, positive-control corollary, same-code-path comparison, generated vs hand-written field, correct a false statement, four shape gates, capability claimed with no call path, before overwriting, stage that filters its input, binds the controller's counts, command grep then parser, number in a comment, fix copied from a sibling, RED-confirmed vs safe, RED proof runs current tree, claims-to-be-generated doc, gate that knows and doesn't print, dead knob default, boundary test interval, "A plan's own tests and fixtures are suspects", "Execute the plan's own claims", "Watch for the asymmetry", "Reporting" | `skill:verification-patterns` |
| verification: rtk section items that are rtk-specific (allowlist, head/tail bug, unparseable config, escape hatches, exit codes, measurement paragraph) | `deleted: rtk hook retired (DECISION-026)` |
| verification: the three general lessons inside the rtk section ("Match the command as invoked", "A positive control built from a convenient fixture", "Check the aggregate's distribution") | `skill:verification-patterns` |
| verification: "`grep` is a shell function here" and its two cautions | `core:3` (the rule) — the cautions `skill:verification-patterns` |
| verification: "A three-state value is typed at introduction" | `core:2` |
| verification: "An absence is only as good as the instrument's headroom" and all its bullets, "Attack the results that CONFIRMED", "When a tool writes two reports" and its bullets | `skill:scientific-evidence` |
| scc.md: everything | `skill:running-sge-jobs`, except "Login node" and the "caller owns qsub / never dispatch wait-and-report" bullet → `core:5` |

Run `PY tools/rule_map.py check` until it prints `0 problem(s)`. Then `PY tools/rule_map.py render > docs/history/rule-index.md`. Commit the history copies, map, index, tool and tests.

### Task 13: Assemble the seven skills (verbatim bodies) and wire preloads

**Files:**
- Create: `REPO/tools/build_skills.py`, `REPO/skill-headers/<name>.md` (7 files: frontmatter + intro only)
- Create (generated): `REPO/.claude/skills/<name>/SKILL.md` and `reference/*.md` where a body exceeds 15 KB
- Create: symlinks `WS/.claude/skills/<name>` → `REPO/.claude/skills/<name>` (and into `~/.claude/skills/` if P4 required it)
- Modify: seat frontmatter `skills:` lines

**Interfaces:**
- Consumes: `rule_map.tsv`, `items()` from Task 12.
- Produces: `build(name) -> str` = header + verbatim source lines for every item whose `dest == skill:<name>`, each item's span running from its line to the line before the next item in the same file; sections in old-file order.

- [ ] **Step 1: Headers** (frontmatter + ≤ 6-line intro; descriptions ≤ 512 bytes). Exact frontmatter:

| name | description | extra |
|---|---|---|
| `dispatch-brief` | `Builds the brief for an implementer or review seat in this workspace: verified claims or UNVERIFIED labels, file ownership, environment block, job-spec handoff, and the review template (findings file first, objection slot). Use when dispatching an implementer or a review seat. Not for deciding which seats run at wave end (wave-review) or plan review (plan-critique).` | — |
| `wave-review` | `Runs the wave-end review in this workspace: which seats to dispatch for this kind of wave, in batches under the concurrency cap, with pragmatism triage last and a ran/not-ran list. Use at the end of a wave, before finishing a branch, or when asked for /wave-review. Briefs for each seat come from dispatch-brief.` | `effort: high` |
| `plan-critique` | `Reviews an architectural plan before Task 1: Calibration block and its hard gate, plan preflight that executes the plan's claims, critique-wave sizing, three-state check, and the escalation wave after repeated failed fixes. Use before starting an approved plan, when asked for /plan-critique, or after a third failed fix. Not for code review of finished work (wave-review).` | `effort: high` |
| `verification-patterns` | `Catalogue of verification failures seen in this workspace — stale artifacts, gates that cannot fail, vacuous tests, counts taken with grep, fixes that are effective but unsafe, claims and docs that decay. Use when implementing or reviewing a fix, a test, a gate or a generated document. Domain-science evidence (absences, anomalies) is in scientific-evidence.` | — |
| `scientific-evidence` | `Rules for scientific claims from pipelines: absence only within the instrument's headroom in that stratum, both branches when biology and data disagree, attacking confirming results, composition effects, tools whose reports are filtered differently. Use when a result says something is absent, surprising, confirmed, or about to be written down as settled.` | — |
| `running-sge-jobs` | `How to submit, wait for and verify BU SCC SGE jobs for project liu-scc: resource defaults, the backgrounded wait loop with a deadline, reading appended logs, artifact checks, storage limits. Use when writing or submitting a qsub script, waiting on a job, or reading a job log. Diagnosing a failed job: scc-monitor.` | — |
| `completion-check` | `Finds unfinished or non-working code: stub scan, unused-code lint, import-graph reachability, and running the changed entry point on a real fixture. Use when asked whether work is finished or actually runs, or via /completion-check. Correctness review of logic is critic-reviewer.` | (Task 17 builds the body) |

- [ ] **Step 2: `build_skills.py`** — reads the map, concatenates spans verbatim under a `## <title>` line per top-level section, writes `SKILL.md`; if the body exceeds 15,360 bytes, keeps the first sections up to 12 KB in `SKILL.md` and writes the rest to `reference/<section-slug>.md`, adding one `See [reference/<slug>.md](reference/<slug>.md)` line per moved section. Test (`tests/test_build_skills.py`): for every skill, the concatenation of all `SKILL.md` + reference bodies (minus header and "See" lines) equals the concatenation of the mapped spans byte-for-byte; and every mapped span appears in exactly one skill.
- [ ] **Step 3: Fix the scc.md wait-loop defect inside `running-sge-jobs` only** (the one sanctioned content edit to a moved body; old text stays in history): the listing-form loop gains a deadline — `deadline=$(( $(date +%s) + H_RT_SECONDS + 3600 )); absent=0; while [ $absent -lt 3 ]; do [ $(date +%s) -ge $deadline ] && { echo "TIMEOUT: check qstat -u phitro (Eqw/hqw?)"; break; }; qstat -u phitro 2>/dev/null | grep -q "^ *<jobid> " && absent=0 || absent=$((absent+1)); sleep 45; done`. Note the edit in the commit message.
- [ ] **Step 4: Preloads.** critic-reviewer `skills: [verification-patterns, completion-check]` (completion-check added after Task 17); domain-reviewer, anomaly-hunter, figure-auditor `skills: [scientific-evidence]`; scc-monitor `skills: [running-sge-jobs]`; implementer `skills: [dispatch-brief, verification-patterns]`.
- [ ] **Step 5: Verify** `PY tools/context_budget.py` (skills within ceilings), tests pass, and a fresh `claude -p "List skills whose names start with dispatch, wave, plan-c, verification, scientific, running-sge" --max-turns 1` lists all six. Commit.

### Task 14: Rewrite `core.md` (always-loaded) with old-beside-new review

**Files:**
- Create: `REPO/workspace-config/rules/core.md` + symlink `WS/.claude/rules/core.md`

- [ ] **Step 1: Write exactly** (≤ 9,216 bytes):
```markdown
# Core rules

Detail and history for every line: `architect-setup-overlapping-claude-copilot-useage/docs/history/rule-index.md`.

## Evidence
1. An artifact on disk is evidence; an exit code or a narrative is not. Check the artifact's
   mtime against your change. A gate counts only after you have seen it fail.
2. Unknown is its own typed state — an enum or a dedicated type, never `bool | None`. When you
   introduce one, list every consumer (`command grep` across src, tests, renderers, exporters).
3. For absence claims use `command grep` — the shell `grep` here skips gitignored paths. Count
   with a parser (table rows, AST nodes), not with grep. An absence is only as good as the
   instrument's headroom in that stratum.
4. A relayed number carries its n, its column and its artifact. A number from a plan or a
   subagent report is unverified until you re-derive it.

## SGE and shared trees
5. Run pytest and anything long only inside an SGE job (`$JOB_ID` set). The caller owns every
   `qsub`: a subagent writes a job spec and stops; the caller waits in one backgrounded loop
   with a deadline and verifies the output artifact, not the exit status.
6. Commit with explicit paths, then run `git show --stat` and confirm only your files are in
   it. Read past commits with `git show <commit>:<path>`.
7. Put scratch in the session scratchpad, in a folder named for the agent. Delete only files you
   created, by name. Output directories are read-only to reviewers. Never create files under
   `tests/` outside your own task. No tool's `--write` mode and no `cp` onto tracked files in a
   shared tree.

## When to load which process
8. - Dispatching an implementer or a review seat → skill `dispatch-brief`.
   - Before Task 1 of an architectural plan, or after a third failed fix → `plan-critique`.
   - End of a wave → `wave-review`. Self-verification is not independent review.
   - Implementing or reviewing a fix, test, gate or generated doc → `verification-patterns`.
   - A result that says absent, surprising or settled → `scientific-evidence`.
   - A release or publication → dispatch security-specialist.
   - A new project or a reframing → one external premise check on the target itself; before any
     research dispatch, `command grep` `.superpowers/` for prior work.

## Scope and context
9. Deliver what was asked. Change only what the task needs and match the surrounding style.
   Report unrelated dead code instead of deleting it. A fix that belongs in a file you do not
   own becomes a dispatched task, not a comment.
10. Clear context between unrelated tasks; compact deliberately with an instruction about what to
    keep; hand long investigations to a seat instead of reading them into this session.

## Governance
11. `ARCHITECTURE.md`, `DECISIONS.md`, any `CLAUDE.md`, `PROJECT_STATE.md`, pushes, GitHub
    issues and CI changes need the owner's explicit approval.
```
- [ ] **Step 2: Old-beside-new review.** Dispatch `domain-reviewer` (role: agent-harness / prompt-engineering specialist) with `core.md`, `rule-index.md` rows whose dest is `core:*`, and the old text at those lines. Question: does any core line say something the old text did not, or lose a condition the old text had? Findings file first. Fix every Blocking/Important.
- [ ] **Step 3:** `PY tools/context_budget.py` → `core.md` within ceiling (the three old files still trigger "unscoped" until Task 16). Commit.

### Task 15: Live pointer updates

**Files (each verified by `command grep -n "verification.md\|subagent-dispatch.md\|rules/scc.md"` before and after):**
- `REPO/workspace-config/agents/{critic-reviewer,pragmatism-officer,scc-monitor,anomaly-hunter}.md` (if any remain after Task 10)
- `REPO/workspace-config/rules/{python,shell}.md`
- `WS/CLAUDE.md` (remove the temporary "Before you finish" pointers from Task 6)
- `REPO/CLAUDE.md`, `REPO/.claude/skills/workspace-audit/SKILL.md`
- **[APPROVAL, project repos]** `WS/projects/EnzymeFinder/.claude/CLAUDE.md:10-11`, `WS/projects/EnzymeFinder/.claude/skills/running-quality-gates/SKILL.md`, `WS/projects/EanB_homologue_search/CLAUDE.md:65`

- [ ] Replace each pointer with the skill name (or `docs/history/rule-index.md` for "see the history"). Project-repo edits are committed in their own repos, path-scoped, after owner approval. Historical citations elsewhere stay (spec D1). Final `command grep -rn "rules/verification.md\|rules/subagent-dispatch.md" WS/.claude WS/CLAUDE.md REPO/workspace-config REPO/.claude` → no hits.

### Task 16: After-arm evals, then retire the old rule files

- [ ] **Step 1:** Quiet tree (no uncommitted changes in `REPO`, no commits until the job returns). Submit `qsub -v ARM=after,K=5 REPO/evals/run_evals.sh`; wait (backgrounded listing loop, deadline 7 h); verify 45 run files; grade to `evals/results-after.md`.
- [ ] **Step 2: Gate.** For every scenario: `after ≥ before − 1`. If any scenario fails the gate, stop; the fix is a description/trigger change or a line back into `core.md`, then re-run that scenario only (k = 5).
- [ ] **Step 3: Retire.** Remove the three symlinks `WS/.claude/rules/{subagent-dispatch,verification,scc}.md`; `git rm` the three files from `REPO/workspace-config/rules/` (their text lives in `docs/history/rules-2026-10-14/`). `PY tools/context_budget.py` → exit 0. `PY tools/rule_map.py check` → 0 problems.
- [ ] **Step 4:** After one week of normal use: `PY tools/measure_context.py --since <retire date>`; record first-call medians per type beside Phase 0 in `phase2.md`.

---

# Phase 3 — Debloat seat and completion tooling

### Task 17: `completion-check` body and scripts

**Files:**
- Create: `REPO/.claude/skills/completion-check/SKILL.md` (header from Task 13 + body below), `REPO/.claude/skills/completion-check/scripts/stub_scan.py`, `REPO/.claude/skills/completion-check/scripts/reach.py`, `REPO/tests/test_stub_scan.py`

- [ ] **Step 1: Failing test for `stub_scan.py`.**
```python
# REPO/tests/test_stub_scan.py
import subprocess, sys
from pathlib import Path
S = Path(__file__).resolve().parents[1] / ".claude/skills/completion-check/scripts/stub_scan.py"

def run(tmp_path, code):
    f = tmp_path / "m.py"; f.write_text(code)
    return subprocess.run([sys.executable, str(S), str(f)], capture_output=True, text=True)

def test_flags_stubs(tmp_path):
    r = run(tmp_path, "def a():\n    pass\n\ndef b():\n    raise NotImplementedError\n\n"
                      "def c():\n    try:\n        return x()\n    except Exception:\n        return []\n# TODO: wire\n")
    assert r.returncode == 1
    for tag in ("empty-body", "not-implemented", "swallowed-except", "todo"):
        assert tag in r.stdout

def test_clean_file_passes(tmp_path):
    r = run(tmp_path, "def a(x):\n    return x + 1\n")
    assert r.returncode == 0 and r.stdout.strip() == ""

def test_abstract_and_protocol_not_flagged(tmp_path):
    r = run(tmp_path, "from abc import abstractmethod\nclass A:\n    @abstractmethod\n    def f(self):\n        ...\n")
    assert r.returncode == 0
```
- [ ] **Step 2: Implement `stub_scan.py`.**
```python
#!/usr/bin/env python3
"""Flag unfinished code: empty bodies, NotImplementedError, swallowed excepts returning empty, TODO/FIXME/shortcut."""
import ast, re, sys
from pathlib import Path

MARK = re.compile(r"#\s*(TODO|FIXME|XXX|shortcut:)", re.I)


def _empty(body):
    """True when a body is only `pass`, `...` and/or a docstring."""
    def trivial(s):
        if isinstance(s, ast.Pass):
            return True
        return (isinstance(s, ast.Expr) and isinstance(s.value, ast.Constant)
                and (s.value.value is Ellipsis or isinstance(s.value.value, str)))
    return all(trivial(s) for s in body)


def scan(path: Path):
    src = path.read_text(errors="replace")
    out = []
    for n, line in enumerate(src.splitlines(), 1):
        if MARK.search(line):
            out.append((n, "todo", line.strip()[:80]))
    try:
        tree = ast.parse(src)
    except SyntaxError as e:
        return [(e.lineno or 0, "syntax-error", str(e))]
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            decos = {getattr(d, "id", getattr(d, "attr", "")) for d in node.decorator_list}
            if "abstractmethod" in decos or "overload" in decos:
                continue
            if _empty(node.body):
                out.append((node.lineno, "empty-body", node.name))
            for s in ast.walk(node):
                if isinstance(s, ast.Raise) and "NotImplementedError" in ast.unparse(s):
                    out.append((s.lineno, "not-implemented", node.name))
        if isinstance(node, ast.ExceptHandler):
            for s in node.body:
                if isinstance(s, ast.Return) and s.value is not None and ast.unparse(s.value) in ("[]", "{}", "None", "''", '""', "()"):
                    out.append((s.lineno, "swallowed-except", ast.unparse(s)))
                if isinstance(s, ast.Pass):
                    out.append((s.lineno, "swallowed-except", "pass"))
    return out


def main(argv):
    hits = 0
    for a in argv:
        for p in ([Path(a)] if Path(a).is_file() else sorted(Path(a).rglob("*.py"))):
            for n, tag, what in scan(p):
                print(f"{p}:{n}: {tag}: {what}")
                hits += 1
    return 1 if hits else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
```
Run tests → 3 pass.
- [ ] **Step 3: `reach.py`** — a wrapper that imports `WS/projects/EnzymeFinder/scripts/audit_reachability.py` by path, overrides its module globals `SRC_ROOT`, `PACKAGE_ROOT`, `PACKAGE_NAME` from `--src` and `--package`, then calls its entry function. First read `audit_reachability.py` to confirm the entry function name and that no other EnzymeFinder-specific constant is read at import time (`command grep -n "^[A-Z_]* = " audit_reachability.py`). Positive control: `reach.py --src WS/projects/EnzymeFinder/src --package enzymefinder` must print the same summary as running `audit_reachability.py` directly (diff = empty). If other constants (entry points, qsub surfaces) are EnzymeFinder-specific and cannot be overridden cleanly, stop and record it in `phase3.md` as a deferred item instead of forking the 999-line script.
- [ ] **Step 4: SKILL.md body** (after the Task 13 header):
```markdown
## Run, in this order
1. `python3 scripts/stub_scan.py <changed files or package dir>` — every hit is either finished
   or reported as unfinished with a reason.
2. `ruff check --select F401,F811,F841,ARG <changed paths>` — unused imports, redefinitions,
   dead assignments and arguments. A dead variable can mean a feature that silently does nothing.
3. `python3 scripts/reach.py --src <repo>/src --package <name>` — modules unreachable from any
   entry point. "It has tests" is not reachability.
4. Run the changed entry point on a real, downsampled input (never a hand-typed row) and check
   that the expected artifact exists and is non-empty. Inside an SGE job only, for anything
   heavier than a few seconds.
5. Silent failures: for every `except` in the diff, does the caller learn that it failed?
   A fallback that returns an empty result must be distinguishable from a genuine empty result.

## Report
List each check, the command, and its result. "Finished" requires all five; otherwise say
which check failed and what is unfinished.
```
- [ ] **Step 5:** Add `completion-check` to critic-reviewer and implementer `skills:`. Commit.

### Task 18: `lean-critic` seat and the thermo-nuclear override

**Files:**
- Create: `REPO/workspace-config/agents/lean-critic.md` + symlink
- Modify: `REPO/.claude/skills/thermo-nuclear-code-quality-review/SKILL.md` (frontmatter only), `SOURCE.md`

- [ ] **Step 1: Override.** Delete the `disable-model-invocation: true` line from the vendored frontmatter; append to `SOURCE.md`: "Local change 2026-10-14: removed `disable-model-invocation: true` so the lean-critic seat can preload it (preloading draws only from model-invocable skills). Body unchanged." Verify `diff <(git -C REPO show 488885b:.claude/skills/thermo-nuclear-code-quality-review/SKILL.md | sed 1,6d) <(sed 1,5d REPO/.claude/skills/thermo-nuclear-code-quality-review/SKILL.md)` → empty (body identical).
- [ ] **Step 2: `lean-critic.md`** — exactly:
```markdown
---
name: lean-critic
description: Debloat review of a finished diff — finds code that can be deleted, collapsed or replaced by something that already exists, without weakening correctness. Use on demand after a feature lands or when a change feels heavy. Not a correctness review (critic-reviewer) and not a plan-stage check (pragmatism-officer's ladder).
tools: Read, Grep, Glob, Bash, Skill
model: sonnet
effort: medium
maxTurns: 35
skills: [thermo-nuclear-code-quality-review, verification-patterns]
---

You review a diff for what can be removed. Apply the thermo-nuclear rubric you were given,
and the ladder: does it need to exist; does the codebase already have it; does the standard
library, a native feature or an installed dependency do it; can it be one line. You may run
`/ponytail-review` on the same diff and fold its cuts into yours.

## What you never cut
Trust-boundary validation, data-loss handling, security checks, accessibility, explicit
third-state handling, tests that can fail, and artifact or provenance checks. Smaller is not
the goal; less that can go wrong is.

## Report
For each finding: file:line, what to delete or collapse, what replaces it, the line delta,
and why behaviour is unchanged. End with the total line delta and the strongest objection to
your own cuts.
```
(append the Task 10 env block and the Sonnet keep-working paragraph)
- [ ] **Step 3:** If P1 showed preload works only with `Skill` in tools or never, record and adapt (`Skill` is already in `tools`). Live check: dispatch lean-critic on one small recent EnzymeFinder diff; confirm the report cites thermo-nuclear questions (preload worked) and contains no cut from the "never cut" list. Commit.

### Task 19: Owner recommendations note (account-side) and Q3

- [ ] Write `REPO/docs/superpowers/reviews/2026-10-14-restructure/owner-actions.md`: (1) restore parked plugins — `for p in example-skills@anthropic-agent-skills research-skills@claude-code-skills planning-with-files@planning-with-files; do claude plugin install $p --scope user && claude plugin disable $p --scope user; done`; (2) disable `humanize-kit` and the character voices in `writing-skills` on the desktop/claude.ai side; paper workflow = `science-writing-edit` → `humanizer` → numbers-and-citations diff; (3) Q3 pr-review-toolkit: keep or disable, with the measured ≈ 2,035 tokens/session and whether `completion-check` now covers `silent-failure-hunter`; (4) Q5 connectors if P5 showed double-sending. Commit.

### Task 20: Wave-end review of the restructure

- [ ] Run `/wave-review` (the new skill) on the whole restructure: critic-reviewer, alignment-officer (against the spec), docs-sync (ARCHITECTURE.md / DECISIONS.md / both CLAUDE.md files), domain-reviewer (agent-harness role), anomaly-hunter (attack the Phase 2 measurement), pragmatism-officer last — in batches of 2. **[APPROVAL]** `ARCHITECTURE.md` update with the new layer table from spec §5.1 after the review.

---

## Self-review notes (controller, 2026-10-14)

- Spec coverage: §5.1 → T5, T6, T9, T14; §5.2 → T14; §5.3 → T12, T13, T17; §5.4 → T10, T18; §5.5 → T5, T7, T8; §5.6 → T4, T5, T6, T15, T19; §5.7 → T1, T9; §5.8 → T14; §5.9 → T10 (ladder), T18, T19; §7 → T3, T12, T16; §8 phases → structure; §10 deferred items stay deferred; §11 Q1 = C → T8, Q2 → T5 + T8 + skill `effort: high`, Q4 → T6.
- Known soft spots, labelled: P1–P4 decide several branches (omitClaudeMd, warn mechanism, effort mechanism, nested discovery); every branch is written into the owning task. Eval regexes are coarse; both arms use the same graders, so the comparison is fair even where the absolute rate is not meaningful.
- Cost: 90 eval runs (2 arms × 9 scenarios × k = 5) in plan mode, plus ~8 review dispatches across the plan.
- **Plan preflight executed 2026-10-14** (scratchpad copy, inside SGE job 8090063): every Python block extracted and run — 30 tests passed across measure_context, grade, bash_guard, context_nudge, context_budget, rule_map, stub_scan, with the fixture built by `make_fixture.sh` from a real subagent transcript (N = 11 calls, first context 49,787). Remove-the-guard: disabling the stash branch turns `test_stash_blocked_variants` red; disabling the band check turns `test_nudge_once_per_band` red. Live `context_budget.py`: the three unscoped rule files and the MEMORY.md size/entry count are flagged, exit 1, as expected before Phases 1–2. Live `measure_context.py --since 2026-10-07`: general-purpose 63.6 % of context (n = 123) with **287 calls above 500k context** — long-context cost is not only a main-session issue; Task 10's implementer seat and Task 8's nudge both bear on it. One defect found and fixed by the preflight: `rule_map.py` contained a literal triple backtick that closed the plan's own markdown fence.
