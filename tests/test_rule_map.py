# REPO/tests/test_rule_map.py
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import rule_map as rm

H = Path(__file__).resolve().parents[1] / "docs/history/rules-2026-10-14"

def test_extract_counts_are_stable():
    its = [i for f in ("subagent-dispatch.md", "verification.md", "scc.md") for i in rm.items(H / f)]
    assert len(its) == len({(i.file, i.line) for i in its})
    assert any(i.title.startswith("Never dispatch") for i in its)
    assert all(i.kind in ("heading", "bold", "bullet") for i in its)

def test_check_reports_unmapped_and_drift(tmp_path):
    its = rm.items(H / "scc.md")
    tsv = tmp_path / "m.tsv"
    first, second = its[0], its[1]
    tsv.write_text(f"{first.file}\t{first.line}\t{first.title}\tskill:running-sge-jobs\n"
                   f"{second.file}\t{second.line}\tWRONG TITLE\tskill:running-sge-jobs\n")
    errs = rm.check(H, tsv)
    assert any("unmapped" in e for e in errs)
    assert any("drift" in e for e in errs)

def test_bad_destination(tmp_path):
    i = rm.items(H / "scc.md")[0]
    tsv = tmp_path / "m.tsv"
    tsv.write_text(f"{i.file}\t{i.line}\t{i.title}\tsomewhere\n")
    assert any("destination" in e for e in rm.check(H, tsv))
