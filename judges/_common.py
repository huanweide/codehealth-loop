"""Shared helpers for codehealth-loop judges.

Zero-dependency, offline, deterministic. This module starts with `_` so the
PerceptionLayer loader (which skips files beginning with `_`) never treats it
as a judge itself.
"""
from __future__ import annotations
import os
import re

# Directories we never descend into (mirrors doctors' "offline, no surprise" rule).
SKIP_DIRS = {
    ".git", "node_modules", "__pycache__", ".venv", "venv", "dist", "build",
    ".next", "out", "target", ".idea", ".vscode", ".tailwind", "coverage",
    ".pytest_cache", ".mypy_cache", ".tox", "site-packages", "tests",
}

# Severity -> health-score penalty.
_WEIGHT = {"high": 25, "medium": 10, "low": 4}


def iter_files(root: str, exts):
    """Yield absolute paths of files under `root` (a directory) with given exts."""
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fn in filenames:
            if any(fn.endswith(e) for e in exts):
                yield os.path.join(dirpath, fn)


def targets(root: str, exts):
    """Resolve scan targets. If `root` is a single file, return [root] when its
    extension matches, else []; if `root` is a directory, walk it."""
    if os.path.isfile(root):
        return [root] if any(root.endswith(e) for e in exts) else []
    return list(iter_files(root, exts))


def is_dir(root: str) -> bool:
    return os.path.isdir(root)


def rel(path: str, root: str) -> str:
    try:
        return os.path.relpath(path, root)
    except ValueError:
        return path


def score_from(findings, base: int = 100) -> int:
    s = base
    for f in findings:
        s -= _WEIGHT.get(f.get("severity", "low"), 4)
    return max(0, min(100, s))


def has_high(findings) -> bool:
    return any(f.get("severity") == "high" for f in findings)


# Common plaintext-secret pattern (ported from repodoctor / devdoctor).
SECRET_RE = re.compile(
    r"(api_key|apikey|secret|token|password|passwd|private_key|access_key)\s*[:=]\s*['\"][A-Za-z0-9_\-./+]{12,}['\"]",
    re.I,
)


def git_available() -> bool:
    from shutil import which
    return which("git") is not None


def git_log(root: str, n: int = 20) -> list[str]:
    """Return last `n` commit messages (full) or [] if not a git repo."""
    if not git_available():
        return []
    import subprocess
    try:
        out = subprocess.run(
            ["git", "-C", root, "log", f"-n{n}", "--pretty=format:%B%x1e"],
            capture_output=True, text=True, timeout=20,
        )
        if out.returncode != 0:
            return []
        return [m for m in out.stdout.split("\x1e") if m.strip()]
    except Exception:
        return []


def git_tags(root: str) -> list[str]:
    if not git_available():
        return []
    import subprocess
    try:
        out = subprocess.run(
            ["git", "-C", root, "tag", "--list"],
            capture_output=True, text=True, timeout=20,
        )
        return out.stdout.split() if out.returncode == 0 else []
    except Exception:
        return []
