# REPO/tests/test_move_transcripts.py — transcripts move off home only when idle, and only after a verified copy
import os
import subprocess
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "tools/move_transcripts.sh"


def _run(cdir, dest):
    return subprocess.run(["bash", str(SCRIPT), str(dest)], env=dict(os.environ, CLAUDE_USER_DIR=str(cdir)),
                          capture_output=True, text=True, timeout=30)


def _tree(cdir, age_s):
    f = cdir / "projects/p1/s1.jsonl"
    f.parent.mkdir(parents=True)
    f.write_text('{"a":1}\n')
    (cdir / "projects/p1/memory").mkdir()
    (cdir / "projects/p1/memory/MEMORY.md").write_text("# idx\n")
    old = time.time() - age_s
    for p in (cdir / "projects").rglob("*"):
        os.utime(p, (old, old))


def test_refuses_while_a_transcript_is_fresh(tmp_path):
    _tree(tmp_path / "c", age_s=60)
    r = _run(tmp_path / "c", tmp_path / "dest")
    assert r.returncode == 1 and "refusing" in r.stdout
    assert not (tmp_path / "c/projects").is_symlink()


def test_moves_verifies_and_links_when_idle(tmp_path):
    _tree(tmp_path / "c", age_s=3600)
    r = _run(tmp_path / "c", tmp_path / "dest")
    assert r.returncode == 0, r.stdout + r.stderr
    link = tmp_path / "c/projects"
    assert link.is_symlink() and link.resolve() == (tmp_path / "dest").resolve()
    assert (link / "p1/memory/MEMORY.md").read_text() == "# idx\n"
    assert list(tmp_path.glob("c/projects.moved-*/p1/s1.jsonl"))
    assert _run(tmp_path / "c", tmp_path / "dest").returncode == 0  # second run: already a link
