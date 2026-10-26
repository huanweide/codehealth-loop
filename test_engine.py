"""Regression test for the closed-loop (Healer) behavior.

Self-contained: builds dirty/clean fixtures in temp dirs so the SecScan judge
never accidentally flags this test file itself (which would poison the sandbox
verification). Cements the discrimination test:
  - dirty fixture  -> round 1 CONVERGED, SecScan fix sandbox-VERIFIED (not auto-applied)
  - clean fixture  -> ALL GREEN
Run: python3 test_engine.py
"""
import os
import sys
import tempfile
import shutil

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import engine  # noqa: E402


def _mk(dirty: bool) -> str:
    d = tempfile.mkdtemp(prefix="chloop_t_")
    if dirty:
        with open(os.path.join(d, "bad.py"), "w", encoding="utf-8") as fh:
            fh.write('def f():\n    return eval("1+1")\n')
    else:
        with open(os.path.join(d, "good.py"), "w", encoding="utf-8") as fh:
            fh.write("def add(a, b):\n    return a + b\n")
    return d


def test_dirty_converges_via_verified_fix():
    d = _mk(True)
    try:
        rep = engine.run_loop(d)
        assert "CONVERGED" in rep["verdict"], f"expected CONVERGED, got: {rep['verdict']}"
        sec = [a for a in rep["fix_candidates"] if a["axis"] == "SecScan"]
        assert sec, "SecScan must produce a fix candidate"
        assert sec[0]["verified_green"], "SecScan fix must be sandbox-verified (not false-red)"
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_clean_passes():
    d = _mk(False)
    try:
        rep = engine.run_loop(d)
        assert "ALL GREEN" in rep["verdict"], f"expected ALL GREEN, got: {rep['verdict']}"
    finally:
        shutil.rmtree(d, ignore_errors=True)


if __name__ == "__main__":
    test_dirty_converges_via_verified_fix()
    test_clean_passes()
    print("ALL TESTS PASSED")
