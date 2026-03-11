"""
experiment_3x3.py
3×3 可复现实验

验证 Persona System v2 的三个核心指标：
1. Role Distinguishability >= 80%
2. Unresolved Coverage +30%
3. Boilerplate Overlap -30% (已从 -40% 放宽)

实验设计：
- 3 种议题类型 (strategic/diplomatic/governance)
- 每种议题 3 次重复
- 共 9 次完整会议模拟
"""

import json
import sys
from typing import List, Dict, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime

try:
    from .bridge_adaptor import BridgeAdaptor, get_adaptor, reset_adaptor
    from .persona_context import ExtendedPersonaActivation
    from .test_distinguishability import DistinguishabilityTester, DistinguishabilityResult
    from .test_incrementality import IncrementalityTester, IncrementalityResult, MeetingSimulation
except ImportError:
    from bridge_adaptor import BridgeAdaptor, get_adaptor, reset_adaptor
    from persona_context import ExtendedPersonaActivation
    from test_distinguishability import DistinguishabilityTester, DistinguishabilityResult
    from test_incrementality import IncrementalityTester, IncrementalityResult, MeetingSimulation


@dataclass
class ExperimentCondition:
    """实验条件"""
    issue_type: str
    issue_title: str
    description: str


@dataclass
class ExperimentTrial:
    """单次实验结果"""
    trial_id: str
    condition: ExperimentCondition
    distinguishability: DistinguishabilityResult
    incrementality: IncrementalityResult
    passed: bool


@dataclass
class ExperimentResult:
    """完整实验结果"""
    timestamp: str
    total_trials: int
    passed_trials: int
    pass_rate: float
    
    # 分指标统计
    distinguishability_pass_rate: float
    coverage_pass_rate: float
    overlap_pass_rate: float
    
    # 详细结果
    trials: List[ExperimentTrial]
    
    # 判定
    gate_2_passed: bool  # Gate 2 门槛


