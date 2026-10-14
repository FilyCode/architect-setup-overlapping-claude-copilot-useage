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
