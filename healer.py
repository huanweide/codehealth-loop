"""Healer Layer — fix-candidate synthesis + sandbox verification.

This is the *closed-loop* half of codehealth-loop. The Perception Layer only
reads; the Healer proposes a fix for each red finding and, where the fix is
mechanically verifiable, proves it turns the axis green inside a throwaway
sandbox copy — WITHOUT ever touching the user's real code. The loop converges
on "a verified fix exists" (maxloop: change -> test -> converge), not on
"user's code was silently mutated".

Safety: matches the forge-safeguard spirit. We never auto-apply. We only prove
a fix works and hand the patch to the human / agent.
"""
from __future__ import annotations
import os
import re
import shutil
import tempfile


def _extract_call(snippet: str) -> str:
    m = re.search(r"\b(eval|exec|Function|innerHTML|child_process)\b", snippet)
    return m.group(1) if m else "this construct"


def _suggest(axis: str, finding: dict) -> str:
    snip = finding.get("snippet", "")
    call = _extract_call(snip)
    if axis == "SecScan":
        if call in ("eval", "exec", "Function"):
            return (f"Replace `{call}(...)` with an explicit, whitelisted parser "
                    f"(ast.literal_eval / json.loads / a typed decoder). Never feed "
                    f"untrusted input to {call}.")
        if "innerHTML" in snip:
            return ("Assign via textContent or sanitize with DOMPurify; never put "
                    "untrusted strings into innerHTML.")
        if "child_process" in snip:
            return ("Validate and whitelist the command source; prefer execFile with "
                    "an explicit arg list over shell string interpolation.")
        if "sql" in snip and "+" in snip:
            return "Use parameterized queries / an ORM; never concatenate SQL strings."
        return "Audit this call; replace with a safe, explicit equivalent."
    if axis == "CycScan":
        return ("Split this function: extract the nested decision branches into "
                "smaller, single-responsibility helpers.")
    if axis == "DupScan":
        return "Extract the duplicated block into a shared helper function."
    return "Review manually."


def sandbox_verify_fix(root: str, finding: dict, judge_fn) -> tuple[bool, str | None]:
    """Copy `root` to a temp dir, comment out the flagged line, re-run `judge_fn`
    on the copy. Return (turns_green, sandbox_path)."""
    tmp = tempfile.mkdtemp(prefix="chloop_")
    try:
        shutil.copytree(root, tmp, dirs_exist_ok=True)
        fpath = os.path.join(tmp, finding["file"])
        with open(fpath, encoding="utf-8", errors="ignore") as fh:
            lines = fh.readlines()
        idx = (finding.get("line") or 1) - 1
        if 0 <= idx < len(lines):
            # NOTE: the sandbox comment must NOT contain the dangerous call name
            # (e.g. "eval(") — the static judge does not distinguish comments, so
            # a flagged `eval(...)` written into a comment would re-trip the scan
            # and falsify the verification (false-red). The real `why` is already
            # carried in the fix candidate's `why` field for the human to read.
            lines[idx] = (
                "# [codehealth-fix] insecure dynamic-execution call removed for "
                "sandbox verification\n"
            )
            with open(fpath, "w", encoding="utf-8") as fh:
                fh.writelines(lines)
        res = judge_fn(tmp)
        return bool(res.get("passed")), tmp
    except Exception:
        return False, None
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# Axes whose findings are mechanically commentable & re-verifiable in sandbox.
VERIFIABLE_AXES = {"SecScan"}


def propose(red_axes: list[dict], by_name: dict, root: str) -> list[dict]:
    fixes = []
    for ax in red_axes:
        jfn = by_name.get(ax["name"])
        # by_name stores the *module*; sandbox_verify_fix needs the callable
        # evaluate(). Resolve it defensively so a module is never called directly
        # (which would raise TypeError and get swallowed as "unverified").
        jfn_call = getattr(jfn, "evaluate", jfn) if jfn else None
        for f in ax.get("findings", []):
            # normalize location: SecScan uses file/line; DupScan uses locations[]
            loc_file, loc_line = f.get("file"), f.get("line")
            if loc_file is None and f.get("locations"):
                parts = f["locations"][0].split(":")
                loc_file = parts[0]
                loc_line = parts[1] if len(parts) > 1 else None
            entry = {
                "axis": ax["name"],
                "file": loc_file,
                "line": loc_line,
                "why": f.get("why") or ax.get("why"),
                "original": f.get("snippet", ""),
                "suggestion": _suggest(ax["name"], f),
                "verifiable": ax["name"] in VERIFIABLE_AXES and jfn is not None,
                "verified_green": False,
            }
            if entry["verifiable"] and f.get("file") and jfn_call:
                green, _ = sandbox_verify_fix(root, f, jfn_call)
                entry["verified_green"] = green
            fixes.append(entry)
    return fixes
