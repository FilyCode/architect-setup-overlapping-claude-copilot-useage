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
    # Owner 2026-10-14: compact between 50 % and 80 % of the 1M window. Nudge at 50 %;
    # auto-compaction (CLAUDE_CODE_AUTO_COMPACT_WINDOW=800000) is the backstop.
    assert cn.DEFAULT_THRESHOLD == 500_000
    msg, _ = cn.message(510_000, "next", {}, cn.DEFAULT_THRESHOLD)
    assert "task boundary" in msg and "800k" in msg


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


def test_effort_hint_ignores_paths():
    # The config repo is named architect-setup-...; every prompt citing a path in it fired the hint.
    p = "findings: /projectnb/liu-scc/philipp/architect-setup-overlapping-claude-copilot-useage/docs/x.md"
    assert cn.message(10_000, p, {}, cn.DEFAULT_THRESHOLD)[0] is None
    assert cn.message(10_000, "see `docs/superpowers/specs/2026-10-14-x-design.md`", {}, cn.DEFAULT_THRESHOLD)[0] is None
    assert cn.message(10_000, "let's architect the import graph", {}, cn.DEFAULT_THRESHOLD)[0] is not None


def test_nudge_rearms_after_compaction():
    # Compaction keeps the session id but drops context; the next climb past the threshold must nudge again.
    state, fired = {}, []
    for ctx in (510_000, 620_000, 90_000, 520_000):
        msg, state = cn.message(ctx, "", state, 500_000)
        fired.append(msg is not None)
    assert fired == [True, True, False, True]


def _log(tmp_path, last, open_items):
    p = tmp_path / "retro-log.md"
    p.write_text(f"# Retro log\n\nLast integrated: {last}\n\n" + "".join(
        f"- [{'x' if i >= open_items else ' '}] R-20261015-{i} something\n" for i in range(3)))
    return p


def test_retro_hint_when_open_items_and_overdue(tmp_path):
    import datetime as dt
    today = dt.date(2026, 10, 30)
    assert "3 open" in cn.retro_hint(_log(tmp_path, "2026-10-15", 3), today)
    assert cn.retro_hint(_log(tmp_path, "never", 1), today)
    assert cn.retro_hint(_log(tmp_path, "2026-10-25", 3), today) is None   # integrated within 7 days
    assert cn.retro_hint(_log(tmp_path, "2026-10-01", 0), today) is None   # nothing open
    assert cn.retro_hint(tmp_path / "missing.md", today) is None


def test_retro_hint_once_per_session():
    import datetime as dt
    state = {}
    msg, state = cn.message(None, "", state, 500_000, retro="Retro log: 2 open proposals")
    assert "Retro log" in msg
    msg, state = cn.message(None, "", state, 500_000, retro="Retro log: 2 open proposals")
    assert msg is None

def test_firm_band_from_650k():
    # R-20261016-2: the 500k nudge was relayed as a footnote and compaction came hours later; 97 calls ran above 650k.
    soft, _ = cn.message(560_000, "next", {}, 500_000)
    firm, _ = cn.message(660_000, "next", {}, 500_000)
    assert "before starting" not in soft.lower()
    assert "660k" in firm and "first line" in firm and "before starting" in firm.lower()
