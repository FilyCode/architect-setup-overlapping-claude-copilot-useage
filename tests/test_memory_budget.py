import json
import subprocess
import sys
from pathlib import Path

HOOK = Path(__file__).resolve().parents[1] / "workspace-config" / "hooks" / "memory_budget.py"


def run(payload, raw=None):
    stdin = raw if raw is not None else json.dumps(payload)
    r = subprocess.run([sys.executable, str(HOOK)], input=stdin, capture_output=True, text=True)
    return r.returncode, r.stdout


def mem(tmp_path, text, name="MEMORY.md"):
    d = tmp_path / ".claude" / "projects" / "x" / "memory"
    d.mkdir(parents=True)
    p = d / name
    p.write_text(text)
    return p


def ev(path, tool="Write"):
    return {"tool_name": tool, "tool_input": {"file_path": str(path)}}


def test_over_bytes_warns(tmp_path):
    p = mem(tmp_path, "- [a](a.md) — " + "x" * 7000 + "\n")
    rc, out = run(ev(p))
    assert rc == 0
    o = json.loads(out)["hookSpecificOutput"]
    assert o["hookEventName"] == "PostToolUse"
    assert "6656" in o["additionalContext"] and "over budget" in o["additionalContext"]
    assert "belongs inside the memory file" in o["additionalContext"]


def test_over_entries_warns(tmp_path):
    p = mem(tmp_path, "".join(f"- [a{i}](a.md) — b\n" for i in range(61)))
    rc, out = run(ev(p, "Edit"))
    assert rc == 0 and "61" in json.loads(out)["hookSpecificOutput"]["additionalContext"]


def test_under_is_silent(tmp_path):
    p = mem(tmp_path, "- [a](a.md) — b\n")
    assert run(ev(p)) == (0, "")


def test_other_file_or_dir_silent(tmp_path):
    p = mem(tmp_path, "x" * 9000, name="other.md")
    assert run(ev(p)) == (0, "")
    q = tmp_path / "MEMORY.md"
    q.write_text("x" * 9000)
    assert run(ev(q)) == (0, "")


def test_malformed_stdin(tmp_path):
    assert run(None, raw="not json") == (0, "")
    assert run({"tool_input": None}) == (0, "")
    assert run(ev(tmp_path / ".claude/projects/x/memory/MEMORY.md")) == (0, "")  # missing file
