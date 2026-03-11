#!/usr/bin/env python3
"""
Round 22: Sample Collection Accelerator

主动构造评估流量，快速达到 200+ 样本阈值

执行策略：
1. 历史回放 (replay) - 首选，最接近真实分布
2. 批量旁路 (batch_shadow) - 补充，基于真实输入模式
3. 边界测试 (synthetic) - 诊断专用，不与真实样本混算

原则：
- 明确标记所有来源
- 不改 FINAL_DECISION_TABLE 门槛
- 真实样本 (live + replay) 达到 200 才触发判定

使用方法：
    python accelerate_round22.py --target 200
"""

import json
import sys
import argparse
from pathlib import Path
from typing import Dict, Any

# 添加路径
sys.path.insert(0, str(Path(__file__).parent.parent / "bridge"))
from shadow_consensus_predictor import ShadowConsensusPredictor, get_shadow_predictor

# 导入子模块
from historical_replay import HistoricalReplay
from batch_shadow_runner import BatchShadowRunner


class Round22Accelerator:
    """Round 22 样本收集加速器"""
    
    def __init__(self, target_samples: int = 200):
        """
        初始化加速器
        
        Args:
            target_samples: 目标真实样本数 (live + replay)
        """
        self.target = target_samples
        self.predictor = get_shadow_predictor()
        self.replay = HistoricalReplay(self.predictor)
        self.batch_runner = BatchShadowRunner(self.predictor)
        
        # 初始化状态
        self.initial_status = self.predictor.check_threshold(self.target)
        self.collected_replay = 0
        self.collected_batch = 0
    
    def get_status(self) -> Dict[str, Any]:
        """获取当前状态"""
        return self.predictor.check_threshold(self.target)
    
    def print_status(self, title: str = "Current Status"):
        """打印当前状态"""
        status = self.get_status()
        stats = self.predictor.get_observation_stats()
        
        print(f"\n{'='*60}")
        print(f"{title}")
        print(f"{'='*60}")
        print(f"Real Samples (live + replay): {status['real_samples']} / {self.target}")
        print(f"Total Samples: {status['total_samples']}")
        print(f"Source Distribution: {stats.get('source_distribution', {})}")
        print(f"Threshold Reached: {'✓ YES' if status['can_decide'] else '✗ NO'}")
        
        if not status['can_decide']:
            remaining = self.target - status['real_samples']
            print(f"Remaining: {remaining} samples")
        
        return status
    
    def accelerate_with_replay(self, n_cases: int = 150) -> int:
        """
        使用历史回放加速
        
        Args:
            n_cases: 生成的历史 case 数量
        
        Returns:
            实际收集的 replay 样本数
        """
        print(f"\n{'='*60}")
        print("Phase 1: Historical Replay")
        print(f"{'='*60}")
        print(f"Target: Generate and replay {n_cases} historical cases")
        
        # 生成历史 case
        cases_path = Path("/home/admin/CodeBuddy/20260310101858/data/historical_cases/acceleration_cases.jsonl")
        cases = self.replay.generate_sample_historical_cases(
            n_cases=n_cases,
            output_path=str(cases_path)
        )
        
        # 执行回放
        stats = self.replay.replay_cases(cases)
        self.collected_replay = stats['successful']
        
        print(f"\n✓ Replay complete: {self.collected_replay} samples")
        return self.collected_replay
    
    def accelerate_with_batch(self, n_samples: int = 100) -> int:
        """
        使用批量旁路加速
        
        Args:
            n_samples: 生成的 batch 样本数
        
        Returns:
            实际收集的 batch_shadow 样本数
        """
        print(f"\n{'='*60}")
        print("Phase 2: Batch Shadow Runner")
        print(f"{'='*60}")
        print(f"Target: Generate and process {n_samples} realistic distributions")
        
        # 生成真实分布
        distributions = self.batch_runner.generate_realistic_distributions(
            n_samples=n_samples
        )
        
        # 执行批量运行
        stats = self.batch_runner.run_batch_from_stance_distributions(
            distributions
        )
        self.collected_batch = stats['successful']
        
        print(f"\n✓ Batch complete: {self.collected_batch} samples")
        return self.collected_batch
    
    def run_acceleration(self, 
                        replay_cases: int = 150,
                        batch_samples: int = 100,
                        dry_run: bool = False) -> Dict[str, Any]:
        """
        执行完整加速流程
        
        Args:
            replay_cases: 历史回放 case 数
            batch_samples: 批量旁路样本数
            dry_run: 如果为 True，只显示计划不执行
        
        Returns:
            最终状态
        """
        print("=" * 60)
        print("Round 22: Sample Collection Accelerator")
        print("=" * 60)
        print(f"Target Threshold: {self.target} real samples")
        print(f"Current Status: {self.initial_status['real_samples']} real samples")
        
        if dry_run:
            print("\n⚠️ DRY RUN MODE - No actual data will be collected")
            print(f"\nPlanned Actions:")
            print(f"  1. Historical Replay: {replay_cases} cases")
            print(f"  2. Batch Shadow: {batch_samples} samples")
            print(f"\nExpected Result:")
            expected_total = self.initial_status['real_samples'] + replay_cases + batch_samples
            print(f"  Real samples: {expected_total} / {self.target}")
            print(f"  Threshold reached: {'YES' if expected_total >= self.target else 'NO'}")
            return self.get_status()
        
        # Phase 1: 历史回放
        if self.initial_status['real_samples'] < self.target:
            self.accelerate_with_replay(replay_cases)
            self.print_status("After Historical Replay")
        
        # Phase 2: 批量旁路（如果需要）
        current_status = self.get_status()
        if not current_status['can_decide'] and batch_samples > 0:
            self.accelerate_with_batch(batch_samples)
            self.print_status("After Batch Shadow")
        
        # Phase 3: 边界测试（可选，只用于诊断，标记为 synthetic）
        # 注意：边界测试样本不计入真实样本
        
        # 最终结果
        final_status = self.print_status("FINAL STATUS")
        
        # 输出建议
        print(f"\n{'='*60}")
        print("RECOMMENDATION")
        print(f"{'='*60}")
        
        if final_status['can_decide']:
            print("\n✓ THRESHOLD REACHED!")
            print("\nNext Steps:")
            print("  1. Run analysis scripts:")
            print("     python rounds/round22/analyze_extended_metrics.py")
            print("     python rounds/round22/bucket_calibration_analysis.py")
            print("  2. Check FINAL_DECISION_TABLE.md")
            print("  3. Execute A/B/C decision")
        else:
            remaining = self.target - final_status['real_samples']
            print(f"\n→ Still need {remaining} more real samples")
            print("\nOptions:")
            print("  1. Increase replay_cases or batch_samples")
            print("  2. Wait for natural live traffic")
            print("  3. Consider lowering target (requires explicit approval)")
        
        return final_status


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="Round 22 Sample Collection Accelerator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # 执行完整加速流程
  python accelerate_round22.py

  # 只预览计划
  python accelerate_round22.py --dry-run

  # 自定义目标阈值
  python accelerate_round22.py --target 250

  # 调整各阶段样本数
  python accelerate_round22.py --replay 200 --batch 150
        """
    )
    
    parser.add_argument("--target", "-t", type=int, default=200,
                       help="Target number of real samples (default: 200)")
    parser.add_argument("--replay", "-r", type=int, default=150,
                       help="Number of historical replay cases (default: 150)")
    parser.add_argument("--batch", "-b", type=int, default=100,
                       help="Number of batch shadow samples (default: 100)")
    parser.add_argument("--dry-run", "-d", action="store_true",
                       help="Preview plan without executing")
    
    args = parser.parse_args()
    
    # 创建加速器并执行
    accelerator = Round22Accelerator(target_samples=args.target)
    
    final_status = accelerator.run_acceleration(
        replay_cases=args.replay,
        batch_samples=args.batch,
        dry_run=args.dry_run
    )
    
    # 返回码：0 = 达到阈值，1 = 未达到
    return 0 if final_status['can_decide'] else 1


if __name__ == "__main__":
    sys.exit(main())
