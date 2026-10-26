---
name: codehealth-loop
description: 工程健康自愈引擎——把 maxloop 四道刹车作为核心循环，调度 doctors 12 轴体检 + advverify 对抗评审 + forge-safeguard 护栏，对代码仓库做"多轴体检→对抗评审→带刹车迭代→真达标才交付"的自愈闭环。用于 AI 写代码后防假绿、自动收敛到真健康。
---

# codehealth-loop · Agent 操作手册

> 本 SKILL 把 `maxloop-overlord` 的刹车内核具象到"代码健康"垂直场景。Agent 用它来**替代"写完就交付"的假绿流程**：写完代码先过本引擎，全绿 + 判别测试通过才算真达标。

---

## 0. 核心铁律（来自 maxloop）

- **不自我声明通过**：任何"健康/达标"结论必须被 Oracle Gate 以真实判据证据背书。
- **证据锚点**：每条根因必须带 `file:line`，否则不出报告。
- **判别测试**：上一轮红、本轮才绿，才算真进步（旧红新绿）。
- **stall guard**：连续 N 轮健康分无改善 → 立即刹车交人，不空转。

---

## 1. 调用方式

```bash
# 对目标项目跑自愈闭环（默认 ≤6 轮，带 stall guard）
python engine.py /path/to/project

# 自定义轮数
python engine.py /path/to/project --max-rounds 8
```

引擎输出 JSON 交付报告，含每个轴的 `passed/score/evidence` 与收敛结论。

---

## 2. 主循环（Chair 视角）

```
每轮：
  1. PerceptionLayer 跑全部已注册 judge（CycScan/SecScan/DupScan + 可插拔轴）
  2. BrakeCore.oracle_gate(results)
       - 任一轴红 或 缺证据 ⇒ 判红
  3. 若全绿：
       - BrakeCore.discrimination_test(prev, results)
         · 首轮即全绿 ⇒ DELIVER
         · 旧红已转绿 ⇒ DELIVER
         · 否则继续（记录 prev）
  4. 若红：
       - BrakeCore.root_cause_gate(red) ⇒ 带 file:line 的根因清单
       - Healer.propose(red, percept.by_name, root) ⇒ 生成修复候选 + **沙箱副本验证变绿**
         · 有 `verified_green` 候选 ⇒ DELIVER("CONVERGED: N axis proven fixable")  # 闭环收敛
         · 无机械可验证修复 ⇒ 继续
       - ConvergenceProtocol.escape_ladder(round) ⇒ 策略升级
       - ConvergenceProtocol.stall_guard(health) ⇒ 触发则 DELIVER(交人)
       - Agent 依据根因清单 + 修复候选修复代码 ⇒ 下一轮
```

---

## 3. 角色分工

- **PerceptionLayer（感知）**：客观判据，不解释、只报 `passed/score/evidence`。
- **AdversarialMatrix（评审）**：多心智模型碰撞，标"共识级必改项"（路线图接口）。
- **GuardrailLayer（护栏）**：自动修复执行前拦截破坏性命令（路线图接口）。
- **BrakeCore（刹车）**：判敛灵魂，决定"能不能说改好了"。
- **Healer（修复候选）**：对红轴生成修复候选，并在沙箱副本上验证其确实让轴变绿；**绝不改用户代码**，只交付"经验证的补丁"。
- **Agent（你）**：消费证据根因清单 + 修复候选 → 真去改代码（或采纳候选）→ 触发下一轮。

---

## 4. 扩展：新增一个健康轴（judge 插件）

在 `judges/` 下放 `<name>.py`，实现：

```python
def evaluate(root: str) -> dict:
    return {
        "axis": 10, "name": "MyAxis", "passed": bool,
        "score": int, "scanned": int,
        "findings": [{"file": "x.py", "line": 1, ...}],
        "evidence": "scanned N files, M hits"   # 必须有
    }
```

引擎启动时自动发现并加载，无需改核心。这把 `doctors` 家族 12 叶子的能力变成可插拔轴。

---

## 5. 与 maxloop-overlord 的关系

- `maxloop-overlord` 是**通用**迭代质量引擎（任何任务的防假绿）。
- 本 SKILL 是它在"代码健康"的**垂直具象**：BrakeCore = maxloop 四道刹车的 Python 实现；PerceptionLayer = doctors 12 轴；AdversarialMatrix = advverify；GuardrailLayer = forge-safeguard。
- 二者共享同一套刹车纪律，互为实证。

---

## 6. 终止条件

- ✅ 全轴绿 + 判别测试通过 ⇒ 真达标交付。
- ⛔ stall guard 触发 ⇒ 交人（附证据报告，不假装修好）。
- ⛔ 达到 `--max-rounds` ⇒ 交付当前证据报告，由人定夺。
