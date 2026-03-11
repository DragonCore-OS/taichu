# Round 17.3: Shadow Deployment Launch
# 新一轮影子部署启动文档

**日期**: 2026-03-11  
**配置版本**: deliberation=70, review=80  
**观察期**: 30天 / 50个真实会议  

---

## 部署决策

### 采用配置
```python
{
    "deliberation_threshold": 70.0,  # Round 17.2 验证的推荐值
    "review_threshold": 80.0,        # 保持不动
    "max_defects": 1,
    "support_weight": 1.0,
    "oppose_penalty": 1.5,
    "veto_penalty": 3.0
}
```

### 决策依据 (Round 17.2 结论)

| 配置 | FB Rate | Alignment | Accepted-Risk | 判定 |
|------|---------|-----------|---------------|------|
| 75/80 (旧) | 38% | 24% | 17 | ❌ 过严 |
| **70/80 (新)** | **16%** | **38%** | **7** | ✅ **采用** |
| 70/75 | 16% | 42% | 7 | ⚠️ 多改一个变量，归因弱 |
| 65/80 | 4% | 48% | 1 | ⚠️ 过松，漏检风险 |

**选择 70/80 的理由**:
1. **最小有效改动**: 只改 deliberation 一个参数
2. **不过度放松**: FB 16% 接近 15% 门槛，非 4% 过松
3. **问题主因匹配**: deliberation 是主要瓶颈，review 不是
4. **风险可控**: Accepted-Risk 7个处于合理水平

---

## 观察目标

### 本轮目标 (30天后验收)

| 指标 | 当前值 | 本轮目标 | 最终目标 |
|------|--------|----------|----------|
| False-Block Rate | 16% | **≤ 15%** | ≤ 15% |
| Decision Alignment | 38% | **≥ 60%** | ≥ 75% |
| Accepted-Risk Cases | 7 | 保持 5-10 | 保持合理水平 |
| Extra Rounds | - | ≤ 0.4 | ≤ 0.4 |

### 通过标准

**Promote (晋升生产默认)**: 需同时满足
- FB Rate ≤ 15%
- Alignment ≥ 75%
- 30天后 Accepted-Risk 验证完成

**Extend (延长观察)**: 如
- FB Rate 15-20% (接近但未达标)
- Alignment 60-75% (改善但未达标)

**Retune (再次调参)**: 如
- FB Rate > 20% (改善不足)
- Alignment < 60% (方向错误)

---

## 启动检查清单

- [x] 配置更新: deliberation_threshold = 70
- [x] 配置保持: review_threshold = 80
- [x] 其他参数: 与 Round 17 保持一致
- [x] 数据目录: `data/shadow/` 已就绪
- [x] 日志格式: 与上一轮保持一致 (确保可比性)

---

## 三条纪律 (重申)

1. **新系统只记录，不拦截**
2. **旧系统仍是唯一执行链**
3. **所有分歧都落日志，不人工挑样本**

---

## 时间线

| 阶段 | 时间 | 动作 |
|------|------|------|
| 启动 | 2026-03-11 | 切换配置，开始收集样本 |
| 中期 | 2026-03-26 (15天) | 可选：检查初步趋势 |
| 验收 | 2026-04-10 (30天) | 收集满50样本，生成报告 |
| 判定 | 2026-04-10 | Promote / Extend / Retune |

---

## 一句话

> **Round 17.2 完成了 P0 定点修复，现在用 deliberation=70/review=80 进入新一轮 Shadow。目标是 FB≤15%, Alignment≥60%，暂不下调 review，暂不 Promote。**
