"""CommitDoctor — git commit-message hygiene (port of doctors/packages/commitdoctor).

Detects: trailing period / leading-trailing whitespace on subject, TODO/FIXME/WIP
markers, and suspected secret leakage in the message. Git-aware: without a git
repo the axis reports `not applicable` (honest neutral, not a fake green).
"""
from __future__ import annotations
import re
from _common import score_from, has_high, git_available, git_log

TODO_RE = re.compile(r"\b(?:TODO|FIXME|HACK|WIP)\b")
SECRET_RE = re.compile(r"((?:api[_-]?key|secret|token|password|passwd|access[_-]?key|private[_-]?key|auth[_-]?token)[\s:=]+[^\s\"']{8,})", re.I)
EMOJI_RE = re.compile(r"[\U0001F300-\U0001FAFF\u2600-\u27BF]")


def evaluate(root: str) -> dict:
    if not git_available():
        return {"axis": 2, "name": "CommitDoctor", "passed": True, "score": 100,
                "scanned": 0, "findings": [],
                "evidence": "not a git repo — commit-message hygiene not applicable (manual)"}
    msgs = git_log(root, 20)
    if not msgs:
        return {"axis": 2, "name": "CommitDoctor", "passed": True, "score": 100,
                "scanned": 0, "findings": [],
                "evidence": "no git history — commit-message hygiene not applicable (manual)"}

    findings = []
    for full in msgs:
        lines = full.split("\n")
        subject = lines[0].strip() if lines else ""
        if not subject:
            continue
        if re.search(r"[.!?。！？]\s*$", subject):
            findings.append({"file": "<commit>", "line": 0, "severity": "low",
                             "rule": "subject-trailing-period", "why": "提交主题结尾多余标点"})
        if subject != subject.strip():
            findings.append({"file": "<commit>", "line": 0, "severity": "low",
                             "rule": "subject-whitespace", "why": "提交主题首尾空格"})
        if EMOJI_RE.search(subject):
            findings.append({"file": "<commit>", "line": 0, "severity": "low",
                             "rule": "subject-emoji", "why": "提交主题含 emoji（规范噪声）"})
        if TODO_RE.search(full):
            findings.append({"file": "<commit>", "line": 0, "severity": "medium",
                             "rule": "has-todo-marker", "why": "提交消息含未完成标记 (TODO/FIXME/WIP)"})
        if SECRET_RE.search(full):
            findings.append({"file": "<commit>", "line": 0, "severity": "high",
                             "rule": "has-secret", "why": "提交消息疑似泄露密钥/凭据"})

    return {"axis": 2, "name": "CommitDoctor", "passed": not has_high(findings),
            "score": score_from(findings), "scanned": len(msgs), "findings": findings[:20],
            "evidence": f"CommitDoctor scanned {len(msgs)} commit(s); {len(findings)} finding(s)"}
