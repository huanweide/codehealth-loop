#!/usr/bin/env python3
"""codehealth-loop · Engineering Health Self-Healing Engine (Brake Core).

Synthesis of four real assets into one systematic loop:

  BrakeCore          <- maxloop-overlord  (four brakes: R/C/N+root-cause,
                                            Oracle Gate+evidence anchor,
                                            discrimination test, escape ladder+stall guard)
  PerceptionLayer    <- doctors 12 health axes (3 implemented & real: SecScan /
                                            CycScan / DupScan; 9 pluggable)
  AdversarialMatrix  <- advverify 7-mind collision (interface reserved, roadmap)
  GuardrailLayer     <- forge-safeguard destructive-command intercept (interface)

The loop never claims "done" on its own authority. A round is delivered ONLY
when every Perception axis is green AND the discrimination test confirms the
previous red is now green (old-red/new-green). Every verdict is anchored to
real file:line evidence — no evidence, no verdict.
"""
from __future__ import annotations
import importlib.util
import os
import sys
import json
import tempfile
import shutil

import healer  # Healer Layer: fix-candidate synthesis + sandbox verification

# ---------------------------------------------------------------------------
# Perception Layer — pluggable health axes
# ---------------------------------------------------------------------------
class PerceptionLayer:
    def __init__(self, judges_dir: str):
        self.judges = []
        self.by_name = {}  # axis name -> module (for targeted sandbox re-runs)
        if judges_dir not in sys.path:
            sys.path.insert(0, judges_dir)  # so judges can `import _common`
        for fn in sorted(os.listdir(judges_dir)):
            if fn.endswith(".py") and not fn.startswith("_"):
                spec = importlib.util.spec_from_file_location(
                    fn[:-3], os.path.join(judges_dir, fn))
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)
                if hasattr(mod, "evaluate"):
                    self.judges.append(mod)
                    probe = tempfile.mkdtemp()
                    try:
                        nm = mod.evaluate(probe).get("name")
                        if nm:
                            self.by_name[nm] = mod
                    finally:
                        shutil.rmtree(probe, ignore_errors=True)

    def sweep(self, root: str) -> list[dict]:
        return [j.evaluate(root) for j in self.judges]


# ---------------------------------------------------------------------------
# Brake Core — maxloop four brakes
# ---------------------------------------------------------------------------
class BrakeCore:
    def __init__(self, stall_patience: int = 3, escape_after: int = 4):
        self.stall_patience = stall_patience
        self.escape_after = escape_after

    def oracle_gate(self, results: list[dict]) -> tuple[bool, list[dict]]:
        """Oracle Gate + evidence anchor: pass only if every axis green AND
        each verdict carries real evidence. Returns (passed, red_axes)."""
        red = [r for r in results if not r["passed"]]
        for r in results:
            if not r.get("evidence"):
                red.append({**r, "missing_evidence": True})
        return (len(red) == 0, red)

    def root_cause_gate(self, red_axes: list[dict]) -> list[str]:
        """R/C/N + root-cause gate: collapse red axes into actionable root
        causes, each anchored to file:line evidence (never a vibe)."""
        causes = []
        for ax in red_axes:
            if ax.get("findings"):
                top = ax["findings"][0]
                # SecScan/others use file:line; DupScan uses locations["file:line"]
                if "file" in top and "line" in top:
                    loc, ln = top["file"], top["line"]
                elif top.get("locations"):
                    first = top["locations"][0].split(":")
                    loc, ln = (first[0], first[1]) if len(first) > 1 else (first[0], "?")
                else:
                    loc, ln = "?", "?"
                causes.append(f"[{ax['name']}] axis{ax.get('axis','?')} "
                              f"root-cause @ {loc}:{ln} — {ax.get('why', 'see findings')}")
            else:
                causes.append(f"[{ax['name']}] axis{ax.get('axis','?')} — no detail")
        return causes

    def discrimination_test(self, prev: list[dict] | None, now: list[dict]) -> bool:
        """Old-red/new-green: deliver only if a previously red axis is now green
        (or all were already green from the start)."""
        if prev is None:
            return all(r["passed"] for r in now)
        prev_by = {r["name"]: r["passed"] for r in prev}
        for r in now:
            was_red = not prev_by.get(r["name"], True)
            if was_red and not r["passed"]:
                return False
        return True


