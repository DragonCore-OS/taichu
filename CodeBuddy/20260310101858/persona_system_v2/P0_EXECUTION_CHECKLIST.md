# P0 执行清单 - Persona v2 接入与验收
# P0 Execution Checklist

**目标**: 把 Persona v2 真接进主路径，用前期 token 买复杂任务成功率  
**不接受**: 空耗 token 买热闹

---

## 执行顺序 (不可跳跃)

### Phase 0: 接入 (1-2 天)

#### P0.1 替换扩展人格路径

**文件**: `bridge/persona_activation.py`

**修改点 1**: 导入 adaptor
```python
# 文件顶部新增
from bridge.bridge_adaptor import BridgeAdaptor, init_adaptor
```

**修改点 2**: 初始化 adaptor
```python
def __init__(self, config: Dict):
    # ... 原有代码 ...
    
    # 新增: 初始化 v2 adaptor
    self.bridge_adaptor = init_adaptor(
        seat_registry_path=config.get("seat_registry", "config/seat_registry.yaml"),
        culture_registry_path=config.get("culture_registry", "config/culture_registry.yaml"),
        strict_mode=True  # 硬约束
    )
```

**修改点 3**: 替换 generate_speech 方法
```python
def generate_speech(self, persona: ExtendedPersonaActivation, 
                   round_num: int, title: str, issue_type: str) -> SpeechTurn:
    """
    替换模板化生成 -> v2 registry-grounded
    保留方法签名，下游无需修改
    """
    return self.bridge_adaptor.generate_speech_v2_compat(
        persona=persona,
        round_num=round_num,
        issue_title=title,
        issue_type=issue_type
    )
```

**验证命令**:
```bash
python -c "from bridge.persona_activation import PersonaActivator; pa = PersonaActivator({}); print('Import OK')"
```

---

#### P0.2 核心 19 席强制检查 (硬门槛)

**文件**: `bridge/persona_activation.py` 或 `MeetingController`

**修改点**: Meeting 启动时强制验证
```python
def start_meeting(self):
    # 新增: 强制检查核心席位
    core_seats = [f"{i:05d}" for i in range(1, 20)]
    missing = self.bridge_adaptor.validate_core_seats(core_seats)
    
    if missing:
        raise RuntimeError(
            f"❌ CRITICAL: {len(missing)} core seats missing registry: {missing}\n"
            f"Meeting CANNOT start. Add registry entries first."
        )
    
    print(f"✅ All 19 core seats validated. Proceeding with meeting.")
    # ... 继续原有逻辑 ...
```

**硬约束行为**:
| 条件 | 结果 |
|------|------|
| 核心席位无 registry | **抛异常，会议无法启动** |
| audit 验证失败 | **发言不入 transcript** |

---

#### P0.3 Audit 挂进 Transcript

**文件**: `bridge/persona_activation.py` 的 `run_meeting()` 或 transcript 生成处

**修改点**: 保存 audit 字段
```python
# 在生成 speech 后
speech = self.generate_speech(persona, round_num, title, issue_type)

# 新增: audit 摘要入 transcript
speech_record = {
    "persona_id": speech.persona_id,
    "name": speech.name,
    "round_num": speech.round_num,
    "content": speech.content,
    "stance": speech.stance,
    # 新增 audit 字段
    "audit_verified": speech.verified,
    "audit_hash": speech.audit.get("context_hash") if speech.audit else None,
    "audit_divergence": speech.audit.get("template_divergence_score") if speech.audit else 0.0,
    "audit_keys_used": len(speech.audit.get("registry_keys_used", [])) if speech.audit else 0
}
```

**验证**: transcript JSON 中能看到 audit 字段

---

### Phase 1: 前导指标验证 (1 天)

#### Gate 1: 接入正确性验证

**测试命令**:
```bash
# 1. 单条发言 smoke test
python -c "
from bridge.bridge_adaptor import BridgeAdaptor
adaptor = BridgeAdaptor(strict_mode=False)
from bridge.bridge_adaptor import ExtendedPersonaActivation
p = ExtendedPersonaActivation('EXT-001', '鬼谷子', ['strategic'], ['high'], ['all'])
try:
    speech = adaptor.generate_speech_v2_compat(p, 1, '测试议题', 'strategic')
    print(f'✅ Speech generated: {len(speech.content)} chars')
    print(f'✅ Audit fields: verified={speech.verified}')
except Exception as e:
    print(f'⚠️  Expected (no registry): {e}')
"
```

**验收标准**:
- [ ] 扩展人格发言生成不崩
- [ ] SpeechTurn.name / stance / round_num 正常
- [ ] audit 字段存在

---

**测试命令**:
```bash
# 2. 完整会议 case (使用现有测试)
python -m pytest tests/test_persona_activation.py -v
# 或
python bridge/persona_activation.py  # 如果有 __main__
```

**验收标准**:
- [ ] 现有会议 case 通过
- [ ] stage summary 正常生成
- [ ] artifacts 正常保存
- [ ] transcript 包含 audit 字段

---

#### Gate 2: 三项前导指标

