#!/usr/bin/env python3
"""Disposition map for the skill consolidation (plan 2026-11-18, T1).

`build <skill>` writes docs/history/consolidation-2026-11/<skill>.tsv with columns
id, source, text, disposition (disposition empty). Rows: every docs/history/rule-map.tsv row
whose destination is `skill:<skill>` (source `<file>:<line>`, text = title) plus every sentence of
the header `git show 36f2a5e:skill-headers/<skill>.md` body (source `header@36f2a5e:<n>`).
`build` refuses to overwrite a TSV that has any filled disposition.

`--check [skill...]` exits 1 on: a skeleton row absent from the TSV; an empty or unknown
disposition; a `dropped` row without `: <reason>`; a `kept`/`merged into` row naming a section
(a markdown heading's text, case-insensitive, `*` and backticks ignored) that is not a heading in
.claude/skills/<skill>/SKILL.md or its reference/*.md; a `kept` row whose key tokens are not all
present in that section's text. Allowed dispositions: `kept <section>` | `merged into <section>`
| `dropped: <reason>`. Prints dropped counts per skill.

Key tokens of a row's text: lowercase alphanumeric/`_-` words of 4+ chars that are not in STOP,
de-duplicated; the 3 longest (ties: first seen). A kept row passes when each occurs as a
substring of the lowercased section text (heading to the next heading of the same or higher level).
`merged into` rows are only checked for the section existing (the text was reworded).
"""
import argparse
import csv
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PIN = "36f2a5e"
OUT = "docs/history/consolidation-2026-11"
COLS = ["id", "source", "text", "disposition"]
STOP = set("""this that with from have will when which what then than they them their there these those
into onto over also only each every must should would could does done been being were your about after
before while where other such more most some same just like make made only both either never always
without within because rather still once even much""".split())
HEAD = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", s.replace("*", "").replace("`", "")).strip().lower()


def key_tokens(text: str, n: int = 3) -> list[str]:
    """The n longest distinct non-stopword tokens of text (see module docstring)."""
    words = []
    for w in re.findall(r"[a-z0-9][a-z0-9_\-]*", _norm(text)):
        w = w.strip("-_")
        if len(w) >= 4 and w not in STOP and w not in words:
            words.append(w)
    return sorted(words, key=lambda w: -len(w))[:n]  # sorted is stable: ties keep first-seen order


def sentences(body: str) -> list[str]:
    out = []
    for block in re.split(r"\n\s*\n", body):
        block = re.sub(r"\s+", " ", block).strip()
        if not block:
            continue
        out += [s.strip() for s in re.split(r"(?<=[.!?:;])\s+(?=[A-Z`*\[(\-\d])", block) if s.strip()]
    return out


def header_sentences(skill: str) -> list[str]:
    raw = subprocess.run(["git", "-C", str(REPO), "show", f"{PIN}:skill-headers/{skill}.md"],
                         capture_output=True, text=True, check=True).stdout
    m = re.match(r"\A---\n.*?\n---\n", raw, re.S)
    return sentences(raw[m.end():] if m else raw)


def skeleton(skill: str) -> list[dict]:
    rows = []
    with open(REPO / "docs/history/rule-map.tsv", newline="") as f:
        for r in csv.reader((ln for ln in f if not ln.startswith("#")), delimiter="\t"):
            if len(r) >= 4 and r[3] == f"skill:{skill}":
                rows.append({"source": f"{r[0]}:{r[1]}", "text": r[2]})
    for i, s in enumerate(header_sentences(skill), 1):
        rows.append({"source": f"header@{PIN}:{i}", "text": s})
    for i, r in enumerate(rows, 1):
        r["id"] = f"{skill}-{i:03d}"
        r["disposition"] = ""
    return rows


def _read_tsv(path: Path) -> list[dict]:
    lines = path.read_text().splitlines()  # plain tab split, no quoting: texts contain quote characters
    return [dict(zip(COLS, ln.split("\t") + [""] * 4)) for ln in lines[1:] if ln.strip()]


