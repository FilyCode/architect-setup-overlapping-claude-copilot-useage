# REPO/tests/test_context_nudge.py
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "workspace-config" / "hooks"))
import context_nudge as cn

def _tx(tmp_path, ctxs, partial=False):
    p = tmp_path / "t.jsonl"
    lines = [json.dumps({"type": "assistant", "message": {"id": f"m{i}", "usage": {"input_tokens": 1,
             "cache_creation_input_tokens": 0, "cache_read_input_tokens": c - 1}}}) for i, c in enumerate(ctxs)]
    p.write_text("\n".join(lines) + ("\n{\"type\": \"assist" if partial else "\n"))
    return p

def test_last_context_ignores_partial_line(tmp_path):
    assert cn.last_context(_tx(tmp_path, [100, 450_000], partial=True)) == 450_000

def test_no_usage_is_none(tmp_path):
    p = tmp_path / "t.jsonl"
    p.write_text('{"type":"user"}\n')
    assert cn.last_context(p) is None

def test_nudge_once_per_band():
    msg, st = cn.message(410_000, "next", {}, 400_000)
    assert msg and "410k" in msg
    msg2, st = cn.message(450_000, "next", st, 400_000)
    assert msg2 is None
    msg3, st = cn.message(520_000, "next", st, 400_000)
    assert msg3 and "520k" in msg3

def test_below_threshold_silent():
    assert cn.message(120_000, "hi", {}, 400_000)[0] is None
    assert cn.message(None, "hi", {}, 400_000)[0] is None

def test_effort_hint_once():
    msg, st = cn.message(10_000, "let's brainstorm the architecture", {}, 400_000)
    assert msg and "/effort high" in msg
    msg2, _ = cn.message(10_000, "brainstorm more", st, 400_000)
    assert msg2 is None


def test_default_threshold_sits_below_auto_compact_window():
    # Auto-compaction fires just under CLAUDE_CODE_AUTO_COMPACT_WINDOW=400000 (DECISION-026);
    # the nudge must come earlier so the user can compact at a task boundary.
    assert cn.DEFAULT_THRESHOLD == 250_000
    msg, _ = cn.message(260_000, "next", {}, cn.DEFAULT_THRESHOLD)
    assert "task boundary" in msg


def test_state_is_per_session(tmp_path, monkeypatch, capsys):
    # Hook input carries session_id but no scratchpad_dir; one shared file let the
    # first session's effort hint silence every later session.
    import io
    monkeypatch.setenv("TMPDIR", str(tmp_path))
    for sid in ("s1", "s2"):
        monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(
            {"prompt": "brainstorm a name", "session_id": sid, "transcript_path": "/nonexistent"})))
        cn.main()
        assert "/effort high" in capsys.readouterr().out, sid
