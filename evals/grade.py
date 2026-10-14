#!/usr/bin/env python3
"""Grade claude -p stream-json runs against evals/scenarios.json."""
import argparse
import json
import re
import sys
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
