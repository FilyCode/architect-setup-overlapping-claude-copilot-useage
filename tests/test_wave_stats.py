# REPO/tests/test_wave_stats.py — per-session cost summary for the retro-officer seat
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import wave_stats as ws


def _call(i, ctx, ts="2026-10-14T12:00:00Z"):
    return {"timestamp": ts, "message": {"id": f"m{i}", "usage": {"input_tokens": ctx}}}


def _session(tmp_path):
    main = tmp_path / "s1.jsonl"
    note = ("<task-notification><task-id>aaa</task-id><status>completed</status><summary>Agent \"x\" "
            "stopped at its 40-turn limit (partial result)</summary></task-notification>")
    lines = [_call(1, 100_000, "2026-10-13T00:00:00Z"), _call(2, 600_000), _call(2, 600_000),
             {"type": "system", "subtype": "compact_boundary", "timestamp": "2026-10-14T13:00:00Z"},
             {"timestamp": "2026-10-14T13:01:00Z", "message": {"role": "user", "content": note}},
             {"timestamp": "2026-10-14T13:02:00Z", "message": {"role": "user", "content": note}},
             _call(3, 50_000)]
    main.write_text("\n".join(json.dumps(x) for x in lines) + "\n{partial")
    sub = tmp_path / "s1" / "subagents"
    sub.mkdir(parents=True)
    for aid, typ, ctxs in (("aaa", "critic-reviewer", [12_000, 30_000]), ("bbb", "implementer", [13_000])):
        (sub / f"agent-{aid}.jsonl").write_text("\n".join(json.dumps(_call(i, c)) for i, c in enumerate(ctxs)))
        (sub / f"agent-{aid}.meta.json").write_text(json.dumps({"agentType": typ}))
    return main


def test_summary_counts_calls_compactions_agents_and_turn_limits(tmp_path):
    s = ws.summarize(_session(tmp_path), since="2026-10-14T00:00:00Z")
    assert s["main"] == {"calls": 2, "context_tokens": 650_000, "max_context": 600_000, "compactions": 1,
                         "share_above_500k": round(600_000 / 650_000, 3)}
    assert s["subagents"]["critic-reviewer"] == {"n": 1, "context_tokens": 42_000}
    assert s["subagents"]["implementer"] == {"n": 1, "context_tokens": 13_000}
    assert s["turn_limit_hits"] == ["aaa"]


def test_cli_prints_json(tmp_path, capsys):
    ws.main([str(_session(tmp_path))])
    assert json.loads(capsys.readouterr().out)["main"]["calls"] == 3


def test_share_of_context_above_500k(tmp_path):
    # R-20261015-4: the nudge targets calls above 500k; the retro must be able to see whether that share moves.
    s = ws.summarize(_session(tmp_path))
    assert s["main"]["share_above_500k"] == round(600_000 / 750_000, 3)


def test_turn_limit_does_not_span_notifications():
    # 2026-10-21 investigator: with re.S, `.*?` ran from a completed task's id into the next block's limit notice.
    done = "<task-notification><task-id>ok1</task-id><status>completed</status><summary>done</summary></task-notification>"
    hit = ("<task-notification><task-id>hit2</task-id><status>completed</status><summary>Agent \"x\" "
           "stopped at its 60-turn limit</summary></task-notification>")
    assert ws.TURN_LIMIT.findall(done + "\n" + hit) == ["hit2"]
