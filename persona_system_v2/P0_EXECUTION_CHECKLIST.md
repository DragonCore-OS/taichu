# P0 执行清单 - Persona System v2 接入

> 目标：用更多前期 token，换更高的复杂任务成功率  
> 原则：前期 token 贵可以接受，空耗 token 不可以  
> 硬门槛：Gate 2 不达标，停止推广；Gate 3 不达标，架构重审

---

## 执行阶段

### P0.1: 接入 bridge_adaptor.py

**文件位置**: `persona_system_v2/bridge_adaptor.py`

**修改目标**: `bridge/persona_activation.py`

```python
# 在文件顶部添加导入
from persona_system_v2.bridge_adaptor import BridgeAdaptor, get_adaptor

# 在 __init__ 中初始化
class PersonaActivator:
    def __init__(self, config: Dict):
        # ... 原有初始化 ...
        
        # 新增: 初始化 bridge adaptor
        self.bridge_adaptor = BridgeAdaptor(
            seat_registry_path=config.get("seat_registry"),
            culture_registry_path=config.get("culture_registry"),
            strict_mode=True  # 硬约束模式
        )
```

---

### P0.2: 核心席位强制检查

**修改目标**: `PersonaActivator.__init__`

```python
# P0: 验证核心席位
CORE_SEAT_IDS = [f"{i:05d}" for i in range(1, 20)]
missing = self.bridge_adaptor.validate_core_seats(CORE_SEAT_IDS)
if missing:
    raise RuntimeError(
        f"Meeting cannot start: core seats missing registry {missing}"
    )
```

**硬约束**:
- 无 registry → 抛 `MissingRegistryError`，会议无法启动
- audit 验证失败 → 不入 transcript

---

### P0.3: 替换 generate_speech 方法

**修改目标**: `PersonaActivator.generate_speech`

```python
def generate_speech(self, persona: ExtendedPersonaActivation, 
                   round_num: int, title: str, issue_type: str) -> SpeechTurn:
    """
    替换原有的模板化生成
    保留方法名，内部调用 v2 兼容层
    """
    return self.bridge_adaptor.generate_speech_v2_compat(
        persona=persona,
        round_num=round_num,
        issue_title=title,
        issue_type=issue_type
    )
```

---

### P0.4: Audit 挂入 Transcript

**修改目标**: Transcript 记录逻辑

```python
# 在 transcript 记录时，同时记录 audit
speech = self.generate_speech(persona, round_num, title, issue_type)

# 原有字段 (向后兼容)
transcript_entry = {
    "name": speech.name,
    "stance": speech.stance,
    "round_num": speech.round_num,
    "content": speech.content,
}

# 新增 audit 字段 (可选，向后兼容)
transcript_entry["verified"] = speech.verified
transcript_entry["audit"] = speech.audit.to_dict()

# 硬约束：unverified 发言可选择不入最终 transcript
if speech.verified or not self.strict_mode:
    transcript.append(transcript_entry)
```

---

## 验证阶段

### Gate 1: 接入正确 ✅

**测试命令**:
```bash
cd /path/to/taichu
python -c "from bridge.persona_activation import PersonaActivator; print('OK')"
```

**验收标准**:
| 检查项 | 预期结果 |
|--------|----------|
| 导入不报错 | OK |
| 初始化 core seats | 19 席全部加载 |
| generate_speech 调用 | 返回 SpeechTurn |
| 字段兼容 | .name, .stance, .round_num 可用 |
| stage summary | 正常生成 |
| artifacts | 正常生成 |

**命令**:
```bash
python persona_system_v2/test_gate1.py
```

---

### Gate 2: 前导指标过线 ✅

**测试命令**:
```bash
cd persona_system_v2
python experiment_3x3.py
```

**门槛**:
| 指标 | 门槛 | 判定 |
|------|------|------|
| Distinguishability | ≥ 80% | 必须过 |
| Coverage Gain | +30% | 必须过 |
| Overlap Reduction | -40% | 必须过 |
| Gate 2 Overall | ≥ 80% trials pass | 必须过 |