**运行测试**:
```bash
# 运行 3×3 实验
python persona_system_v2/experiment_3x3.py
```

**硬门槛**:
| 指标 | Baseline | Target | 状态 |
|------|----------|--------|------|
| Role Distinguishability | ~50% | **≥ 80%** | ⬜ |
| Unresolved Coverage | ~10% | **+30% (≥ 40%)** | ⬜ |
| Boilerplate Overlap | ~70% | **-40% (≤ 30%)** | ⬜ |

**判定**:
- ✅ 全部达标 → 进入 Gate 3
- ❌ 任一不达标 → **停止推广，回滚到优化阶段**

---

### Phase 2: 任务级 Benchmark (3-5 天)

#### Gate 3: 复杂任务成功率

**测试设计**:

| 对照组 | 说明 |
|--------|------|
| **Baseline A** | 单强 agent (Claude/GPT-4) |
| **Baseline B** | 无结构 multi-agent (19个相同模型自由讨论) |
| **Variant** | 19-agent structured system (Persona v2) |

**任务集** (至少4类):
1. **多约束规划**: 资源分配、并发规划
2. **跨角色诊断**: 性能瓶颈 + 风险评估 + 资源调整
3. **多阶段交付**: 需求澄清 → 方案 → 风险 → 决议 → 执行计划
4. **冲突恢复**: 中途插入 veto/错误约束，测收敛能力

**5个硬指标**:
```python
{
    "task_success_rate": 0.0,        # 任务最终成功率 (目标: > Baseline A)
    "first_pass_success_rate": 0.0,  # 一次完成率 (目标: > Baseline A)
    "rework_count": 0,               # 返工次数 (目标: < Baseline A)
    "new_bug_introduction_rate": 0.0,# 新 bug 引入率 (目标: < Baseline A)
    "lifecycle_token_cost": 0        # 生命周期总 token (目标: 可接受范围内)
}
```

**判定**:
- ✅ 成功率显著优于 Baseline A/B → **产品级推广**
- ⚠️ 仅优于 B 但不优于 A → **优化后重测**
- ❌ 不优于任一 Baseline → **架构回滚，重新设计**

---

## 失败回滚条件

### 立即回滚 (P0 阶段)

| 条件 | 动作 |
|------|------|
| 现有会议 case 崩溃 | 回滚到原 `generate_speech()` |
| stage summary / artifacts 断裂 | 检查 SpeechTurn 兼容性 |
| 核心席位无法启动 | 检查 registry 路径和格式 |

**回滚命令**:
```python
# 在 persona_activation.py 中切换
USE_V2 = False  # 改回 True 重新测试

def generate_speech(self, ...):
    if USE_V2:
        return self.bridge_adaptor.generate_speech_v2_compat(...)
    else:
        return self._legacy_generate_speech(...)  # 原模板方法
```

---

### 暂停推广 (P1 阶段)

| 条件 | 动作 |
|------|------|
| Distinguishability < 80% | 优化 grounding/synthesis，重测 |
| Coverage 未提升 30% | 检查 unresolved_points 传递 |
| Boilerplate > 30% | 强化约束，接入真实 LLM |

---

### 架构重审 (P2 阶段)

| 条件 | 动作 |
|------|------|
| 成功率不优于单 agent | 重新审视 19-agent 必要性 |
| 返工次数未减少 | 检查 conflict resolution 机制 |
| 生命周期成本失控 | 优化缓存和减少无效发言 |

---

## 关键决策点

```
Week 1
├── Day 1-2: P0 接入
│   ├── P0.1 扩展人格路径 ✅
│   ├── P0.2 核心席位强制检查 ✅
│   └── P0.3 Audit 挂进 transcript ✅
│
├── Day 3: Gate 1 验证
│   ├── 单条 smoke test ✅
│   ├── 完整会议 case ✅
│   └── 下游兼容检查 ✅
│
└── Day 4-5: Gate 2 验证
    ├── 运行 3×3 实验
    ├── 检查三项指标
    └── 判定: 通过/优化/回滚

Week 2-3
└── Gate 3 验证 (如 Gate 2 通过)
    ├── 构建任务级 benchmark
    ├── 三组对照测试
    ├── 收集 5 个硬指标
    └── 判定: 产品级推广/优化/重审
```

---

## 一句话收口

> **前期 token 贵可以接受，空耗 token 不可以。**
> 
> **前导 deliberation 指标必须提升，最终复杂任务成功率必须赢。**

---

## 附件: 快速验证脚本

```bash
#!/bin/bash
# run_validation.sh

echo "=== Gate 1: Integration Check ==="
python -c "from bridge.persona_activation import PersonaActivator; print('✅ Import OK')"

echo ""
echo "=== Gate 2: Leading Indicators ==="
python persona_system_v2/experiment_3x3.py

echo ""
echo "=== Gate 3: Task Benchmark (if Gate 2 passed) ==="
# python tests/task_benchmark.py  # 待实现

echo ""
echo "Validation complete. Check results above."
```

---

**下一步动作**: 按 P0.1 → P0.2 → P0.3 顺序执行，每步验证后再进入下一步。不跳跃，不猜测，对结果说话。
