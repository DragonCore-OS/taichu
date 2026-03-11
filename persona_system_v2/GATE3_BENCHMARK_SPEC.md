# Gate 3: 任务级 Benchmark 设计规范

> 状态: 设计阶段  
> 目标: 验证 Persona System v2 在复杂任务上的实际效果  
> 原则: **前期 token 贵可以接受，空耗 token 不可以**

---

## 实验设计

### 三组对照

| 组别 | 名称 | 描述 | 预期表现 |
|------|------|------|----------|
| A | `single_strong_agent` | 单 GPT-4 agent，最强 baseline | 高成功率，高返工 |
| B | `structured_19_agent` | Persona System v2 (核心 19 席) | **目标最优** |
| C | `unstructured_multi` | 19 agents 无结构，自由讨论 | 高噪音，高 token |

### 任务集定义

**50 个复杂任务**，分为 5 类，每类 10 个:

1. **战略分析类** (strategic): 市场进入、竞争策略、资源分配
2. **系统设计类** (system_design): 架构设计、技术选型、扩展规划
3. **冲突调解类** (conflict_resolution): 利益冲突、谈判策略、共识达成
4. **危机应对类** (crisis_response): 紧急决策、风险管控、声誉修复
5. **创新规划类** (innovation): 产品规划、技术路线、组织变革

每个任务包含:
- `task_id`: 唯一标识
- `task_type`: 任务类型
- `complexity_score`: 复杂度评分 (1-10)
- `description`: 任务描述
- `success_criteria`: 成功标准 (可客观判定)
- `max_turns`: 最大对话轮数
- `time_limit`: 时间限制

---

## 胜负指标

### 核心指标 (必须赢)

| 指标 | 计算方式 | 胜负标准 | 权重 |
|------|----------|----------|------|
| `success_rate` | 成功任务数 / 总任务数 | B > A 且 B > C | 40% |
| `rework_count` | 平均每任务返工次数 | B < A 且 B < C | 25% |
| `new_bug_rate` | 引入新问题数 / 总问题数 | B < A 且 B < C | 20% |

### 辅助指标 (参考)

| 指标 | 计算方式 | 参考标准 |
|------|----------|----------|
| `first_attempt_success` | 一次成功 / 总任务 | B >= A |
| `total_token_cost` | 生命周期总 token | B <= 2x A |
| `time_to_solution` | 平均解决时间 | B <= 1.5x A |

### Gate 3 通过公式

```
Gate 3 PASSED = 
    (success_rate_B > success_rate_A) AND
    (rework_count_B < rework_count_A) AND
    (new_bug_rate_B < new_bug_rate_A) AND
    (total_token_cost_B <= 2x total_token_cost_A)
```

---

## 日志结构

每任务记录:

```json
{
  "task_id": "strategic_001",
  "group": "structured_19_agent",
  "result": {
    "success": true,
    "success_score": 0.85,
    "rework_count": 2,
    "new_bugs_introduced": 1
  },
  "process": {
    "total_turns": 15,
    "total_tokens": 15000,
    "time_seconds": 120,
    "rounds_breakdown": [
      {"round": 1, "speeches": 5, "tokens": 3000},
      {"round": 2, "speeches": 5, "tokens": 3500},
      ...
    ]
  },
  "audit": {
    "distinguishability_score": 0.9,
    "coverage_gain": 0.45,
    "overlap_reduction": -0.32
  }
}
```

---

## 执行流程

### Phase 1: 任务准备 (1-2 天)
- [ ] 编写 50 个任务定义
- [ ] 定义 success_criteria (可客观判定)
- [ ] 设计评分 rubric
- [ ] 准备测试环境

### Phase 2: 单任务 pilot (1 天)
- [ ] 每组各跑 3 个 pilot 任务
- [ ] 验证日志结构完整性
- [ ] 调整 token 限制和超时

### Phase 3: 全量实验 (3-5 天)
- [ ] 每组各跑 50 任务
- [ ] 记录完整日志
- [ ] 实时监控资源消耗

### Phase 4: 结果分析 (1 天)
- [ ] 计算所有指标
- [ ] 生成对比报告
- [ ] Gate 3 裁决

---

## 风险与缓解

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| 任务定义模糊 | 评分主观 | 明确 success_criteria，双人盲评 |
| token 成本失控 | 预算超支 | 设置硬性上限，超限标记失败 |
| 时间过长 | 进度延迟 | 单任务超时 10 分钟，强制结束 |
| 结果不稳定 | 难以复现 | 每个任务跑 3 次取平均 |

---

## 后续决策

### Gate 3 PASSED
- 正式切换 Persona System v2 为默认路径
- 进入生产部署准备
- 持续监控真实任务指标

### Gate 3 FAILED
- 分析失败原因 (哪类任务/哪组指标)
- 针对性调优或架构重审
- 可能回退到 Shadow 模式继续观察

---

## 附录: 任务示例

### strategic_001: 新兴市场进入策略

**描述**:
公司 A 是成熟的 SaaS 企业，现考虑进入东南亚新兴市场。市场特点:
- 本地化需求高
- 支付方式分散
- 竞争激烈但分散
- 监管环境复杂

请制定 6 个月进入策略，包括:
1. 目标国家优先级
2. 产品本地化重点
3. GTM 策略
4. 风险评估

**成功标准**:
- 明确优先级排序 (有据可依)
- 本地化方案具体可执行
- 风险识别全面且有应对
- 6 个月里程碑清晰

**复杂度**: 7/10

---

*本规范作为 Gate 3 执行基准，实验开始前需团队确认。*
