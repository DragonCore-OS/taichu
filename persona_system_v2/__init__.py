"""
Persona System v2

用更多前期 token，换更高的复杂任务成功率。

核心模块:
- bridge_adaptor: 兼容包装层
- persona_context: 核心数据结构  
- pipeline_implementation: Grounding + Synthesis 管道
- experiment_3x3: 3×3 验证实验

验证门槛:
- Distinguishability >= 80%
- Unresolved Coverage +30%
- Boilerplate Overlap -40%
"""

__version__ = "2.0.0"

from .bridge_adaptor import BridgeAdaptor, get_adaptor, generate_speech_v2_compat
from .persona_context import (
    PersonaContext, SpeechTurn, AuditTrail, CultureContext,
    ExtendedPersonaActivation, MissingRegistryError
)

__all__ = [
    "BridgeAdaptor",
    "get_adaptor",
    "generate_speech_v2_compat",
    "PersonaContext",
    "SpeechTurn",
    "AuditTrail",
    "CultureContext",
    "ExtendedPersonaActivation",
    "MissingRegistryError",
]
