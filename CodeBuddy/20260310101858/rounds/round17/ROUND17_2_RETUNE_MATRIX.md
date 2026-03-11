# Round 17.2: Retune Matrix
# 定点调参矩阵

**状态**: 归因分析完成，Retune 条件已满足  
**触发依据**: live_manual source concentration 63.2% > 60% 阈值  
**目标**: 定点修复 deliberation/review 阈值过严问题，不改架构

---

## 问题定位总结

### 当前指标 (50样本)
| 指标 | 当前值 | 目标值 | 状态 |
|------|--------|--------|------|
| False-Block Rate | 38% | ≤15% | ⚠️ 超标2.5x |
| Decision Alignment | 24% | ≥75% | ⚠️ 严重不足 |
| live_manual FB Rate | 40% | ≤15% | 🔴 最集中 |

### 集中点分析
```
Source Concentration:  live_manual = 63.2% ✅ >60% (Retune触发)
Gate Concentration:    deliberation_minimum = 41.5% (未触发但显著)
                       review_minimum = 41.5%

边界样本分布:
  deliberation_score: 61-74 (阈值75) → 大量接近但未过线
  review_score: 63-79 (阈值80) → 大量接近但未过线
```

### 议题敏感型
```
strategic_initiative:  6/6 分歧 (100%) 🔴
technical_decision:    5/6 分歧 (83%) 🔴
compliance_check:      7/9 分歧 (78%) 🔴
```

---

## Retune 优先级矩阵

### P0: 下调 Deliberation Threshold (第一优先)

| 参数 | 当前值 | 目标值 | 改动 |
|------|--------|--------|------|
| deliberation_threshold | 75 | 70 | -5 |

**预期影响**:
- False-Block Rate: 38% → 20-25%
- Decision Alignment: 24% → 40-50%
- Accepted-Risk: 保持或轻微下降
- Extra Rounds: 可能轻微上升

**验证指标**:
- 重新跑同一批50样本
- 重点关注 deliberation_score 61-74 区间的案例
- 检查 strategic_initiative / technical_decision 改善情况

**停止条件**:
- 如果 False-Block 下降 < 5% → 继续 P1
- 如果 Accepted-Risk 恶化 > 50% → 回滚

---

### P1: Source-Aware Calibration (第二优先)

| Source | deliberation_threshold | review_threshold |
|--------|------------------------|------------------|
| live_manual (默认) | 70 | 80 |
| live_auto | 72 | 80 |
| replay_real | 75 | 80 |

**预期影响**:
- live_manual FB Rate: 40% → 25-30%
- 整体 FB Rate: 25% → 18-20%

**验证指标**:
- 按 source 分桶统计 FB Rate
- 确保 live_auto/replay_real 不显著恶化

**停止条件**:
- live_manual FB Rate > 30% → 继续下调至 65
- live_auto FB Rate > 25% → 回滚 source-aware

---

### P2: Topic-Aware Margin (第三优先)

| Topic Type | deliberation_threshold | margin |
|------------|------------------------|--------|
| strategic_initiative | 65 | -5 (相对默认) |
| technical_decision | 68 | -2 |
| compliance_check | 68 | -2 |
| 其他 | 70 | 0 |

**预期影响**:
- strategic_initiative 分歧: 6/6 → 3-4/6
- technical_decision 分歧: 5/6 → 3/6

**验证指标**:
- 按 topic 分桶统计分歧率
- 检查是否引入新的漏检

**停止条件**:
- 任何 topic 的 accepted_risk 显著上升 → 回滚该 topic 配置

---

### 不建议调整

| 组件 | 原因 |
|------|------|
| defect_check | 当前仅14 blocks，非主因 |
| review_threshold (全局) | 先观察 deliberation 调整效果 |
| oppose_penalty / veto_penalty | 当前配置已验证有效 |

---

## 最小可复现实验流程

### 实验1: Deliberation Threshold 75→70

```bash
# 1. 创建新配置
deliberation_threshold: 70
review_threshold: 80 (保持)
其他参数: 保持

# 2. 重跑50样本
python3 rounds/round17/retune_experiment.py \
  --config deliberation_70 \
  --samples SHADOW-20260311-PROD_observations.jsonl

# 3. 检查指标
- False-Block Rate target: < 30%
- Decision Alignment target: > 40%
- Accepted-Risk count: < 20 (不恶化)

# 4. 判定
PASS → 进入实验2 (source-aware)
FAIL → 继续下调至 65
```

### 实验2: Source-Aware Calibration

```bash
# 1. 配置
live_manual: deliberation_threshold=70
live_auto: deliberation_threshold=72
replay_real: deliberation_threshold=75

# 2. 重跑50样本
python3 rounds/round17/retune_experiment.py \
  --config source_aware \
  --samples SHADOW-20260311-PROD_observations.jsonl

# 3. 检查指标
- live_manual FB Rate: < 30%
- live_auto FB Rate: < 20%
- 整体 FB Rate: < 20%

# 4. 判定
PASS → 进入实验3 (topic-aware) 或结束
FAIL → 下调 live_manual 至 65
```

### 实验3: Topic-Aware Margin (可选)

```bash
# 仅当议题分歧仍显著时使用
strategic_initiative: deliberation_threshold=65
其他: 按 source-aware 配置
```

---

## 验证通过标准

### 阶段性通过 (进入下一轮)
- False-Block Rate 每次下降 ≥ 5%
- Decision Alignment 每次上升 ≥ 10%
- Accepted-Risk count 不恶化 > 20%

### 最终通过 (进入新 Shadow 期)
- False-Block Rate ≤ 20% (接近 15% 门槛)
- Decision Alignment ≥ 60% (接近 75% 门槛)
- 有明确配置可归因改善

### 回滚条件
- 任何指标恶化超过基线
- Accepted-Risk 显著上升 (漏检增加)

---

## 输出交付物

1. **retune_experiment.py**: 实验执行脚本
2. **retune_report.json**: 每次实验结果
3. **config_recommendation.json**: 最终推荐配置

---

## 一句话策略

> 先降 deliberation 门槛 75→70，再对 live_manual 做 source-aware 校准，最后按需做 topic-aware。每次只改一个变量，用同一批50样本验证，直到 FB Rate < 20% 且 Alignment > 60%。
