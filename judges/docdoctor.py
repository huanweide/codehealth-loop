"""DocDoctor — Markdown documentation health (ported from doctors/packages/docdoctor).

Detects: images without alt text, bare URLs (not wrapped in a link), heading
level jumps (e.g. h1 -> h3), and broken internal anchors (a `#anchor` link that
matches no heading slug). Deterministic, no network.
"""
from __future__ import annotations
import os
import re
from _common import targets, rel, score_from, has_high

MD_EXTS = (".md", ".markdown")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*#*\s*$", re.M)
IMG_RE = re.compile(r"<img\b", re.I)
IMG_ALT_RE = re.compile(r"<img\b[^>]*\balt\s*=", re.I)
MD_IMG_RE = re.compile(r"!\[([^\]]*)\]\(([^)]+)\)")
BARE_URL_RE = re.compile(r"(?<!\()(?<!\]\()https?://[^\s)>\]]+")
ANCHOR_LINK_RE = re.compile(r"\]\(#([^)\s]+)\)")
MD_LINK_RE = re.compile(r"\[[^\]]*\]\([^)]+\)")


def _slug(heading: str) -> str:
    s = heading.strip().lower()
    s = re.sub(r"[^\w\u4e00-\u9fff\s-]", "", s)
    return re.sub(r"\s+", "-", s)


def _check_images(text, p, root):
    findings = []
    for m in IMG_RE.finditer(text):
        seg = text[m.start():m.start() + 200].split(">")[0] + ">"
        if not IMG_ALT_RE.search(seg):
            findings.append({"file": rel(p, root), "line": text[:m.start()].count("\n") + 1,
                             "severity": "high", "rule": "img-no-alt",
                             "why": "<img> 缺 alt 属性（可访问性/屏幕阅读器）"})
    for m in MD_IMG_RE.finditer(text):
        if m.group(1).strip() == "":
            findings.append({"file": rel(p, root), "line": text[:m.start()].count("\n") + 1,
                             "severity": "low", "rule": "md-img-empty-alt",
                             "why": "Markdown 图片空 alt（装饰图应显式 alt=\"\"）"})
    return findings


def _check_bare_urls(text, p, root):
    findings = []
    masked = MD_LINK_RE.sub("", text)
    for m in BARE_URL_RE.finditer(masked):
        findings.append({"file": rel(p, root), "line": masked[:m.start()].count("\n") + 1,
                         "severity": "medium", "rule": "bare-url",
                         "why": f"裸 URL 未包裹为链接: {m.group(0)[:40]}…"})
    return findings


def _check_headings(text, p, root):
    findings = []
    heads = [(len(h.group(1)), h.group(2)) for h in HEADING_RE.finditer(text)]
    slugs = {_slug(h[1]) for h in heads}
    prev = 0
    for lvl, txt in heads:
        if prev and lvl > prev + 1:
            findings.append({"file": rel(p, root), "line": text[:text.find(txt)].count("\n") + 1,
                             "severity": "low", "rule": "heading-jump",
                             "why": f"标题层级跳变 h{prev} -> h{lvl}"})
        prev = lvl
    for m in ANCHOR_LINK_RE.finditer(text):
        a = m.group(1)
        if a and _slug(a.replace("-", " ")) not in slugs and a not in slugs:
            findings.append({"file": rel(p, root), "line": text[:m.start()].count("\n") + 1,
                             "severity": "medium", "rule": "broken-anchor",
                             "why": f"内部锚点 #{a} 无对应标题"})
    return findings


def evaluate(root: str) -> dict:
    findings = []
    scanned = 0
    for p in targets(root, MD_EXTS):
        try:
            with open(p, encoding="utf-8", errors="ignore") as f:
                text = f.read()
        except Exception:
            continue
        scanned += 1
        findings += _check_images(text, p, root)
        findings += _check_bare_urls(text, p, root)
        findings += _check_headings(text, p, root)
    score = score_from(findings)
    passed = not has_high(findings)
    evidence = f"DocDoctor scanned {scanned} Markdown file(s); {len(findings)} finding(s)"
    return {"axis": 5, "name": "DocDoctor", "passed": passed, "score": score,
            "scanned": scanned, "findings": findings[:20], "evidence": evidence}
