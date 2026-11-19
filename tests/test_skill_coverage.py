# REPO/tests/test_skill_coverage.py — tools/skill_coverage.py (plan 2026-11-18 T1); tmp_path fixtures only
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import skill_coverage as sc

ROWS = [
    {"id": "s-001", "source": "f.md:1", "text": "Never dispatch a waiting subagent for polling", "disposition": ""},
    {"id": "s-002", "source": "header@36f2a5e:1", "text": "Turn budget goes in the first line.", "disposition": ""},
]
SKILL_MD = "# S\n\n## Dispatch rules\nNever dispatch a waiting subagent; polling is the caller's job.\n\n## Budget\nturn budget first.\n"


def _repo(tmp_path, monkeypatch, dispositions, skill_md=SKILL_MD, rows=ROWS):
    monkeypatch.setattr(sc, "skeleton", lambda skill: [dict(r) for r in rows])
    (tmp_path / sc.OUT).mkdir(parents=True)
    (tmp_path / ".claude/skills/s/reference").mkdir(parents=True)
    (tmp_path / ".claude/skills/s/SKILL.md").write_text(skill_md)
    lines = ["\t".join(sc.COLS)]
    for r, d in zip(rows, dispositions):
        lines.append("\t".join([r["id"], r["source"], r["text"], d]))
    (tmp_path / sc.OUT / "s.tsv").write_text("\n".join(lines) + "\n")
    return tmp_path


GOOD = ["kept Dispatch rules", "merged into Budget"]


def test_key_tokens_are_three_longest_non_stopwords():
    assert sc.key_tokens("Never dispatch a waiting subagent for polling") == ["dispatch", "subagent", "waiting"]
    assert sc.key_tokens("This that with from") == []  # stopwords only


def test_sentences_split_on_sentence_ends():
    assert sc.sentences("One thing here. Another thing.\n\nThird para.") == ["One thing here.", "Another thing.", "Third para."]


def test_good_tsv_passes_and_counts_dropped(tmp_path, monkeypatch):
    repo = _repo(tmp_path, monkeypatch, ["kept Dispatch rules", "dropped: superseded by core.md"])
    assert sc.check_skill("s", repo) == ([], 1)


def test_all_good_with_merged(tmp_path, monkeypatch):
    assert sc.check_skill("s", _repo(tmp_path, monkeypatch, GOOD)) == ([], 0)


def test_missing_row_fails(tmp_path, monkeypatch):
    repo = _repo(tmp_path, monkeypatch, GOOD)
    (repo / sc.OUT / "s.tsv").write_text("\n".join((repo / sc.OUT / "s.tsv").read_text().splitlines()[:-1]) + "\n")
    errs, _ = sc.check_skill("s", repo)
    assert len(errs) == 1 and "missing-row" in errs[0] and "f.md:1" not in errs[0] and "header@36f2a5e:1" in errs[0]


def test_kept_row_with_absent_tokens_fails(tmp_path, monkeypatch):
    repo = _repo(tmp_path, monkeypatch, GOOD, skill_md="# S\n\n## Dispatch rules\nunrelated words only\n\n## Budget\nx\n")
    errs, _ = sc.check_skill("s", repo)
    assert len(errs) == 1 and "key-token" in errs[0] and "s-001" in errs[0]


def test_kept_row_in_reference_file_passes(tmp_path, monkeypatch):
    repo = _repo(tmp_path, monkeypatch, ["kept Extra", "merged into Budget"])
    (repo / ".claude/skills/s/reference/r.md").write_text("## Extra\nnever dispatch waiting subagent\n")
    assert sc.check_skill("s", repo) == ([], 0)


def test_missing_section_fails(tmp_path, monkeypatch):
    repo = _repo(tmp_path, monkeypatch, ["kept No such heading", "merged into Budget"])
    errs, _ = sc.check_skill("s", repo)
    assert len(errs) == 1 and "section-exists" in errs[0]


def test_merged_into_missing_section_fails(tmp_path, monkeypatch):
    errs, _ = sc.check_skill("s", _repo(tmp_path, monkeypatch, ["kept Dispatch rules", "merged into Nowhere"]))
    assert len(errs) == 1 and "section-exists" in errs[0] and "s-002" in errs[0]


@pytest.mark.parametrize("bad,kind", [("dropped", "dropped-reason"), ("dropped:", "dropped-reason"),
                                      ("dropped: ", "dropped-reason"), ("", "disposition"),
                                      ("maybe later", "disposition")])
def test_bad_disposition_fails(tmp_path, monkeypatch, bad, kind):
    errs, _ = sc.check_skill("s", _repo(tmp_path, monkeypatch, ["kept Dispatch rules", bad]))
    assert len(errs) == 1 and kind in errs[0] and "s-002" in errs[0]


def test_main_exit_code_follows_errors(tmp_path, monkeypatch, capsys):
    _repo(tmp_path, monkeypatch, ["", ""])
    monkeypatch.setattr(sc, "REPO", tmp_path)
    monkeypatch.setattr(sc, "check_skill", lambda s, repo=tmp_path, _f=sc.check_skill: _f(s, tmp_path))
    assert sc.main(["--check", "s"]) == 1
    (tmp_path / sc.OUT / "s.tsv").write_text(
        "\n".join(["\t".join(sc.COLS)] + ["\t".join([r["id"], r["source"], r["text"], d]) for r, d in zip(ROWS, GOOD)]) + "\n")
    assert sc.main(["--check", "s"]) == 0
    assert "0 dropped" in capsys.readouterr().out


def test_build_refuses_to_overwrite_filled_disposition(tmp_path, monkeypatch):
    repo = _repo(tmp_path, monkeypatch, GOOD)
    monkeypatch.setattr(sc, "REPO", repo)
    with pytest.raises(SystemExit, match="refusing"):
        sc.build("s")
    (repo / sc.OUT / "s.tsv").write_text("\t".join(sc.COLS) + "\ns-001\tf.md:1\tt\t\n")  # empty dispositions: may rebuild
    assert sc.build("s").read_text().splitlines()[0] == "\t".join(sc.COLS)


def test_real_skeleton_row_counts_match_rule_map():
    n = {s: sum(1 for r in sc.skeleton(s) if not r["source"].startswith("header@")) for s in sc.SKILLS}
    assert n == {"dispatch-brief": 29, "plan-critique": 32, "running-sge-jobs": 21, "scientific-evidence": 12,
                 "verification-patterns": 56, "wave-review": 15}
