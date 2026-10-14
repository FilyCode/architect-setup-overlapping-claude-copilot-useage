#!/usr/bin/env python3
"""Byte ceilings for the always-loaded instruction text we own (spec §5.1).

Attribution tool only; the gate of record is tools/measure_context.py.
"""
import argparse
import re
import sys
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
