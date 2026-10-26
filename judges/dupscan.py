"""Perception Layer · Axis 9 — Duplicate Code Block Scanner (dupscan).

Real probe: tokenizes each source file into normalized 4-line blocks, hashes
them, and reports blocks that recur across the tree. Surfaces the concrete
file:line pairs so the convergence loop can target refactors. Offline, no LLM.
"""
from __future__ import annotations
import hashlib
import os
import re

BLOCK = 4
NORM = re.compile(r"\s+")


def _blocks(text: str):
    lines = [NORM.sub(" ", ln).strip() for ln in text.splitlines()]
    lines = [ln for ln in lines if ln]
    for i in range(len(lines) - BLOCK + 1):
        yield hashlib.md5(" ".join(lines[i:i + BLOCK]).encode()).hexdigest(), i + 1


def evaluate(root: str, ratio_thresh: float = 0.05, max_findings: int = 50) -> dict:
    seen = {}
    file_count = 0
    for dirpath, _, files in os.walk(root):
        if any(seg in dirpath for seg in ("/node_modules/", "\\node_modules\\", "/.git/", "\\.git\\")):
            continue
        for fn in files:
            if not fn.endswith((".py", ".js", ".ts", ".jsx", ".tsx", ".mjs", ".cjs")):
                continue
            file_count += 1
            path = os.path.join(dirpath, fn)
            try:
                with open(path, "r", encoding="utf-8", errors="ignore") as fh:
                    src = fh.read()
            except OSError:
                continue
            rel = os.path.relpath(path, root)
            for h, ln in _blocks(src):
                seen.setdefault(h, []).append(f"{rel}:{ln}")
    dups = {h: locs for h, locs in seen.items() if len(locs) > 1}
    total_blocks = sum(len(v) for v in seen.values())
    dup_blocks = sum(len(v) for v in dups.values())
    ratio = (dup_blocks / total_blocks) if total_blocks else 0.0
    findings = []
    for h, locs in sorted(dups.items(), key=lambda kv: -len(kv[1]))[:max_findings]:
        findings.append({"hash": h[:8], "occurrences": len(locs), "locations": locs[:10]})
    score = max(0, 100 - int(ratio * 100 * 2))
    passed = ratio <= ratio_thresh
    return {
        "axis": 9, "name": "DupScan", "passed": passed,
        "score": score, "scanned": file_count,
        "findings": findings,
        "evidence": f"{file_count} files, dup-ratio={ratio:.2%} (thresh {ratio_thresh:.0%}), {len(dups)} dup blocks",
    }
