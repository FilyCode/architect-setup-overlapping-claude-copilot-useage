import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import build_skills as bs  # noqa: E402
import rule_map as rm  # noqa: E402

HIST = ROOT / "docs/history/rules-2026-10-14"
MAP = ROOT / "docs/history/rule-map.tsv"


def _spans_for(name):
    return [s for s in bs.spans(HIST, MAP) if s.dest == f"skill:{name}"]


def test_every_skill_body_is_verbatim(tmp_path):
    bs.build_all(HIST, MAP, ROOT / "skill-headers", tmp_path)
    for name in bs.SKILLS:
        body = bs.body_text(tmp_path / name)
        expected = "".join(s.text for s in _spans_for(name))
        assert body == expected, name


def test_each_span_lands_in_exactly_one_skill():
    seen = {}
    for s in bs.spans(HIST, MAP):
        if s.dest.startswith("skill:"):
            assert (s.file, s.line) not in seen
            seen[(s.file, s.line)] = s.dest
    n_items = sum(len(rm.items(HIST / f)) for f in rm.FILES)
    assert len(seen) <= n_items


def test_skill_md_within_ceiling_and_references_listed(tmp_path):
    bs.build_all(HIST, MAP, ROOT / "skill-headers", tmp_path)
    for name in bs.SKILLS:
        skill = (tmp_path / name / "SKILL.md").read_text()
        assert len(skill.encode()) <= 15_360 + 4_096, name  # header allowance
        for ref in (tmp_path / name / "reference").glob("*.md") if (tmp_path / name / "reference").exists() else []:
            assert f"reference/{ref.name}" in skill, (name, ref.name)
