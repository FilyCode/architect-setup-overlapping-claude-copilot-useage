#!/usr/bin/env python3
"""Import-graph reachability for any src-layout package, via EnzymeFinder's audit_reachability.py.

The EnzymeFinder script reads REPO_ROOT, SRC_ROOT, PACKAGE_ROOT and PACKAGE_NAME as module
globals at call time; this wrapper repoints them and runs its main(). It reads the target
repo's pyproject.toml [project.scripts], scripts/*.py and scripts/scc-submissions/*.sh as
entry surfaces when present. Positive control: on EnzymeFinder itself the output is identical
to running the original (tests/test_reach.py).
"""
import argparse
import importlib.util
import sys
from pathlib import Path

AUDIT = Path("/projectnb/liu-scc/philipp/projects/EnzymeFinder/scripts/audit_reachability.py")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo", required=True, help="repository root (contains src/<package>)")
    ap.add_argument("--package", required=True, help="top-level import name, e.g. enzymefinder")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    spec = importlib.util.spec_from_file_location("audit_reachability", AUDIT)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["audit_reachability"] = mod
    spec.loader.exec_module(mod)
    repo = Path(a.repo).resolve()
    mod.REPO_ROOT = repo
    mod.SRC_ROOT = repo / "src"
    mod.PACKAGE_ROOT = mod.SRC_ROOT / a.package
    mod.PACKAGE_NAME = a.package
    sys.argv = [str(AUDIT)] + (["--json"] if a.json else [])
    return mod.main()


if __name__ == "__main__":
    sys.exit(main())