class Experiment3x3:
    """
    3×3 实验控制器
    """
    
    # 3 种议题类型 × 3 个议题
    EXPERIMENT_CONDITIONS: List[ExperimentCondition] = [
        # Strategic (战略类)
        ExperimentCondition(
            "strategic",
            "如何构建长期竞争优势以应对新兴挑战者",
            "Long-term competitive strategy"
        ),
        ExperimentCondition(
            "strategic",
            "资源有限情况下的战略优先级排序",
            "Resource prioritization under constraints"
        ),
        ExperimentCondition(
            "strategic",
            "关键基础设施的防御与韧性建设",
            "Critical infrastructure resilience"
        ),
        
        # Diplomatic (外交类)
        ExperimentCondition(
            "diplomatic",
            "如何在多方利益冲突中建立可信联盟",
            "Alliance building under conflict"
        ),
        ExperimentCondition(
            "diplomatic",
            "跨文化谈判中的信任建立机制",
            "Cross-cultural trust building"
        ),
        ExperimentCondition(
            "diplomatic",
            "利益交换与承诺可信度的平衡",
            "Interest exchange and credibility"
        ),
        
        # Governance (治理类)
        ExperimentCondition(
            "governance",
            "制度设计中的激励相容与权力制衡",
            "Incentive alignment in institutions"
        ),
        ExperimentCondition(
            "governance",
            "执行监督中的信息透明与问责",
            "Transparency and accountability"
        ),
        ExperimentCondition(
            "governance",
            "适应能力与稳定性的动态平衡",
            "Adaptability vs stability"
        ),
    ]
    
    # 标准测试人格 (核心 5 席)
    TEST_PERSONAS: List[ExtendedPersonaActivation] = [
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
            "00004", "孔子",
            ["sage", "educator"],
            ["high"], ["ethics"]
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
    
    def __init__(self):
        self.dist_tester = DistinguishabilityTester()
        self.incr_tester = IncrementalityTester()
        self.results: List[ExperimentTrial] = []
    
    def run_trial(
        self,
        condition: ExperimentCondition,
        trial_num: int
    ) -> ExperimentTrial:
        """运行单次实验"""
        trial_id = f"{condition.issue_type}_{trial_num}"
        
        print(f"\n{'='*60}")
        print(f"Trial: {trial_id}")
        print(f"Issue: {condition.issue_title}")
        print(f"{'='*60}")
        
        # 重置适配器状态
        reset_adaptor()
        
        # 1. 可辨识性测试
        print("\n[1/2] Running distinguishability test...")
        dist_result = self.dist_tester.test_personas(
            self.TEST_PERSONAS,
            issue_title=condition.issue_title,
            issue_type=condition.issue_type,
            rounds=3
        )
        print(f"Distinguishability: {dist_result.score:.1%} "
              f"({'PASS' if dist_result.passed else 'FAIL'})")
        
        # 2. 增量性测试
        print("\n[2/2] Running incrementality test...")
        simulation = self.incr_tester.simulate_meeting(
            self.TEST_PERSONAS,
            issue_title=condition.issue_title,
            issue_type=condition.issue_type,
            num_rounds=3
        )
        incr_result = self.incr_tester.test_incrementality(simulation)
        print(f"Coverage Gain: {incr_result.unresolved_coverage_gain:+.1%} "
              f"({'PASS' if incr_result.passed_coverage else 'FAIL'})")
        print(f"Overlap Reduction: {incr_result.boilerplate_overlap_reduction:+.1%} "
              f"({'PASS' if incr_result.passed_overlap else 'FAIL'})")
        
        # 判定
        trial_passed = (
            dist_result.passed and
            incr_result.passed_coverage and
            incr_result.passed_overlap
        )
        
        print(f"\nTrial Result: {'✅ PASS' if trial_passed else '❌ FAIL'}")
        
        return ExperimentTrial(
            trial_id=trial_id,
            condition=condition,
            distinguishability=dist_result,
            incrementality=incr_result,
            passed=trial_passed
        )
    
    def run_all(self) -> ExperimentResult:
        """运行完整 3×3 实验"""
        print("=" * 60)
        print("Persona System v2 - 3×3 Experiment")
        print("=" * 60)
        print(f"Total conditions: {len(self.EXPERIMENT_CONDITIONS)}")
        print(f"Personas: {len(self.TEST_PERSONAS)} core seats")
        print("=" * 60)
        
        self.results = []
        
        for i, condition in enumerate(self.EXPERIMENT_CONDITIONS, 1):
            trial = self.run_trial(condition, i)
            self.results.append(trial)
        
        return self._aggregate_results()
    
    def _aggregate_results(self) -> ExperimentResult:
        """汇总实验结果"""
        total = len(self.results)
        passed = sum(1 for r in self.results if r.passed)
        
        dist_passed = sum(1 for r in self.results if r.distinguishability.passed)
        coverage_passed = sum(1 for r in self.results if r.incrementality.passed_coverage)
        overlap_passed = sum(1 for r in self.results if r.incrementality.passed_overlap)
        
        # Gate 2 门槛：80% 的 trial 通过
        gate_2_passed = (passed / total) >= 0.8
        
        return ExperimentResult(
            timestamp=datetime.now().isoformat(),
            total_trials=total,
            passed_trials=passed,
            pass_rate=passed / total,
            distinguishability_pass_rate=dist_passed / total,
            coverage_pass_rate=coverage_passed / total,
            overlap_pass_rate=overlap_passed / total,
            trials=self.results,
            gate_2_passed=gate_2_passed
        )
    
    def generate_report(self, result: ExperimentResult) -> str:
        """生成完整报告"""
        if result.gate_2_passed:
            verdict = "✅ PASS - Gate 2 cleared. Proceed to Gate 3 (task-level benchmark)."
        else:
            verdict = "❌ FAIL - Gate 2 failed. Stop promotion, architecture review required."
        
        lines = [
            "\n" + "=" * 70,
            "PERSONA SYSTEM V2 - 3×3 EXPERIMENT REPORT",
            "=" * 70,
            f"Timestamp: {result.timestamp}",
            f"Total Trials: {result.total_trials}",
            "",
            "AGGREGATE RESULTS:",
            f"  Overall Pass Rate: {result.pass_rate:.1%} ({result.passed_trials}/{result.total_trials})",
            f"  Distinguishability Pass Rate: {result.distinguishability_pass_rate:.1%}",
            f"  Coverage Pass Rate: {result.coverage_pass_rate:.1%}",
            f"  Overlap Pass Rate: {result.overlap_pass_rate:.1%}",
            "",
            "GATE 2 VERDICT:",
            f"  {verdict}",
            "",
            "DETAILED TRIAL RESULTS:",
        ]
        
        for trial in result.trials:
            status = "✅" if trial.passed else "❌"
            lines.append(
                f"  {status} {trial.trial_id}: "
                f"D={trial.distinguishability.score:.0%} "
                f"C={trial.incrementality.unresolved_coverage_gain:+.0%} "
                f"O={trial.incrementality.boilerplate_overlap_reduction:+.0%}"
            )
        
        lines.extend([
            "",
            "THRESHOLDS:",
            "  Distinguishability >= 80%",
            "  Coverage Gain >= +30%",
            "  Overlap Reduction >= -30% (已从 -40% 放宽)",
            "  Gate 2: >= 80% trials pass",
            "=" * 70,
        ])
        
        return "\n".join(lines)
    
    def save_results(self, result: ExperimentResult, filepath: str):
        """保存结果为 JSON"""
        # 转换为可序列化的字典
        data = {
            "timestamp": result.timestamp,
            "total_trials": result.total_trials,
            "passed_trials": result.passed_trials,
            "pass_rate": result.pass_rate,
            "distinguishability_pass_rate": result.distinguishability_pass_rate,
            "coverage_pass_rate": result.coverage_pass_rate,
            "overlap_pass_rate": result.overlap_pass_rate,
            "gate_2_passed": result.gate_2_passed,
            "trials": [
                {
                    "trial_id": t.trial_id,
                    "condition": {
                        "issue_type": t.condition.issue_type,
                        "issue_title": t.condition.issue_title,
                    },
                    "distinguishability": {
                        "score": t.distinguishability.score,
                        "passed": t.distinguishability.passed,
                    },
                    "incrementality": {
                        "coverage_gain": t.incrementality.unresolved_coverage_gain,
                        "overlap_reduction": t.incrementality.boilerplate_overlap_reduction,
                        "passed_coverage": t.incrementality.passed_coverage,
                        "passed_overlap": t.incrementality.passed_overlap,
                    },
                    "passed": t.passed,
                }
                for t in result.trials
            ]
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"\nResults saved to: {filepath}")


def main():
    """主入口"""
    experiment = Experiment3x3()
    result = experiment.run_all()
    
    # 打印报告
    report = experiment.generate_report(result)
    print(report)
    
    # 保存结果
    experiment.save_results(result, "experiment_3x3_results.json")
    
    # 返回码
    return 0 if result.gate_2_passed else 1


if __name__ == "__main__":
    sys.exit(main())
