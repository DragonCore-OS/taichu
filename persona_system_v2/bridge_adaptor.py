"""
bridge_adaptor.py
兼容包装层 - Bridge Adaptor

关键适配点：
- 调用签名: generate_speech() -> generate_speech_v2_compat()
- 返回对象: SpeechTurn (向后兼容，新增 audit/verified 字段)
- 硬约束: 无 registry -> 抛异常, audit 失败 -> 不入 transcript
"""

import os
import json
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime

# 导入 v2 核心组件
from persona_context import (
    PersonaContext, SpeechTurn, AuditTrail, CultureContext,
    ExtendedPersonaActivation, MissingRegistryError, AuditVerificationError,
    PersonaRole
)
from pipeline_implementation import (
    GenerationPipeline, RegistryLoader, CultureRegistry
)


class BridgeAdaptor:
    """
    Bridge Adaptor - 兼容包装层
    
    职责：
    1. 适配现有调用签名到 v2 管道
    2. 强制 Registry 验证 (硬约束)
    3. 向后兼容 SpeechTurn 结构
    """
    
    def __init__(
        self,
        seat_registry_path: Optional[str] = None,
        culture_registry_path: Optional[str] = None,
        strict_mode: bool = True
    ):
        """
        Args:
            seat_registry_path: 席位注册表路径
            culture_registry_path: 文化脉络注册表路径
            strict_mode: 严格模式 (True = 硬约束)
        """
        self.strict_mode = strict_mode
        
        # 设置默认路径
        base_dir = os.path.dirname(os.path.abspath(__file__))
        
        self.seat_registry_path = seat_registry_path or \
            os.path.join(base_dir, "data", "seat_registry.json")
        self.culture_registry_path = culture_registry_path or \
            os.path.join(base_dir, "data", "culture_registry.json")
        
        # 初始化管道
        self._ensure_registries_exist()
        self.pipeline = GenerationPipeline(
            registry_path=self.seat_registry_path,
            culture_path=self.culture_registry_path
        )
        
        # 统计
        self.generation_count = 0
        self.verification_failure_count = 0
    
    def _ensure_registries_exist(self):
        """确保 registry 文件存在 (如果不存在则创建默认)"""
        os.makedirs(os.path.dirname(self.seat_registry_path), exist_ok=True)
        
        # 创建默认席位注册表
        if not os.path.exists(self.seat_registry_path):
            default_seats = self._generate_default_seats()
            with open(self.seat_registry_path, 'w', encoding='utf-8') as f:
                json.dump({"seats": default_seats}, f, indent=2, ensure_ascii=False)
        
        # 创建默认文化注册表
        if not os.path.exists(self.culture_registry_path):
            default_cultures = self._generate_default_cultures()
            with open(self.culture_registry_path, 'w', encoding='utf-8') as f:
                json.dump({"cultures": default_cultures}, f, indent=2, ensure_ascii=False)
    
    def _generate_default_seats(self) -> List[Dict]:
        """生成默认核心 19 席注册信息"""
        seats = []
        
        # 核心 19 席定义
        core_seats = [
            ("00001", "鬼谷子", "strategist", ["strategy", "persuasion"], "analytical"),
            ("00002", "苏秦", "diplomat", ["alliance", "negotiation"], "collaborative"),
            ("00003", "张仪", "strategist", ["strategy", "deception"], "analytical"),
            ("00004", "孔子", "sage", ["ethics", "governance"], "principled"),
            ("00005", "孟子", "sage", ["ethics", "humanity"], "principled"),
            ("00006", "老子", "sage", ["philosophy", "nature"], "intuitive"),
            ("00007", "庄子", "philosopher", ["philosophy", "freedom"], "intuitive"),
            ("00008", "韩非", "legalist", ["law", "governance"], "analytical"),
            ("00009", "商鞅", "legalist", ["law", "reform"], "analytical"),
            ("00010", "孙子", "strategist", ["warfare", "strategy"], "analytical"),
            ("00011", "吴起", "strategist", ["warfare", "reform"], "pragmatic"),
            ("00012", "管仲", "statesman", ["economics", "governance"], "pragmatic"),
            ("00013", "范蠡", "strategist", ["economics", "strategy"], "pragmatic"),
            ("00014", "吕不韦", "merchant", ["politics", "commerce"], "opportunistic"),
            ("00015", "李斯", "statesman", ["law", "administration"], "pragmatic"),
            ("00016", "张良", "strategist", ["strategy", "counsel"], "analytical"),
            ("00017", "萧何", "administrator", ["administration", "logistics"], "pragmatic"),
            ("00018", "韩信", "commander", ["warfare", "tactics"], "bold"),
            ("00019", "陈平", "strategist", ["intelligence", "deception"], "cunning"),
        ]
        
        for seat_id, name, archetype, domains, style in core_seats:
            seats.append({
                "seat_id": seat_id,
                "name": name,
                "archetype": archetype,
                "expertise_domains": domains,
                "thinking_style": style,
                "cultural_lineage": self._infer_lineage(name),
                "version": "1.0.0",
                "created_at": datetime.now().isoformat()
            })
        
        return seats
    
    def _generate_default_cultures(self) -> Dict[str, Dict]:
        """生成默认文化脉络定义"""
        return {
            "zongheng": {
                "lineage": "纵横家",
                "core_texts": ["鬼谷子", "战国策"],
                "historical_period": "战国时期",
                "key_concepts": ["合纵", "连横", "权谋", "游说", "利害"]
            },
            "ru": {
                "lineage": "儒家",
                "core_texts": ["论语", "孟子", "大学", "中庸"],
                "historical_period": "春秋战国时期",
                "key_concepts": ["仁", "义", "礼", "智", "信", "修身", "治国"]
            },
            "dao": {
                "lineage": "道家",
                "core_texts": ["道德经", "庄子"],
                "historical_period": "春秋战国时期",
                "key_concepts": ["道", "德", "无为", "自然", "虚实"]
            },
            "fa": {
                "lineage": "法家",
                "core_texts": ["韩非子", "商君书"],
                "historical_period": "战国时期",
                "key_concepts": ["法", "术", "势", "刑名", "赏罚"]
            },
            "bing": {
                "lineage": "兵家",
                "core_texts": ["孙子兵法", "吴子", "六韬"],
                "historical_period": "春秋战国时期",
                "key_concepts": ["兵者", "诡道", "攻守", "虚实", "奇正"]
            }
        }
    
    def _infer_lineage(self, name: str) -> str:
        """从名称推断文化谱系"""
        mapping = {
            "鬼谷子": "zongheng", "苏秦": "zongheng", "张仪": "zongheng",
            "孔子": "ru", "孟子": "ru",
            "老子": "dao", "庄子": "dao",
            "韩非": "fa", "商鞅": "fa",
            "孙子": "bing", "吴起": "bing",
        }
        return mapping.get(name, "default")
    
    def validate_core_seats(self, core_seat_ids: List[str]) -> List[str]:
        """
        验证核心席位是否都在 Registry 中
        
        Returns:
            缺失的席位 ID 列表 (空列表 = 全部存在)
        """
        missing = []
        for seat_id in core_seat_ids:
            if not self.pipeline.registry.has_entry(seat_id):
                missing.append(seat_id)
        return missing
    
    def generate_core_seat_speech(
        self,
        seat_id: str,
        round_num: int,
        issue_title: str,
        issue_type: str
    ) -> SpeechTurn:
        """
        生成核心席位发言 (强制 Registry)
        
        这是核心席位的专用入口，必须保证 Registry 存在
        """
        entry = self.pipeline.registry.get_entry(seat_id)
        if not entry:
            raise MissingRegistryError(
                f"Core seat {seat_id} missing from registry. "
                "Meeting cannot start without core seats."
            )
        
        # 构建完整上下文
        culture = self.pipeline.cultures.get_culture(
            self._infer_lineage(entry.name)
        ) or CultureContext(
            lineage=entry.cultural_lineage,
            core_texts=[],
            historical_period="战国时期",
            key_concepts=[]
        )
        
        context = PersonaContext(
            seat_id=seat_id,
            name=entry.name,
            role=PersonaRole.CORE,
            archetypes=[entry.archetype],
            expertise_domains=entry.expertise_domains,
            thinking_style=entry.thinking_style,
            culture=culture,
            registry_entry=entry
        )
        
        return self._generate_with_audit(context, round_num, issue_title, issue_type)
    
    def generate_speech_v2_compat(
        self,
        persona: ExtendedPersonaActivation,
        round_num: int,
        issue_title: str,
        issue_type: str
    ) -> SpeechTurn:
        """
        v2 兼容生成入口 - 匹配现有调用签名
        
        Args:
            persona: ExtendedPersonaActivation 对象
            round_num: 轮次
            issue_title: 议题标题
            issue_type: 议题类型
        
        Returns:
            SpeechTurn (向后兼容，包含 audit/verified)
        """
        # 转换为完整上下文
        context = persona.to_context()
        
        # 尝试匹配文化脉络
        culture = self.pipeline.cultures.match_culture(persona.name)
        if culture:
            context.culture = culture
        
        return self._generate_with_audit(context, round_num, issue_title, issue_type)
    
    def _generate_with_audit(
        self,
        context: PersonaContext,
        round_num: int,
        issue_title: str,
        issue_type: str
    ) -> SpeechTurn:
        """
        带审计的生成
        
        硬约束：
        1. 无 Registry -> 抛 MissingRegistryError
        2. audit 验证失败 -> 返回 unverified SpeechTurn (不入 transcript)
        """
        self.generation_count += 1
        
        try:
            # 执行完整管道
            speech, audit = self.pipeline.generate(
                context, round_num, issue_title, issue_type
            )
            
            # 硬约束：验证 audit
            if self.strict_mode and not speech.verified:
                self.verification_failure_count += 1
                # 仍然返回，但标记为未验证
                # 调用方负责决定是否入 transcript
            
            return speech
            
        except MissingRegistryError as e:
            if self.strict_mode:
                raise  # 硬约束：重新抛出
            else:
                # 非严格模式：生成一个占位发言
                return self._generate_placeholder(context, round_num, issue_title)
    
    def _generate_placeholder(
        self,
        context: PersonaContext,
        round_num: int,
        issue_title: str
    ) -> SpeechTurn:
        """生成占位发言 (非严格模式 fallback)"""
        return SpeechTurn(
            name=context.name,
            stance="neutral",
            round_num=round_num,
            content=f"[{context.name}] 正在准备发言... (Registry 缺失)",
            seat_id=context.seat_id,
            verified=False,
            audit=AuditTrail(
                verified=False,
                template_divergence_score=0.0,
                generation_pipeline="fallback_placeholder"
            )
        )
    
    def get_stats(self) -> Dict[str, Any]:
        """获取生成统计"""
        return {
            "generation_count": self.generation_count,
            "verification_failures": self.verification_failure_count,
            "failure_rate": (
                self.verification_failure_count / max(1, self.generation_count)
            ),
            "strict_mode": self.strict_mode,
            "registry_path": self.seat_registry_path,
        }


