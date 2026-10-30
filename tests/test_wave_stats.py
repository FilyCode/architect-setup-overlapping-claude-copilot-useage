# REPO/tests/test_wave_stats.py — per-session cost summary for the retro-officer seat
import json
import pytest
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


# --- regressions found by the 2026-10-29 MeMES retro ------------------------------------
# Both were verified against the pre-fix code before being fixed: the explicit-offset bound
# returned 2 calls instead of 1, and the list-content notice returned [] instead of ["zzz"].

def _tz_session(tmp_path):
    """Two calls four hours apart, straddling a local-vs-UTC boundary."""
    main = tmp_path / "tz.jsonl"
    lines = [_call(1, 10_000, "2026-10-29T15:00:00Z"),   # 11:00 EDT
             _call(2, 20_000, "2026-10-29T19:00:00Z")]   # 15:00 EDT
    main.write_text("\n".join(json.dumps(x) for x in lines) + "\n")
    return main


def test_since_with_an_explicit_offset_is_honoured(tmp_path):
    """14:00 EDT == 18:00Z, so only the 19:00Z call is in window."""
    s = ws.summarize(_tz_session(tmp_path), since="2026-10-29T14:00:00-04:00")
    assert s["main"]["calls"] == 1
    assert s["main"]["context_tokens"] == 20_000


def test_since_with_a_trailing_Z_is_honoured(tmp_path):
    s = ws.summarize(_tz_session(tmp_path), since="2026-10-29T18:00:00Z")
    assert s["main"]["calls"] == 1


def test_a_midnight_bound_keeps_the_whole_day(tmp_path):
    s = ws.summarize(_tz_session(tmp_path), since="2026-10-29T00:00:00Z")
    assert s["main"]["calls"] == 2


def test_an_entry_with_no_timestamp_is_kept(tmp_path):
    """Silently dropping it would shrink the window without saying so."""
    main = tmp_path / "nots.jsonl"
    main.write_text(json.dumps({"message": {"id": "x", "usage": {"input_tokens": 7_000}}}) + "\n")
    s = ws.summarize(main, since="2026-10-29T00:00:00Z")
    assert s["main"]["calls"] == 1


def test_turn_limit_notice_in_list_content_is_found(tmp_path):
    """Notices arrive as list-of-blocks far more often than as a bare string.

    The string-only version reported turn_limit_hits: [] for the 2026-10-29 MeMES wave, in
    which two seats demonstrably hit their limits.
    """
    main = tmp_path / "blocks.jsonl"
    note = ("<task-notification><task-id>zzz</task-id><summary>Agent \"y\" stopped at its "
            "35-turn limit (partial result)</summary></task-notification>")
    main.write_text(json.dumps({"timestamp": "2026-10-29T19:00:00Z",
                                "message": {"role": "user",
                                            "content": [{"type": "text", "text": note}]}}) + "\n")
    assert ws.summarize(main)["turn_limit_hits"] == ["zzz"]


# --- R-20261029-2: review-seat share and register delta ---------------------------------
import subprocess  # noqa: E402


def _git(repo, *args):
    return subprocess.run(["git", "-C", str(repo), "-c", "user.name=t", "-c", "user.email=t@t", *args],
                          check=True, capture_output=True, text=True).stdout.strip()


def test_review_seat_share_of_subagent_context(tmp_path):
    # fixture: critic-reviewer 42_000 (review seat), implementer 13_000 (not one)
    s = ws.summarize(_session(tmp_path))
    assert s["review_seats"] == {"context_tokens": 42_000, "subagent_tokens": 55_000, "share": round(42_000 / 55_000, 3)}


def test_review_seat_share_is_zero_not_error_without_subagents(tmp_path):
    main = tmp_path / "s.jsonl"
    main.write_text(json.dumps(_call(1, 10)) + "\n")
    assert ws.summarize(main)["review_seats"] == {"context_tokens": 0, "subagent_tokens": 0, "share": 0.0}


REG_A = "# Register\n\n| ID | Title | Status |\n|---|---|---|\n| D-1 | one | OPEN |\n| D-2 | two | OPEN |\n"
REG_B = REG_A.replace("D-1 | one | OPEN", "D-1 | one | CLOSED") + "| D-3 | three | OPEN |\n| D-4 | four | CLOSED |\n"


def _repo(tmp_path, a_text, b_text, name="REGISTER.md"):
    repo = tmp_path / "repo"
    (repo / "docs").mkdir(parents=True)
    _git(repo, "init", "-q")
    (repo / "docs" / name).write_text(a_text)
    _git(repo, "add", ".")
    _git(repo, "commit", "-qm", "a")
    a = _git(repo, "rev-parse", "HEAD")
    (repo / "docs" / name).write_text(b_text)
    _git(repo, "commit", "-qam", "b")
    return repo, f"{a}..{_git(repo, 'rev-parse', 'HEAD')}"


def test_register_delta_counts_added_and_closed_rows(tmp_path):
    repo, rng = _repo(tmp_path, REG_A, REG_B)
    assert ws.register_delta(repo, rng, "docs/REGISTER.md") == {
        "status_column": "present", "rows_before": 2, "rows_after": 4, "rows_added": 2, "rows_closed": 2}


def test_register_without_status_column_reports_it_instead_of_zero_closed(tmp_path):
    a = "| ID | Title |\n|---|---|\n| 1 | x |\n"
    repo, rng = _repo(tmp_path, a, a + "| 2 | y |\n")
    d = ws.register_delta(repo, rng, "docs/REGISTER.md")
    assert d == {"status_column": "absent", "rows_before": 1, "rows_after": 2, "rows_added": 1}


def test_register_absent_at_range_start_counts_every_row_as_added(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q")
    (repo / "x").write_text("x")
    _git(repo, "add", "x")
    _git(repo, "commit", "-qm", "a")
    a = _git(repo, "rev-parse", "HEAD")
    (repo / "R.md").write_text(REG_A)
    _git(repo, "add", "R.md")
    _git(repo, "commit", "-qm", "b")
    assert ws.register_delta(repo, f"{a}..HEAD", "R.md")["rows_added"] == 2


def test_register_missing_at_range_end_is_an_error_naming_the_check(tmp_path):
    repo, rng = _repo(tmp_path, REG_A, REG_B)
    with pytest.raises(SystemExit, match="register delta"):
        ws.register_delta(repo, rng, "docs/NOPE.md")


def test_cli_repo_range_register_prints_both_sections(tmp_path, capsys):
    repo, rng = _repo(tmp_path, REG_A, REG_B)
    ws.main([str(_session(tmp_path)), "--repo", str(repo), "--range", rng, "--register", "docs/REGISTER.md"])
    out = json.loads(capsys.readouterr().out)
    assert out["review_seats"]["share"] == round(42_000 / 55_000, 3)
    assert out["register"]["rows_added"] == 2
