# 执行计划: Round 17.4 + Gate 3 Phase 1 并行

> 状态: 2026-03-11  
> 策略: **80/20 并行** - Round 17.4 主线优先，Gate 3 Phase 1 同步准备

---

## 当前仓库状态

### Round 17.4 (主线安全修复)
- **位置**: `CodeBuddy/20260310101858/rounds/round17/ROUND17_4_START.md`
- **基线**: Capability PASS (76%), Safety FAIL (FB 16%, live_auto 23.1%)
- **目标**: live_auto FB ≤20%, Overall FB ≤15%, 不破坏 Capability
- **约束**: deliberation=70, review=80 固定

### Persona System v2 (已落档)
- **Gate 2**: ✅ **PASSED** (9/9 trials)
- **最新提交**: `6548a3f` (GATE2_VERDICT.md + GATE3_BENCHMARK_SPEC.md)
- **门槛统一**: Distinguishability ≥80%, Coverage +30%, Overlap -30%
- **状态**: Ready for Gate 3 Phase 1

---

## 并行策略: 80/20 分配

### P0 (80% 精力): Round 17.4 live_auto 修复

**为什么优先**: 生产安全问题，现有系统的安全修复

**当前进度**: Step 1 起点定义已完成 (ROUND17_4_START.md)

**下一步执行**:

| Step | 任务 | 预计时间 | 产出 |
|------|------|----------|------|
| 1 | 样本抽取 | 1 天 | live_auto false-block 样本集 (6-7 个) |
| 2 | 误伤分型 | 1 天 | 错误模式聚类报告 |
| 3 | 根因归类 | 1-2 天 | 根因分类: 阈值/上下文/boundary/聚合 |
| 4 | 单点修复 | 2-3 天 | source-aware 调整代码 |
| 5 | 50 样本验证 | 2 天 | 验证报告: FB ≤15%, live_auto ≤20% |

**成功标准**:
- Overall FB Rate: 16% → ≤15%
- live_auto FB Rate: 23.1% → ≤20%
- Alignment: ≥75% (不破坏)

**失败回滚**:
- Alignment < 75% → 回滚
- live_manual FB > 25% → 检查影响
- Overall FB > 18% → 重新分型

---

### P1 (20% 精力): Gate 3 Phase 1 任务准备

**为什么并行**: 不干扰 Round 17.4，为后续 benchmark 打地基

**当前进度**: GATE3_BENCHMARK_SPEC.md 已完成

**Phase 1 任务集**:

| 子任务 | 内容 | 预计时间 | 产出 |
|--------|------|----------|------|
| 1.1 | 定义 50 个任务 | 2-3 天 | 5 类 × 10 任务 JSON 文件 |
| 1.2 | 设计 success criteria | 1 天 | 每任务客观判定标准 |
| 1.3 | 编写评分 rubric | 0.5 天 | 评分员指南 |
| 1.4 | 准备测试环境 | 0.5 天 | 环境配置脚本 |

**任务分类**:
1. **strategic** (10): 市场进入、竞争策略、资源分配
2. **system_design** (10): 架构设计、技术选型、扩展规划
3. **conflict_resolution** (10): 利益冲突、谈判策略、共识达成
4. **crisis_response** (10): 紧急决策、风险管控、声誉修复
5. **innovation** (10): 产品规划、技术路线、组织变革

**暂不执行** (等 Round 17.4 完成后):
- ❌ Phase 2: Pilot (3 任务 × 3 组)
- ❌ Phase 3: 全量实验 (50 任务 × 3 组)
- ❌ Phase 4: 结果分析

---

## 时间节点规划

```
Week 1 (现在起)
├── Day 1-2: Round 17.4 Step 1-2 (样本抽取 + 误伤分型)
├── Day 3-4: Gate 3 Phase 1.1-1.2 (定义 20-30 任务 + criteria)
└── Day 5: Round 17.4 Step 3 (根因归类)

Week 2
├── Day 1-3: Round 17.4 Step 4 (单点修复)
├── Day 4-5: Gate 3 Phase 1.3-1.4 (完成 50 任务 + 环境)
└── 同步: Round 17.4 Step 5 (50 样本验证)

Week 3
├── Round 17.4 收尾
├── Round 17.5? 或直接进入 Gate 3 Phase 2
└── Gate 3 Phase 2 Pilot (3 任务 × 3 组)
```

---

## 资源分配

| 资源 | Round 17.4 | Gate 3 Phase 1 | 备注 |
|------|------------|----------------|------|
| 人力 | 80% | 20% | 开发人员时间 |
| GPU/Token | 按需 (验证时高) | 低 (仅文档) | Phase 1 不跑模型 |
| 存储 | 中等 (样本+日志) | 低 | 任务定义 JSON |
| 注意力 | 高 (需深度分析) | 中 (标准设计) | 错峰执行 |

---

## 决策检查点

### 检查点 1: Round 17.4 Step 3 完成 (Week 1 结束)
- **问题**: 根因是否清晰？是否可单点修复？
- **Go**: 继续 Step 4
- **No-Go**: 重新分型，考虑是否需 threshold 调整

### 检查点 2: Round 17.4 Step 5 完成 (Week 2 结束)
- **问题**: 是否达成 FB ≤15%, live_auto ≤20%?
- **Go**: Round 17.4 完成，启动 Gate 3 Phase 2
- **No-Go**: 回滚或进入 Round 17.5

### 检查点 3: Gate 3 Phase 1 完成 (Week 2 结束)
- **问题**: 50 任务定义是否完整？criteria 是否客观？
- **Go**: 等待 Round 17.4 完成后启动 Phase 2
- **No-Go**: 补充任务定义

---

## 风险与缓解

| 风险 | 概率 | 影响 | 缓解 |
|------|------|------|------|
| Round 17.4 超期 | 中 | Gate 3 延迟 | Phase 1 继续并行，不阻塞 |
| Gate 3 任务定义模糊 | 低 | 后续评分主观 | 提前设计 rubric，双人盲评 |
| 精力分散导致两者都慢 | 中 | 整体延迟 | 严格 80/20， Round 17.4 优先 |
| Round 17.4 失败 | 低 | 需回滚或重设计 | 保留基线，快速回滚能力 |

---

## 下一步立即执行

### 今天 (Hour 0-4)
1. **Round 17.4**: 开始 Step 1 - 从 shadow data 提取 live_auto false-block 样本
2. **Gate 3**: 开始 Phase 1.1 - 设计前 10 个 strategic 任务框架

### 明天 (Hour 4-8)
1. **Round 17.4**: 完成 Step 1，开始 Step 2 - 误伤分型聚类
2. **Gate 3**: 继续 Phase 1.1 - 设计 10 system_design 任务

### 本周目标
- Round 17.4: 完成 Step 3 (根因归类)
- Gate 3: 完成 30-40 个任务定义

---

## 一句话

> **Round 17.4 主线优先 (安全修复)，Gate 3 Phase 1 同步准备 (打地基)，80/20 精力分配，不等不靠，但也不冒进。**
