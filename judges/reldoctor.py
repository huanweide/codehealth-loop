"""RelDoctor — release hygiene: version / git tag / CHANGELOG three-way consistency
(port of doctors/packages/reldoctor). Git-aware: when git history is unavailable
the tag/CHANGELOG checks degrade to `manual` (honest, not a fake pass).
"""
from __future__ import annotations
import os
import json
import re
from _common import is_dir, score_from, has_high, git_available, git_tags

SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?$")


def _load_version(root):
    pj = os.path.join(root, "package.json") if is_dir(root) else os.path.join(os.path.dirname(root), "package.json")
    if not os.path.isfile(pj):
        return None
    try:
        with open(pj, encoding="utf-8") as f:
            return json.load(f).get("version")
    except Exception:
        return None


def _check_semver(version):
    if version is not None and (not isinstance(version, str) or not SEMVER_RE.match(version)):
        return [{"file": "package.json", "line": 0, "severity": "high",
                 "rule": "version-not-semver", "why": f"version '{version}' 非合法 semver"}]
    return []


def _check_tags(root, version):
    if not git_available():
        return [{"file": ".", "line": 0, "severity": "medium", "rule": "manual-tag",
                 "why": "git 不可用 — version/tag/CHANGELOG 一致性需人工核对"}]
    tags = git_tags(root)
    out = []
    semver_tags = [t.lstrip("vV") for t in tags if SEMVER_RE.match(t.lstrip("vV"))]
    if version and semver_tags:
        latest = sorted(semver_tags, key=lambda v: [int(x) for x in v.split("-")[0].split(".")])[-1]
        if latest != version:
            out.append({"file": ".", "line": 0, "severity": "medium", "rule": "version-tag-mismatch",
                        "why": f"package.json version {version} 与最新 tag {latest} 不一致"})
    return out


def _check_changelog(root, version):
    cl_path = os.path.join(root, "CHANGELOG.md") if is_dir(root) else os.path.join(os.path.dirname(root), "CHANGELOG.md")
    if not version:
        return []
    if not os.path.isfile(cl_path):
        return [{"file": ".", "line": 0, "severity": "medium", "rule": "no-changelog",
                 "why": "声明了 version 但无 CHANGELOG.md"}]
    with open(cl_path, encoding="utf-8", errors="ignore") as f:
        cl = f.read()
    if re.search(r"\b" + re.escape(version) + r"\b", cl) is None:
        return [{"file": "CHANGELOG.md", "line": 0, "severity": "medium",
                 "rule": "changelog-missing-version", "why": f"CHANGELOG 不含当前 version {version} 章节"}]
    return []


def evaluate(root: str) -> dict:
    version = _load_version(root)
    findings = _check_semver(version) + _check_tags(root, version) + _check_changelog(root, version)
    score = score_from(findings)
    passed = not has_high(findings)
    evidence = f"RelDoctor: version={version}; {len(findings)} finding(s)"
    return {"axis": 8, "name": "RelDoctor", "passed": passed, "score": score,
            "scanned": 1, "findings": findings[:20], "evidence": evidence}