# 全局适配器实例 (单例模式)
_adaptor_instance: Optional[BridgeAdaptor] = None


def get_adaptor(
    seat_registry_path: Optional[str] = None,
    culture_registry_path: Optional[str] = None,
    strict_mode: bool = True
) -> BridgeAdaptor:
    """
    获取全局 BridgeAdaptor 实例
    
    用法：
        adaptor = get_adaptor(strict_mode=True)
        speech = adaptor.generate_speech_v2_compat(persona, round_num, title, issue_type)
    """
    global _adaptor_instance
    if _adaptor_instance is None:
        _adaptor_instance = BridgeAdaptor(
            seat_registry_path=seat_registry_path,
            culture_registry_path=culture_registry_path,
            strict_mode=strict_mode
        )
    return _adaptor_instance


def reset_adaptor():
    """重置全局实例 (用于测试)"""
    global _adaptor_instance
    _adaptor_instance = None


# 向后兼容别名
def generate_speech_v2_compat(
    persona: ExtendedPersonaActivation,
    round_num: int,
    issue_title: str,
    issue_type: str,
    seat_registry_path: Optional[str] = None,
    strict_mode: bool = True
) -> SpeechTurn:
    """
    函数式接口 - 快速调用
    
    用法：
        speech = generate_speech_v2_compat(persona, 1, "议题", "strategic")
    """
    adaptor = get_adaptor(seat_registry_path=seat_registry_path, strict_mode=strict_mode)
    return adaptor.generate_speech_v2_compat(persona, round_num, issue_title, issue_type)
