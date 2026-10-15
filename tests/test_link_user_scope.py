# REPO/tests/test_link_user_scope.py — the user-scope links are reproducible from the repo
import os
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "tools/link_user_scope.sh"


def _run(home):
    return subprocess.run(["bash", str(SCRIPT)], env=dict(os.environ, CLAUDE_USER_DIR=str(home)),
                          capture_output=True, text=True, timeout=30)


def test_links_every_seat_skill_hook_and_core(tmp_path):
    r = _run(tmp_path)
    assert r.returncode == 0, r.stderr
    agents = {p.name for p in (REPO / "workspace-config/agents").glob("*.md")}
    assert {p.name for p in (tmp_path / "agents").iterdir()} == agents
    assert (tmp_path / "rules/core.md").resolve() == (REPO / "workspace-config/rules/core.md").resolve()
    for s in ("dispatch-brief", "wave-review", "plan-critique", "verification-patterns", "scientific-evidence",
              "running-sge-jobs", "completion-check", "thermo-nuclear-code-quality-review"):
        assert (tmp_path / "skills" / s / "SKILL.md").is_file(), s
    for h in ("bash_guard.py", "context_nudge.py", "large-change-check.py"):
        assert (tmp_path / "hooks" / h).resolve().parent == (REPO / "workspace-config/hooks").resolve()


def test_idempotent_and_never_replaces_a_real_file(tmp_path):
    _run(tmp_path)
    assert "linked" not in _run(tmp_path).stdout
    (tmp_path / "skills/mine").mkdir()
    (tmp_path / "agents/implementer.md").unlink()
    (tmp_path / "agents/implementer.md").write_text("local copy")
    r = _run(tmp_path)
    assert r.returncode == 1 and "implementer.md" in r.stderr
    assert (tmp_path / "agents/implementer.md").read_text() == "local copy"
