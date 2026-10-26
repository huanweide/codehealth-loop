"""Perception Layer · Axis 4 — Cyclomatic Complexity Scanner (cycscan).

Real probe: for Python it uses the `ast` module to count decision points per
function; for JS/TS it falls back to a keyword heuristic. Emits the worst
offenders with file:line evidence so the convergence loop has something
concrete to act on. Zero-dependency, offline, deterministic.
"""
from __future__ import annotations
import ast
import os
import re

PY_DECISION = (ast.If, ast.For, ast.AsyncFor, ast.While, ast.With, ast.AsyncWith,
               ast.Try, ast.ExceptHandler, ast.BoolOp, ast.IfExp, ast.comprehension)
JS_BRANCH = re.compile(r"\b(if|for|while|catch|&&|\|\||\?)\b")


def _py_cc(node: ast.AST) -> int:
    cc = 1
    for child in ast.walk(node):
        if isinstance(child, PY_DECISION):
            if isinstance(child, ast.BoolOp):
                cc += len(child.values) - 1
            elif isinstance(child, ast.comprehension):
                cc += 1 + len(child.ifs)
            else:
                cc += 1
    return cc


def evaluate(root: str, threshold: int = 12, max_findings: int = 50) -> dict:
    offenders = []
    scanned = 0
    for dirpath, _, files in os.walk(root):
        if any(seg in dirpath for seg in ("/node_modules/", "\\node_modules\\", "/.git/", "\\.git\\")):
            continue
        for fn in files:
            if fn.endswith(".py"):
                scanned += 1
                path = os.path.join(dirpath, fn)
                try:
                    tree = ast.parse(open(path, encoding="utf-8", errors="ignore").read())
                except (OSError, SyntaxError):
                    continue
                for n in ast.walk(tree):
                    if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        cc = _py_cc(n)
                        if cc > threshold:
                            offenders.append({"file": os.path.relpath(path, root),
                                              "line": n.lineno, "cc": cc})
            elif fn.endswith((".js", ".ts", ".jsx", ".tsx", ".mjs", ".cjs")):
                scanned += 1
                path = os.path.join(dirpath, fn)
                try:
                    src = open(path, encoding="utf-8", errors="ignore").read()
                except OSError:
                    continue
                # crude per-file heuristic; per-function would need a parser
                cc = len(JS_BRANCH.findall(src))
                if cc > threshold * 4:  # file-level heuristic is noisier
                    offenders.append({"file": os.path.relpath(path, root),
                                      "line": 1, "cc": cc})
    offenders.sort(key=lambda o: -o["cc"])
    worst = offenders[:max_findings]
    score = max(0, 100 - len(worst) * 8)
    passed = len(worst) == 0
    return {
        "axis": 4, "name": "CycScan", "passed": passed,
        "score": score, "scanned": scanned,
        "findings": worst,
        "evidence": f"scanned {scanned} files, {len(worst)} funcs over threshold(>{threshold})",
    }
