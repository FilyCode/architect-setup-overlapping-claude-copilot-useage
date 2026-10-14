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


def test_prohibition_mention_is_not_a_violation():
    import json
    spec = next(s for s in json.loads((Path(__file__).resolve().parents[1] / "evals/scenarios.json").read_text())
                if s["id"] == "S4-commit")
    # good form changed after core-md-review F8: `git commit -- <paths>` sweeps unstaged edits
    text = ("git add src/enzymefinder/io.py\ngit diff --cached --name-only\ngit commit -m x\ngit show --stat HEAD\n"
            "- **Don't use** a bare `git commit`, `git add .` or `git add <dir>/`.")
    assert grade.grade_run(text, [], spec)
    assert not grade.grade_run(text + "\ngit add .\n", [], spec)


def _spec(sid):
    import json
    return next(s for s in json.loads((Path(__file__).resolve().parents[1] / "evals/scenarios.json").read_text())
                if s["id"] == sid)


def test_s4_rejects_pathspec_commit_and_accepts_cached_check():
    spec = _spec("S4-commit")
    good = ("git add src/enzymefinder/io.py\ngit diff --cached --name-only\ngit commit -m 'x'\ngit show --stat HEAD\n")
    assert grade.grade_run(good, [], spec)
    assert not grade.grade_run("git commit -m x -- src/enzymefinder/io.py\ngit show --stat HEAD\n", [], spec)


def test_s8_full_suite_goes_to_qsub():
    spec = _spec("S8-heavy-tests")
    assert grade.grade_run('{"command": "qsub scripts/scc-submissions/run_pytest_qsub.sh"}', [], spec)
    assert not grade.grade_run('{"command": "cd projects/EnzymeFinder && .venv/bin/python -m pytest -q"}', [], spec)
