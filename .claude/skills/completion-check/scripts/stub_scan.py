#!/usr/bin/env python3
"""Flag unfinished code: empty bodies, NotImplementedError, swallowed excepts returning empty, TODO/FIXME/shortcut."""
import ast
import re
import sys
from pathlib import Path

MARK = re.compile(r"#\s*(TODO|FIXME|XXX|shortcut:)", re.I)


def _empty(body):
    """True when a body is only `pass`, `...` and/or a docstring."""
    def trivial(s):
        if isinstance(s, ast.Pass):
            return True
        return (isinstance(s, ast.Expr) and isinstance(s.value, ast.Constant)
                and (s.value.value is Ellipsis or isinstance(s.value.value, str)))
    return all(trivial(s) for s in body)


def scan(path: Path):
    src = path.read_text(errors="replace")
    out = []
    for n, line in enumerate(src.splitlines(), 1):
        if MARK.search(line):
            out.append((n, "todo", line.strip()[:80]))
    try:
        tree = ast.parse(src)
    except SyntaxError as e:
        return [(e.lineno or 0, "syntax-error", str(e))]
    interface = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and any(
                (getattr(b, "id", None) or getattr(b, "attr", None)) in ("Protocol", "ABC") for b in node.bases):
            interface |= {id(n) for n in node.body}
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and id(node) in interface:
            continue
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            decos = {getattr(d, "id", getattr(d, "attr", "")) for d in node.decorator_list}
            if "abstractmethod" in decos or "overload" in decos:
                continue
            if _empty(node.body):
                out.append((node.lineno, "empty-body", node.name))
            for s in ast.walk(node):
                if isinstance(s, ast.Raise) and "NotImplementedError" in ast.unparse(s):
                    out.append((s.lineno, "not-implemented", node.name))
        if isinstance(node, ast.ExceptHandler) and (
                node.type is None or ast.unparse(node.type) in ("Exception", "BaseException")):
            for s in node.body:
                if isinstance(s, ast.Return) and s.value is not None and ast.unparse(s.value) in ("[]", "{}", "None", "''", '""', "()"):
                    out.append((s.lineno, "swallowed-except", ast.unparse(s)))
                if isinstance(s, ast.Pass):
                    out.append((s.lineno, "swallowed-except", "pass"))
    return out


def main(argv):
    hits = 0
    for a in argv:
        for p in ([Path(a)] if Path(a).is_file() else sorted(Path(a).rglob("*.py"))):
            for n, tag, what in scan(p):
                print(f"{p}:{n}: {tag}: {what}")
                hits += 1
    return 1 if hits else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
