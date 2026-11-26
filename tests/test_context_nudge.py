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


# Owner 2026-10-22 (compact start lowered 300k -> 200k on 2026-11-26): firm nudge at 500k, auto-compaction at 650k.
def test_bands_are_200_500_650():
    assert (cn.DEFAULT_THRESHOLD, cn.FIRM, cn.AUTO_COMPACT) == (200_000, 500_000, 650_000)


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


def test_retro_hint_counts_indented_proposals(tmp_path):
    """2026-11-18 audit: entries since 11-10 write `  - [ ] R-...`; the hint said 12 open when 25 were."""
    p = tmp_path / "retro-log.md"
    p.write_text("Last integrated: 2026-10-01\n- [ ] R-1 a\n  - [ ] R-2 b\n  - [x] R-3 c\n")
    import datetime
    assert "2 open" in cn.retro_hint(p, datetime.date(2026, 11, 18))


# --- speed: one small tail read, 2 MB only as a fallback (SGE 8929862: median 6.1 s, all hit the 5 s timeout) ---
def _count_reads(monkeypatch):
    sizes, real = [], cn._read_tail
    monkeypatch.setattr(cn, "_read_tail", lambda p, n: (sizes.append(n), real(p, n))[1])
    return sizes


def _pad(path, n_bytes):
    """Prepend `n_bytes` of usage-free lines so earlier entries fall outside a 256 KB tail."""
    junk = json.dumps({"type": "system", "x": "y" * 900}) + "\n"
    return junk * (n_bytes // len(junk) + 1)


def test_tail_sizes_are_256k_then_2m():
    assert (cn.TAIL_SMALL, cn.TAIL) == (256 * 1024, 2_000_000)


def test_usage_in_last_256k_never_reads_2m(tmp_path, monkeypatch):
    p = _tx(tmp_path, [100])
    p.write_text(p.read_text() + _pad(p, 600_000) + _tx(tmp_path, [777_000]).read_text())
    sizes = _count_reads(monkeypatch)
    assert cn.last_context(p) == 777_000
    assert sizes == [cn.TAIL_SMALL]


def test_usage_outside_256k_retries_once_at_2m(tmp_path, monkeypatch):
    p = _tx(tmp_path, [1, 321_000])  # first line is dropped by the tail reader (existing behaviour)
    p.write_text(p.read_text() + _pad(p, 600_000))
    sizes = _count_reads(monkeypatch)
    assert cn.last_context(p) == 321_000
    assert sizes == [cn.TAIL_SMALL, cn.TAIL]


def test_boundary_retries_at_2m_only_when_prompt_not_found(tmp_path, monkeypatch):
    now = cn.dt.datetime(2026, 10, 22, 12, 0, tzinfo=cn.dt.timezone.utc)
    body = "".join(json.dumps(e) + "\n" for e in [_user("go", "2026-10-22T11:50:00Z"), _bash("git commit -m a", "2026-10-22T11:51:00Z")])
    p = tmp_path / "x.jsonl"
    p.write_text(body + _pad(p, 600_000))  # user prompt and commit are > 256 KB back
    sizes = _count_reads(monkeypatch)
    assert cn.boundary(p, now) == "commit"
    assert sizes == [cn.TAIL_SMALL, cn.TAIL]
    q = tmp_path / "y.jsonl"
    q.write_text(_pad(q, 600_000) + body)  # commit inside the small tail
    del sizes[:]
    assert cn.boundary(q, now) == "commit"
    assert sizes == [cn.TAIL_SMALL]


def test_main_reads_the_tail_once(tmp_path, monkeypatch, capsys):
    import io
    p = _tx(tmp_path, [400_000])
    monkeypatch.setenv("TMPDIR", str(tmp_path))
    monkeypatch.setattr(cn, "RETRO_LOG", tmp_path / "none.md")
    sizes = _count_reads(monkeypatch)
    monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps({"prompt": "x", "session_id": "once", "transcript_path": str(p)})))
    cn.main()
    assert sizes == [cn.TAIL_SMALL]  # last_context and boundary share one read


# --- good point to /clear + handoff (owner 2026-11-25) ---
def _run_main(monkeypatch, tmp_path, tx, sid, cwd="/projectnb/x/My Proj", clear_min=None):
    import io
    monkeypatch.setenv("JOB_ID", "8963259")
    monkeypatch.setenv("TMPDIR", str(tmp_path))
    monkeypatch.setattr(cn, "RETRO_LOG", tmp_path / "none.md")
    monkeypatch.setenv("CLAUDE_HANDOFF_DIR", str(tmp_path / "handoffs"))
    if clear_min is not None:
        monkeypatch.setenv("CLAUDE_CLEAR_MIN", str(clear_min))
    monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(
        {"prompt": "next", "session_id": sid, "transcript_path": str(tx), "cwd": cwd})))
    cn.main()


WAVE_CMD = "git add PROJECT_STATE.md && git commit -m x"


