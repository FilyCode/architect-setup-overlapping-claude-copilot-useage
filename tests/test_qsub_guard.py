import json
import subprocess

import pytest
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "workspace-config" / "hooks"))
sys.path.insert(0, str(REPO / "tools"))
from qsub_guard import decide  # noqa: E402
from sge_efficiency import parse_line, suggest, summarize  # noqa: E402

HIST = {"rs_screenboot": {"n": 117, "slots": 4, "cores_used": 1.07, "eff": 0.27, "gpu": False},
        "aligner": {"n": 5, "slots": 8, "cores_used": 7.4, "eff": 0.92, "gpu": False},
        "once": {"n": 1, "slots": 8, "cores_used": 1.0, "eff": 0.12, "gpu": False}}


@pytest.fixture(autouse=True)
def _tmp_is_not_node_local(monkeypatch):
    """pytest's tmp_path is under /scratch here; only the node-local test turns the check on."""
    import qsub_guard
    monkeypatch.setattr(qsub_guard, "NODE_LOCAL", ("/nonexistent-node-local/",))


def d(cmd, cwd="/tmp", hist=HIST, sub=False):
    return decide(cmd, cwd, hist, sub)[0]


def script(tmp_path, body, name="job.sh"):
    p = tmp_path / name
    p.write_text("#!/bin/bash -l\n" + body)
    return p


def test_single_slot_passes(tmp_path):
    s = script(tmp_path, "#$ -N rs_screenboot\n#$ -pe omp 1\npython x.py\n")
    assert d(f"qsub {s}") == "allow"
    assert d("qsub -b y -N t hostname") == "allow"
    assert d("echo qsub is a word") == "allow"


def test_multi_slot_without_reason_denied_inline_and_in_script(tmp_path):
    s = script(tmp_path, "#$ -N newjob\n#$ -pe omp 8\npython x.py\n")
    assert d(f"qsub {s}") == "deny"
    plain = script(tmp_path, "python x.py\n", "plain.sh")
    assert d(f"qsub -pe omp 4 {plain}") == "deny"
    assert d(f"cd {tmp_path} && qsub job.sh") == "deny"
    assert d("qsub job.sh", cwd=str(tmp_path)) == "deny"


def test_command_line_overrides_script(tmp_path):
    s = script(tmp_path, "#$ -pe omp 8\npython x.py\n")
    assert d(f"qsub -pe omp 1 {s}") == "allow"


def test_reason_note_passes_when_history_agrees_or_is_thin(tmp_path):
    s = script(tmp_path, "#$ -N aligner\n#$ -pe omp 8  # cores: bowtie2 -p $NSLOTS\nbowtie2\n")
    assert d(f"qsub {s}") == "allow"
    s2 = script(tmp_path, "#$ -N once\n#$ -pe omp 8  # cores: new threaded code\n", "o.sh")
    assert d(f"qsub {s2}") == "allow"  # one run is not enough history to overrule the note
    s3 = script(tmp_path, "#$ -N brandnew\n#$ -pe omp 16  # cores: hmmsearch --cpu $NSLOTS\n", "n.sh")
    assert d(f"qsub {s3}") == "allow"


def test_history_contradicting_the_note_denies_once(tmp_path):
    s = script(tmp_path, "#$ -N rs_screenboot\n#$ -pe omp 4  # cores: torch threads\npython b.py\n")
    verdict, reason = decide(f"qsub {s}", "/tmp", HIST)
    assert verdict == "deny-once"
    assert "1.07" in reason and "-pe omp 1" in reason


def test_heredoc_job_is_read():
    cmd = "qsub <<'EOF'\n#!/bin/bash\n#$ -N hd\n#$ -pe omp 8\npython x.py\nEOF"
    assert d(cmd) == "deny"
    ok = "qsub <<EOF\n#$ -pe omp 8  # cores: make -j $NSLOTS\nmake\nEOF"
    assert d(ok) == "allow"


def test_array_and_qalter_and_qrsh(tmp_path):
    s = script(tmp_path, "#$ -t 1-100\n#$ -pe omp 4\n")
    assert d(f"qsub {s}") == "deny"
    assert d("qalter -pe omp 1 8376975") == "allow"
    assert d("qalter -pe omp 8 8376975") == "deny"
    assert d("qrsh -pe omp 8") == "deny"


def test_unresolved_slot_count_or_missing_script_warns(tmp_path):
    s = script(tmp_path, "python x.py\n")
    assert d(f"qsub -pe omp $N {s}") == "warn"
    assert d("qsub /nonexistent/job.sh") == "warn"