**输出示例**:
```
AGGREGATE RESULTS:
  Overall Pass Rate: 88.9% (8/9)
  Distinguishability Pass Rate: 100.0%
  Coverage Pass Rate: 88.9%
  Overlap Pass Rate: 100.0%

GATE 2 VERDICT:
  ✅ PASS - Gate 2 cleared. Proceed to Gate 3.
```

**失败处理**:
- Gate 2 FAIL → 停止推广，架构重审
- 不允许在指标不达标的情况下进入主路径

---

### Gate 3: 任务级 Benchmark ✅

**仅在 Gate 2 通过后执行**

**测试设计**:
```python
# 三组对照
experiments = {
    "single_strong_agent": SingleAgentBaseline(model="gpt-4"),
    "structured_19_agent": PersonaSystemV2(core_seats=19),
    "unstructured_multi": UnstructuredMultiAgent(n_agents=19),
}

# 高难任务集
tasks = load_complex_tasks(n=50)  # 50 个复杂任务

# 指标
metrics = {
    "success_rate": "任务最终成功率",
    "first_attempt_success": "一次完成率",
    "rework_count": "返工次数",
    "new_bug_rate": "新 bug 引入率",
    "total_token_cost": "生命周期总 token 成本",
}
```

**胜负标准**:
```
Persona System v2 胜出条件：
  - 成功率 > single_strong_agent
  - 返工次数 < single_strong_agent
  - 新 bug 率 < single_strong_agent
  - 总 token 成本可控 (不超过 2x)
```

**验收**:
- Gate 3 PASS → 正式切换为默认路径
- Gate 3 FAIL → 回 shadow，分析失败原因

---

## 文件清单

| 文件 | 作用 | 状态 |
|------|------|------|
| `bridge_adaptor.py` | 兼容包装层 | ✅ 已创建 |
| `persona_context.py` | 核心数据结构 | ✅ 已创建 |
| `pipeline_implementation.py` | Grounding + Synthesis 管道 | ✅ 已创建 |
| `test_distinguishability.py` | 可辨识性测试 | ✅ 已创建 |
| `test_incrementality.py` | 增量性测试 | ✅ 已创建 |
| `experiment_3x3.py` | 3×3 可复现实验 | ✅ 已创建 |
| `P0_EXECUTION_CHECKLIST.md` | 本执行清单 | ✅ 已创建 |
| `INTEGRATION_GUIDE.md` | 详细集成指南 | ✅ 已创建 |

---

## 立即执行序列

```bash
# Step 1: 放置文件
cp -r persona_system_v2/ /path/to/taichu/

# Step 2: 修改 bridge/persona_activation.py (按 P0.1-P0.4)

# Step 3: 验证 Gate 1
python -c "from bridge.persona_activation import PersonaActivator; print('Gate 1: OK')"

# Step 4: 运行完整会议 case
python bridge/run_meeting.py --test-case=default

# Step 5: 验证 Gate 2
cd persona_system_v2
python experiment_3x3.py

# Step 6: Gate 2 通过后，准备 Gate 3
# (任务级 benchmark，需 50 个真实复杂任务)
```

---

## 关键保证

1. **向后兼容**: SpeechTurn 对象与原结构兼容，下游无需修改
2. **硬约束**: 无 registry 抛异常，audit 失败不入 transcript
3. **渐进切换**: 先 shadow，验证后再 promote 到 default
4. **指标驱动**: Gate 2 不过不推广，Gate 3 不过不重审

---

## 核心原则

> **前期 token 贵可以接受，空耗 token 不可以。**

每一轮 token 都在买三样东西：
1. 更清晰的职责分工
2. 更真实的 unresolved 推进
3. 更低的返工概率

**对结果说话** — Gate 2 不达标，停止推广；Gate 3 不达标，架构重审。
