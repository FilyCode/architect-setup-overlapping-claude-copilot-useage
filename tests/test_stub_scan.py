# REPO/tests/test_stub_scan.py
import subprocess
import sys
from pathlib import Path
S = Path(__file__).resolve().parents[1] / ".claude/skills/completion-check/scripts/stub_scan.py"

def run(tmp_path, code):
    f = tmp_path / "m.py"
    f.write_text(code)
    return subprocess.run([sys.executable, str(S), str(f)], capture_output=True, text=True)

def test_flags_stubs(tmp_path):
    r = run(tmp_path, "def a():\n    pass\n\ndef b():\n    raise NotImplementedError\n\n"
                      "def c():\n    try:\n        return x()\n    except Exception:\n        return []\n# TODO: wire\n")
    assert r.returncode == 1
    for tag in ("empty-body", "not-implemented", "swallowed-except", "todo"):
        assert tag in r.stdout

def test_clean_file_passes(tmp_path):
    r = run(tmp_path, "def a(x):\n    return x + 1\n")
    assert r.returncode == 0 and r.stdout.strip() == ""

def test_abstract_and_protocol_not_flagged(tmp_path):
    r = run(tmp_path, "from abc import abstractmethod\nclass A:\n    @abstractmethod\n    def f(self):\n        ...\n")
    assert r.returncode == 0


def test_protocol_methods_not_flagged(tmp_path):
    r = run(tmp_path, "from typing import Protocol\nclass Searcher(Protocol):\n    def search(self, q: str) -> list:\n        ...\n"
                      "    @property\n    def name(self) -> str:\n        ...\n")
    assert r.returncode == 0, r.stdout


def test_narrow_except_not_flagged_broad_is(tmp_path):
    r = run(tmp_path, "def a(d):\n    try:\n        return d['k']\n    except KeyError:\n        return None\n")
    assert r.returncode == 0, r.stdout
    r = run(tmp_path, "def a(d):\n    try:\n        return d['k']\n    except Exception:\n        return None\n")
    assert "swallowed-except" in r.stdout


def test_non_python_paths_are_skipped(tmp_path):
    # Implementers pass every changed path; a shell script is not Python and must not fail the gate.
    sh = tmp_path / "run.sh"
    sh.write_text('#!/bin/bash\nSKILLS="a\nb"\n')
    md = tmp_path / "notes.md"
    md.write_text("pass\n")
    r = subprocess.run([sys.executable, str(S), str(sh), str(md)], capture_output=True, text=True)
    assert r.returncode == 0 and r.stdout == "", r.stdout
