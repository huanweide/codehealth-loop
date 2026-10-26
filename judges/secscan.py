"""Perception Layer · Axis 7 — Security Anti-Pattern Scanner (secscan).

Real static probe: greps source for dangerous call patterns and surfaces the
exact file:line evidence. This is the *SecScan* axis of the self-healing
engineering-health engine. No LLM, no network, deterministic.
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


def evaluate(root: str, max_findings: int = 50) -> dict:
    findings = []
    scanned = 0
    for dirpath, _, files in os.walk(root):
        if any(seg in dirpath for seg in ("/node_modules/", "\\node_modules\\", "/.git/", "\\.git\\")):
            continue
        for fn in files:
            if not fn.endswith((".py", ".js", ".ts", ".jsx", ".tsx", ".mjs", ".cjs")):
                continue
            scanned += 1
            path = os.path.join(dirpath, fn)
            try:
                with open(path, "r", encoding="utf-8", errors="ignore") as fh:
                    for i, line in enumerate(fh, 1):
                        for pat, sev, why in PATTERNS:
                            if re.search(pat, line):
                                findings.append(
                                    {"file": os.path.relpath(path, root), "line": i,
                                     "sev": sev, "why": why, "snippet": line.strip()[:120]}
                                )
                                if len(findings) >= max_findings:
                                    break
            except OSError:
                continue
    high = sum(1 for f in findings if f["sev"] == "high")
    # score: 100 minus penalty; high costs more than mid
    penalty = high * 12 + (len(findings) - high) * 3
    score = max(0, 100 - penalty)
    passed = high == 0 and len(findings) <= 3
    return {
        "axis": 7, "name": "SecScan", "passed": passed,
        "score": score, "scanned": scanned,
        "findings": findings[:max_findings],
        "evidence": f"scanned {scanned} files, {len(findings)} hits ({high} high)",
    }
