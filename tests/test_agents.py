# REPO/tests/test_agents.py — contract for workspace-config/agents (agent-seat-review 2026-10-14)
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
AGENTS = sorted((REPO / "workspace-config" / "agents").glob("*.md"))
ENV = (REPO / "workspace-config" / "seat-environment.md").read_text()
REVIEW_SEATS = {"critic-reviewer", "alignment-officer", "docs-sync", "inventory-auditor", "figure-auditor",
                "security-specialist", "lean-critic", "pragmatism-officer", "domain-reviewer", "anomaly-hunter",
                "investigator", "research-scout", "retro-officer"}


def _fm(text):
    fm = text.split("\n---\n", 1)[0]
    return {k.strip(): v.strip() for k, _, v in (ln.partition(":") for ln in fm.splitlines()[1:]) if v}


def _skill_flags(name):
    for p in (REPO / ".claude" / "skills" / name / "SKILL.md", REPO / "skill-headers" / f"{name}.md"):
        if p.exists():
            return p.read_text().split("\n---\n", 1)[0]
    return None


def test_agent_set():
    names = {p.stem for p in AGENTS}
    assert {"implementer", "investigator", "lean-critic", "critic-reviewer", "scc-monitor", "retro-officer"} <= names
    assert len(names) == 15


def test_frontmatter_complete():
    for p in AGENTS:
        fm = _fm(p.read_text())
        for key in ("name", "description", "tools", "model", "effort", "maxTurns", "omitClaudeMd"):
            assert key in fm, (p.stem, key)
        assert fm["omitClaudeMd"] == "true", p.stem
        assert fm["model"] in {"haiku", "sonnet", "opus"}, p.stem
        assert len(fm["description"]) <= 600 and "use " in fm["description"].lower(), p.stem


def test_environment_block_matches_single_source():
    for p in AGENTS:
        text = p.read_text()
        assert text.count("## Environment") == 1, p.stem
        block = re.search(r"## Environment\n.*?(?=\n## |\nKeep working|\Z)", text, re.S).group(0).rstrip()
        assert block == ENV.rstrip(), p.stem


def test_preloaded_skills_are_preloadable():
    for p in AGENTS:
        m = re.search(r"^skills: \[(.*)\]$", p.read_text(), re.M)
        for s in [x.strip() for x in m.group(1).split(",")] if m else []:
            flags = _skill_flags(s)
            assert flags is not None, (p.stem, s)
            assert "disable-model-invocation: true" not in flags, (p.stem, s)


def test_review_seats_create_findings_file_first():
    for p in AGENTS:
        if p.stem in REVIEW_SEATS:
            body = p.read_text().split("\n---\n", 1)[1]
            assert re.search(r"(?i)first action.{0,200}findings file", body, re.S), p.stem


def test_implementer_contract():
    text = (REPO / "workspace-config" / "agents" / "implementer.md").read_text()
    fm = _fm(text)
    assert "dispatch-brief" not in fm.get("skills", "")
    assert "Agent" not in fm["tools"] and "Skill" not in fm["tools"]
    assert "Status:" in text and "DONE_WITH_CONCERNS" in text
    assert "git diff --cached --name-only" in text
    assert not re.search(r'git commit -m "[^"]*" -- ', text)  # core.md #6: no pathspec commit


def test_no_memory_on_scc_monitor_and_no_skill_tool_on_lean_critic():
    assert "memory" not in _fm((REPO / "workspace-config/agents/scc-monitor.md").read_text())
    assert "Skill" not in _fm((REPO / "workspace-config/agents/lean-critic.md").read_text())["tools"]


def test_patch_is_idempotent_and_keeps_spacing(tmp_path, capsys):
    import shutil
    import sys
    sys.path.insert(0, str(REPO / "tools"))
    import patch_agents_2026_10 as pa
    for p in AGENTS:
        shutil.copy(p, tmp_path / p.name)
    pa.main(tmp_path)
    capsys.readouterr()
    pa.main(tmp_path)
    assert capsys.readouterr().out == ""
    for p in tmp_path.glob("*.md"):
        assert "\n## Environment" in p.read_text() and "moved.\n## " not in p.read_text(), p.stem
