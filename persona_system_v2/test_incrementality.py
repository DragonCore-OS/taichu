"""
test_incrementality.py
增量性测试

验证多轮讨论是否真正推进议题解决
门槛: Unresolved Coverage +30%, Boilerplate Overlap -40%
"""

import json
import re
from typing import List, Dict, Set, Tuple
from dataclasses import dataclass, field
from collections import defaultdict

from bridge_adaptor import BridgeAdaptor, get_adaptor
from persona_context import ExtendedPersonaActivation, SpeechTurn


@dataclass
class IncrementalityResult:
    """增量性测试结果"""
    # 指标
    unresolved_coverage_gain: float   # 未解决点覆盖增益
    boilerplate_overlap_reduction: float  # 套话重叠减少
    novel_contribution_rate: float    # 新贡献率
    
    # 详细数据
    round_by_round_coverage: List[float]
    round_by_round_overlap: List[float]
    
    # 判定
    passed_coverage: bool
    passed_overlap: bool
    passed: bool


@dataclass
class MeetingSimulation:
    """会议模拟记录"""
    issue_title: str
    issue_type: str
    rounds: List[List[SpeechTurn]] = field(default_factory=list)
    
    def add_round(self, speeches: List[SpeechTurn]):
        self.rounds.append(speeches)