def _committed_tx(tmp_path, ctx, tool_id="toolu_A", ts="2026-10-22T11:58:00Z", cmd="git commit -m x"):
    use = _bash(cmd, ts)
    use["message"]["content"][0]["id"] = tool_id
    use["message"]["usage"] = {"input_tokens": ctx, "cache_creation_input_tokens": 0, "cache_read_input_tokens": 0}
    return _turns(tmp_path, [_user("go", "2026-10-22T11:50:00Z"), use])


def test_clear_signal_fires_once_per_wave_event(tmp_path, monkeypatch, capsys):
    tx = _committed_tx(tmp_path, 180_000, cmd=WAVE_CMD)
    _run_main(monkeypatch, tmp_path, tx, "c1")
    o = json.loads(capsys.readouterr().out)
    assert o["systemMessage"] == "Good point to /clear: wave/phase boundary at 180k context. Claude is writing a handoff first."
    h = o["hookSpecificOutput"]
    assert h["hookEventName"] == "UserPromptSubmit"
    for w in ("8963259.md", "safe to /clear",
              "UNVERIFIED", "SGE job", "uncommitted", "Next step"):
        assert w in h["additionalContext"], w
    assert "-projectnb-x-My-Proj" in h["additionalContext"]  # sanitized cwd
    path = str(tmp_path / "handoffs" / "-projectnb-x-My-Proj" / "8963259.md")
    assert f"{path}.tmp" in h["additionalContext"] and f"mv {path}.tmp {path}" in h["additionalContext"]
    assert "latest.md" not in h["additionalContext"]
    _run_main(monkeypatch, tmp_path, tx, "c1")
    assert capsys.readouterr().out == ""  # same commit: silent
    tx2 = _committed_tx(tmp_path, 190_000, tool_id="toolu_B", ts="2026-10-22T12:30:00Z", cmd=WAVE_CMD)
    _run_main(monkeypatch, tmp_path, tx2, "c1")
    assert "systemMessage" in json.loads(capsys.readouterr().out)  # a new wave event re-arms


def test_clear_signal_needs_clear_min_and_env_overrides(tmp_path, monkeypatch, capsys):
    tx = _committed_tx(tmp_path, 120_000, cmd=WAVE_CMD)
    _run_main(monkeypatch, tmp_path, tx, "c2")
    assert capsys.readouterr().out == ""  # below 150k
    _run_main(monkeypatch, tmp_path, tx, "c3", clear_min=100_000)
    assert "systemMessage" in json.loads(capsys.readouterr().out)


def test_clear_signal_not_without_boundary(tmp_path, monkeypatch, capsys):
    tx = _turns(tmp_path, [_user("go", "2026-10-22T11:50:00Z"), _bash("ls", "2026-10-22T11:58:00Z")])
    tx.write_text(tx.read_text().replace('"id": "2026-10-22T11:58:00Z"', '"id": "m", "usage": {"input_tokens": 200000}'))
    monkeypatch.setattr(cn.dt, "datetime", type("D", (cn.dt.datetime,), {"now": classmethod(lambda c, tz=None: c(2026, 10, 22, 11, 59, tzinfo=tz))}))
    _run_main(monkeypatch, tmp_path, tx, "c4")
    assert capsys.readouterr().out == ""


def test_handoff_path_is_keyed_and_shared_with_session_handoff():
    import session_handoff as sh
    assert cn.handoff_path is sh.handoff_path  # one home for the path
    assert cn.handoff_path("/a/b c/d_e", {"JOB_ID": "9"}, "/h").as_posix() == "/h/-a-b-c-d-e/9.md"
    assert cn.handoff_path("/a", {"JOB_ID": "10"}, "/h") != cn.handoff_path("/a", {"JOB_ID": "11"}, "/h")


def test_clear_signal_replaces_the_compact_nudge(tmp_path, monkeypatch, capsys):
    _run_main(monkeypatch, tmp_path, _committed_tx(tmp_path, 350_000, cmd=WAVE_CMD), "c5")
    o = json.loads(capsys.readouterr().out)
    assert "systemMessage" in o and "/clear" in o["hookSpecificOutput"]["additionalContext"]
    assert "/compact" not in o["hookSpecificOutput"]["additionalContext"]
    _run_main(monkeypatch, tmp_path, _committed_tx(tmp_path, 550_000, tool_id="toolu_Z", cmd=WAVE_CMD), "c6")
    assert "/compact" not in capsys.readouterr().out  # firm band too: one message, not two


def test_compact_nudge_still_fires_without_clear_signal():
    assert "/compact" in cn.message(350_000, "next", {}, cn.DEFAULT_THRESHOLD, boundary="commit")[0]


