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


def test_below_threshold_silent():
    assert cn.message(120_000, "hi", {}, 400_000)[0] is None
    assert cn.message(None, "hi", {}, 400_000)[0] is None

def test_effort_hint_once():
    msg, st = cn.message(10_000, "let's brainstorm the architecture", {}, 400_000)
    assert msg and "/effort high" in msg
    msg2, _ = cn.message(10_000, "brainstorm more", st, 400_000)
    assert msg2 is None



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


# Owner 2026-10-22: look for a good compaction point from 300k, firm nudge at 500k, auto-compaction at 650k.
def test_bands_are_300_500_650():
    assert (cn.DEFAULT_THRESHOLD, cn.FIRM, cn.AUTO_COMPACT) == (300_000, 500_000, 650_000)


def test_window_300_500_nudges_only_at_a_boundary():
    assert cn.message(350_000, "next", {}, cn.DEFAULT_THRESHOLD)[0] is None
    msg, st = cn.message(350_000, "next", {}, cn.DEFAULT_THRESHOLD, boundary="commit")
    assert msg and "350k" in msg and "good point" in msg
    assert cn.message(380_000, "next", st, cn.DEFAULT_THRESHOLD, boundary="commit")[0] is None  # once per 100k band
    assert cn.message(420_000, "next", st, cn.DEFAULT_THRESHOLD, boundary="idle")[0]


def test_firm_from_500k_without_boundary():
    msg, st = cn.message(510_000, "next", {}, cn.DEFAULT_THRESHOLD)
    assert "510k" in msg and "first line" in msg and "before starting" in msg.lower() and "650k" in msg
    assert cn.message(560_000, "next", st, cn.DEFAULT_THRESHOLD)[0] is None
    assert cn.message(610_000, "next", st, cn.DEFAULT_THRESHOLD)[0]


def test_nudge_rearms_after_compaction():
    state, fired = {}, []
    for ctx in (510_000, 90_000, 520_000):
        msg, state = cn.message(ctx, "", state, cn.DEFAULT_THRESHOLD)
        fired.append(msg is not None)
    assert fired == [True, False, True]


def _turns(tmp_path, entries):
    p = tmp_path / "b.jsonl"
    p.write_text("\n".join(json.dumps(e) for e in entries) + "\n")
    return p


def _user(text, ts):
    return {"type": "user", "timestamp": ts, "message": {"role": "user", "content": text}}


def _bash(cmd, ts):
    return {"type": "assistant", "timestamp": ts, "message": {"id": ts, "content": [
        {"type": "tool_use", "name": "Bash", "input": {"command": cmd}}]}}


def test_boundary_detects_commit_since_last_prompt(tmp_path):
    now = cn.dt.datetime(2026, 10, 22, 12, 0, tzinfo=cn.dt.timezone.utc)
    commit = _turns(tmp_path, [_user("go", "2026-10-22T11:50:00Z"), _bash("git commit -q -F - <<EOF", "2026-10-22T11:58:00Z")])
    assert cn.boundary(commit, now) == "commit"
    old = _turns(tmp_path, [_bash("git commit -m x", "2026-10-22T11:40:00Z"), _user("go", "2026-10-22T11:50:00Z"),
                            _bash("ls", "2026-10-22T11:58:00Z")])
    assert cn.boundary(old, now) is None   # the commit belongs to an earlier task
    idle = _turns(tmp_path, [_user("go", "2026-10-22T11:00:00Z"), _bash("ls", "2026-10-22T11:10:00Z")])
    assert cn.boundary(idle, now) == "idle"  # 50 min idle: the cache is cold, compaction costs nothing extra



def test_boundary_ignores_request_blobs(tmp_path):
    # Real transcripts hold `api-request-blob` entries that replay the whole history, old commits included.
    now = cn.dt.datetime(2026, 10, 22, 12, 0, tzinfo=cn.dt.timezone.utc)
    blob = {"type": "api-request-blob", "message": {"content": [
        {"type": "tool_use", "name": "Bash", "input": {"command": "git commit -m old"}}]}}
    p = _turns(tmp_path, [_bash("git commit -m old", "2026-10-22T11:00:00Z"), _user("go", "2026-10-22T11:50:00Z"),
                          _bash("ls", "2026-10-22T11:58:00Z"), blob])
    assert cn.boundary(p, now) is None


def test_boundary_needs_a_real_git_commit_command(tmp_path):
    now = cn.dt.datetime(2026, 10, 22, 12, 0, tzinfo=cn.dt.timezone.utc)
    text = _turns(tmp_path, [_user("go", "2026-10-22T11:50:00Z"), _bash("python3 - <<EOF\nx = 'git commit' in s\nEOF", "2026-10-22T11:58:00Z")])
    assert cn.boundary(text, now) is None
    for cmd in ("cd repo && git add a && git commit -q -F - <<'EOF'", "git -C /x/repo commit -m y"):
        p = _turns(tmp_path, [_user("go", "2026-10-22T11:50:00Z"), _bash(cmd, "2026-10-22T11:58:00Z")])
        assert cn.boundary(p, now) == "commit", cmd


def test_boundary_ignores_commit_text_inside_a_heredoc(tmp_path):
    now = cn.dt.datetime(2026, 10, 22, 12, 0, tzinfo=cn.dt.timezone.utc)
    cmd = "cat >> t.py <<'EOF'\nfor c in ('a && git commit -q',):\nEOF\npytest -q"
    p = _turns(tmp_path, [_user("go", "2026-10-22T11:50:00Z"), _bash(cmd, "2026-10-22T11:58:00Z")])
    assert cn.boundary(p, now) is None
    msg = "git commit -q -F - <<'EOF'\nsubject\nEOF\ngit show --stat HEAD"
    p = _turns(tmp_path, [_user("go", "2026-10-22T11:50:00Z"), _bash(msg, "2026-10-22T11:58:00Z")])
    assert cn.boundary(p, now) == "commit"