class IncrementalityTester:
    """
    增量性测试器
    
    测试方法：
    1. 模拟多轮会议
    2. 追踪每轮覆盖的"未解决点"
    3. 计算套话重叠度变化
    """
    
    # 议题相关的常见"未解决点"
    ISSUE_UNRESOLVED_POINTS = {
        "strategic": [
            "战略目标", "资源配置", "时机选择", "风险评估",
            "利益平衡", "执行路径", "退出机制", "长期影响"
        ],
        "diplomatic": [
            "联盟构建", "信任建立", "利益交换", "冲突调解",
            "声誉管理", "承诺可信", "信息不对称", "文化差异"
        ],
        "governance": [
            "制度设计", "执行监督", "激励相容", "权力制衡",
            "信息透明", "参与机制", "问责制度", "适应能力"
        ],
    }
    
    # 常见套话模式
    BOILERPLATE_PATTERNS = [
        r"愿诸君共议之",
        r"此事需审慎考量",
        r".*?以为.*?(关乎|在于)",
        r"以.*?之视角观之",
    ]
    
    def __init__(self, adaptor: BridgeAdaptor = None):
        self.adaptor = adaptor or get_adaptor(strict_mode=False)
    
    def simulate_meeting(
        self,
        personas: List[ExtendedPersonaActivation],
        issue_title: str,
        issue_type: str,
        num_rounds: int = 3
    ) -> MeetingSimulation:
        """
        模拟完整会议
        """
        simulation = MeetingSimulation(issue_title, issue_type)
        
        for round_num in range(1, num_rounds + 1):
            round_speeches = []
            
            for persona in personas:
                try:
                    speech = self.adaptor.generate_speech_v2_compat(
                        persona, round_num, issue_title, issue_type
                    )
                    round_speeches.append(speech)
                except Exception as e:
                    print(f"Warning: Generation failed for {persona.name}: {e}")
            
            simulation.add_round(round_speeches)
        
        return simulation
    
    def test_incrementality(
        self,
        simulation: MeetingSimulation
    ) -> IncrementalityResult:
        """
        测试会议的增量性
        """
        issue_type = simulation.issue_type
        unresolved_points = self.ISSUE_UNRESOLVED_POINTS.get(
            issue_type, self.ISSUE_UNRESOLVED_POINTS["strategic"]
        )
        
        # 计算每轮的指标
        coverage_by_round = []
        overlap_by_round = []
        
        covered_so_far: Set[str] = set()
        prev_round_content: List[str] = []
        
        for round_num, speeches in enumerate(simulation.rounds, 1):
            round_content = [s.content for s in speeches]
            round_text = " ".join(round_content)
            
            # 计算未解决点覆盖
            newly_covered = set()
            for point in unresolved_points:
                if point in round_text and point not in covered_so_far:
                    newly_covered.add(point)
            
            covered_so_far.update(newly_covered)
            coverage_rate = len(covered_so_far) / len(unresolved_points)
            coverage_by_round.append(coverage_rate)
            
            # 计算套话重叠
            if prev_round_content:
                overlap = self._calculate_overlap(round_content, prev_round_content)
            else:
                overlap = 0.0
            overlap_by_round.append(overlap)
            
            prev_round_content = round_content
        
        # 计算整体指标
        if len(coverage_by_round) >= 2:
            coverage_gain = coverage_by_round[-1] - coverage_by_round[0]
        else:
            coverage_gain = 0.0
        
        if len(overlap_by_round) >= 2:
            overlap_reduction = overlap_by_round[0] - overlap_by_round[-1]
        else:
            overlap_reduction = 0.0
        
        # 新贡献率 = 新增覆盖点数 / 总轮数
        novel_rate = len(covered_so_far) / max(1, len(simulation.rounds))
        
        # 判定门槛
        passed_coverage = coverage_gain >= 0.30  # +30%
        passed_overlap = overlap_reduction >= 0.40 or overlap_by_round[-1] <= 0.30  # -40%
        passed = passed_coverage and passed_overlap
        
        return IncrementalityResult(
            unresolved_coverage_gain=coverage_gain,
            boilerplate_overlap_reduction=overlap_reduction,
            novel_contribution_rate=novel_rate,
            round_by_round_coverage=coverage_by_round,
            round_by_round_overlap=overlap_by_round,
            passed_coverage=passed_coverage,
            passed_overlap=passed_overlap,
            passed=passed
        )
    
    def _calculate_overlap(
        self,
        current: List[str],
        previous: List[str]
    ) -> float:
        """计算两轮发言的套话重叠度"""
        
        def extract_boilerplate(text: str) -> Set[str]:
            """提取可能的套话片段"""
            matches = set()
            for pattern in self.BOILERPLATE_PATTERNS:
                for match in re.finditer(pattern, text):
                    matches.add(match.group(0))
            return matches
        
        current_text = " ".join(current)
        previous_text = " ".join(previous)
        
        current_boilerplate = extract_boilerplate(current_text)
        previous_boilerplate = extract_boilerplate(previous_text)
        
        if not current_boilerplate:
            return 0.0
        
        overlap = current_boilerplate & previous_boilerplate
        return len(overlap) / len(current_boilerplate)
    
    def generate_report(self, result: IncrementalityResult) -> str:
        """生成可读报告"""
        lines = [
            "=" * 60,
            "增量性测试报告",
            "=" * 60,
            "",
            "关键指标:",
            f"  未解决点覆盖增益: {result.unresolved_coverage_gain:+.1%} "
            f"({'✅ PASS' if result.passed_coverage else '❌ FAIL'} 门槛: +30%)",
            f"  套话重叠减少: {result.boilerplate_overlap_reduction:+.1%} "
            f"({'✅ PASS' if result.passed_overlap else '❌ FAIL'} 门槛: -40%)",
            f"  新贡献率: {result.novel_contribution_rate:.1%}",
            "",
            "轮次详情:",
        ]
        
        for i, (cov, over) in enumerate(zip(
            result.round_by_round_coverage,
            result.round_by_round_overlap
        ), 1):
            lines.append(f"  Round {i}: 覆盖 {cov:.1%}, 重叠 {over:.1%}")
        
        lines.extend([
            "",
            f"总体判定: {'✅ PASS - 可推广' if result.passed else '❌ FAIL - 需重调'}",
            "=" * 60
        ])
        
        return "\n".join(lines)


def run_default_test() -> IncrementalityResult:
    """运行默认测试"""
    
    # 测试人格
    test_personas = [
        ExtendedPersonaActivation(
            "00001", "鬼谷子",
            ["strategist", "tactician"],
            ["high"], ["all"]
        ),
        ExtendedPersonaActivation(
            "00002", "苏秦",
            ["diplomat", "negotiator"],
            ["high"], ["alliance"]
        ),
        ExtendedPersonaActivation(
            "00008", "韩非",
            ["legalist", "statesman"],
            ["high"], ["law"]
        ),
    ]
    
    tester = IncrementalityTester()
    
    # 模拟会议
    simulation = tester.simulate_meeting(
        test_personas,
        "测试议题：如何应对外部联盟压力",
        "diplomatic",
        num_rounds=3
    )
    
    # 测试增量性
    result = tester.test_incrementality(simulation)
    
    print(tester.generate_report(result))
    
    return result


if __name__ == "__main__":
    result = run_default_test()
    exit(0 if result.passed else 1)
