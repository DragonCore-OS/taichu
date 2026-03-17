"""
persona_activation.py
人格激活模块 - Persona System v2 集成版本

P0 接入点：
1. 初始化 BridgeAdaptor
2. 核心席位强制检查
3. generate_speech 调用 v2 兼容层
4. Audit 挂入 transcript
"""

import sys
import os
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

# 添加 persona_system_v2 到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

try:
    from persona_system_v2.bridge_adaptor import BridgeAdaptor, get_adaptor
    from persona_system_v2.persona_context import (
        ExtendedPersonaActivation, MissingRegistryError, SpeechTurn
    )
    PERSONA_V2_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Persona System v2 not available: {e}")
    PERSONA_V2_AVAILABLE = False
    # Fallback 定义
    from dataclasses import dataclass
    
    @dataclass
    class ExtendedPersonaActivation:
        """扩展人格激活 - 兼容旧系统 (fallback)"""
        persona_id: str
        name: str
        archetypes: List[str]
        expertise: List[str]
        domains: List[str]
        seat_id: Optional[str] = None
        
        def __post_init__(self):
            if self.seat_id is None:
                self.seat_id = self.persona_id
        
        def to_context(self, culture=None):
            """Fallback to_context"""
            from persona_system_v2.persona_context import (
                PersonaContext, CultureContext, PersonaRole
            )
            if culture is None:
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
    
    class MissingRegistryError(Exception):
        pass
    
    @dataclass
    class SpeechTurn:
        name: str
        stance: str
        round_num: int
        content: str
        seat_id: Optional[str] = None
        persona_id: Optional[str] = None
        verified: bool = False


class PersonaActivator:
    """
    人格激活器
    
    职责：
    1. 管理人格激活状态
    2. 协调发言生成
    3. 与 Persona System v2 集成
    """
    
    # 核心 19 席 ID
    CORE_SEAT_IDS = [f"{i:05d}" for i in range(1, 20)]
    
    def __init__(self, config: Optional[Dict] = None):
        """
        初始化人格激活器
        
        Args:
            config: 配置字典
                - use_persona_v2: 是否使用 v2 系统 (默认 True)
                - strict_mode: 严格模式 (默认 True)
                - seat_registry_path: 席位注册表路径
                - culture_registry_path: 文化注册表路径
        """
        config = config or {}
        
        self.use_v2 = config.get("use_persona_v2", True) and PERSONA_V2_AVAILABLE
        self.strict_mode = config.get("strict_mode", True)
        self.transcript: List[Dict] = []
        
        # 初始化 v2 适配器
        if self.use_v2:
            self._init_v2_adaptor(config)
        else:
            print("Info: Using legacy persona system")
            self.bridge_adaptor = None
    
    def _init_v2_adaptor(self, config: Dict):
        """初始化 v2 适配器"""
        print("Info: Initializing Persona System v2...")
        
        # 确定 registry 路径
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        seat_registry = config.get("seat_registry_path")
        if not seat_registry:
            seat_registry = os.path.join(
                base_dir, "persona_system_v2", "data", "seat_registry.json"
            )
        
        culture_registry = config.get("culture_registry_path")
        if not culture_registry:
            culture_registry = os.path.join(
                base_dir, "persona_system_v2", "data", "culture_registry.json"
            )
        
        # 创建适配器
        self.bridge_adaptor = BridgeAdaptor(
            seat_registry_path=seat_registry,
            culture_registry_path=culture_registry,
            strict_mode=self.strict_mode
        )
        
        # P0.2: 核心席位强制检查
        missing = self.bridge_adaptor.validate_core_seats(self.CORE_SEAT_IDS)
        if missing:
            error_msg = (
                f"Meeting cannot start: core seats missing from registry: {missing}\n"
                f"Please ensure all core seats (00001-00019) are registered."
            )
            if self.strict_mode:
                raise RuntimeError(error_msg)
            else:
                print(f"Warning: {error_msg}")
        else:
            print(f"✅ All {len(self.CORE_SEAT_IDS)} core seats validated")
        
        print("✅ Persona System v2 initialized")
    
    def generate_speech(
        self,
        persona: ExtendedPersonaActivation,
        round_num: int,
        title: str,
        issue_type: str
    ) -> SpeechTurn:
        """
        生成发言
        
        P0.3: 保留方法名，内部调用 v2 兼容层
        
        Args:
            persona: 激活的人格
            round_num: 轮次
            title: 议题标题
            issue_type: 议题类型 (strategic/diplomatic/governance)
        
        Returns:
            SpeechTurn - 向后兼容，包含 audit/verified
        """
        if self.use_v2 and self.bridge_adaptor:
            try:
                # v2 路径
                return self.bridge_adaptor.generate_speech_v2_compat(
                    persona=persona,
                    round_num=round_num,
                    issue_title=title,
                    issue_type=issue_type
                )
            except MissingRegistryError as e:
                if self.strict_mode:
                    raise
                # 非严格模式: fallback
                print(f"Warning: Registry error, using fallback: {e}")
                return self._generate_speech_fallback(persona, round_num, title, issue_type)
        else:
            # 旧路径 (legacy)
            return self._generate_speech_legacy(persona, round_num, title, issue_type)
    
    def _generate_speech_legacy(
        self,
        persona: ExtendedPersonaActivation,
        round_num: int,
        title: str,
        issue_type: str
    ) -> SpeechTurn:
        """
        旧版模板化生成 (fallback)
        
        保留作为兼容层
        """
        # 简单的模板生成
        templates = {
            "strategist": f"以{persona.name}之谋略观之，{title}需审慎布局。",
            "sage": f"{persona.name}曰：{title}关乎道义，当以德为先。",
            "default": f"{persona.name}以为，{title}值得深入探讨。",
        }
        
        archetype = persona.archetypes[0] if persona.archetypes else "default"
        content = templates.get(archetype, templates["default"])
        
        return SpeechTurn(
            name=persona.name,
            stance="neutral",
            round_num=round_num,
            content=content,
            seat_id=persona.seat_id,
            verified=False  # legacy 生成未验证
        )
    
    def _generate_speech_fallback(
        self,
        persona: ExtendedPersonaActivation,
        round_num: int,
        title: str,
        issue_type: str
    ) -> SpeechTurn:
        """v2 失败时的 fallback"""
        return self._generate_speech_legacy(persona, round_num, title, issue_type)
    
    def add_to_transcript(self, speech: SpeechTurn) -> bool:
        """
        添加发言到 transcript
        
        P0.4: 同时记录 audit 信息
        
        Args:
            speech: 发言对象
        
        Returns:
            bool: 是否成功添加
        """
        # 构建 transcript 条目
        entry = {
            # 原有字段 (向后兼容)
            "name": speech.name,
            "stance": speech.stance,
            "round_num": speech.round_num,
            "content": speech.content,
        }
        
        # 新增字段 (v2)
        if hasattr(speech, 'seat_id') and speech.seat_id:
            entry["seat_id"] = speech.seat_id
        if hasattr(speech, 'persona_id') and speech.persona_id:
            entry["persona_id"] = speech.persona_id
        
        # Audit 信息
        if hasattr(speech, 'verified'):
            entry["verified"] = speech.verified
        if hasattr(speech, 'audit'):
            entry["audit"] = speech.audit.to_dict()
        
        # 硬约束: unverified 发言可选择不入 transcript
        is_verified = getattr(speech, 'verified', True)
        
        if is_verified or not self.strict_mode:
            self.transcript.append(entry)
            return True
        else:
            print(
                f"Warning: Unverified speech from {speech.name} "
                f"(divergence: {speech.audit.template_divergence_score:.1%}) "
                f"not added to transcript"
            )
            return False
    
    def get_transcript(self) -> List[Dict]:
        """获取完整 transcript"""
        return self.transcript.copy()
    
    def get_stats(self) -> Dict[str, Any]:
        """获取生成统计"""
        if self.bridge_adaptor:
            v2_stats = self.bridge_adaptor.get_stats()
        else:
            v2_stats = {}
        
        return {
            "use_v2": self.use_v2,
            "strict_mode": self.strict_mode,
            "transcript_length": len(self.transcript),
            "verified_count": sum(
                1 for e in self.transcript if e.get("verified", False)
            ),
            "v2_stats": v2_stats,
        }


