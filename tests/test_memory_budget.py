import json
import os
import subprocess
import sys
import time
from pathlib import Path

HOOK = Path(__file__).resolve().parents[1] / "workspace-config" / "hooks" / "memory_budget.py"


def run(payload, raw=None, env=None):
    stdin = raw if raw is not None else json.dumps(payload)
    r = subprocess.run([sys.executable, str(HOOK)], input=stdin, capture_output=True, text=True,
                       env=None if env is None else {**os.environ, **env})
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


def bash(cmd):
    return {"tool_name": "Bash", "tool_input": {"command": cmd}}


def cfg_mem(tmp_path, text, age_s=0):
    d = tmp_path / "cfg" / "projects" / "y" / "memory"
    d.mkdir(parents=True)
    p = d / "MEMORY.md"
    p.write_text(text)
    t = time.time() - age_s
    os.utime(p, (t, t))
    return p


def test_bash_write_to_fresh_over_budget_memory_warns(tmp_path):
    cfg_mem(tmp_path, "- [a](a.md) — " + "x" * 7000 + "\n")
    rc, out = run(bash("cat >> ~/.claude/projects/y/memory/MEMORY.md <<EOF\n- [b]\nEOF"),
                  env={"CLAUDE_CONFIG_DIR": str(tmp_path / "cfg")})
    o = json.loads(out)["hookSpecificOutput"]
    assert rc == 0 and o["hookEventName"] == "PostToolUse" and "over budget" in o["additionalContext"]


def test_bash_stale_memory_or_unrelated_command_silent(tmp_path):
    cfg_mem(tmp_path, "- [a](a.md) — " + "x" * 7000 + "\n", age_s=600)
    env = {"CLAUDE_CONFIG_DIR": str(tmp_path / "cfg")}
    assert run(bash("echo x >> MEMORY.md"), env=env) == (0, "")
    os.utime(tmp_path / "cfg/projects/y/memory/MEMORY.md")
    assert run(bash("ls -l"), env=env) == (0, "")
