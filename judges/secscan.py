"""Perception Layer · Axis 7 — Security Anti-Pattern Scanner (secscan).

Real static probe: greps source for dangerous call patterns and surfaces the
exact file:line evidence. Deterministic, no LLM, no network. Comments and
string/template/regex literals are stripped first (dogfood discipline) so a
pattern written *inside* a string, comment or regex never trips a false positive.
"""
from __future__ import annotations
import os
import re

# (pattern, severity, why) — severity in {high, mid}
PATTERNS = [
    (r"\beval\s*\(", "high", "eval() executes arbitrary strings — code-injection surface"),
    (r"\bexec\s*\(", "high", "exec() executes arbitrary strings — code-injection surface"),
    (r"child_process", "mid", "spawns subprocess — audit the command source"),
    (r"new\s+Function\s*\(", "high", "Function() constructor == eval-class injection"),
    (r"innerHTML\s*=", "mid", "untrusted innerHTML assignment — XSS surface"),
    (r"sql.*\+.*\+", "mid", "string-concatenated SQL — prefer parameterized queries"),
]

# Strip comments + string/template literals so we only judge real code.
_STRIP_RE = re.compile(
    r"#[^\n]*"                       # python comment
    r"|//[^\n]*"                     # js line comment
    r"|/\*.*?\*/"                   # js block comment
    r"|\"(?:\\.|[^\"\\])*\""        # double-quoted string
    r"|'(?:\\.|[^'\\])*'"           # single-quoted string
    r"|`(?:\\.|[^`\\])*`"           # template string
    r"|/(?:\\.|[^/\\\n])*/[gimsuy]*"  # regex literal
    , re.S)


def _code_only(src: str) -> str:
    return _STRIP_RE.sub(" ", src)


def _scan_file(path: str, root: str, max_findings: int, collected: list):
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as fh:
            for i, line in enumerate(fh, 1):
                code = _code_only(line)
                for pat, sev, why in PATTERNS:
                    if re.search(pat, code):
                        collected.append({
                            "file": os.path.relpath(path, root), "line": i,
                            "sev": sev, "why": why, "snippet": line.strip()[:120]})
                        if len(collected) >= max_findings:
                            return
    except OSError:
        return


def evaluate(root: str, max_findings: int = 50) -> dict:
    findings = []
    scanned = 0
    for dirpath, _, files in os.walk(root):
        parts = dirpath.split(os.sep)
        if "node_modules" in parts or ".git" in parts or "tests" in parts:
            continue
        for fn in files:
            if not fn.endswith((".py", ".js", ".ts", ".jsx", ".tsx", ".mjs", ".cjs")):
                continue
            scanned += 1
            _scan_file(os.path.join(dirpath, fn), root, max_findings, findings)
            if len(findings) >= max_findings:
                break
        if len(findings) >= max_findings:
            break
    high = sum(1 for f in findings if f["sev"] == "high")
    penalty = high * 12 + (len(findings) - high) * 3
    score = max(0, 100 - penalty)
    passed = high == 0 and len(findings) <= 3
    return {
        "axis": 7, "name": "SecScan", "passed": passed,
        "score": score, "scanned": scanned,
        "findings": findings[:max_findings],
        "evidence": f"scanned {scanned} files, {len(findings)} hits ({high} high)",
    }