# --- owner 2026-11-26: /clear only at wave/phase boundaries; commit and idle give the compact nudge only ---
def _agent(subagent, ts, tool="Agent"):
    return {"type": "assistant", "timestamp": ts, "message": {"id": ts, "content": [
        {"type": "tool_use", "id": "toolu_" + subagent, "name": tool, "input": {"subagent_type": subagent}}]}}


def _with_usage(entries, ctx):
    entries[-1]["message"]["usage"] = {"input_tokens": ctx, "cache_creation_input_tokens": 0, "cache_read_input_tokens": 0}
    return entries


NOW = cn.dt.datetime(2026, 10, 22, 12, 0, tzinfo=cn.dt.timezone.utc)


def test_retro_officer_dispatch_is_a_wave_boundary(tmp_path, monkeypatch, capsys):
    for sub, tool in (("retro-officer", "Agent"), ("aim-keeper", "Task")):
        p = _turns(tmp_path, [_user("go", "2026-10-22T11:50:00Z"), _agent(sub, "2026-10-22T11:58:00Z", tool)])
        assert cn.boundary(p, NOW) == "wave", sub
    other = _turns(tmp_path, [_user("go", "2026-10-22T11:50:00Z"), _agent("implementer", "2026-10-22T11:58:00Z")])
    assert cn.boundary(other, NOW) is None  # fail proof: only the subagent_type differs
    tx = _turns(tmp_path, [_user("go", "2026-10-22T11:50:00Z")] + _with_usage([_agent("retro-officer", "2026-10-22T11:58:00Z")], 250_000))
    _run_main(monkeypatch, tmp_path, tx, "w1")
    o = json.loads(capsys.readouterr().out)
    assert "wave/phase boundary at 250k" in o["systemMessage"] and "/compact" not in o["hookSpecificOutput"]["additionalContext"]


def test_phase_state_commit_is_a_wave_boundary(tmp_path, monkeypatch, capsys):
    for cmd in (WAVE_CMD, "git add docs/phases/p3.md && git commit -m x", "git commit -m x PROJECT_STATE.md"):
        p = _turns(tmp_path, [_user("go", "2026-10-22T11:50:00Z"), _bash(cmd, "2026-10-22T11:58:00Z")])
        assert cn.boundary(p, NOW) == "wave", cmd
    for cmd in ("git commit -m x", "cat PROJECT_STATE.md", "git add src/a.py && git commit -m 'x'\ngit log"):
        p = _turns(tmp_path, [_user("go", "2026-10-22T11:50:00Z"), _bash(cmd, "2026-10-22T11:58:00Z")])
        assert cn.boundary(p, NOW) == ("commit" if "commit" in cmd else None), cmd
    _run_main(monkeypatch, tmp_path, _committed_tx(tmp_path, 250_000, cmd=WAVE_CMD), "w2")
    assert "systemMessage" in json.loads(capsys.readouterr().out)


def test_plain_commit_gives_compact_nudge_not_clear(tmp_path, monkeypatch, capsys):
    _run_main(monkeypatch, tmp_path, _committed_tx(tmp_path, 250_000), "p1")
    o = json.loads(capsys.readouterr().out)
    assert "systemMessage" not in o and "/compact" in o["hookSpecificOutput"]["additionalContext"]
    assert "/clear" not in o["hookSpecificOutput"]["additionalContext"]
    _run_main(monkeypatch, tmp_path, _committed_tx(tmp_path, 180_000), "p2")
    assert capsys.readouterr().out == ""  # below the 200k compact start; same commit at 250k above spoke


def test_idle_gives_compact_nudge_not_clear(tmp_path, monkeypatch, capsys):
    tx = _turns(tmp_path, [_user("go", "2026-10-22T11:00:00Z")] + _with_usage([_bash("ls", "2026-10-22T11:10:00Z")], 250_000))
    _run_main(monkeypatch, tmp_path, tx, "i1")  # the real clock is years past the transcript: idle
    o = json.loads(capsys.readouterr().out)
    assert "systemMessage" not in o and "idle" in o["hookSpecificOutput"]["additionalContext"]
    assert "/compact" in o["hookSpecificOutput"]["additionalContext"]


def test_wave_marker_behind_a_later_commit_wins(tmp_path):
    entries = [_user("go", "2026-10-22T11:50:00Z"), _agent("aim-keeper", "2026-10-22T11:55:00Z"),
               _bash("git commit -m x", "2026-10-22T11:58:00Z")]
    kind, key = cn.boundary_info(_turns(tmp_path, entries), NOW)
    assert (kind, key) == ("wave", "toolu_aim-keeper")
    assert cn.boundary(_turns(tmp_path, entries[:1] + entries[2:]), NOW) == "commit"  # fail proof: marker removed
    old = [_agent("aim-keeper", "2026-10-22T11:40:00Z")] + entries[:1] + entries[2:]
    cn._CACHE.clear()  # same path and byte size as the first file: mtime_ns can tie on NFS
    assert cn.boundary(_turns(tmp_path, old), NOW) == "commit"  # a marker before the last prompt does not count