def build(skill: str) -> Path:
    path = REPO / OUT / f"{skill}.tsv"
    if path.exists() and any(r.get("disposition", "").strip() for r in _read_tsv(path)):
        raise SystemExit(f"refusing to overwrite {path}: it has filled dispositions")
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = skeleton(skill)
    clean = lambda t: t.replace("\t", " ").replace("\n", " ")  # noqa: E731
    path.write_text("\n".join(["\t".join(COLS), *("\t".join([r["id"], r["source"], clean(r["text"]), ""])
                                                  for r in rows)]) + "\n")
    return path


def sections(skill_dir: Path) -> dict[str, str]:
    """normalised heading text -> section text, over SKILL.md and reference/*.md (same heading in two files: concatenated)."""
    out: dict[str, str] = {}
    files = [skill_dir / "SKILL.md", *sorted((skill_dir / "reference").glob("*.md"))]
    for fp in files:
        if not fp.exists():
            continue
        lines = fp.read_text().splitlines()
        heads = [(i, len(m.group(1)), _norm(m.group(2))) for i, ln in enumerate(lines) if (m := HEAD.match(ln))]
        for k, (i, lvl, name) in enumerate(heads):
            end = next((j for j, l2, _ in heads[k + 1:] if l2 <= lvl), len(lines))
            out[name] = out.get(name, "") + "\n" + _norm("\n".join(lines[i + 1:end]))
    return out


def check_skill(skill: str, repo: Path = REPO) -> tuple[list[str], int]:
    """Return (errors, dropped count) for one skill."""
    tsv = repo / OUT / f"{skill}.tsv"
    if not tsv.exists():
        return [f"{skill}: missing-row check: {tsv} does not exist (run `build {skill}`)"], 0
    rows = {r["id"]: r for r in _read_tsv(tsv)}
    by_src = {(r["source"], r["text"]) for r in rows.values()}
    errs, dropped = [], 0
    for sk in skeleton(skill):
        if (sk["source"], sk["text"]) not in by_src:
            errs.append(f"{skill}: missing-row check (every skeleton row must be in the TSV): "
                        f"{sk['source']} absent: {sk['text'][:60]!r}")
    secs = sections(repo / ".claude/skills" / skill)
    for r in rows.values():
        d = (r.get("disposition") or "").strip()
        rid = r["id"]
        if not d:
            errs.append(f"{skill} {rid}: disposition check (must be kept/merged/dropped): empty disposition")
        elif d.startswith("dropped"):
            dropped += 1
            if not re.match(r"dropped:\s*\S", d):
                errs.append(f"{skill} {rid}: dropped-reason check (`dropped: <reason>` required): {d!r}")
        elif m := re.match(r"(kept|merged into)\s+(.+)$", d):
            name = _norm(m.group(2))
            if name not in secs:
                errs.append(f"{skill} {rid}: section-exists check (named section must be a heading in "
                            f"SKILL.md or reference/*.md): no heading {m.group(2)!r}")
            elif m.group(1) == "kept":
                absent = [t for t in key_tokens(r["text"]) if t not in secs[name]]
                if absent:
                    errs.append(f"{skill} {rid}: key-token check (the 3 longest words of the rule text must "
                                f"occur in the named section): {absent} absent from {m.group(2)!r}")
        else:
            errs.append(f"{skill} {rid}: disposition check (must be kept/merged/dropped): unknown {d!r}")
    return errs, dropped


SKILLS = ["dispatch-brief", "plan-critique", "running-sge-jobs", "scientific-evidence",
          "verification-patterns", "wave-review"]


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", nargs="*", metavar="SKILL", help="check these skills (default: all six)")
    ap.add_argument("cmd", nargs="*", help="build <skill>")
    a = ap.parse_args(argv)
    if a.check is not None:
        rc = 0
        for sk in a.check or SKILLS:
            errs, dropped = check_skill(sk)
            for e in errs:
                print("ERROR:", e)
            print(f"{sk}: {len(errs)} errors, {dropped} dropped")
            rc |= bool(errs)
        return rc
    if len(a.cmd) == 2 and a.cmd[0] == "build":
        print(build(a.cmd[1]))
        return 0
    ap.error("use `build <skill>` or `--check [skill...]`")


if __name__ == "__main__":
    sys.exit(main())
