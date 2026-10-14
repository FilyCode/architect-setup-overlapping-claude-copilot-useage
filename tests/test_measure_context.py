# REPO/tests/test_measure_context.py
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import measure_context as mc

FIX = Path(__file__).parent / "fixtures" / "sub" / "agent-fixture.jsonl"
N_CALLS = 11
FIRST_CTX = 49787

def test_calls_deduplicated_and_first_context():
    calls = mc.call_contexts(FIX)
    assert len(calls) == N_CALLS
    assert calls[0] == FIRST_CTX

def test_agent_type_from_sidecar():
    meta = json.loads(FIX.with_suffix(".meta.json").read_text())
    assert mc.agent_type(FIX) == meta["agentType"]

def test_instructions_attachment_measured():
    att = mc.first_attachments(FIX)
    assert att.get("instructions", 0) > 1000
    assert att["memory_in_instructions"] in (0, 1)

def test_missing_sidecar_and_no_usage(tmp_path):
    p = tmp_path / "agent-x.jsonl"
    p.write_text('{"type": "user", "message": {"role": "user", "content": "hi"}}\n{not json\n')
    assert mc.agent_type(p) == "unknown"
    assert mc.call_contexts(p) == []
    rows = mc.summarize([p])
    assert rows["unknown"]["no_usage"] == 1


def test_headless_sessions_excluded_by_default(tmp_path):
    # Evals and probes run as `claude -p` (entrypoint sdk-cli) and swamp the pool (doctor note #1).
    def main_tx(sid, ep):
        (tmp_path / f"{sid}.jsonl").write_text(json.dumps(
            {"type": "user", "entrypoint": ep, "timestamp": "2026-10-14T10:00:00Z", "message": {"role": "user", "content": "x"}}) + "\n")
    main_tx("aaa", "cli")
    main_tx("bbb", "sdk-cli")
    (tmp_path / "bbb" / "subagents").mkdir(parents=True)
    (tmp_path / "bbb" / "subagents" / "agent-x.jsonl").write_text("")
    (tmp_path / "aaa" / "subagents").mkdir(parents=True)
    (tmp_path / "aaa" / "subagents" / "agent-y.jsonl").write_text("")
    names = {p.name for p in mc.collect(tmp_path, None)}
    assert names == {"aaa.jsonl", "agent-y.jsonl"}
    assert len(mc.collect(tmp_path, None, include_headless=True)) == 4
