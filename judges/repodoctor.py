"""RepoDoctor — git-repo hygiene (ported from doctors/packages/repodoctor).

Checks: tracked .env, plaintext secrets, oversized files, missing LICENSE /
README, package.json without a lockfile. Filesystem-based and deterministic;
does not require git.
"""
from __future__ import annotations
import os
import re
from _common import targets, is_dir, rel, score_from, has_high, SECRET_RE

ENVFILE_RE = re.compile(r"^(\.env|env\.)", re.I)
LARGE_BYTES = 1024 * 1024
SRC_EXTS = (".py", ".js", ".ts", ".tsx", ".jsx", ".java", ".go", ".rb", ".php", ".env")


def _scan_secrets_and_large(root):
    findings = []
    scanned = 0
    for p in targets(root, SRC_EXTS):
        base = os.path.basename(p)
        if ENVFILE_RE.match(base):
            findings.append({"file": rel(p, root), "line": 0, "severity": "high",
                             "rule": "env-tracked", "why": f"{base} 进入仓库（密钥泄露高风险）"})
            scanned += 1
            continue
        if p.endswith(".env"):
            continue
        try:
            with open(p, encoding="utf-8", errors="ignore") as f:
                for i, line in enumerate(f, 1):
                    if SECRET_RE.search(line):
                        findings.append({"file": rel(p, root), "line": i, "severity": "high",
                                         "rule": "secret-leak",
                                         "why": f"疑似明文密钥: {line.strip()[:24]}…"})
            if os.path.getsize(p) > LARGE_BYTES:
                findings.append({"file": rel(p, root), "line": 0, "severity": "medium",
                                 "rule": "large-file",
                                 "why": f"{os.path.getsize(p)//1024}KB 大文件（应走 LFS/外部存储）"})
        except Exception:
            pass
        scanned += 1
    return findings, scanned


def _scan_repo_meta(root):
    if not is_dir(root):
        return []
    tracked = os.listdir(root)
    findings = []
    if not any(re.match(r"^license(\.|$)", t, re.I) for t in tracked):
        findings.append({"file": ".", "line": 0, "severity": "medium",
                         "rule": "no-license", "why": "仓库缺 LICENSE"})
    if not any(re.match(r"^readme(\.|$)", t, re.I) for t in tracked):
        findings.append({"file": ".", "line": 0, "severity": "medium",
                         "rule": "no-readme", "why": "仓库缺 README"})
    if "package.json" in tracked and not any(
        re.match(r"^(package-lock\.json|yarn\.lock|pnpm-lock\.yaml|npm-shrinkwrap\.json)$", t, re.I)
            for t in tracked):
        findings.append({"file": ".", "line": 0, "severity": "medium",
                         "rule": "no-lockfile", "why": "package.json 无锁文件（依赖不可复现）"})
    return findings


def evaluate(root: str) -> dict:
    findings, scanned = _scan_secrets_and_large(root)
    findings += _scan_repo_meta(root)
    score = score_from(findings)
    passed = not has_high(findings)
    has_lic = is_dir(root) and any(re.match(r"^license", t, re.I) for t in os.listdir(root))
    has_readme = is_dir(root) and any(re.match(r"^readme", t, re.I) for t in os.listdir(root))
    evidence = (f"RepoDoctor scanned {scanned} file(s); {len(findings)} finding(s); "
                f"has-license={'y' if has_lic else 'n'}; has-readme={'y' if has_readme else 'n'}")
    return {"axis": 1, "name": "RepoDoctor", "passed": passed, "score": score,
            "scanned": scanned, "findings": findings[:20], "evidence": evidence}
