# REPO/tests/test_context_budget.py
import shutil
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import context_budget as cb

WS = Path("/projectnb/liu-scc/philipp")

def _ws(tmp_path, core_bytes=100):
    ws = tmp_path / "ws"
    (ws / ".claude/rules").mkdir(parents=True)
    (ws / ".claude/skills/s1").mkdir(parents=True)
    shutil.copy(WS / ".claude/rules/python.md", ws / ".claude/rules/python.md")
    (ws / ".claude/rules/core.md").write_text("x" * core_bytes)
    (ws / "CLAUDE.md").write_text("root")
    (ws / ".claude/skills/s1/SKILL.md").write_text("---\nname: s1\ndescription: short\n---\nbody\n")
    home = tmp_path / "home"
    home.mkdir()
    (home / "CLAUDE.md").write_text("h")
    mem = tmp_path / "MEMORY.md"
    mem.write_text("- [a](a.md) — b\n")
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


def test_memory_entry_and_byte_caps(tmp_path):
    ws, home, mem = _ws(tmp_path)
    mem.write_text("".join(f"- [m{i}](m{i}.md) — x\n" for i in range(60)))
    assert cb.check(ws, home, mem) == []
    mem.write_text("".join(f"- [m{i}](m{i}.md) — x\n" for i in range(61)))
    assert any("entries" in v for v in cb.check(ws, home, mem))
    mem.write_text("- [a](a.md) — " + "y" * 6_700 + "\n")
    assert any("MEMORY.md loaded part" in v for v in cb.check(ws, home, mem))


def test_user_scope_skills_are_checked(tmp_path):
    # Process skills are linked into ~/.claude/skills, not the workspace .claude/skills.
    # Only skills that resolve into the workspace (ours) count; third-party user skills do not.
    ws, home, mem = _ws(tmp_path)
    src = ws / "repo/.claude/skills/big"
    src.mkdir(parents=True)
    (src / "SKILL.md").write_text("---\nname: big\ndescription: " + "x" * 600 + "\n---\n" + "y" * 16_000)
    (home / "skills").mkdir()
    (home / "skills/big").symlink_to(src)
    other = home / "skills/vendor"
    other.mkdir()
    (other / "SKILL.md").write_text("---\nname: vendor\ndescription: v\n---\n" + "z" * 50_000)
    v = " ".join(cb.check(ws, home, mem))
    assert "big body" in v and "big description" in v and "vendor" not in v


def test_user_scope_rules_are_counted(tmp_path):
    # core.md is linked at ~/.claude/rules so sessions started inside a project load it too.
    ws, home, mem = _ws(tmp_path)
    (ws / ".claude/rules/core.md").unlink()
    (home / "rules").mkdir()
    (home / "rules/core.md").write_text("x" * 10_000)
    (home / "rules/extra.md").write_text("y")
    v = " ".join(cb.check(ws, home, mem))
    assert "core.md 10000 >" in v and "unscoped rule extra.md" in v
    assert str(home / "rules/core.md") in cb.always_loaded(ws, home, mem)