def test_subagent_cannot_submit(tmp_path):
    s = script(tmp_path, "#$ -pe omp 1\n")
    assert d(f"qsub {s}", sub=True) == "deny"
    assert d("qalter -pe omp 1 123", sub=True) == "allow"


def test_hook_end_to_end_deny_once_then_pass(tmp_path):
    cache = tmp_path / "cache"
    cache.mkdir()
    import time
    (cache / "efficiency.json").write_text(json.dumps({"updated": time.time(), "summary": HIST}))
    s = script(tmp_path, "#$ -N rs_screenboot\n#$ -pe omp 4  # cores: torch\n")
    inp = json.dumps({"tool_name": "Bash", "session_id": "t1", "cwd": "/tmp",
                      "tool_input": {"command": f"qsub {s}"}})
    env = {"PATH": "/usr/bin:/bin", "TMPDIR": str(tmp_path), "SGE_EFF_CACHE": str(cache),
           "QSUB_GUARD_NODE_LOCAL": "/nonexistent-node-local/"}
    hook = REPO / "workspace-config" / "hooks" / "qsub_guard.py"
    first = subprocess.run([sys.executable, str(hook)], input=inp, capture_output=True, text=True, env=env)
    assert json.loads(first.stdout)["hookSpecificOutput"]["permissionDecision"] == "deny"
    second = subprocess.run([sys.executable, str(hook)], input=inp, capture_output=True, text=True, env=env)
    assert second.stdout == ""
    log = [json.loads(x) for x in (cache / "guard.log").read_text().splitlines()]
    assert [e["final"] for e in log] == ["deny", "allow-resubmit"]


def test_accounting_parse_and_summary():
    f = ["q", "h", "g", "phitro", "rs_screenboot", "8319349", "sge", "0", "1", "2", "1793254091", "0", "0",
         "13360"] + ["0"] * 17 + ["ec523kb", "dept", "omp", "4", "68", "14209.5", "0", "0",
                                  "-l h_rt=28800,mem_per_core=4G -pe omp 4", "0", "NONE", "19539185664.0", "0"]
    r = parse_line(":".join(f), "phitro")
    assert r["slots"] == 4 and r["name"] == "rs_screenboot" and abs(r["cpu"] / r["wall"] - 1.064) < 0.01
    assert parse_line(":".join(f), "someone") is None
    s = summarize([r, dict(r, job="2")])["rs_screenboot"]
    assert s["n"] == 2 and s["eff"] == 0.27


def test_suggest():
    assert suggest(1.07) == 1 and suggest(1.25) == 1
    assert suggest(3.2) == 4 and suggest(4.43) == 8 and suggest(7.4) == 16 and suggest(30) == 28


def test_variables_in_script_path_are_expanded(tmp_path):
    script(tmp_path, "#$ -pe omp 8\n")
    assert d(f"S={tmp_path}; qsub $S/job.sh") == "deny"
    assert d(f"export S={tmp_path} && qsub -verify ${{S}}/job.sh") == "deny"


def test_unmeasured_big_array_gets_a_probe_first(tmp_path):
    s = script(tmp_path, "#$ -N fresh\n#$ -t 1-74\n#$ -pe omp 8  # cores: dataloader workers\n")
    assert d(f"qsub {s}") == "deny-once"
    assert d(f"qsub -t 1-2 {s}") == "allow"  # the probe
    small = script(tmp_path, "#$ -N fresh\n#$ -t 1-5:1\n#$ -pe omp 8  # cores: x\n", "small.sh")
    assert d(f"qsub {small}") == "allow"
    measured = script(tmp_path, "#$ -N aligner\n#$ -t 1-74\n#$ -pe omp 8  # cores: bowtie2\n", "m.sh")
    assert d(f"qsub {measured}") == "allow"


def test_node_local_script_path_denied(tmp_path, monkeypatch):
    """R-20261102-3 (SenC w5, EF F5): jobs 8393676 and 8393908 failed to start from /scratch scripts."""
    import qsub_guard
    s = script(tmp_path, "#$ -N x\npython x.py\n")
    monkeypatch.setattr(qsub_guard, "NODE_LOCAL", (str(tmp_path) + "/",))
    assert d(f"qsub {s}") == "deny"
    assert d("qsub job.sh", cwd=str(tmp_path)) == "deny"
    assert "node-local" in decide(f"qsub {s}", "/", HIST)[1]
    monkeypatch.setattr(qsub_guard, "NODE_LOCAL", ("/elsewhere/",))
    assert d(f"qsub {s}") == "allow"
