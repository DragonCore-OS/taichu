# Round 17.4: Start Point
# 阶段起点定义

**日期**: 2026-04-10  
**基线来源**: Round 17.3 Go/No-Go Review  
**全局配置**: deliberation=70, review=80 (固定，不做全局调整)

---

## 当前基线 (Fixed)

| Gate | 指标 | 数值 | 状态 |
|------|------|------|------|
| **Capability** | Alignment | **76%** | ✅ **PASS** |
| **Safety** | FB Rate | **16%** | ❌ **FAIL** |
| **Primary Driver** | live_auto FB | **23.1%** | 🔴 **Target** |

---

## 阶段目标

```
Round 17.4 objective: source-targeted remediation on live_auto 
under fixed global thresholds (deliberation=70, review=80).
```

**核心原则**: 在不破坏已达标 Capability (Alignment ≥75%) 的前提下，将 live_auto 误伤压到可接受范围，使总体 FB 从 16% 降至 ≤15%。

---

## 关键约束

| 约束 | 说明 |
|------|------|
| **不做全局降阈值** | deliberation=70, review=80 保持固定 |
| **不破坏 Capability** | Alignment 必须维持 ≥75% |
| **单点修复** | 仅针对 live_auto source |

---

## 执行流程

```
┌─────────────────────────────────────────────────────────────┐
│  Step 1: 样本抽取                                             │
│  └─ 提取全部 live_auto false-block 样本 (约 6-7 个)            │
├─────────────────────────────────────────────────────────────┤
│  Step 2: 误伤分型                                             │
│  └─ 聚类分析错误模式                                          │
├─────────────────────────────────────────────────────────────┤
│  Step 3: 根因归类                                             │
│  ├─ 阈值问题?                                                 │
│  ├─ 上下文缺失?                                               │
│  ├─ topic/classification boundary 问题?                       │
│  └─ 评分聚合偏差?                                             │
├─────────────────────────────────────────────────────────────┤
│  Step 4: 单点修复                                             │
│  └─ source-aware 调整 (仅 live_auto)                          │
├─────────────────────────────────────────────────────────────┤
│  Step 5: 50 样本再验证                                         │
│  └─ 验证: overall FB ≤15%, live_auto FB ≤20%, Alignment ≥75%  │
└─────────────────────────────────────────────────────────────┘
```

---

## 成功标准

| 指标 | 当前 | 目标 | 验证方式 |
|------|------|------|----------|
| Overall FB Rate | 16% | **≤15%** | 50样本Shadow |
| live_auto FB Rate | 23.1% | **≤20%** | Source分桶 |
| Alignment | 76% | **≥75%** | 总体统计 |
| live_manual FB | 20.8% | ≤20% | 不恶化 |

---

## 失败回滚条件

| 条件 | 动作 |
|------|------|
| Alignment < 75% | 回滚修复，保持基线 |
| live_manual FB > 25% | 检查是否影响其他source |
| Overall FB > 18% | 重新分型，考虑 threshold=68 |

---

## 一句话

> **Round 17.4 Start: Capability PASS, Safety FAIL on live_auto. Objective: source-targeted fix under fixed thresholds, validate 50 samples.**
