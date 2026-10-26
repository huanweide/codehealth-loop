"""EngHealth — engineering-process maturity (the 12th axis, synthesizing the
`enghealth` unified-runner concept). Advisory, not a hard gate: it measures
whether the repo carries the basic signals of a maintained project —
LICENSE, README, CI configuration, and a self-test setup. Low coverage lowers
the score but never hard-fails (these are process recommendations, not defects).
"""
from __future__ import annotations
import os
import re
from _common import is_dir, score_from

SIGNALS = [
    ("LICENSE", r"^license(\.|$)", "legal clarity for consumers"),
    ("README", r"^readme(\.|$)", "entry point / docs"),
    ("CI", r"^.github[\\/]workflows[\\/].+\.ya?ml$", "continuous integration gate"),
    ("tests", r"(^|[\/\\])(test|tests|spec|__tests__)[\/\\]", "automated verification"),
]


def _scan_signals(base: str) -> dict:
    present = {name: False for name, _, _ in SIGNALS}
    for dirpath, dirnames, filenames in os.walk(base):
        dirnames[:] = [d for d in dirnames if d not in {".git", "node_modules", "__pycache__", "tests"}]
        for fn in filenames:
            relp = os.path.relpath(os.path.join(dirpath, fn), base)
            for name, pat, _ in SIGNALS:
                if re.search(pat, relp, re.I):
                    present[name] = True
    return present


def evaluate(root: str) -> dict:
    base = root if is_dir(root) else os.path.dirname(root)
    present = _scan_signals(base)
    missing = [n for n, _, _ in SIGNALS if not present[n]]
    findings = [{"file": ".", "line": 0, "severity": "low",
                 "rule": f"missing-{n.lower()}", "why": f"缺少 {n}（过程成熟度信号）"} for n in missing]
    score = score_from(findings, base=100)
    evidence = "EngHealth process signals: " + ", ".join(
        f"{n}={'y' if present[n] else 'n'}" for n, _, _ in SIGNALS)
    return {"axis": 12, "name": "EngHealth", "passed": True,  # advisory only
            "score": score, "scanned": len(SIGNALS), "findings": findings,
            "evidence": evidence}
