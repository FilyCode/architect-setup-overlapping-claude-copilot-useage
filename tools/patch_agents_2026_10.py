#!/usr/bin/env python3
"""One-off Task 10 patch for the 11 existing seats (plan 2026-10-14). Idempotent.

Usage: patch_agents_2026_10.py <agents dir>
"""
import re
import sys
from pathlib import Path

ENV = Path(__file__).resolve().parents[1] / "docs/superpowers/plans/2026-10-14-setup-restructure.md"
TABLE = {  # name: (model, effort, preloaded skills)
    "critic-reviewer": ("opus", "medium", ["verification-patterns", "completion-check"]),
    "domain-reviewer": ("opus", "high", ["scientific-evidence"]),
    "anomaly-hunter": ("opus", "high", ["scientific-evidence"]),
    "alignment-officer": ("sonnet", "medium", []),
    "docs-sync": ("sonnet", "medium", []),
    "inventory-auditor": ("sonnet", "medium", []),
    "pragmatism-officer": ("sonnet", "medium", []),
    "figure-auditor": ("opus", "medium", ["scientific-evidence"]),
    "security-specialist": ("opus", "high", []),
    "research-scout": ("sonnet", "medium", []),
    "scc-monitor": ("haiku", "medium", ["running-sge-jobs"]),
}
KEEP_WORKING = ("Keep working until the task is done or you are blocked; there is no one to answer a\n"
                "question mid-run. Before you report, check your claims against the files or command\n"
                "output you cite.\n")
POINTERS = [
    ("Check the patterns in `.claude/rules/verification.md`:", "Check the patterns in the `verification-patterns` skill:"),
    ("`verification.md` for the full measurement.", "the `scientific-evidence` skill for the full measurement."),
    ("`subagent-dispatch.md`'s Minor-triage content test", "the Minor-triage content test (skill `wave-review`)"),
    ("see scc.md's job-wait pattern for that.", "see the running-sge-jobs skill's wait loop for that."),
    ("Baseline expectations from `.claude/rules/scc.md`:", "Baseline expectations from the `running-sge-jobs` skill:"),
    ("`scc.md` baseline", "`running-sge-jobs` baseline"),
]
EXTRA = {
    "alignment-officer": "\nYou check scope delivered against what was promised; drift between governance docs and\nreality belongs to docs-sync.\n",
    "docs-sync": "\nYou check governance docs against reality; whether the work delivered its promised scope\nbelongs to alignment-officer.\n",
    "research-scout": "\nSearch for current sources; prefer primary documentation over aggregators; give the URL\nfor every claim.\n",
    "pragmatism-officer": (
        "\n## Plan stage: the ladder\n\nFor each item a plan proposes to build, ask in order and stop at the first yes: does it\n"
        "need to exist; does it exist in this codebase; does the standard library do it; does a\n"
        "native platform feature do it; does an installed dependency do it; can it be one line.\n"
        "Report the rung per item. Never cut trust-boundary validation, data-loss handling or\n"
        "evidence checks to climb a rung.\n"),
}


def env_block() -> str:
    plan = ENV.read_text()
    m = re.search(r"```markdown\n(## Environment\n.*?)```", plan, re.S)
    return m.group(1)


def patch(path: Path) -> str:
    name = path.stem
    model, effort, skills = TABLE[name]
    s = path.read_text()
    for old, new in POINTERS:
        s = s.replace(old, new)
    fm_end = s.index("\n---\n", 4)
    fm, body = s[:fm_end], s[fm_end:]
    lines = [ln for ln in fm.split("\n") if not ln.startswith(("effort:", "omitClaudeMd:", "skills:"))]
    fm = "\n".join(f"model: {model}" if ln.startswith("model:") else ln for ln in lines)
    fm += f"\neffort: {effort}\nomitClaudeMd: true"
    if skills:
        fm += f"\nskills: [{', '.join(skills)}]"
    body = re.sub(r"- \*\*`rtk` filters only `cat`\*\*.*?a pipeline is not a bypass\.\n", "", body, flags=re.S)
    body = re.sub(r"5\. If the verdict is APPROVED \*\*and\*\*.*?where it doesn't apply\.\n", "", body, flags=re.S)
    body = body.replace(
        " You do\n   not have access to the `simplify`/`code-review` skills here (no `Skill` tool) — this\n"
        "   item exists so that gap doesn't silently drop the check.", "")
    add = ""
    if "## Environment" not in body:
        add += "\n" + env_block()
    if model in ("sonnet", "haiku") and "Keep working until the task is done" not in body:
        add += "\n" + KEEP_WORKING
    if name in EXTRA and EXTRA[name].strip().splitlines()[0] not in body:
        add += EXTRA[name]
    anchor = next((a for a in ("\n## Output", "\n## The one you close with", "\n## Report") if a in body), None)
    if add:
        body = body.replace(anchor, add.rstrip("\n") + "\n" + anchor, 1) if anchor else body.rstrip("\n") + "\n" + add
    return fm + body


def main(d):
    for name in TABLE:
        p = Path(d) / f"{name}.md"
        p.write_text(patch(p))
        print("patched", p.name)


if __name__ == "__main__":
    main(sys.argv[1])