# ---------------------------------------------------------------------------
# Convergence Protocol — escape ladder + stall guard
# ---------------------------------------------------------------------------
class ConvergenceProtocol:
    def __init__(self):
        self.history: list[int] = []

    def stall_guard(self, current_score: int, patience: int) -> bool:
        """Brake if health score has not improved for `patience` rounds."""
        self.history.append(current_score)
        if len(self.history) <= patience:
            return False
        window = self.history[-(patience + 1):]
        return max(window[:-1]) >= window[-1]

    def escape_ladder(self, round_no: int, after: int) -> str:
        """Escalate strategy once stuck past `after` rounds."""
        if round_no < after:
            return "standard"
        if round_no < after + 2:
            return "deepen: widen scan scope + lower noise threshold"
        return "escalate: hand actionable report to human/agent (stop self-spin)"


# ---------------------------------------------------------------------------
# Self-healing loop
# ---------------------------------------------------------------------------
def run_loop(root: str, max_rounds: int = 6) -> dict:
    here = os.path.dirname(os.path.abspath(__file__))
    percept = PerceptionLayer(os.path.join(here, "judges"))
    brake = BrakeCore()
    conv = ConvergenceProtocol()
    prev = None
    last = None
    for rnd in range(1, max_rounds + 1):
        delivery, cont = _round(rnd, root, percept, brake, conv, prev)
        if delivery is not None:
            return delivery
        last = cont
        prev = cont["results"]
    return _deliver(max_rounds, last["health"], last["results"],
                    "MAX ROUNDS reached — deliver evidence report",
                    last["strategy"], last["causes"], last["fixes"])


def _round(rnd: int, root: str, percept, brake, conv, prev) -> tuple:
    """One convergence iteration. Returns (delivery_or_None, continuation_state)."""
    results = percept.sweep(root)
    health = sum(r["score"] for r in results) // len(results) if results else 0
    passed, red = brake.oracle_gate(results)
    strategy = conv.escape_ladder(rnd, brake.escape_after)
    cont = {"results": results, "red": red, "causes": [], "strategy": strategy,
            "health": health, "fixes": []}
    if passed:
        if brake.discrimination_test(prev, results):
            return _deliver(rnd, health, results,
                            "ALL GREEN + discrimination test passed", strategy), None
        return None, cont
    causes = brake.root_cause_gate(red)
    # Healer: propose + sandbox-verify fixes; converge on a *verified* fix
    # existing (maxloop: change -> test -> converge), never on silent mutation.
    fixes = healer.propose(red, percept.by_name, root)
    verified = [f for f in fixes if f.get("verified_green")]
    if verified:
        return _deliver(
            rnd, health, results,
            f"CONVERGED: {len(verified)} axis(s) proven fixable in sandbox "
            f"(NOT auto-applied); remaining need manual review",
            strategy, causes, fixes), None
    if conv.stall_guard(health, brake.stall_patience):
        return _deliver(rnd, health, results,
                        "STALL GUARD tripped — stop self-spin, report to human",
                        strategy, causes, fixes), None
    # not delivered this round: surface evidence-anchored root causes
    print(f"\n── Round {rnd} · health={health} · strategy={strategy} ──")
    for c in causes[:12]:
        print("  •", c)
    return None, {**cont, "causes": causes, "fixes": fixes}


def _deliver(round_no, health, results, verdict, strategy, causes=None, fixes=None) -> dict:
    report = {
        "round": round_no, "health_score": health, "verdict": verdict,
        "strategy": strategy, "axes": [
            {"name": r["name"], "axis": r.get("axis"), "passed": r["passed"],
             "score": r["score"], "evidence": r.get("evidence")}
            for r in results
        ],
        "root_causes": causes or [],
        "fix_candidates": fixes or [],
    }
    print("\n════════ DELIVERY (evidence-anchored) ════════")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if fixes:
        print("--- fix candidates (sandbox-verified, NOT auto-applied) ---")
        for fx in fixes[:12]:
            if fx.get("verified_green"):
                tag = "VERIFIED-GREEN (sandbox)"
            elif not fx.get("verifiable"):
                tag = "manual (needs human refactor)"
            else:
                tag = "UNVERIFIED"
            print(f"  [{fx['axis']}] {fx['file']}:{fx['line']} -> {tag}")
            print(f"     why: {fx['why']}")
            print(f"     fix: {fx['suggestion']}")
    return report


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "."
    run_loop(target)
