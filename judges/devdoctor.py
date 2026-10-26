"""DevDoctor — dependency & source hygiene (ported from doctors/packages/devdoctor).

Three sub-checks, all static:
  * secrets : plaintext secret patterns in source (see _common.SECRET_RE)
  * bloat   : too many direct dependencies (heuristic threshold)
  * license : SPDX license classification (permissive / weak / strong copyleft)
Cycles detection (present in the JS original) requires dependency-graph analysis
and is flagged `manual` — honest hand-off, not a fake "green".
"""
from __future__ import annotations
import os
import json
from _common import targets, is_dir, rel, score_from, has_high, SECRET_RE

SRC_EXTS = (".py", ".js", ".ts", ".tsx", ".jsx", ".java", ".go", ".rb", ".php", ".env")
BLOAT_THRESHOLD = 60
STRONG = {"GPL", "AGPL", "GPL-2.0", "GPL-3.0", "AGPL-3.0", "EUPL"}
WEAK = {"LGPL", "LGPL-2.1", "LGPL-3.0", "MPL", "MPL-2.0", "EPL", "EPL-2.0"}
PERMISSIVE = {"MIT", "BSD", "ISC", "Apache", "Apache-2.0", "Zlib", "Unlicense", "0BSD", "CC0"}


def _scan_source_secrets(root):
    findings = []
    for p in targets(root, SRC_EXTS):
        if p.endswith(".env") or os.path.basename(p).startswith(".env"):
            continue
        try:
            with open(p, encoding="utf-8", errors="ignore") as f:
                for i, line in enumerate(f, 1):
                    m = SECRET_RE.search(line)
                    if m:
                        findings.append({"file": rel(p, root), "line": i, "severity": "high",
                                         "rule": "source-secret",
                                         "why": f"源码明文密钥: {line.strip()[:24]}…"})
        except Exception:
            pass
    return findings


def _classify(lic):
    u = str(lic).upper()
    if any(s.upper() in u for s in STRONG):
        return "strong"
    if any(w.upper() in u for w in WEAK):
        return "weak"
    if any(p.upper() in u for p in PERMISSIVE):
        return "permissive"
    return "unknown"


def _scan_dependencies(root):
    pj = os.path.join(root, "package.json") if is_dir(root) else os.path.join(os.path.dirname(root), "package.json")
    if not os.path.isfile(pj):
        return []
    findings = []
    try:
        with open(pj, encoding="utf-8") as f:
            pkg = json.load(f)
    except Exception:
        return []
    deps = sum(len(pkg.get(k, {}) or {}) for k in
               ("dependencies", "devDependencies", "peerDependencies", "optionalDependencies"))
    if deps > BLOAT_THRESHOLD:
        findings.append({"file": "package.json", "line": 0, "severity": "medium",
                         "rule": "dep-bloat", "why": f"直接依赖 {deps} 个（> {BLOAT_THRESHOLD}，需审视）"})
    lic = pkg.get("license")
    if lic:
        cls = _classify(lic)
        if cls == "strong":
            findings.append({"file": "package.json", "line": 0, "severity": "low",
                             "rule": "license-strong", "why": f"强 Copyleft 许可证 {lic}（分发需注意）"})
        elif cls == "unknown":
            findings.append({"file": "package.json", "line": 0, "severity": "low",
                             "rule": "license-unknown", "why": f"许可证 {lic} 无法归类（合规风险）"})
    return findings


def evaluate(root: str) -> dict:
    findings = _scan_source_secrets(root) + _scan_dependencies(root)
    scanned = len(targets(root, SRC_EXTS)) if is_dir(root) else (1 if os.path.isfile(root) else 0)
    score = score_from(findings)
    passed = not has_high(findings)
    evidence = (f"DevDoctor scanned {scanned} file(s); {len(findings)} finding(s); "
                f"dependency-cycles=MANUAL (graph analysis needed)")
    return {"axis": 3, "name": "DevDoctor", "passed": passed, "score": score,
            "scanned": scanned, "findings": findings[:20], "evidence": evidence}
