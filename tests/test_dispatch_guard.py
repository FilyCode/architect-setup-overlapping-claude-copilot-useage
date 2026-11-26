import json
import os
import subprocess
import sys
from pathlib import Path

HOOK = Path(__file__).resolve().parents[1] / "workspace-config" / "hooks" / "dispatch_guard.py"


def run(payload, raw=None, tmpdir=None):
    stdin = raw if raw is not None else json.dumps(payload)
    env = {**os.environ, "TMPDIR": str(tmpdir)} if tmpdir else None
    r = subprocess.run([sys.executable, str(HOOK)], input=stdin, capture_output=True, text=True, env=env)
    return r.returncode, r.stdout


def ev(prompt="Implement X", model="opus", sub="implementer", tool="Agent"):
    ti = {"subagent_type": sub, "prompt": prompt}
    if model:
        ti["model"] = model
    return {"tool_name": tool, "tool_input": ti}


def denied(out):
    o = json.loads(out)["hookSpecificOutput"]
    assert o["hookEventName"] == "PreToolUse" and o["permissionDecision"] == "deny"
    return o["permissionDecisionReason"]


def test_opus_without_marker_is_denied_with_fix():
    rc, out = run(ev("\n\nImplement the parser\nthis is a contract change"))
    assert rc == 0
    why = denied(out)
    assert "Opus because:" in why and "model" in why


def test_task_alias_and_claude_opus_id_denied():
    denied(run(ev(tool="Task"))[1])
    denied(run(ev(model="claude-opus-5-5"))[1])


def test_marker_with_reason_passes():
    for first in ("Opus because: cross-module rename of the API", "  opus BECAUSE: needs the whole contract in view",
                  "OPUS because:   ten chars++"):
        assert run(ev(first + "\nbody")) == (0, ""), first
    assert run(ev("\n\nOpus because: long enough reason\nbody")) == (0, "")  # leading blank lines skipped


def test_marker_needs_first_line_and_ten_nonspace_chars():
    denied(run(ev("Implement X\nOpus because: a perfectly good reason"))[1])  # not the first line
    denied(run(ev("Opus because: short"))[1])                                   # 5 chars
    denied(run(ev("Opus because:      a b c d e"))[1])                         # 5 non-space chars, many spaces
    denied(run(ev("Opus because:"))[1])
    denied(run(ev("The old words: cross-module contract retry"))[1])           # old vocabulary no longer passes
    assert run(ev("Opus because: 1234567890")) == (0, "")                       # exactly 10


def test_sonnet_other_seat_other_tool_silent():
    assert run(ev(model="sonnet")) == (0, "")
    assert run(ev(model=None)) == (0, "")
    assert run(ev(sub="reviewer")) == (0, "")
    assert run(ev(tool="Bash")) == (0, "")


def test_malformed_stdin_stays_silent():
    assert run(None, raw="{{") == (0, "")
    assert run({"tool_name": "Agent", "tool_input": "str"}) == (0, "")
    assert run(ev(prompt=None))[0] == 0


# --- brief preflight (owner ruling 2026-11-26) ---------------------------------------------------------------

def brief(prompt, cwd, sub="reviewer", sid="s1"):
    d = ev(prompt, model=None, sub=sub)
    d.update(cwd=str(cwd), session_id=sid)
    return d


