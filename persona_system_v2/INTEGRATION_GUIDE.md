# Persona System v2 - 集成指南

## 概述

本文档描述如何将 Persona System v2 集成到现有 Taichu 系统中。

## 架构图

```
┌─────────────────────────────────────────────────────────────┐
│                    Existing System                          │
│  ┌─────────────────┐    ┌──────────────────────────────┐   │
│  │ PersonaActivator│    │ Transcript / Stage Summary   │   │
│  │  generate_speech│───▶│  Artifacts                   │   │
│  └────────┬────────┘    └──────────────────────────────┘   │
│           │                                                  │
│           ▼                                                  │
│  ┌────────────────────────────────────────────────────┐    │
│  │              Bridge Adaptor (v2)                    │    │
│  │  ┌──────────────┐    ┌──────────────────────────┐  │    │
│  │  │   Grounding  │───▶│       Synthesis          │  │    │
│  │  │  (Registry/  │    │   (Culture + Expertise)  │  │    │
│  │  │   Culture)   │    │                          │  │    │
│  │  └──────────────┘    └──────────────────────────┘  │    │
│  │           │                    │                   │    │
│  │           ▼                    ▼                   │    │
│  │  ┌────────────────────────────────────────────┐   │    │
│  │  │              Audit Trail                    │   │    │
│  │  │  (verified, divergence, registry_keys)     │   │    │
│  │  └────────────────────────────────────────────┘   │    │
│  └────────────────────────────────────────────────────┘    │
│           │                                                  │
│           ▼                                                  │
│  ┌────────────────────────────────────────────────────┐    │
│  │              Registry Storage                       │    │
│  │  ┌──────────────┐    ┌──────────────────────────┐  │    │
│  │  │ Seat Registry│    │    Culture Registry      │  │    │
│  │  │ (00001-00019)│    │ (zongheng/ru/dao/fa/bing)│  │    │
│  │  └──────────────┘    └──────────────────────────┘  │    │
│  └────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

## 集成步骤

### 1. 文件复制

```bash
# 复制 Persona System v2 到目标目录
cp -r persona_system_v2/ /path/to/taichu/

# 或者创建符号链接
ln -s /path/to/persona_system_v2 /path/to/taichu/persona_system_v2
```

### 2. 修改 `bridge/persona_activation.py`

#### 2.1 添加导入

```python
# 在文件顶部添加
import sys
import os

# 添加 persona_system_v2 到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from persona_system_v2.bridge_adaptor import BridgeAdaptor, get_adaptor
from persona_system_v2.persona_context import MissingRegistryError
```

#### 2.2 修改 `__init__` 方法

```python
class PersonaActivator:
    def __init__(self, config: Dict):
        # ... 原有初始化代码 ...
        
        # ===== Persona System v2 集成开始 =====
        self.use_v2 = config.get("use_persona_v2", True)
        self.strict_mode = config.get("strict_mode", True)
        
        if self.use_v2:
            self.bridge_adaptor = BridgeAdaptor(
                seat_registry_path=config.get("seat_registry_path"),
                culture_registry_path=config.get("culture_registry_path"),
                strict_mode=self.strict_mode
            )
            
            # 核心席位强制检查 (P0.2)
            self.core_seat_ids = [f"{i:05d}" for i in range(1, 20)]
            missing = self.bridge_adaptor.validate_core_seats(self.core_seat_ids)
            if missing:
                raise RuntimeError(
                    f"Meeting cannot start: core seats missing from registry: {missing}"
                )
            
            print(f"✅ Persona System v2 initialized with {len(self.core_seat_ids)} core seats")
        # ===== Persona System v2 集成结束 =====
```

#### 2.3 修改 `generate_speech` 方法

```python
def generate_speech(self, persona: ExtendedPersonaActivation,
                   round_num: int, title: str, issue_type: str) -> SpeechTurn:
    """
    生成发言
    
    Persona System v2: 使用 grounding + synthesis 管道
    向后兼容: 保持原有方法签名和返回类型
    """
    if self.use_v2 and hasattr(self, 'bridge_adaptor'):
        # v2 路径
        try:
            speech = self.bridge_adaptor.generate_speech_v2_compat(
                persona=persona,
                round_num=round_num,
                issue_title=title,
                issue_type=issue_type
            )
            return speech
        except MissingRegistryError as e:
            if self.strict_mode:
                raise
            # 非严格模式: fallback 到旧路径
            print(f"Warning: Registry missing, falling back to legacy: {e}")
            return self._generate_speech_legacy(persona, round_num, title, issue_type)
    else:
        # 旧路径
        return self._generate_speech_legacy(persona, round_num, title, issue_type)
```

#### 2.4 保留旧方法作为 fallback

```python
def _generate_speech_legacy(self, persona, round_num, title, issue_type):
    """原有的模板化生成方法"""
    # ... 原有代码 ...
    pass
