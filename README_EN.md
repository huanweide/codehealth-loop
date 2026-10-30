**中文** · [README.md](./README.md)

<p align="center">
  <img src="assets/banner.svg" alt="codehealth-loop · engineering-health self-healing engine" width="1280">
</p>

# codehealth-loop · Engineering-health self-healing engine

![License](https://img.shields.io/github/license/huanweide/codehealth-loop)
![Stars](https://img.shields.io/github/stars/huanweide/codehealth-loop)
![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)
![Deps](https://img.shields.io/badge/deps-zero--stdlib-4ecca3)
![Powered by](https://img.shields.io/badge/powered%20by-maxloop--overlord-ef4444)
![CI](https://github.com/huanweide/codehealth-loop/actions/workflows/ci.yml/badge.svg)

> **TL;DR** — A *self-healing* engineering-health engine. It fuses the **brake-driven iteration core** of [`maxloop-overlord`](https://github.com/huanweide/maxloop-overlord) (external-judgment brakes, no fake-green), a **12-axis perception layer** ported from [`doctors`](https://github.com/huanweide/doctors), and a **sandbox-verified healer** into one systematic loop that refuses to declare "done" until every health axis is genuinely green. Zero third-party dependencies, stdlib only.

> It is **not another linter.** It replaces the "write code → fake-green → ship → blow up" death loop with a self-healing loop: "multi-axis checkup → converge to root cause → braked iteration → sandbox-verified repair → deliver only when truly met".

Any code repo → automatically completes "12-axis checkup → converge red findings into root cause → four-brake iteration → sandbox-verified repair → deliver when truly met".

[Overview](#overview) · [What it does](#what-it-does) · [Features](#features) · [Quick start](#quick-start) · [CLI reference](#cli-reference) · [Architecture](#architecture) · [Implemented vs roadmap](#implemented-vs-roadmap) · [Contributing](#contributing)

---

## Overview

"Runs" ≠ "should ship". The gate that decides "done" comes from **outside the engine**, not from a self-reported status.

---

## Who should use it

- You want a health check that **proves its fixes in a sandbox** rather than reporting a pretty score.
- You run AI-generated or AI-iterated code and want an objective, evidence-anchored gate before shipping.
- You want something that drops into CI and **stops empty spinning** (stall guard).

## Who should NOT use it

- You expect it to **auto-edit your code**. It only delivers sandbox-verified fix candidates; landing them is up to you.
- You want a single quick lint — this runs a multi-round loop (slower but convergent).
- You need a GUI; this is a CLI / CI tool.

---

## What it does

### Real run 1: the engine runs the loop on **itself** (`python engine.py .`)

```text
── Round 1 · health=95 · strategy=standard ──
── Round 2 · health=95 · strategy=standard ──
── Round 3 · health=95 · strategy=standard ──

════════ DELIVERY (evidence-anchored) ══════
{
  "round": 4,
  "health_score": 95,
  "verdict": "STALL GUARD tripped — stop self-spin, report to human",
  "strategy": "deepen: widen scan scope + lower noise threshold",
  "axes": [
    {"name":"SecScan","axis":7,"passed":true,"score":100,
     "evidence":"scanned 16 files, 0 hits (0 high)"},
    {"name":"CycScan","axis":4,"passed":true,"score":100,
     "evidence":"scanned 16 files, 0 funcs over threshold(>12)"},
    {"name":"EngHealth","axis":12,"passed":true,"score":96,
     "evidence":"EngHealth process signals: LICENSE=y, README=y, CI=y, tests=n"},
    {"name":"DocDoctor","axis":5,"passed":false,"score":55,
     "evidence":"DocDoctor scanned 3 Markdown file(s); 3 finding(s)"}
  ]
}
--- fix candidates (sandbox-verified, NOT auto-applied) ---
  [DocDoctor] architecture.md:57 -> manual (needs human refactor)
     why: <img> missing alt attribute (accessibility / screen reader)
  [DocDoctor] README.md:92 -> manual (needs human refactor)
     why: bare URL not wrapped as a link
```

> Note the last line's attitude: the engine **did not declare "all green"**. The remaining items are example snippets inside docs that can't be mechanically verified, so it marks them `manual` and hands off to a human, triggering the stall guard to stop spinning — **that is the difference from "report a nice score and call it done."**

### Real run 2: discriminating test (`python test_engine.py`)

The self-test builds dirty/clean samples in a temp dir and **never scans this repo's own source**, so results are stable and reproducible:

```text
[ok] axis registry: 12 axes, numbers [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
[ok] dirty sample CONVERGED; SecScan verified-green in sandbox
[ok] clean sample ALL GREEN; health=99
ALL TESTS PASSED
```

The dirty sample (with `eval`) **CONVERGED** in round 1: the Healer removes the call on a sandbox copy and re-runs `SecScan` to prove it turned green → `verified_green`. Structurally unverifiable problems are marked `manual` — **honestly handed to a human, never faked as fixed**.

---

## Features

- **PerceptionLayer 12-axis perception (zero-dep, fully landed)** — 12 real static probes under `judges/`: 8 axes ported from `doctors` (Repo / Commit / Dev / Doc / Pkg / Rel / Type / A11y) + SecScan / CycScan / DupScan + EngHealth process-maturity axis. Offline, deterministic, inherits the dogfood discipline (won't falsely flag strings / comments / regex).
- **BrakeCore four-brake kernel (from maxloop)** — R/C/N + root-cause gate, Oracle Gate + evidence anchor, discriminating test (old RED new GREEN), escape ladder + stall guard. The soul: "criteria come from outside the model".
- **Healer sandbox-verified layer** — generates fix candidates → re-runs that axis on a **sandbox copy** → marks `verified_green` only after proving it turned green; **never auto-edits your code**, only delivers proven-effective patches.
- **Evidence-anchored delivery** — every finding carries `file:line` and real scan evidence; the delivery report is `json`, diffable, reproducible, CI-ready.
- **Stall-guard anti-spin** — N consecutive rounds with zero improvement → brake and hand to a human, no "edit back and forth, messier each time".
- **Zero third-party dependencies** — Python standard library only; `git clone` and run, no `pip install`, no network, no API key.
- **Built-in discriminating regression test** — `test_engine.py` asserts both "dirty sample must CONVERGE and SecScan turns green in sandbox" and "clean sample must ALL GREEN", isomorphic to maxloop's old-RED-new-GREEN.

---

## Quick start

### Install

Zero third-party dependencies; just Python ≥ 3.10 on the machine:

```bash
git clone https://github.com/huanweide/codehealth-loop.git
cd codehealth-loop
```

### Run a self-healing loop

```bash
python engine.py /path/to/your/project          # default max 6 rounds, with stall guard
python engine.py ./your-project --max-rounds 8  # custom round count
```

### Self-test (discriminating test, truly green locally)

```bash
python test_engine.py
```

> The self-test builds dirty/clean samples in a temp dir and **never scans this repo's own source** (dogfood discipline), so results are stable and reproducible.

---

## CLI reference

| Command | Purpose |
|---|---|
| `python engine.py <dir>` | Run the self-healing loop on a project (default max 6 rounds) |
| `python engine.py <dir> --max-rounds N` | Custom max iteration rounds |
| `python engine.py .` | Self-check on current dir (including this repo) |
| `python engine.py --help` | All options |
| `python test_engine.py` | Regression + discriminating test (non-zero exit on failure) |

---

## Architecture

The engine fuses four real weapons into one pipeline: **perceive → brake → heal → converge**. The four brakes form an iron chain; the convergence standard is "all external criteria green", not "the model says good".

| Primitive | Meaning |
|---|---|
| **Red finding** | A concrete problem with `file:line`, not "feels off" |
| **Axis** | A pluggable static probe (12 of them, numbered 1–12, unique) |
| **R/C/N judgment** | R must-change / C optional / N shouldn't-add — necessity and root-cause gate |
| **Discriminating test** | On a sandbox copy "old must-RED / new must-GREEN", proving the change worked |
| **verified_green** | Fix candidate re-run on sandbox and proven green |
| **manual** | No mechanically verifiable fix (needs refactor); honestly handed to human, not faked |

```text
   code repo
      ↓
  ① PerceptionLayer · 12-axis scan (judges/)
      ↓ red findings (file:line + evidence)
  ② BrakeCore · R/C/N root-cause gate + Oracle Gate + evidence anchor
      ↓ not met
  ③ Healer · generate candidate → re-run axis on sandbox copy → old RED new GREEN → verified_green
      ↓
  ④ ConvergenceProtocol · escape ladder / stall guard
      ↓ all green + discriminating test passed
   deliver: DELIVERY json (evidence-anchored) + fix candidates (not auto-landed)
```

| Module | File | Description |
|---|---|---|
| Perception layer | `engine.py` → `PerceptionLayer` | Discovers and schedules all 12 axes under `judges/` |
| Brake core | `engine.py` → `BrakeCore` | R/C/N root-cause gate + Oracle Gate + evidence anchor |
| Convergence protocol | `engine.py` → `ConvergenceProtocol` | Escape ladder + stall guard |
| Main loop | `engine.py` → `run_loop` / `_round` / `_deliver` | Round driver and evidence-anchored delivery |
| Heal layer | `healer.py` → `propose` / `sandbox_verify_fix` | Sandbox-verified repair, never touches user code |
| 12 health axes | `judges/*.py` | repodoctor / commitdoctor / devdoctor / docdoctor / pkgdoctor / reldoctor / typedoctor / a11ydoctor / secscan / cycscan / dupscan / enghealth |
| Judge common lib | `judges/_common.py` | Shared scan / comment-strip / severity logic |
| Regression self-test | `test_engine.py` | Axis registry + dirty-sample convergence + clean-sample all-green |

---

## Add your own health axis

Axes are pluggable: drop a file into `judges/`, export `run(root)` returning a finding list, and the perception layer auto-adopts it.

```python
# judges/myrule.py
from _common import walk_files, strip_comments

AXIS = 13
NAME = "MyRule"

def run(root):
    findings = []
    for path in walk_files(root, (".py",)):
        for lineno, line in enumerate(strip_comments(path), start=1):
            if "TODO(security)" in line:
                findings.append({
                    "file": path, "line": lineno,
                    "severity": "high",
                    "message": "Leftover security TODO not handled",
                })
    return findings
```

The perception layer requires: **unique axis number, unique name, every finding must carry `file:line` evidence** — `test_engine.py` guards this door for you.

---

## Implemented vs roadmap (honest labeling)

| Layer | Status | Description |
|---|---|---|
| PerceptionLayer · 12 axes | ✅ implemented | 12 real static probes under `judges/`, zero-dep, offline, deterministic |
| BrakeCore four brakes | ✅ implemented | genuinely runs in `engine.py`, discriminating test locked by `test_engine.py` |
| Healer sandbox-verified | ✅ implemented | `healer.py`: candidate → sandbox re-run → `verified_green` |
| Regression / discriminating test | ✅ implemented | `test_engine.py`, bidirectional assertions on dirty & clean samples |
| AdversarialMatrix 7-perspective review | 🔜 interface reserved | plans to wire [`advverify`](https://github.com/huanweide/advverify) multi-perspective review as R/C/N adversarial input |
| GuardrailLayer | 🔜 interface reserved | plans to wire [`forge-safeguard-20260812`](https://github.com/huanweide/forge-safeguard-20260812) to block destructive commands |
| Auto-landing fixes into user code | ❌ not provided (safety rule) | only delivers "sandbox-verified fix candidates"; landing by human / upper agent |

---

## Related projects

The same paradigm (**external-criteria brakes · no fake-green spinning · four brakes**) landed on different carriers, cross-linking:

| Project | Carrier | One line |
|---|---|---|
| [`maxloop-overlord`](https://github.com/huanweide/maxloop-overlord) | Agent Skill | The paradigm itself: BrakeCore's four brakes come from here |
| [`codehealth-loop`](https://github.com/huanweide/codehealth-loop) | Python engine (this repo) | Paradigm made concrete for engineering health |
| [`veriloop`](https://github.com/huanweide/veriloop) | Python CLI | Paradigm made concrete for code audit: 12 analysis axes + 4 verification brakes |
| [`overlord-loop`](https://github.com/huanweide/overlord-loop) | Engine implementation | Braked AI code-evolution loop engine |
| [`doctors`](https://github.com/huanweide/doctors) | Node CLI bundle | Source of 8 axes in this engine's perception layer, faithfully ported to Python probes |
| [`family-showcase`](https://github.com/huanweide/family-showcase) | Single-page HTML | 18-axis panoramic dashboard of the engineering-health family |

---

## Contributing

- File an issue describing the real health problem you hit, with the project type and axis involved.
- PRs should add a discriminating test: your change needs both a "must-RED-before" and a "must-GREEN-after" real output where applicable.
- New axes are welcome — keep them zero-dep, offline, deterministic, and `file:line`-anchored.

## Safety boundary

> ⚠️ **It never auto-edits your code.**
> - Repairs are verified only on a **sandbox copy**; once verified they are delivered as candidates, landing by you / your upper agent.
> - Unverifiable repairs (e.g. high cyclomatic complexity needing refactor) are marked `manual` and handed to a human, **never faked as fixed**.
> - Zero third-party dependencies, no network, no secret reading; scans are read-only.

## License

[MIT](LICENSE) © 2026 huanweide

---

<div align="center">
  <b>If codehealth-loop helped you catch one real problem before shipping, drop a ⭐ Star so more people see it.</b><br/>
  <a href="https://github.com/huanweide/codehealth-loop">huanweide/codehealth-loop</a>
</div>