def git_repo(path):
    def g(*a):
        subprocess.run(["git", "-C", str(path), "-c", "user.name=t", "-c", "user.email=t@t", *a], check=True,
                       capture_output=True)
    g("init", "-q")
    (path / "f.txt").write_text("x\n")
    g("add", "f.txt")
    g("commit", "-q", "-m", "init")
    return subprocess.run(["git", "-C", str(path), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()


def test_missing_path_denied_existing_passes(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "a.py").write_text("x\n")
    assert run(brief("Read `src/a.py` first", tmp_path), tmpdir=tmp_path) == (0, "")
    why = denied(run(brief("Read `src/b.py` first", tmp_path), tmpdir=tmp_path)[1])
    assert "`src/b.py`: missing" in why and "resubmit the identical prompt" in why


def test_relative_path_resolves_against_git_toplevel(tmp_path):
    git_repo(tmp_path)
    (tmp_path / "sub").mkdir()
    assert run(brief("see `f.txt`", tmp_path / "sub"), tmpdir=tmp_path) == (0, "")           # via toplevel
    denied(run(brief("see `g.txt`", tmp_path / "sub"), tmpdir=tmp_path)[1])


def test_line_beyond_eof_denied(tmp_path):
    (tmp_path / "a.py").write_text("1\n2\n3\n")
    assert run(brief("see `a.py:3` and `a.py:2-3`", tmp_path), tmpdir=tmp_path) == (0, "")
    why = denied(run(brief("see `a.py:4`", tmp_path), tmpdir=tmp_path)[1])
    assert "`a.py:4`: file has only 3 lines" in why
    denied(run(brief("see `a.py:2-9`", tmp_path), tmpdir=tmp_path)[1])


def test_creation_verb_line_and_non_path_tokens_skipped(tmp_path):
    assert run(brief("Create `out/res.tsv` for me", tmp_path), tmpdir=tmp_path) == (0, "")
    denied(run(brief("Read `out/res.tsv` for me", tmp_path), tmpdir=tmp_path)[1])  # same token, verb removed
    for tok in ("out/*.tsv", "<dir>/a.py", "$HOME/x/y.py", "git log -1 --format=%h", "http://x.org/a.py"):
        assert run(brief(f"see `{tok}`", tmp_path), tmpdir=tmp_path) == (0, ""), tok
    home = Path.home()
    assert run(brief(f"see `~/{home.name}_nonexistent_zz.md`", tmp_path), tmpdir=tmp_path)[1]  # ~ is expanded, then missing


def test_head_mismatch_denied_match_passes(tmp_path):
    head = git_repo(tmp_path)
    assert run(brief(f"State: HEAD `{head[:7]}` clean", tmp_path), tmpdir=tmp_path) == (0, "")
    assert run(brief(f"State: HEAD `{head}`", tmp_path), tmpdir=tmp_path) == (0, "")
    why = denied(run(brief("State: HEAD `deadbee` clean", tmp_path), tmpdir=tmp_path)[1])
    assert f"HEAD is now {head[:7]}" in why
    assert run(brief("State: HEAD `deadbee`", tmp_path / "nonexistent"), tmpdir=tmp_path) == (0, "")  # no repo: skip


def test_identical_resubmit_passes_changed_prompt_does_not(tmp_path):
    p = "Read `nope.py`"
    denied(run(brief(p, tmp_path), tmpdir=tmp_path)[1])
    assert run(brief(p, tmp_path), tmpdir=tmp_path) == (0, "")
    denied(run(brief(p + " now", tmp_path), tmpdir=tmp_path)[1])                # different prompt denied again
    denied(run(brief(p, tmp_path, sid="other"), tmpdir=tmp_path)[1])            # different session denied again


def test_non_seat_subagent_types_skipped(tmp_path):
    for sub in ("general-purpose", "Explore", "Plan", "claude-code-guide", "fork", ""):
        assert run(brief("Read `nope.py`", tmp_path, sub=sub), tmpdir=tmp_path) == (0, ""), sub
    denied(run(brief("Read `nope.py`", tmp_path, sub="implementer"), tmpdir=tmp_path)[1])


def test_reason_lists_at_most_15_tokens(tmp_path):
    why = denied(run(brief("\n".join(f"see `m{i}.py`" for i in range(20)), tmp_path), tmpdir=tmp_path)[1])
    assert "`m14.py`" in why and "`m15.py`" not in why and "+5 more" in why


def test_opus_rule_still_denies_before_preflight(tmp_path):
    d = brief("Opus because: short\nbody", tmp_path, sub="implementer")
    d["tool_input"]["model"] = "opus"
    assert "Opus because:" in denied(run(d, tmpdir=tmp_path)[1])
    d["tool_input"]["prompt"] = "Opus because: cross-module rename of the API"
    assert run(d, tmpdir=tmp_path) == (0, "")


# --- preflight false-positive fixes (2026-11-26) ----------------------------------------------------------------

def test_elided_path_skipped_but_real_missing_still_flagged(tmp_path):
    for tok in (".../doc-research/inventory-investigator.md", "…/doc-research/x.md", "a/.../b.md"):
        assert run(brief(f"see `{tok}`", tmp_path), tmpdir=tmp_path) == (0, ""), tok
    assert "`doc-research/inventory-investigator.md`: missing" in denied(
        run(brief("see `doc-research/inventory-investigator.md`", tmp_path), tmpdir=tmp_path)[1])


def test_single_segment_trailing_slash_skipped_but_two_segments_flagged(tmp_path):
    for tok in ("reference/", "implementer-trim/"):
        assert run(brief(f"see `{tok}`", tmp_path), tmpdir=tmp_path) == (0, ""), tok
    assert "`reference/sub/`: missing" in denied(run(brief("see `reference/sub/`", tmp_path), tmpdir=tmp_path)[1])
    assert "`reference/a.md`: missing" in denied(run(brief("see `reference/a.md`", tmp_path), tmpdir=tmp_path)[1])


def test_absolute_token_with_nonexistent_root_segment_skipped(tmp_path):
    assert not Path("/provenance").exists()
    assert run(brief("metric `/provenance/n_hits`", tmp_path), tmpdir=tmp_path) == (0, "")
    why = denied(run(brief("see `/projectnb/zz_no_such_dir_9/a.md`", tmp_path), tmpdir=tmp_path)[1])
    assert "`/projectnb/zz_no_such_dir_9/a.md`: missing" in why
