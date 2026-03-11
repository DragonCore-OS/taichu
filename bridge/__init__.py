"""
bridge module
桥接模块 - 连接 Persona System v2 与现有系统
"""

from .persona_activation import (
    PersonaActivator,
    ExtendedPersonaActivation,
    create_activator
)

__all__ = [
    "PersonaActivator",
    "ExtendedPersonaActivation", 
    "create_activator",
]