```

### 3. 修改 Transcript 记录逻辑

```python
def add_to_transcript(self, speech: SpeechTurn):
    """
    添加发言到 transcript
    
    P0.3: 同时记录 audit 信息
    """
    entry = {
        # 原有字段 (向后兼容)
        "name": speech.name,
        "stance": speech.stance,
        "round_num": speech.round_num,
        "content": speech.content,
    }
    
    # 新增字段 (v2)
    if hasattr(speech, 'verified'):
        entry["verified"] = speech.verified
    if hasattr(speech, 'audit'):
        entry["audit"] = speech.audit.to_dict()
    if hasattr(speech, 'seat_id') and speech.seat_id:
        entry["seat_id"] = speech.seat_id
    
    # 硬约束: unverified 发言可选择不入 transcript
    if getattr(speech, 'verified', True) or not self.strict_mode:
        self.transcript.append(entry)
        return True
    else:
        print(f"Warning: Unverified speech from {speech.name} not added to transcript")
        return False
```

### 4. 配置文件

在系统配置中添加:

```yaml
# config.yaml
persona_system:
  use_v2: true
  strict_mode: true
  seat_registry_path: "persona_system_v2/data/seat_registry.json"
  culture_registry_path: "persona_system_v2/data/culture_registry.json"
```

## 数据结构

### SpeechTurn (向后兼容)

```python
@dataclass
class SpeechTurn:
    # 原有字段
    name: str
    stance: str
    round_num: int
    content: str
    
    # 新增字段 (可选)
    seat_id: Optional[str] = None
    persona_id: Optional[str] = None
    
    # 审计字段
    audit: AuditTrail = field(default_factory=AuditTrail)
    verified: bool = False
```

### AuditTrail

```python
@dataclass
class AuditTrail:
    verified: bool
    verification_timestamp: str
    registry_keys_used: List[str]
    template_divergence_score: float  # 0.0-1.0
    culture_context_hash: str
    culture_match_score: float
    generation_pipeline: str
```

## 测试

### 单元测试

```bash
cd persona_system_v2

# 测试可辨识性
python test_distinguishability.py

# 测试增量性
python test_incrementality.py

# 完整 3×3 实验
python experiment_3x3.py
```

### 集成测试

```bash
# 测试导入
python -c "from persona_system_v2.bridge_adaptor import BridgeAdaptor; print('OK')"

# 测试核心功能
python -c "
from persona_system_v2.bridge_adaptor import BridgeAdaptor
from persona_system_v2.persona_context import ExtendedPersonaActivation

adaptor = BridgeAdaptor(strict_mode=True)
persona = ExtendedPersonaActivation('00001', '鬼谷子', ['strategist'], ['high'], ['all'])

try:
    speech = adaptor.generate_speech_v2_compat(persona, 1, '测试议题', 'strategic')
    print(f'Success: {speech.name} - {speech.stance}')
    print(f'Verified: {speech.verified}')
    print(f'Divergence: {speech.audit.template_divergence_score:.1%}')
except Exception as e:
    print(f'Error: {e}')
"
```

## 故障排查

### 问题: MissingRegistryError

**原因**: 席位未在 registry 中注册

**解决**:
```python
# 检查 registry 内容
adaptor = BridgeAdaptor(strict_mode=False)
missing = adaptor.validate_core_seats(["00001", "00002", ...])
print(f"Missing: {missing}")
```

### 问题: 发言内容不符合文化特征

**原因**: CultureContext 未正确匹配

**解决**:
```python
# 手动指定文化脉络
from persona_system_v2.pipeline_implementation import CultureRegistry

culture = CultureRegistry("path/to/culture_registry.json")
context = persona.to_context(culture.get_culture("zongheng"))
```

### 问题: Audit verification 失败

**原因**: Grounding 阶段找不到相关 registry 条目

**解决**: 检查 registry 中的 expertise_domains 是否覆盖议题关键词

## 性能优化

### 缓存策略

```python
# 启用缓存
adaptor = BridgeAdaptor(
    seat_registry_path=...,
    cache_enabled=True,  # 缓存 registry 查询
    cache_ttl=300        # 5分钟 TTL
)
```

### 异步生成

```python
# 异步批量生成
import asyncio

async def generate_batch(personas, round_num, title, issue_type):
    tasks = [
        adaptor.generate_speech_v2_compat_async(p, round_num, title, issue_type)
        for p in personas
    ]
    return await asyncio.gather(*tasks)
```

## 监控指标

```python
# 获取生成统计
stats = adaptor.get_stats()
print(f"""
Generation Stats:
  Total: {stats['generation_count']}
  Failures: {stats['verification_failures']}
  Failure Rate: {stats['failure_rate']:.1%}
  Strict Mode: {stats['strict_mode']}
""")
```

## 升级路径

```
Phase 1: Shadow (当前)
  - 新系统并行运行
  - 只记录建议，不拦截
  - 与旧系统对比验证

Phase 2: Gate 2 验证
  - 运行 3×3 实验
  - 指标 >= 门槛
  - 失败则重调

Phase 3: Gate 3 验证
  - 任务级 benchmark
  - 对比单 agent baseline
  - 胜出则切换

Phase 4: Promote
  - 正式切换为默认路径
  - 旧路径作为 fallback
  - 持续监控
```

## 联系方式

如有问题，请参考:
- P0_EXECUTION_CHECKLIST.md - 执行清单
- experiment_3x3.py - 验证实验
- bridge_adaptor.py - 实现代码