# 便捷函数
def create_activator(
    use_v2: bool = True,
    strict_mode: bool = True,
    seat_registry_path: Optional[str] = None,
    culture_registry_path: Optional[str] = None
) -> PersonaActivator:
    """
    快速创建 PersonaActivator
    
    用法:
        activator = create_activator(strict_mode=True)
        speech = activator.generate_speech(persona, 1, "议题", "strategic")
    """
    config = {
        "use_persona_v2": use_v2,
        "strict_mode": strict_mode,
    }
    if seat_registry_path:
        config["seat_registry_path"] = seat_registry_path
    if culture_registry_path:
        config["culture_registry_path"] = culture_registry_path
    
    return PersonaActivator(config)


# 测试入口
if __name__ == "__main__":
    print("=" * 60)
    print("PersonaActivator Smoke Test")
    print("=" * 60)
    
    try:
        # 创建激活器
        activator = create_activator(strict_mode=False)
        
        # 测试人格
        test_persona = ExtendedPersonaActivation(
            persona_id="00001",
            name="鬼谷子",
            archetypes=["strategist"],
            expertise=["high"],
            domains=["all"]
        )
        
        # 生成发言
        speech = activator.generate_speech(
            test_persona,
            round_num=1,
            title="如何应对外部联盟压力",
            issue_type="strategic"
        )
        
        print(f"\nGenerated Speech:")
        print(f"  Name: {speech.name}")
        print(f"  Stance: {speech.stance}")
        print(f"  Content: {speech.content[:50]}...")
        print(f"  Verified: {getattr(speech, 'verified', 'N/A')}")
        
        # 添加到 transcript
        activator.add_to_transcript(speech)
        
        # 统计
        stats = activator.get_stats()
        print(f"\nStats: {stats}")
        
        print("\n✅ Smoke test passed")
        
    except Exception as e:
        print(f"\n❌ Smoke test failed: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
