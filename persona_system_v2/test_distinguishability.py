"""
test_distinguishability.py
可辨识性测试

验证不同人格的发言是否具有足够的区分度
门槛: Distinguishability >= 80%
"""

import json
from typing import List, Dict, Tuple
from collections import defaultdict
from dataclasses import dataclass

from bridge_adaptor import BridgeAdaptor, get_adaptor
from persona_context import ExtendedPersonaActivation, SpeechTurn


@dataclass
class DistinguishabilityResult:
    """可辨识性测试结果"""
    score: float                      # 0.0-1.0
    total_comparisons: int
    correctly_identified: int
    confusion_matrix: Dict[str, Dict[str, int]]
    per_persona_scores: Dict[str, float]
    passed: bool


class DistinguishabilityTester:
    """
    可辨识性测试器
    
    测试方法：
    1. 为每个人格生成多个发言
    2. 使用简单的内容特征来"猜测"发言者
    3. 计算猜测准确率
    """
    
    def __init__(self, adaptor: BridgeAdaptor = None):
        self.adaptor = adaptor or get_adaptor(strict_mode=False)
        
    def test_personas(
        self,
        personas: List[ExtendedPersonaActivation],
        issue_title: str = "测试议题：如何应对外部威胁",
        issue_type: str = "strategic",
        rounds: int = 3
    ) -> DistinguishabilityResult:
        """
        测试一组人格的可辨识性
        
        Args:
            personas: 待测试的人格列表
            issue_title: 测试议题
            issue_type: 议题类型
            rounds: 测试轮数
        """
        all_speeches: List[Tuple[str, SpeechTurn]] = []  # (persona_id, speech)
        
        # 为每个人格生成发言
        for persona in personas:
            for round_num in range(1, rounds + 1):
                try:
                    speech = self.adaptor.generate_speech_v2_compat(
                        persona, round_num, issue_title, issue_type
                    )
                    all_speeches.append((persona.persona_id, speech))
                except Exception as e:
                    print(f"Warning: Failed to generate speech for {persona.name}: {e}")
        
        # 计算可辨识性
        return self._calculate_distinguishability(all_speeches, personas)
    
    def _calculate_distinguishability(
        self,
        speeches: List[Tuple[str, SpeechTurn]],
        personas: List[ExtendedPersonaActivation]
    ) -> DistinguishabilityResult:
        """计算可辨识性分数"""
        
        # 构建人格特征库
        persona_features = self._build_feature_library(personas)
        
        # 混淆矩阵
        confusion = defaultdict(lambda: defaultdict(int))
        correct = 0
        total = 0
        
        # 对每条发言进行"识别"
        for true_id, speech in speeches:
            predicted_id = self._identify_speaker(speech, persona_features)
            
            confusion[true_id][predicted_id] += 1
            if predicted_id == true_id:
                correct += 1
            total += 1
        
        # 计算分数
        score = correct / max(1, total)
        
        # 计算每个人格的分数
        per_persona = {}
        for persona in personas:
            pid = persona.persona_id
            persona_correct = confusion[pid].get(pid, 0)
            persona_total = sum(confusion[pid].values())
            per_persona[pid] = persona_correct / max(1, persona_total)
        
        # 门槛: 80%
        passed = score >= 0.80
        
        return DistinguishabilityResult(
            score=score,
            total_comparisons=total,
            correctly_identified=correct,
            confusion_matrix=dict(confusion),
            per_persona_scores=per_persona,
            passed=passed
        )
    
    def _build_feature_library(
        self,
        personas: List[ExtendedPersonaActivation]
    ) -> Dict[str, List[str]]:
        """构建人格特征库"""
        features = {}
        
        for p in personas:
            # 提取关键词作为特征
            keywords = []
            keywords.extend(p.archetypes)
            keywords.extend(p.expertise)
            keywords.append(p.name)
            
            # 添加文化相关特征
            cultural_keywords = {
                "鬼谷子": ["纵横", "权谋", "捭阖"],
                "苏秦": ["合纵", "六国"],
                "张仪": ["连横", "连横"],
                "孔子": ["仁", "礼", "义"],
                "孟子": ["仁政", "民本"],
                "老子": ["道", "无为", "自然"],
                "韩非": ["法", "术", "势"],
                "孙子": ["兵", "计", "谋"],
            }
            
            if p.name in cultural_keywords:
                keywords.extend(cultural_keywords[p.name])
            
            features[p.persona_id] = keywords
        
        return features
    
    def _identify_speaker(
        self,
        speech: SpeechTurn,
        persona_features: Dict[str, List[str]]
    ) -> str:
        """
        基于内容特征识别发言者
        
        简单启发式：匹配关键词最多的为人格
        """
        content = speech.content
        scores = {}
        
        for pid, features in persona_features.items():
            score = sum(1 for f in features if f in content)
            scores[pid] = score
        
        # 返回得分最高的人格
        if scores:
            return max(scores, key=scores.get)
        return list(persona_features.keys())[0] if persona_features else "unknown"
    
    def generate_report(self, result: DistinguishabilityResult) -> str:
        """生成可读报告"""
        lines = [
            "=" * 60,
            "可辨识性测试报告",
            "=" * 60,
            f"总体分数: {result.score:.1%}",
            f"测试样本: {result.total_comparisons} 条发言",
            f"正确识别: {result.correctly_identified}",
            f"通过门槛: {'✅ PASS' if result.passed else '❌ FAIL'} (门槛: 80%)",
            "",
            "各人格分数:",
        ]
        
        for pid, score in sorted(result.per_persona_scores.items()):
            status = "✅" if score >= 0.8 else "❌"
            lines.append(f"  {status} {pid}: {score:.1%}")
        
        lines.extend(["", "混淆矩阵 (部分):"])
        
        # 只显示前 5 个人格的混淆
        for true_id in list(result.confusion_matrix.keys())[:5]:
            row = result.confusion_matrix[true_id]
            row_str = ", ".join([f"{k}={v}" for k, v in list(row.items())[:3]])
            lines.append(f"  {true_id} -> {{{row_str}}}")
        
        lines.append("=" * 60)
        
        return "\n".join(lines)


def run_default_test() -> DistinguishabilityResult:
    """运行默认测试 (核心 5 席)"""
    
    # 定义测试人格 (核心 5 席)
    test_personas = [
        ExtendedPersonaActivation(
            "00001", "鬼谷子",
            ["strategist", "tactician"],
            ["high"], ["all"]
        ),
        ExtendedPersonaActivation(
            "00004", "孔子",
            ["sage", "educator"],
            ["high"], ["ethics"]
        ),
        ExtendedPersonaActivation(
            "00006", "老子",
            ["sage", "philosopher"],
            ["high"], ["philosophy"]
        ),
        ExtendedPersonaActivation(
            "00008", "韩非",
            ["legalist", "statesman"],
            ["high"], ["law"]
        ),
        ExtendedPersonaActivation(
            "00010", "孙子",
            ["strategist", "commander"],
            ["high"], ["warfare"]
        ),
    ]
    
    tester = DistinguishabilityTester()
    result = tester.test_personas(test_personas)
    
    print(tester.generate_report(result))
    
    return result


if __name__ == "__main__":
    result = run_default_test()
    exit(0 if result.passed else 1)
