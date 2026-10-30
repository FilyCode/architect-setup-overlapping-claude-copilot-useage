#!/usr/bin/env python3
"""Assemble the workspace skills from the 2026-10-14 rule files, verbatim (plan Task 13).

Each mapped item's span (its line up to the next item in the same file) is copied unchanged
into the skill named by `skill:<name>` in docs/history/rule-map.tsv. A skill whose moved text
exceeds PART bytes is split into reference/part-N.md files, listed in SKILL.md before the moved
text. `body_text()` reverses the assembly; the tests use it to prove the bodies are verbatim.
Provenance (source file:line of each span) is written to `<skill>/provenance.tsv`, a sidecar that
SKILL.md does not reference, so it costs no context; the loaded files carry no provenance comments.
"""
import argparse
import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import rule_map as rm  # noqa: E402

SKILLS = ("dispatch-brief", "wave-review", "plan-critique", "verification-patterns",
          "scientific-evidence", "running-sge-jobs")
PART = 12_000
PART_BY_SKILL = {"dispatch-brief": 11_400}  # header grew with retro rules; keeps the body under its ceiling
OLD_NAMES = ("Old file names in the moved text are retired: `subagent-dispatch.md` is now the skills\n"
             "`dispatch-brief`, `wave-review` and `plan-critique`; `verification.md` is `verification-patterns`\n"
             "and `scientific-evidence`; `scc.md` is `running-sge-jobs`.\n\n")
MARK = "<!-- BEGIN MOVED TEXT (verbatim; do not edit — source: docs/history/rules-2026-10-14) -->\n"
PROVENANCE = "provenance.tsv"


@dataclass(frozen=True)
class Span:
    file: str
    line: int
    dest: str
    title: str
    text: str


def spans(hist: Path, tsv: Path) -> list[Span]:
    dests = {(f, ln): d for (f, ln), (_, d) in rm._load(tsv).items()}
    out = []
    for f in rm.FILES:
        lines = (hist / f).read_text().splitlines(keepends=True)
        its = rm.items(hist / f)
        for i, it in enumerate(its):
            end = its[i + 1].line - 1 if i + 1 < len(its) else len(lines)
            out.append(Span(f, it.line, dests[(f, it.line)], it.title, "".join(lines[it.line - 1:end])))
    return out


def _chunks(items: list[Span], limit: int = PART) -> list[list[Span]]:
    parts, cur, size = [], [], 0
    for s in items:
        if cur and size + len(s.text.encode()) > limit:
            parts.append(cur)
            cur, size = [], 0
        cur.append(s)
        size += len(s.text.encode())
    if cur:
        parts.append(cur)
    return parts


def _render(items: list[Span]) -> str:
    return "".join(s.text for s in items)


def _prov_rows(items: list[Span], dest: str) -> str:
    return "".join(f"{s.file}:{s.line}\t{dest}\t{s.title[:80]}\n" for s in items)


def build(name: str, hist: Path, tsv: Path, headers: Path, out: Path) -> None:
    mine = [s for s in spans(hist, tsv) if s.dest == f"skill:{name}"]
    parts = _chunks(mine, PART_BY_SKILL.get(name, PART))
    d = out / name
    (d / "reference").mkdir(parents=True, exist_ok=True)
    for old in (d / "reference").glob("part-*.md"):
        old.unlink()
    prov = _prov_rows(parts[0] if parts else [], "SKILL.md")
    header = (headers / f"{name}.md").read_text().rstrip("\n") + "\n"
    if len(parts) > 1:
        header += "\n## Reference files (read the one you need)\n\n"
        for n, part in enumerate(parts[1:], 2):
            titles = "; ".join(s.title[:60] for s in part if s.title)[:400]
            header += f"- See [reference/part-{n}.md](reference/part-{n}.md) — {titles}\n"
            (d / "reference" / f"part-{n}.md").write_text(
                f"# {name} — reference part {n}\n\n{OLD_NAMES}{MARK}{_render(part)}")
            prov += _prov_rows(part, f"reference/part-{n}.md")
    else:
        (d / "reference").rmdir()
    (d / "SKILL.md").write_text(f"{header}\n{OLD_NAMES}{MARK}{_render(parts[0] if parts else [])}")
    (d / PROVENANCE).write_text("source\tfile\ttitle\n" + prov)


def build_all(hist: Path, tsv: Path, headers: Path, out: Path) -> None:
    for name in SKILLS:
        build(name, hist, tsv, headers, out)


def _moved(path: Path) -> str:
    return path.read_text().split(MARK, 1)[1]


def body_text(skill_dir: Path) -> str:
    """Concatenated moved text of SKILL.md and its reference parts, in order."""
    body = _moved(skill_dir / "SKILL.md")
    ref = skill_dir / "reference"
    if ref.exists():
        for p in sorted(ref.glob("part-*.md"), key=lambda p: int(p.stem.split("-")[1])):
            body += _moved(p)
    return body


def main(argv=None):
    root = Path(__file__).resolve().parents[1]
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default=str(root / ".claude/skills"))
    a = ap.parse_args(argv)
    build_all(root / "docs/history/rules-2026-10-14", root / "docs/history/rule-map.tsv",
              root / "skill-headers", Path(a.out))
    for name in SKILLS:
        files = [Path(a.out) / name / "SKILL.md"] + sorted((Path(a.out) / name).glob("reference/*.md"))
        print(name, [f"{f.name}:{len(f.read_bytes())}" for f in files])
    return 0


if __name__ == "__main__":
    sys.exit(main())
