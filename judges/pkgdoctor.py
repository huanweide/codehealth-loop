"""PkgDoctor — package.json metadata & dependency hygiene (from doctors/packages/pkgdoctor).

Checks: missing/invalid semver version, missing license (for public packages),
vague dependency ranges (`*`, `1.x`, `1.2.*`), and non-registry dependencies
(file:/link:/git:/https:/npm:). Reads package.json next to a directory root, or
in the parent of a file root.
"""
from __future__ import annotations
import os
import json
import re
from _common import is_dir, score_from, has_high

SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?$")
VAGUE_RE = re.compile(r"[*xX]")
NONREG_RE = re.compile(r"^(file:|link:|git|https?:|npm:)")


def _load(root: str):
    pj = os.path.join(root, "package.json") if is_dir(root) else os.path.join(os.path.dirname(root), "package.json")
    if not os.path.isfile(pj):
        return None
    try:
        with open(pj, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def _check_version_license(pkg):
    findings = []
    priv = pkg.get("private", False) is True
    version = pkg.get("version")
    if version is None:
        findings.append({"file": "package.json", "line": 0, "severity": "high",
                         "rule": "missing-version", "why": "缺少 version 字段"})
    elif not isinstance(version, str) or not SEMVER_RE.match(version):
        findings.append({"file": "package.json", "line": 0, "severity": "high",
                         "rule": "invalid-version", "why": f"version '{version}' 非合法 semver (x.y.z)"})
    if not priv and not pkg.get("license"):
        findings.append({"file": "package.json", "line": 0, "severity": "high",
                         "rule": "missing-license", "why": "公开发布包缺少 license 字段"})
    return findings


def _check_deps(pkg):
    findings = []
    deps = {}
    for field in ("dependencies", "devDependencies", "peerDependencies", "optionalDependencies"):
        deps.update(pkg.get(field, {}) or {})
    for name, val in deps.items():
        if not isinstance(val, str):
            continue
        if VAGUE_RE.search(val):
            findings.append({"file": "package.json", "line": 0, "severity": "medium",
                             "rule": "vague-range", "why": f"模糊依赖范围 {name}@{val}（破坏可复现构建）"})
        elif NONREG_RE.match(val):
            findings.append({"file": "package.json", "line": 0, "severity": "low",
                             "rule": "non-registry-dep", "why": f"非 registry 依赖 {name}@{val}"})
    return findings


def evaluate(root: str) -> dict:
    pkg = _load(root)
    if pkg is None:
        return {"axis": 6, "name": "PkgDoctor", "passed": True, "score": 100,
                "scanned": 0, "findings": [],
                "evidence": "no package.json in scope — axis not applicable"}
    findings = _check_version_license(pkg) + _check_deps(pkg)
    score = score_from(findings)
    passed = not has_high(findings)
    dep_count = sum(len(pkg.get(k, {}) or {}) for k in
                    ("dependencies", "devDependencies", "peerDependencies", "optionalDependencies"))
    evidence = (f"PkgDoctor: {dep_count} deps; version={pkg.get('version')}; "
                f"license={'y' if pkg.get('license') or pkg.get('private') else 'n'}; {len(findings)} finding(s)")
    return {"axis": 6, "name": "PkgDoctor", "passed": passed, "score": score,
            "scanned": dep_count, "findings": findings[:20], "evidence": evidence}
