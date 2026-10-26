"""TypeDoctor — TypeScript/JS type-discipline smells (ported from doctors/packages/typedoctor).

Detects: explicit-any in type annotations, any-cast (`as any` / `as unknown as`),
and ts-ignore family comments. Mirrors the original dogfood discipline: skips
`.d.ts` (any is legal there), comments, string/JSX literals, and regex sources
so the judge never flags its own code or legitimate text.
"""
from __future__ import annotations
import os
import re
from _common import targets, rel, score_from, has_high

TS_EXTS = (".ts", ".tsx", ".js", ".jsx", ".vue", ".svelte")
SKIP_FILE_RE = re.compile(r"\.d\.ts$", re.I)

# Strip line comments and string/template/regex literals so we only judge code.
_STRIP_RE = re.compile(
    r"//[^\n]*"                              # line comment
    r"|/\*.*?\*/"                           # block comment
    r"|\"(?:\\.|[^\"\\])*\""                # double string
    r"|'(?:\\.|[^'\\])*'"                   # single string
    r"|`(?:\\.|[^`\\])*`"                   # template string
    r"|/(?:\\.|[^/\\\n])*/[gimsuy]*"        # regex literal
    , re.S)


def _code_only(src: str) -> str:
    return _STRIP_RE.sub(" ", src)


def evaluate(root: str) -> dict:
    findings = []
    scanned = 0
    for p in targets(root, TS_EXTS):
        if SKIP_FILE_RE.search(p):
            continue
        try:
            with open(p, encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()
        except Exception:
            continue
        code = _code_only("".join(lines))
        for i, raw in enumerate(lines, 1):
            line_code = _code_only(raw)
            # T1 explicit-any: `: any` type annotation (not JSX <any> element)
            if re.search(r":\s*any\b", line_code):
                findings.append({"file": rel(p, root), "line": i, "severity": "medium",
                                 "rule": "explicit-any", "why": "显式 any 注解（类型系统洞）"})
            # T2 any-cast: `as any` / `as readonly any` / `as unknown as`
            if re.search(r"\bas\s+(readonly\s+)?any\b", line_code) or re.search(r"\bas\s+unknown\s+as\b", line_code):
                findings.append({"file": rel(p, root), "line": i, "severity": "medium",
                                 "rule": "any-cast", "why": "any 强转（类型信息被丢弃）"})
            # T3 ts-ignore family
            if re.search(r"@ts-(ignore|nocheck|expect-error)\b", line_code):
                findings.append({"file": rel(p, root), "line": i, "severity": "medium",
                                 "rule": "ts-ignore-comment", "why": "ts-ignore 注释（静默压制类型错误）"})
        scanned += 1

    score = score_from(findings)
    # type smells are medium -> never hard-fail, but surfaced as health loss
    passed = not has_high(findings)
    evidence = f"TypeDoctor scanned {scanned} TS/JS file(s); {len(findings)} type-smell(s) found"
    return {"axis": 10, "name": "TypeDoctor", "passed": passed, "score": score,
            "scanned": scanned, "findings": findings[:20], "evidence": evidence}
