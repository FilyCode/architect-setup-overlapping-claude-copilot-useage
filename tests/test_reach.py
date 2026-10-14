import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REACH = ROOT / ".claude/skills/completion-check/scripts/reach.py"
EF = Path("/projectnb/liu-scc/philipp/projects/EnzymeFinder")


def test_wrapper_reproduces_enzymefinder_audit():
    direct = subprocess.run([sys.executable, str(EF / "scripts/audit_reachability.py")],
                            capture_output=True, text=True, cwd=EF, timeout=600)
    wrapped = subprocess.run([sys.executable, str(REACH), "--repo", str(EF), "--package", "enzymefinder"],
                             capture_output=True, text=True, timeout=600)
    assert direct.stdout.strip(), direct.stderr[-500:]
    assert wrapped.returncode == direct.returncode
    assert wrapped.stdout == direct.stdout


def test_overrides_take_effect(tmp_path):
    pkg = tmp_path / "src" / "pkgx"
    pkg.mkdir(parents=True)
    (pkg / "__init__.py").write_text("")
    (pkg / "cli.py").write_text("from pkgx import used\n\ndef main():\n    return used.f()\n")
    (pkg / "used.py").write_text("def f():\n    return 1\n")
    (pkg / "orphan.py").write_text("def g():\n    return 2\n")
    (tmp_path / "pyproject.toml").write_text('[project]\nname = "pkgx"\n[project.scripts]\npkgx = "pkgx.cli:main"\n')
    r = subprocess.run([sys.executable, str(REACH), "--repo", str(tmp_path), "--package", "pkgx"],
                       capture_output=True, text=True, timeout=120)
    assert "pkgx.orphan" in r.stdout, r.stdout + r.stderr[-800:]
    assert "Reachable from CLI: 3" in r.stdout
