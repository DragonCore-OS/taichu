# Persona System v2

> 用更多前期 token，换更高的复杂任务成功率  
> **原则**: 前期 token 贵可以接受，空耗 token 不可以

## 快速开始

```bash
# 1. 运行 3×3 实验 (验证 Gate 2)
cd persona_system_v2
python experiment_3x3.py

# 2. 单独测试可辨识性
python test_distinguishability.py

# 3. 单独测试增量性
python test_incrementality.py
```

## 核心文件

| 文件 | 作用 |
|------|------|
| `bridge_adaptor.py` | 兼容包装层，匹配现有调用签名 |
| `persona_context.py` | 核心数据结构 |
| `pipeline_implementation.py` | Grounding + Synthesis 管道 |
| `experiment_3x3.py` | 3×3 可复现实验 |
| `test_distinguishability.py` | 可辨识性测试 |
| `test_incrementality.py` | 增量性测试 |
| `P0_EXECUTION_CHECKLIST.md` | 执行清单 |
| `INTEGRATION_GUIDE.md` | 详细集成指南 |

## 核心概念

### Grounded Generation

```
传统模板生成:
  Template -> [Personality A] thinks... -> Speech

Grounded Generation (v2):
  Registry Entry + Culture Context -> Grounding -> Synthesis -> Speech
                                    (验证支撑)   (文化风格)
```

### 审计追踪

每个发言包含 `audit` 字段:
- `verified`: 是否通过验证
- `template_divergence_score`: 偏离纯模板的程度
- `registry_keys_used`: 使用的 registry 条目
- `culture_match_score`: 文化匹配度

## 使用示例

### 基础用法

```python
from persona_system_v2.bridge_adaptor import BridgeAdaptor
from persona_system_v2.persona_context import ExtendedPersonaActivation

# 初始化适配器
adaptor = BridgeAdaptor(strict_mode=True)

# 创建人格
persona = ExtendedPersonaActivation(
    persona_id="00001",
    name="鬼谷子",
    archetypes=["strategist", "tactician"],
    expertise=["high"],
    domains=["all"]
)

# 生成发言
speech = adaptor.generate_speech_v2_compat(
    persona=persona,
    round_num=1,
    issue_title="如何应对外部威胁",
    issue_type="strategic"
)

print(f"{speech.name}: {speech.content}")
print(f"Verified: {speech.verified}")
print(f"Divergence: {speech.audit.template_divergence_score:.1%}")
```

### 批量生成

```python
personas = [
    ExtendedPersonaActivation("00001", "鬼谷子", ["strategist"], ["high"], ["all"]),
    ExtendedPersonaActivation("00004", "孔子", ["sage"], ["high"], ["ethics"]),
    ExtendedPersonaActivation("00010", "孙子", ["strategist"], ["high"], ["warfare"]),
]

for p in personas:
    speech = adaptor.generate_speech_v2_compat(p, 1, "议题", "strategic")
    print(f"{speech.name}: {speech.stance}")
```

## 接入现有系统

```python
# bridge/persona_activation.py
from persona_system_v2.bridge_adaptor import BridgeAdaptor

class PersonaActivator:
    def __init__(self, config):
        self.bridge_adaptor = BridgeAdaptor(strict_mode=True)
        
        # 核心席位强制检查
        core_seats = [f"{i:05d}" for i in range(1, 20)]
        missing = self.bridge_adaptor.validate_core_seats(core_seats)
        if missing:
            raise RuntimeError(f"Missing core seats: {missing}")
    
    def generate_speech(self, persona, round_num, title, issue_type):
        return self.bridge_adaptor.generate_speech_v2_compat(
            persona, round_num, title, issue_type
        )
```

## 验证门槛

### Gate 2 (必须过)

```
Distinguishability      >= 80%
Unresolved Coverage     +30%
Boilerplate Overlap     -40%
Overall Pass Rate       >= 80%
```

运行验证:
```bash
python experiment_3x3.py
```

### Gate 3 (任务级)

```
复杂任务成功率        > 单 agent baseline
返工次数              < 单 agent baseline
新 bug 引入率         < 单 agent baseline
总 token 成本         可控 (<= 2x)
```

## 项目结构

```
persona_system_v2/
├── bridge_adaptor.py           # 兼容包装层
├── persona_context.py          # 数据结构
├── pipeline_implementation.py  # 生成管道
├── test_distinguishability.py  # 可辨识性测试
├── test_incrementality.py      # 增量性测试
├── experiment_3x3.py           # 3×3 实验
├── P0_EXECUTION_CHECKLIST.md   # 执行清单
├── INTEGRATION_GUIDE.md        # 集成指南
├── README.md                   # 本文件
└── data/                       # 运行时生成
    ├── seat_registry.json      # 席位注册表
    └── culture_registry.json   # 文化注册表
```

## 关键保证

1. **向后兼容**: `SpeechTurn` 与原结构兼容
2. **硬约束**: 无 registry 抛异常，audit 失败不入 transcript
3. **渐进切换**: Shadow -> Gate 2 -> Gate 3 -> Promote
4. **指标驱动**: Gate 2 不过不推广，Gate 3 不过不重审

## 核心原则

> **前期 token 贵可以接受，空耗 token 不可以。**

每一轮 token 都在买三样东西：
1. 更清晰的职责分工
2. 更真实的 unresolved 推进
3. 更低的返工概率

**对结果说话** — Gate 2 不达标，停止推广；Gate 3 不达标，架构重审。

## License

AGLv3 - 华夏文明谱 (Ectrox-Lab/taichu)
