# Round 17.3: Go/No-Go Review
# 投产评审结论

**评审日期**: 2026-04-10 (30天Shadow期满)  
**配置**: deliberation=70, review=80  
**样本**: 50个真实观测 (seed 20260322)

---

## 评审结论: NO-GO

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│   决策: CONTINUE SHADOW (继续影子验证)                           │
│   状态: 接近门槛，但未达标                                        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 门槛检查

| 门槛 | 要求 | 实测 | 状态 |
|------|------|------|------|
| **FB Rate** | ≤ 15.0% | **16.0%** | ❌ **FAIL** (差距 1.0%) |
| **Alignment** | ≥ 75.0% | **76.0%** | ✅ PASS |
| Extra Rounds | ≤ 40% | 14% | ✅ PASS |
| 样本数 | ≥ 50 | 50 | ✅ PASS |
| 天数 | ≥ 30 | 30 | ✅ PASS |

**判定规则**: 必须**全部同时满足**才能Promote，任一FAIL即NO-GO。

---

## 根因分析

### Source分层诊断

| Source | FB Rate | 目标 | 状态 | 诊断 |
|--------|---------|------|------|------|
| replay_real | **0.0%** | ≤15% | ✅ | 历史回放稳定 |
| live_manual | **20.8%** | ≤20% | 🟡 | 接近目标 |
| **live_auto** | **23.1%** | ≤20% | ❌ | **主因，需优先修复** |

**关键洞察**: 
- 系统在历史数据上表现稳定 (replay_real 0% FB)
- 在线自动流 (live_auto) 是主要拖累项
- 问题不是架构性的，是在线场景误判控制不足

### 定性判断

```
Alignment gate:  PASS (能力方向正确)
Safety gate:     FAIL (风险控制不足)
─────────────────────────────────────
Decision:        NO-GO (继续Shadow)
```

**解读**: 策略主方向可接受，但误伤仍需压低。

---

## 下一步行动计划

### P0: 定向修复 live_auto FB (第一优先)

**目标**: live_auto FB Rate 23.1% → ≤20%

**动作**:
1. 提取全部 live_auto false block 样本 (约6个)
2. 聚类分析误伤模式
3. 对比 live_manual 与 live_auto 的错误类型差异
4. 识别: 阈值问题 / 上下文缺失 / 分类边界过紧

**验证**: 再跑50样本Shadow，确认 live_auto FB ≤20%

### P1: 整体FB压线 (第二优先)

**目标**: Overall FB Rate 16.0% → ≤15%

**动作**:
- 若 live_auto 修复后整体FB仍>15%，考虑 deliberation=68
- 单次微调幅度不超过2分

### P2: 保持Alignment (监控)

**目标**: Alignment 保持 ≥75%

**警戒线**: 若修复FB导致Alignment<70%，回滚调整

---

## 下轮Shadow目标

| 指标 | 当前 | 下轮目标 | Promote门槛 |
|------|------|----------|-------------|
| Overall FB | 16.0% | **≤15%** | ≤15% |
| live_auto FB | 23.1% | **≤20%** | - |
| live_manual FB | 20.8% | ≤20% | - |
| Alignment | 76.0% | ≥75% | ≥75% |

---

## 一句话结论

> **Round 17.3 NO-GO: FB Rate 16% 超门槛1个百分点，live_auto (23.1%) 是主因。继续Shadow，定向修复live_auto误伤，再验证。**

---

## 附录: 原始数据路径

- 观测数据: `data/shadow/SHADOW-R17-3-REAL_observations.jsonl`
- 汇总报告: `data/shadow/SHADOW-R17-3-REAL_report.json`
- 生成脚本: `rounds/round17/generate_real_shadow_data.py` (seed 20260322)
