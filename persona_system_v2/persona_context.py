"""
persona_context.py
核心数据结构 - PersonaContext / Audit

定义 Persona System v2 的核心数据模型
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any, Set
from enum import Enum
import hashlib
import json
from datetime import datetime


class Stance(str, Enum):
    """发言立场"""
    SUPPORT = "support"
    OPPOSE = "oppose"
    NEUTRAL = "neutral"
    QUESTION = "question"
    PROPOSE = "propose"


class PersonaRole(str, Enum):
    """人格角色类型"""
    CORE = "core"           # 核心席位
    EXTENDED = "extended"   # 扩展人格
    GUEST = "guest"         # 特邀嘉宾


@dataclass
class RegistryEntry:
    """席位注册条目"""
    seat_id: str                    # 席位编号 (如 00001)
    name: str                       # 人格名称
    archetype: str                  # 原型 (如 strategist, diplomat)
    expertise_domains: List[str]    # 专长领域
    thinking_style: str             # 思维模式
    cultural_lineage: str           # 文化脉络
    version: str = "1.0.0"          # 版本
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class CultureContext:
    """文化脉络上下文"""
    lineage: str                    # 文化谱系 (如 纵横家, 儒家)
    core_texts: List[str]           # 核心典籍
    historical_period: str          # 历史时期
    key_concepts: List[str]         # 关键概念
    
    def hash(self) -> str:
        """生成内容哈希用于审计"""
        content = json.dumps(self.to_dict(), sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class AuditTrail:
    """审计追踪 - 每个发言的可验证元数据"""
    
    # 基础验证
    verified: bool = False
    verification_timestamp: str = ""
    
    # Registry 使用情况
    registry_keys_used: List[str] = field(default_factory=list)
    registry_version: str = ""
    
    # 生成溯源
    template_divergence_score: float = 0.0  # 0.0-1.0, 越高越偏离模板
    grounding_source_hash: str = ""         #  grounding 数据来源哈希
    
    # 文化脉络验证
    culture_context_hash: str = ""          # CultureContext 哈希
    culture_match_score: float = 0.0        # 文化匹配度
    
    # 处理元数据
    generation_pipeline: str = ""           # 使用的管道版本
    cache_hit: bool = False                 # 是否命中缓存
    processing_time_ms: float = 0.0
    
    def to_dict(self) -> Dict:
        return {
            "verified": self.verified,
            "verification_timestamp": self.verification_timestamp,
            "registry_keys_used": self.registry_keys_used,
            "registry_version": self.registry_version,
            "template_divergence_score": self.template_divergence_score,
            "grounding_source_hash": self.grounding_source_hash,
            "culture_context_hash": self.culture_context_hash,
            "culture_match_score": self.culture_match_score,
            "generation_pipeline": self.generation_pipeline,
            "cache_hit": self.cache_hit,
            "processing_time_ms": self.processing_time_ms,
        }


@dataclass
class SpeechTurn:
    """
    发言回合 - 向后兼容原结构
    新增 audit/verified 字段，但原有字段保持不变
    """
    
    # 原有字段 (向后兼容)
    name: str                       # 发言者名称
    stance: str                     # 立场 (support/oppose/neutral/question/propose)
    round_num: int                  # 轮次
    content: str                    # 发言内容
    
    # 扩展字段 (可选，向后兼容)
    seat_id: Optional[str] = None   # 席位编号
    persona_id: Optional[str] = None  # 人格标识
    
    # 审计字段 (新增)
    audit: AuditTrail = field(default_factory=AuditTrail)
    verified: bool = False          # 是否通过验证
    
    # 元数据
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict:
        """转换为字典，保持向后兼容"""
        result = {
            "name": self.name,
            "stance": self.stance,
            "round_num": self.round_num,
            "content": self.content,
        }
        
        # 可选字段
        if self.seat_id:
            result["seat_id"] = self.seat_id
        if self.persona_id:
            result["persona_id"] = self.persona_id
            
        # 审计字段 (新系统可用，旧系统忽略)
        result["audit"] = self.audit.to_dict()
        result["verified"] = self.verified
        result["metadata"] = self.metadata
        result["created_at"] = self.created_at
        
        return result
    
    @classmethod
    def from_legacy(cls, legacy_data: Dict) -> "SpeechTurn":
        """从旧格式创建 (向后兼容)"""
        return cls(
            name=legacy_data.get("name", "Unknown"),
            stance=legacy_data.get("stance", "neutral"),
            round_num=legacy_data.get("round_num", 0),
            content=legacy_data.get("content", ""),
            seat_id=legacy_data.get("seat_id"),
            persona_id=legacy_data.get("persona_id"),
        )


@dataclass
class PersonaContext:
    """
    人格上下文 - 生成发言的完整上下文
    """
    
    # 基础身份
    seat_id: str
    name: str
    role: PersonaRole
    
    # 能力画像
    archetypes: List[str]             # 原型标签
    expertise_domains: List[str]      # 专长领域
    thinking_style: str               # 思维模式
    
    # 文化脉络
    culture: CultureContext
    
    # Registry 引用
    registry_entry: Optional[RegistryEntry] = None
    
    # 运行时上下文
    meeting_history: List[Dict] = field(default_factory=list)
    current_issue: Optional[Dict] = None
    
    def hash(self) -> str:
        """生成上下文哈希用于审计"""
        content = {
            "seat_id": self.seat_id,
            "name": self.name,
            "archetypes": sorted(self.archetypes),
            "expertise": sorted(self.expertise_domains),
            "culture_hash": self.culture.hash(),
        }
        return hashlib.sha256(
            json.dumps(content, sort_keys=True).encode()
        ).hexdigest()[:16]
    
    def to_dict(self) -> Dict:
        return {
            "seat_id": self.seat_id,
            "name": self.name,
            "role": self.role.value,
            "archetypes": self.archetypes,
            "expertise_domains": self.expertise_domains,
            "thinking_style": self.thinking_style,
            "culture": self.culture.to_dict(),
            "context_hash": self.hash(),
        }


class ExtendedPersonaActivation:
    """
    扩展人格激活 - 兼容旧系统接口
    """
    
    def __init__(
        self,
        persona_id: str,
        name: str,
        archetypes: List[str],
        expertise: List[str],
        domains: List[str],
        seat_id: Optional[str] = None
    ):
        self.persona_id = persona_id
        self.name = name
        self.archetypes = archetypes
        self.expertise = expertise
        self.domains = domains
        self.seat_id = seat_id or persona_id
        
    def to_context(self, culture: Optional[CultureContext] = None) -> PersonaContext:
        """转换为完整上下文"""
        if culture is None:
            # 默认文化脉络
            culture = CultureContext(
                lineage="default",
                core_texts=[],
                historical_period="contemporary",
                key_concepts=[]
            )
            
        return PersonaContext(
            seat_id=self.seat_id,
            name=self.name,
            role=PersonaRole.EXTENDED,
            archetypes=self.archetypes,
            expertise_domains=self.expertise,
            thinking_style="analytical",
            culture=culture
        )


# 异常定义
class MissingRegistryError(Exception):
    """缺少 Registry 条目异常"""
    pass


class AuditVerificationError(Exception):
    """审计验证失败异常"""
    pass


class CultureMismatchError(Exception):
    """文化脉络不匹配异常"""
    pass
