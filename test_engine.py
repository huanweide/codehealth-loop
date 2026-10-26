"""Regression gate for codehealth-loop.

Self-contained: builds dirty/clean fixtures in temp dirs so the engine never
scans its own source (dogfood discipline). Asserts:
  1. exactly 12 health axes registered, with unique axis numbers 1..12
  2. a dirty project ( lone eval ) -> run_loop CONVERGED with a sandbox-verified
     SecScan fix (old-red/new-green, the maxloop discrimination test)
  3. a clean project -> run_loop ALL GREEN
Run: python3 test_engine.py
"""
from __future__ import annotations
import os
import sys
import tempfile
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import engine  # noqa: E402


def _write(path: str, content: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def test_axis_registry():
    percept = engine.PerceptionLayer(os.path.join(HERE, "judges"))
    res = percept.sweep(tempfile.mkdtemp())
    names = [r["name"] for r in res]
    nums = [r["axis"] for r in res]
    assert len(names) == 12, f"expected 12 axes, got {len(names)}: {names}"
    assert len(set(nums)) == 12, f"axis numbers not unique: {nums}"
    assert set(nums) == set(range(1, 13)), f"axis numbers must be 1..12: {nums}"
    print(f"[ok] axis registry: {len(names)} axes, numbers {sorted(nums)}")


def test_dirty_converges():
    d = tempfile.mkdtemp()
    try:
        _write(os.path.join(d, "LICENSE"), "MIT")
        _write(os.path.join(d, "README.md"), "# demo\n")
        _write(os.path.join(d, "src", "dirty.py"), "def f():\n    return eval('1+1')\n")
        _write(os.path.join(d, "src", "clean.py"), "def g():\n    return 1 + 1\n")
        rep = engine.run_loop(d, max_rounds=4)
        assert "CONVERGED" in rep["verdict"], f"expected CONVERGED, got {rep['verdict']}"
        verified = [fx for fx in rep["fix_candidates"] if fx.get("verified_green")]
        assert any(fx["axis"] == "SecScan" for fx in verified), \
            "SecScan fix must be sandbox-verified green"
        print(f"[ok] dirty sample CONVERGED; SecScan verified-green in sandbox")
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_clean_all_green():
    d = tempfile.mkdtemp()
    try:
        _write(os.path.join(d, "LICENSE"), "MIT")
        _write(os.path.join(d, "README.md"), "# demo\n")
        _write(os.path.join(d, "src", "app.py"), "def add(a, b):\n    return a + b\n")
        rep = engine.run_loop(d, max_rounds=3)
        assert "ALL GREEN" in rep["verdict"], f"expected ALL GREEN, got {rep['verdict']}"
        print(f"[ok] clean sample ALL GREEN; health={rep['health_score']}")
    finally:
        shutil.rmtree(d, ignore_errors=True)


if __name__ == "__main__":
    test_axis_registry()
    test_dirty_converges()
    test_clean_all_green()
    print("\nALL TESTS PASSED")
