# REPO/tests/test_job_ledger.py
import json
import subprocess
import sys
from pathlib import Path

HOOK = Path(__file__).resolve().parents[1] / "workspace-config" / "hooks" / "job_ledger.py"


def run(tmp_path, command, stdout, session="s1"):
    payload = {"tool_name": "Bash", "session_id": session, "tool_input": {"command": command},
               "tool_response": {"stdout": stdout, "stderr": "", "interrupted": False}}
    r = subprocess.run([sys.executable, str(HOOK)], input=json.dumps(payload), capture_output=True, text=True,
                       env={"CLAUDE_SESSION_JOBS_DIR": str(tmp_path / "led"), "PATH": "/usr/bin"}, timeout=10)
    assert r.returncode == 0, r.stderr
    f = tmp_path / "led" / f"{session}.txt"
    return f.read_text().split() if f.exists() else []


def test_records_real_submit_line(tmp_path):
    assert run(tmp_path, "qsub -N cc-evals job.sh", 'Your job 8762857 ("cc-evals") has been submitted\n') == ["8762857"]


def test_records_array_line_and_appends(tmp_path):
    run(tmp_path, "cd x && qsub -t 1-4 a.sh", 'Your job-array 8762900.1-4:1 ("a") has been submitted\n')
    assert run(tmp_path, "FOO=1 qsub b.sh", 'Your job 8762901 ("b") has been submitted\n') == ["8762900", "8762901"]


def test_non_qsub_records_nothing(tmp_path):
    assert run(tmp_path, "echo 'Your job 5 (\"x\") has been submitted'", 'Your job 5 ("x") has been submitted\n') == []
    assert run(tmp_path, "qstat -u me", "job-ID 123\n") == []
    assert run(tmp_path, "qsub bad.sh", "Unable to run job: denied\n") == []


def test_unsafe_session_id_records_nothing(tmp_path):
    assert run(tmp_path, "qsub a.sh", 'Your job 7 ("a") has been submitted\n', session="..") == []
