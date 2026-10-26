"""A11yDoctor — Web accessibility anti-patterns (ported from doctors/packages/a11ydoctor).

Detects (static, no DOM): <img> missing alt, form controls without an
accessible name / associated label, heading-level jumps, deprecated presentational
tags (blink/marquee/center/font), and clickable div/span without keyboard
handlers. Scans HTML / JSX / TSX / Vue / Svelte. Heuristic, not a full axe-core.
"""
from __future__ import annotations
import os
import re
from _common import targets, rel, score_from, has_high

A11Y_EXTS = (".html", ".htm", ".jsx", ".tsx", ".vue", ".svelte")
IMG_RE = re.compile(r"<img\b", re.I)
IMG_ALT_RE = re.compile(r"<img\b[^>]*\balt\s*=", re.I)
INPUT_RE = re.compile(r"<(input|select|textarea)\b", re.I)
INPUT_NAME_RE = re.compile(r"\b(?:aria-label|aria-labelledby|alt|title)\s*=", re.I)
INPUT_TYPE_HIDDEN = re.compile(r"\btype\s*=\s*[\"']hidden[\"']", re.I)
HEADING_RE = re.compile(r"<h([1-6])\b", re.I)
DEPRECATED_RE = re.compile(r"<(blink|marquee|center|font)\b", re.I)
CLICKABLE_RE = re.compile(r"<(div|span)\b[^>]*\bonclick\b", re.I)
KEYBOARD_RE = re.compile(r"\b(?:onkeydown|onkeyup|onkeypress|role\s*=|tabindex)\b", re.I)


def _lineno(html, idx):
    return html[:idx].count("\n") + 1


def _check_img(html, p, root):
    out = []
    for m in IMG_RE.finditer(html):
        seg = html[m.start():m.start() + 300].split(">")[0] + ">"
        if not IMG_ALT_RE.search(seg):
            out.append({"file": rel(p, root), "line": _lineno(html, m.start()), "severity": "high",
                        "rule": "img-no-alt", "why": "<img> 缺 alt（屏幕阅读器无法描述）"})
    return out


def _check_controls(html, p, root):
    out = []
    for m in INPUT_RE.finditer(html):
        seg = html[m.start():m.start() + 300].split(">")[0] + ">"
        if INPUT_TYPE_HIDDEN.search(seg):
            continue
        if not INPUT_NAME_RE.search(seg):
            out.append({"file": rel(p, root), "line": _lineno(html, m.start()), "severity": "medium",
                        "rule": "control-no-name",
                        "why": f"{m.group(1)} 缺少可访问名称 (aria-label/alt/关联 label)"})
    return out


def _check_headings(html, p, root):
    out = []
    levels = [int(h.group(1)) for h in HEADING_RE.finditer(html)]
    prev = 0
    for lv in levels:
        if prev and lv > prev + 1:
            out.append({"file": rel(p, root), "line": 0, "severity": "low",
                        "rule": "heading-jump", "why": f"标题层级跳变 h{prev} -> h{lv}"})
        prev = lv
    return out


def _check_deprecated(html, p, root):
    out = []
    for m in DEPRECATED_RE.finditer(html):
        out.append({"file": rel(p, root), "line": _lineno(html, m.start()), "severity": "low",
                    "rule": "deprecated-tag", "why": f"<{m.group(1)}> 已废弃的呈现性标签"})
    return out


def _check_clickable(html, p, root):
    out = []
    for m in CLICKABLE_RE.finditer(html):
        seg = html[m.start():m.start() + 400].split(">")[0] + ">"
        if not KEYBOARD_RE.search(seg):
            out.append({"file": rel(p, root), "line": _lineno(html, m.start()), "severity": "medium",
                        "rule": "click-no-keyboard",
                        "why": f"{m.group(1)} 绑定 onclick 但缺键盘事件/role（不可键盘操作）"})
    return out


def evaluate(root: str) -> dict:
    findings = []
    scanned = 0
    for p in targets(root, A11Y_EXTS):
        try:
            with open(p, encoding="utf-8", errors="ignore") as f:
                html = f.read()
        except Exception:
            continue
        scanned += 1
        findings += _check_img(html, p, root)
        findings += _check_controls(html, p, root)
        findings += _check_headings(html, p, root)
        findings += _check_deprecated(html, p, root)
        findings += _check_clickable(html, p, root)
    score = score_from(findings)
    passed = not has_high(findings)
    evidence = f"A11yDoctor scanned {scanned} file(s); {len(findings)} a11y finding(s)"
    return {"axis": 11, "name": "A11yDoctor", "passed": passed, "score": score,
            "scanned": scanned, "findings": findings[:20], "evidence": evidence}
