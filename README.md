**English** · [README_EN.md](./README_EN.md)

<p align="center">
  <img src="assets/banner.svg" alt="codehealth-loop · 工程健康自愈引擎" width="1280">
</p>

# 🔁 codehealth-loop · 工程健康自愈引擎

![License](https://img.shields.io/github/license/huanweide/codehealth-loop)
![Stars](https://img.shields.io/github/stars/huanweide/codehealth-loop)
![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)
![Deps](https://img.shields.io/badge/deps-zero--stdlib-4ecca3)
![Powered by](https://img.shields.io/badge/powered%20by-maxloop--overlord-ef4444)
![CI](https://github.com/huanweide/codehealth-loop/actions/workflows/ci.yml/badge.svg)

> **English TL;DR** — A *self-healing* engineering-health engine. It fuses the **brake-driven iteration core** of [`maxloop-overlord`](https://github.com/huanweide/maxloop-overlord) (external-judgement brakes, no fake-green), a **12-axis perception layer** ported from [`doctors`](https://github.com/huanweide/doctors), and a **sandbox-verified healer** into one systematic loop that refuses to declare "done" until every health axis is genuinely green. Zero third-party dependencies, stdlib only.

> **它不是又一个 linter。** 它是把「写代码 → 假绿 → 上线 → 爆雷」的死循环，换成「多轴体检 → 根因收敛 → 带刹车迭代 → 沙箱验证修复 → 真达标才交付」的自愈闭环。

**任意代码仓库 → 自动完成「12 轴体检 → 红点收敛成根因 → 四道刹车迭代 → 沙箱验证修复 → 真达标交付」**

[30 秒看懂](#-30-秒看懂) · [它能做什么](#-它能做什么) · [特性](#-特性) · [快速开始](#-快速开始) · [CLI 速查](#-cli-速查) · [架构](#-架构) · [诚实标注](#-已实现-vs-路线图诚实标注) · [相关项目](#-相关项目)

---

## 🔁 30 秒看懂

```text
普通体检：health = 78 分，2 个 warning          ← 数字好看，没人知道改没改到位
          AI 说"已优化"，测试过了，能跑了      ← 但 eval 还在、复杂度还爆表

codehealth-loop：
  轴 7  SecScan   RED  src/app.py:12  命中 eval（high）
        ↓ 根因闸门：R（非改不可）—— 危险调用真实存在，带 file:line 证据
        ↓ Healer：在沙箱副本上移除该调用 → 重跑 SecScan → 0 hits
        ↓ 判别测试：旧版必红 / 新版必绿 → verified_green
        ↓ 交付：修复补丁 + 证据，绝不自动改你的代码
```

差别只有一句话：**"能跑" ≠ "该上线"；放行的判据来自引擎之外，不来自模型自述。**

---

## 🔁 它能做什么

### 真实运行 1：引擎对**自己**跑闭环（`python engine.py .`）

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
     why: <img> 缺 alt 属性（可访问性/屏幕阅读器）
  [DocDoctor] README.md:92 -> manual (needs human refactor)
     why: 裸 URL 未包裹为链接
```

> 注意最后一行的态度：**引擎没有宣布"全绿"**。剩下几条是文档里的示例片段，无法机械验证，
> 它就标 `manual` 交给人工、触发 stall guard 停止空转 —— **这才是它和"报个好看分数就完事"的区别**。

### 真实运行 2：判别测试（`python test_engine.py`）

自测在临时目录里造脏/干净样例，**从不扫描本仓源码**，结果稳定可复现：

```text
[ok] axis registry: 12 axes, numbers [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
[ok] dirty sample CONVERGED; SecScan verified-green in sandbox
[ok] clean sample ALL GREEN; health=99
ALL TESTS PASSED
```

脏样本（带 `eval`）第 1 轮即 `CONVERGED`：`Healer` 在沙箱副本上移除该调用并重跑 `SecScan` 证明变绿 → `verified_green`。
无机械可验证修复的结构性问题则标 `manual`，**诚实移交人工，不假装修好了**。

---

## 🔁 特性

- **PerceptionLayer 12 轴感知层（零依赖 · 已全落地）** —— `judges/` 下 12 个真实静态探针：`doctors` 移植的 8 轴（Repo / Commit / Dev / Doc / Pkg / Rel / Type / A11y）+ SecScan / CycScan / DupScan 3 轴 + EngHealth 过程成熟度轴。离线、确定性，继承 dogfood 纪律（不误伤字符串 / 注释 / 正则）。
- **BrakeCore 四道刹车内核（源自 maxloop）** —— R/C/N + 根因闸门、Oracle Gate + 证据锚点、判别测试（旧红新绿）、逃逸阶梯 + stall guard。灵魂就在"判据来自模型之外"。
- **Healer 沙箱验证层** —— 生成修复候选 → 在**沙箱副本**上重跑该轴 → 证明"确实变绿"才标 `verified_green`；**绝不自动改你的代码**，只交付已证明有效的补丁。
- **证据锚点交付（evidence-anchored）** —— 每条 finding 带 `file:line` 与真实扫描证据；交付报告是 `json`，可 diff、可复现、可进 CI。
- **防空转 stall guard** —— 连续 N 轮零改善立即刹车交给人，杜绝"来回改、越改越乱"。
- **零第三方依赖** —— 只用 Python 标准库，`git clone` 即可跑，无 `pip install`、无网络、无 API Key。
- **回归自测自带判别测试** —— `test_engine.py` 同时断言「脏样本必须 CONVERGED 且 SecScan 沙箱变绿」与「干净样本必须 ALL GREEN」，和 maxloop 的旧红新绿同构。

---

## 🔁 快速开始

### 安装

零第三方依赖，只要本机有 Python ≥ 3.10：

```bash
git clone https://github.com/huanweide/codehealth-loop.git
cd codehealth-loop
```

### 跑一次自愈闭环

```bash
python engine.py /path/to/your/project          # 默认最多 6 轮，带 stall guard
python engine.py ./your-project --max-rounds 8  # 自定义轮数
```

### 自测（判别测试，本地真绿）

```bash
python test_engine.py
```

真实输出：

```text
[ok] axis registry: 12 axes, numbers [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
[ok] dirty sample CONVERGED; SecScan verified-green in sandbox
[ok] clean sample ALL GREEN; health=99
ALL TESTS PASSED
```

> 自测自己在临时目录里造脏/干净样例，**从不扫描本仓源码**（dogfood 纪律），因此结果稳定可复现。

---

## 🔁 CLI 速查

| 命令 | 用途 |
|---|---|
| `python engine.py <dir>` | 对指定项目跑自愈闭环（默认最多 6 轮） |
| `python engine.py <dir> --max-rounds N` | 自定义最大迭代轮数 |
| `python engine.py .` | 对当前目录（含本仓自身）自检 |
| `python engine.py --help` | 查看全部参数 |
| `python test_engine.py` | 回归 + 判别测试（退出码非 0 即失败） |

---

## 🔁 架构

引擎把四件真实武器熔成一条流水线：**感知 → 刹车 → 修复 → 收敛**，四道刹车串成铁链，收敛标准是"外部判据全绿"，不是"模型说好了"。

| 原语 Primitive | 含义 |
|---|---|
| **红点 finding** | 带 `file:line` 的具体问题，不是"感觉不好" |
| **轴 axis** | 一个可插拔的静态探针（12 个，编号 1–12，唯一） |
| **R/C/N 判定** | R 非改不可 / C 可选项 / N 不该加 —— 必要性与根因闸门 |
| **判别测试** | 沙箱副本上"旧版必红 / 新版必绿"，证明是改动起的效 |
| **verified_green** | 修复候选已在沙箱里被重跑证明变绿 |
| **manual** | 无可机械验证的修复（需重构），诚实移交人工，不假装修好 |

```text
   代码仓库
      ↓
  ① PerceptionLayer 感知层 · 12 轴扫描（judges/）
      ↓ 红点（file:line + evidence）
  ② BrakeCore 刹车内核 · R/C/N 根因闸门 + Oracle Gate + 证据锚点
      ↓ 未达标
  ③ Healer 修复层 · 生成候选 → 沙箱副本重跑该轴 → 旧红新绿 → verified_green
      ↓
  ④ ConvergenceProtocol 收敛协议 · 逃逸阶梯 / stall guard
      ↓ 全绿 + 判别测试通过
   交付：DELIVERY json（证据锚定）+ 修复候选（不自动落地）
```

| 模块 Module | 文件 | 说明 |
|---|---|---|
| 感知层 | `engine.py` → `PerceptionLayer` | 发现并调度 `judges/` 下全部 12 个轴 |
| 刹车内核 | `engine.py` → `BrakeCore` | R/C/N 根因闸门 + Oracle Gate + 证据锚点 |
| 收敛协议 | `engine.py` → `ConvergenceProtocol` | 逃逸阶梯 + stall guard 防空转 |
| 主循环 | `engine.py` → `run_loop` / `_round` / `_deliver` | 轮次驱动与 evidence-anchored 交付 |
| 修复层 | `healer.py` → `propose` / `sandbox_verify_fix` | 沙箱副本验证修复，绝不改用户代码 |
| 12 个健康轴 | `judges/*.py` | repodoctor / commitdoctor / devdoctor / docdoctor / pkgdoctor / reldoctor / typedoctor / a11ydoctor / secscan / cycscan / dupscan / enghealth |
| 裁判公共库 | `judges/_common.py` | 扫描、去注释、严重度等共享逻辑 |
| 回归自测 | `test_engine.py` | 轴注册表 + 脏样本收敛 + 干净样本全绿 |

---

## 🔁 加一个你自己的健康轴

轴是可插拔的：往 `judges/` 丢一个文件，导出 `run(root)` 返回 finding 列表，感知层会自动纳管。

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
                    "message": "遗留安全 TODO 未处理",
                })
    return findings
```

感知层要求：**轴编号唯一、名称唯一、每条 finding 必须带 `file:line` 证据** —— `test_engine.py` 会替你把住这道门。

---

## 🔁 已实现 vs 路线图（诚实标注）

| 层 | 状态 | 说明 |
|---|---|---|
| PerceptionLayer · 12 轴 | ✅ 已实现 | `judges/` 下 12 个真实静态探针，零依赖、离线、确定性 |
| BrakeCore 四道刹车 | ✅ 已实现 | `engine.py` 真实跑通，判别测试由 `test_engine.py` 锁死 |
| Healer 沙箱验证层 | ✅ 已实现 | `healer.py`：候选 → 沙箱重跑 → `verified_green` |
| 回归 / 判别测试 | ✅ 已实现 | `test_engine.py`，脏样本与干净样本双向断言 |
| AdversarialMatrix 7 视角对抗评审 | 🔜 接口预留 | 计划接入 [`advverify`](https://github.com/huanweide/advverify) 的多视角评审作为 R/C/N 对抗输入 |
| GuardrailLayer 护栏层 | 🔜 接口预留 | 计划接入 [`forge-safeguard-20260812`](https://github.com/huanweide/forge-safeguard-20260812) 拦截破坏性命令 |
| 自动落地修复到用户代码 | ❌ 不提供（安全铁律） | 只交付"经沙箱验证的修复候选"，落地由人 / 上层 agent 执行 |

---

## 🔁 相关项目

同一套范式（**外部判据刹车 · 杜绝假绿空转 · 四道刹车**）在不同载体的落地，互相导流：

| 项目 | 载体 | 一句话 |
|---|---|---|
| [`maxloop-overlord`](https://github.com/huanweide/maxloop-overlord) | Agent Skill | 范式本体：BrakeCore 四道刹车就来自它 |
| [`codehealth-loop`](https://github.com/huanweide/codehealth-loop) | Python 引擎（本仓库） | 范式在"工程健康"垂直场景的具象化 |
| [`veriloop`](https://github.com/huanweide/veriloop) | Python CLI | 范式在"代码审计"场景的具象化：12 分析轴 + 4 道验证刹车 |
| [`overlord-loop`](https://github.com/huanweide/overlord-loop) | 引擎实现 | 带刹车的 AI 代码进化闭环引擎 |
| [`doctors`](https://github.com/huanweide/doctors) | Node CLI 全家桶 | 本引擎感知层 8 个轴的来源，逻辑已忠实移植为 Python 探针 |
| [`family-showcase`](https://github.com/huanweide/family-showcase) | 单页 HTML | 工程健康家族 18 轴全景仪表盘 |

---

## 🔁 安全边界

> ⚠️ **它绝不自动改你的代码。**
> - 修复只在**沙箱副本**上验证，验证通过后作为候选交付，落地由你 / 上层 agent 执行。
> - 无可机械验证的修复（如高圈复杂度需重构）标 `manual` 移交人工，**不假装修好**。
> - 零第三方依赖、不联网、不读取任何密钥；扫描只读。

## 🔁 License

[MIT](LICENSE) © 2026 huanweide

---

<div align="center">
  <b>如果 codehealth-loop 让你在上线前多抓了一个真问题，点个 ⭐ Star 让更多人看到。</b><br/>
  <a href="https://github.com/huanweide/codehealth-loop">huanweide/codehealth-loop</a>
</div>
