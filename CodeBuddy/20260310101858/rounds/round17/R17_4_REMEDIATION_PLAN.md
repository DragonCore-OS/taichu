# Round 17.4 Remediation Plan
# 修复方案

**日期**: 2026-04-10  
**基线**: deliberation=70, review=80 (全局固定)
**目标**: live_auto FB 23.1% → ≤20%

---

## 根因确认

### 关键发现 (Step 1 & 2)

| 发现 | 数据支持 |
|------|----------|
| live_auto false blocks | 3个样本 |
| 100% review threshold失败 | 3/3 |
| live_auto review score平均 | **75.8** |
| live_manual review score平均 | **77.5** |

### 根因结论

```
┌─────────────────────────────────────────────────────────────┐
│  根因: review_threshold=80 对 live_auto 过严                  │
│                                                             │
│  证据:                                                      │
│    - live_auto review score 平均比 live_manual 低 1.7分      │
│    - 同样 threshold=80，live_auto 更容易被拦截               │
│    - 100% false blocks 都是 review threshold 失败            │
│                                                             │
│  修复: source-aware review_threshold                         │
│    - live_auto: 78 (降低2分)                                │
│    - live_manual: 80 (保持)                                 │
│    - replay_real: 80 (保持)                                 │
└─────────────────────────────────────────────────────────────┘
```

---

## 修复方案

### 方案: Source-Aware Review Threshold

```python
CONFIG = {
    "deliberation_threshold": 70.0,  # 全局保持
    "review_threshold": {
        "live_auto": 78.0,      # 降低2分
        "live_manual": 80.0,    # 保持
        "replay_real": 80.0,    # 保持
    }
}
```

### 预期效果

| 指标 | 当前 | 预期 | 验证方式 |
|------|------|------|----------|
| live_auto FB | 23.1% | ≤20% | 50样本Shadow |
| Overall FB | 16.0% | ≤15% | 50样本Shadow |
| Alignment | 76.0% | ≥75% | 50样本Shadow |

### 不破坏Capability的保证

- deliberation_threshold 保持 70 (不动)
- 仅降低 review threshold 2分 (live_auto)
- 这是局部微调，不会显著影响 Alignment

---

## 执行计划

### Step 3: 实现修复 (现在)

1. 修改 shadow_deployment.py 支持 source-aware review_threshold
2. 设置 live_auto review_threshold = 78

### Step 4: 验证 (下一步)

1. 生成50样本新Shadow数据
2. 检查指标: live_auto FB ≤20%, Overall FB ≤15%, Alignment ≥75%
3. 若达标 → Promote; 若未达标 → Extend

---

## 一句话

> **Round 17.4 Remediation: Source-aware review_threshold (live_auto=78, others=80) to reduce live_auto FB from 23.1% to ≤20%.**
