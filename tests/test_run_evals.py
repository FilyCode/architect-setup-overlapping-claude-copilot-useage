import json
import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_runner_iterates_every_scenario_even_when_claude_reads_stdin(tmp_path):
    fake = tmp_path / "bin"
    fake.mkdir()
    (fake / "claude").write_text("#!/bin/bash\ncat > /dev/null\necho '{\"type\":\"result\"}'\n")
    (fake / "claude").chmod(0o755)
    out = tmp_path / "out"
    env = dict(os.environ, PATH=f"{fake}:{os.environ['PATH']}", ARM="t", K="2", EVAL_OUT=str(out))
    r = subprocess.run(["bash", str(ROOT / "evals/run_evals.sh")], env=env, capture_output=True, text=True, timeout=60)
    n = len(json.loads((ROOT / "evals/scenarios.json").read_text()))
    assert len(list(out.glob("*.jsonl"))) == 2 * n, r.stdout + r.stderr


def test_runner_only_filter(tmp_path):
    fake = tmp_path / "bin"
    fake.mkdir()
    (fake / "claude").write_text("#!/bin/bash\ncat > /dev/null\necho '{}'\n")
    (fake / "claude").chmod(0o755)
    out = tmp_path / "out"
    env = dict(os.environ, PATH=f"{fake}:{os.environ['PATH']}", ARM="t", K="1", EVAL_OUT=str(out), EVAL_ONLY="S8-heavy-tests")
    subprocess.run(["bash", str(ROOT / "evals/run_evals.sh")], env=env, capture_output=True, text=True, timeout=60)
    assert sorted(p.name for p in out.glob("*.jsonl")) == ["S8-heavy-tests-1.jsonl"]


def test_runner_records_claude_version_per_run(tmp_path):
    # The binary auto-updates mid-experiment; each run line must carry the version it ran under.
    fake = tmp_path / "bin"
    fake.mkdir()
    (fake / "claude").write_text('#!/bin/bash\n[ "$1" = --version ] && { echo "9.9.9 (Claude Code)"; exit 0; }\ncat > /dev/null\necho "{}"\n')
    (fake / "claude").chmod(0o755)
    env = dict(os.environ, PATH=f"{fake}:{os.environ['PATH']}", ARM="t", K="1", EVAL_OUT=str(tmp_path / "out"),
               EVAL_ONLY="S8-heavy-tests")
    r = subprocess.run(["bash", str(ROOT / "evals/run_evals.sh")], env=env, capture_output=True, text=True, timeout=60)
    assert "S8-heavy-tests-1 exit=0 claude=9.9.9" in r.stdout, r.stdout
