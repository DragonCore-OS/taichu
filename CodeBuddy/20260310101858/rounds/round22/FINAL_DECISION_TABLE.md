# Round 22: FINAL_DECISION_TABLE

**状态**: 样本收集完成，等待分析判定  
**阈值**: 200 真实样本 (live + replay)  
**当前**: 200 replay + 50 batch_shadow = 250 总样本  
**锁定时间**: 2026-03-11  

---

## 1. 决策门槛（冻结，不可更改）

| 指标 | A (Proceed) | B (Continue) | C (Reject) | F (严重不达标) |
|------|-------------|--------------|------------|----------------|
| **Total ECE** | < 0.18 | 0.18-0.22 | 0.22-0.25 | > 0.25 |
| **Rolling ECE(50)** | < 0.12 | 0.12-0.18 | 0.18-0.20 | > 0.20 |
| **very_high gap** | < +0.08 | +0.08~+0.12 | +0.12~+0.15 | > +0.15 |
| **High-conf error** | < 12% | 12-18% | 18-20% | > 20% |

**决策规则**:
- 全部 A → **PROCEED** (集成)
- 全部 A/B → **CONTINUE** (继续观察)
- 任一 C/F → **REJECT** (放弃)

---

## 2. 当前测量值

**数据来源**: replay (200 样本)  
**测量时间**: 2026-03-11  

| 指标 | 测量值 | 档次 | 状态 |
|------|--------|------|------|
| Total ECE | 0.2621 | F | ❌ 超标 |
| Rolling ECE(50) | 0.2021 | F | ❌ 超标 |
| very_high gap | 1.0000 | F | ❌ 无数据 |
| High-conf error | 0.00% | A | ✅ 正常 |

**综合判定**: **F - REJECT - 严重不达标**

---

## 3. 分析说明

### 3.1 当前结果解读

当前模型使用的是**默认随机权重**（未训练），因此：
- ECE 高（0.26）= 模型未校准，所有预测集中在 ~0.5
- very_high gap = 1.0 = 没有 very_high bucket 的样本
- 这是**预期行为**，不代表最终模型质量

### 3.2 下一步要求

要使用此框架进行真实决策，需要：

1. **替换为训练好的模型**
   ```python
   # 使用 Round 19 训练的模型
   model_path = '/data/taichu/tests/consensus_predictor_model.pkl'
   ```

2. **重新运行分析**
   ```bash
   python3 rounds/round22/analyze_extended_metrics.py
   ```

3. **执行判定**
   - 根据输出等级决定 A/B/C
   - 只有全部指标达到 B 以上才考虑继续

---

## 4. 样本收集状态

### 4.1 来源分布

| 来源 | 数量 | 说明 | 用于决策 |
|------|------|------|----------|
| replay | 200 | 历史回放 | ✅ 是 |
| batch_shadow | 50 | 批量旁路 | ❌ 否 |
| **合计真实** | **200** | live + replay | ✅ **是** |
| **合计全部** | **250** | 所有来源 | - |

### 4.2 收集工具

```bash
# 历史回放（推荐，最接近真实）
python3 rounds/round22/historical_replay.py --count 150

# 批量旁路（补充）
python3 rounds/round22/batch_shadow_runner.py --count 100

# 一键加速
python3 rounds/round22/accelerate_round22.py --target 200
```

---

## 5. 审计原则

### 5.1 样本来源标记

所有样本必须标记来源：
- `live`: 真实生产流量
- `replay`: 历史回放
- `batch_shadow`: 批量旁路
- `synthetic`: 合成边界测试（**不用于决策**）

### 5.2 日志分离存储

```
logs/
├── shadow_predictions_20260311.jsonl          # 主日志（全部）
├── shadow_predictions_live_20260311.jsonl     # 真实流量
├── shadow_predictions_replay_20260311.jsonl   # 历史回放
├── shadow_predictions_batch_shadow_20260311.jsonl  # 批量旁路
└── shadow_predictions_synthetic_20260311.jsonl     # 诊断专用
```

### 5.3 决策优先级

1. **只看 live + replay** 作为真实样本
2. **batch_shadow** 用于快速积累但不计入阈值
3. **synthetic** 仅用于诊断模型薄弱区
4. **绝不混算** 不同来源的指标

---

## 6. 执行指令

### 6.1 检查当前状态

```bash
python3 -c "
import sys
sys.path.insert(0, 'bridge')
from shadow_consensus_predictor import get_shadow_predictor

p = get_shadow_predictor()
status = p.check_threshold(200)
print(f'Real samples: {status[\"real_samples\"]}')
print(f'Can decide: {status[\"can_decide\"]}')
"
```

### 6.2 执行分析

```bash
# 分析真实数据
python3 rounds/round22/analyze_extended_metrics.py --source replay

# 分析所有数据
python3 rounds/round22/analyze_extended_metrics.py
```

### 6.3 触发决策

当 `can_decide = True` 时：

```bash
# 生成报告
python3 rounds/round22/analyze_extended_metrics.py --output report.json

# 根据 overall_grade 执行决策：
# A → 集成到生产环境
# B → 继续观察，扩大样本
# C/F → 放弃，保持 Python 实现
```

---

## 7. 关键规则

| 规则 | 状态 | 说明 |
|------|------|------|
| 不改门槛 | ✅ 锁定 | ECE < 0.22 才能进入 B 档 |
| 不提前集成 | ✅ 锁定 | 必须 200+ 样本才能决策 |
| 来源可审计 | ✅ 实施 | 所有样本标记 live/replay/synthetic |
| 真实优先 | ✅ 锁定 | synthetic 不用于最终决策 |
| 可加速收集 | ✅ 允许 | 主动构造 replay/batch_shadow |

---

## 8. 当前状态总结

```
Round 22 Status: SAMPLE COLLECTION COMPLETE
├── Real samples: 200 ✓
├── Threshold reached: YES ✓
├── Model quality: UNTRAINED (default weights)
├── ECE: 0.26 (F grade - expected for untrained)
└── Decision: PENDING (need trained model)

Next Action Required:
    Replace default model with trained ConsensusPredictor
    Then re-run analysis for actual decision.
```

---

**文档版本**: 1.0  
**最后更新**: 2026-03-11  
**决策冻结**: 是（门槛已锁定）  
