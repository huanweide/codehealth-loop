# Architecture · 工程健康自愈引擎概念架构

> 本文档走"概念与架构路线"：把散落的四个真实项目，按一套系统化、可扩展的架构重新编排。
> 每个概念层都**真实映射到代码或已存在的仓库**，不发明不存在的能力。

---

## 0. 总览：四层一协议

```
            ┌─────────────────────────────────────────────┐
  代码仓库 → │  PerceptionLayer  │ AdversarialMatrix │ GuardrailLayer │
            │   感知层 (12轴)    │   评审矩阵(7视角)  │   护栏层        │
            └─────────────────────────────────────────────┘
                              │ 原始信号 + 评审 + 安全约束
                              ▼
                    ┌───────────────────────┐
                    │   BrakeCore 刹车内核   │  ← maxloop 四道刹车
                    │ R/C/N+根因 │ Oracle   │
                    │ Gate+证据  │ 判别测试 │
                    └───────────────────────┘
                              │ 未达标
                              ▼
                    ┌───────────────────────┐
                    │ ConvergenceProtocol   │  逃逸阶梯 + stall guard
                    └───────────────────────┘
                              │ 再迭代
                              ▼
                           回到 代码仓库
                              │ 全绿 + 判别测试通过
                              ▼
                       真达标交付（证据报告）
```

设计铁律：**任何一层的"通过"都不能由自身声明，必须被上一层（或 Oracle Gate）以真实证据背书。**

---

## 1. PerceptionLayer · 感知层（12 Health Axes）

**概念**：代码不是"对/错"二值，而是 12 个正交的健康维度。每层轴是一个**零依赖、离线、确定性**的静态探针，输出 `{passed, score, findings, evidence}`。

**已实现的 3 轴（真实可跑，`judges/`）：**
| Axis | 名称 | 真实实现 | 探针逻辑 |
|---|---|---|---|
| 4 | CycScan | `judges/cycscan.py` | Python 用 `ast` 数决策点；JS/TS 用分支关键字启发式 |
| 7 | SecScan | `judges/secscan.py` | 正则扫危险调用（`eval`/`exec`/`child_process`/`innerHTML=`/拼接 SQL） |
| 9 | DupScan | `judges/dupscan.py` | 4 行块归一化哈希，统计跨文件重复率 |

**可插拔的 9 轴（路线图）**：直接复用 `doctors` 家族的 12 个零依赖 CLI（a11y/commit/dev/doc/pkg/rel/repo/type/test/lit/debug/debt/await/chaineye/idiot/lic/gha），每个抽成 `judges/<name>.py` 的 `evaluate(root)` 接口即可。

**接口契约**：
```python
def evaluate(root: str) -> dict:
    return {"axis": int, "name": str, "passed": bool,
            "score": int, "scanned": int,
            "findings": [{"file": str, "line": int, ...}],
            "evidence": str}   # 必须有真实证据串，否则 BrakeCore 判其无效
```

---

## 2. AdversarialMatrix · 评审矩阵（7-Mind Collision）

**概念**：单一视角挑不出全部问题。把同一份代码丢给 7 个独立"人格思维模型"评审，取**碰撞点**（多个框架同时标红的位置）= 共识级"必改项"。

**真实来源**：`advverify` 的 7 思维模型（Munger / Musk / Feynman / Taleb / 张雪峰 / Linus / Carmack）。

**在本架构的角色**：作为 BrakeCore 中 **R/C/N 根因闸门** 的对抗输入 —— 不止看判据红不红，还看"多个心智模型是否独立觉得这里危险"。MVP 阶段接口预留，不强制实现。

---

## 3. GuardrailLayer · 护栏层

**概念**：自愈引擎若被允许"自动改代码"，必须有一道**执行前护栏**拦截破坏性命令（删除、强制推送、危险 rm 等），区分"引用提及"与"真实执行"。

**真实来源**：`forge-safeguard` 的破坏性命令识别逻辑。

**接口**：`should_block(command: str) -> bool`。在自动修复闭环（路线图）中，任何写盘/执行动作先过护栏。

---

## 4. BrakeCore · 刹车内核（maxloop 四道刹车）

**概念**：这是引擎的灵魂，源自 `maxloop-overlord`。它解决的不是"怎么改代码"，而是"**什么时候能说改好了**"。四道刹车：

1. **R/C/N + 根因闸门（Root-Cause Gate）**
   每轮先把所有红轴收敛成带 `file:line` 证据的根因，禁止"我觉得差不多了"。
2. **Oracle Gate + 证据锚点（Evidence Anchor）**
   判据输出必须携带真实 `evidence` 串；缺证据的"通过"一律判为红。杜绝自说自话。
3. **判别测试（Discrimination Test · 旧红新绿）**
   本轮相较上一轮，曾经的红色必须转绿，才算"真进步"；否则视为假绿。
4. **逃逸阶梯 + stall guard（Convergence）**
   卡住自动升级策略（standard → deepen → escalate-to-human）；连续 `stall_patience` 轮健康分无改善，立即刹车交人，绝不空转。

**代码位置**：`engine.py` 的 `BrakeCore` / `ConvergenceProtocol` 类，真实跑通（见 README 示例）。

---

## 5. 数据流（一轮迭代）

```
1. PerceptionLayer.sweep(root) → results[ {axis,name,passed,score,findings,evidence} ]
2. BrakeCore.oracle_gate(results) → (passed, red_axes)   # 缺证据也判红
3. if passed:
     BrakeCore.discrimination_test(prev, results) → 全绿且旧红转绿 ⇒ DELIVER
   else:
     causes = BrakeCore.root_cause_gate(red_axes)  # 带 file:line 证据
     strategy = ConvergenceProtocol.escape_ladder(round)
     if ConvergenceProtocol.stall_guard(health): DELIVER(w/ "STALL GUARD")
     else: 打印证据根因 → 上层 agent 据此修复 → 下一轮
```

---

## 6. 设计哲学（为什么这样分）

- **分层解耦**：感知（判据）、评审（对抗）、护栏（安全）、刹车（收敛）各司其职，可独立替换/扩展。
- **证据优先**：任何结论必须能逐字符回溯到真实工具输出，否则不出报告（VulnClaw 偷学纪律）。
- **刹车不是装饰**：stall guard 是反"假绿空转"的硬保险，宁可交人也不自嗨。
- **合成而非重写**：12 轴来自 doctors、7 视角来自 advverify、护栏来自 forge-safeguard、刹车来自 maxloop —— 本引擎是它们的**编排层**，不是第 5 套重复轮子。
