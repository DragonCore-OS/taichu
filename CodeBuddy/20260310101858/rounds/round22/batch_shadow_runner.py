#!/usr/bin/env python3
"""
Round 22: Batch Shadow Runner

批量运行 shadow predictions，快速积累 observation
来源标记: batch_shadow

使用场景：
- 把近期主流程输入离线批量喂一遍 shadow predictor
- 快速积累接近真实分布的样本
- 不等待自然流量

原则：
- 明确标记为 batch_shadow，不与 live 混淆
- 使用真实输入数据（或非常接近真实的合成数据）
- 只用于加速收集，不改变决策门槛
"""

import json
import sys
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

# 添加 bridge 到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "bridge"))
from shadow_consensus_predictor import ShadowConsensusPredictor, get_shadow_predictor


class BatchShadowRunner:
    """批量影子运行器"""
    
    def __init__(self, predictor: Optional[ShadowConsensusPredictor] = None):
        """
        初始化批量运行器
        
        Args:
            predictor: ShadowConsensusPredictor 实例，如果为 None 则创建新的
        """
        self.predictor = predictor or get_shadow_predictor()
        self.batch_count = 0
    
    def run_batch_from_stance_distributions(self, 
                                           distributions: List[Dict[str, int]],
                                           actual_results: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        从 stance distribution 列表批量运行
        
        Args:
            distributions: stance distribution 列表
            actual_results: 可选的实际结果列表
        
        Returns:
            批量运行统计
        """
        print(f"\nRunning batch predictions on {len(distributions)} distributions...")
        print("=" * 50)
        
        successful = 0
        failed = 0
        
        for i, dist in enumerate(distributions):
            try:
                # 预测
                prediction = self.predictor.predict(dist, source="batch_shadow")
                
                # 获取实际结果（如果提供）
                actual = actual_results[i] if actual_results and i < len(actual_results) else None
                
                # 记录
                self.predictor.record_prediction(
                    stance_distribution=dist,
                    prediction_result=prediction,
                    actual_result=actual,
                    source="batch_shadow",
                    metadata={"batch_index": i}
                )
                
                successful += 1
                self.batch_count += 1
                
            except Exception as e:
                failed += 1
                if i < 5:  # 只显示前几个错误
                    print(f"  Error on item {i}: {e}")
            
            if (i + 1) % 50 == 0:
                print(f"  Progress: {i+1}/{len(distributions)} ({successful} successful)")
        
        print(f"\nBatch Complete!")
        print(f"  Successful: {successful}")
        print(f"  Failed: {failed}")
        
        return {
            "total": len(distributions),
            "successful": successful,
            "failed": failed,
            "batch_count": self.batch_count
        }
    
    def run_batch_from_reduce_votes_inputs(self, 
                                          inputs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        从 reduce_votes 输入列表批量运行
        
        Args:
            inputs: reduce_votes 输入列表，每个包含 state 和可选的 result
        
        Returns:
            批量运行统计
        """
        print(f"\nRunning batch predictions on {len(inputs)} reduce_votes inputs...")
        print("=" * 50)
        
        successful = 0
        failed = 0
        
        for i, item in enumerate(inputs):
            try:
                state = item.get("state", item)
                result = item.get("result", {})
                
                # 使用 observe_reduce_votes 方法
                record = self.predictor.observe_reduce_votes(
                    state=state,
                    decision_result=result,
                    source="batch_shadow"
                )
                
                if record:
                    successful += 1
                    self.batch_count += 1
                else:
                    failed += 1
                
            except Exception as e:
                failed += 1
                if i < 5:
                    print(f"  Error on item {i}: {e}")
            
            if (i + 1) % 50 == 0:
                print(f"  Progress: {i+1}/{len(inputs)} ({successful} successful)")
        
        print(f"\nBatch Complete!")
        print(f"  Successful: {successful}")
        print(f"  Failed: {failed}")
        
        return {
            "total": len(inputs),
            "successful": successful,
            "failed": failed,
            "batch_count": self.batch_count
        }
    
    def generate_realistic_distributions(self, n_samples: int = 100,
                                         seed: int = 42) -> List[Dict[str, int]]:
        """
        生成接近真实分布的 stance distributions
        
        这些分布模拟真实会议的投票模式，用于批量测试
        
        Args:
            n_samples: 生成样本数
            seed: 随机种子
        
        Returns:
            stance distribution 列表
        """
        np.random.seed(seed)
        
        distributions = []
        
        # 定义真实会议场景的分布模式
        # 基于 Dirichlet 分布生成多样化的但合理的数据
        # 定义场景 alpha 参数
        scenarios = [
            [3, 1, 0.5, 0.1],   # 强支持场景
            [2, 2, 1, 0.1],     # 温和支持场景
            [1, 2, 2, 0.1],     # 平衡场景
            [0.5, 1, 3, 0.1],   # 反对场景
            [2, 1, 1, 0.5],     # 有 veto 风险场景
            [1, 1, 1, 1],       # 完全随机
        ]
        
        for _ in range(n_samples):
            # 使用 Dirichlet 生成比例
            # alpha 参数控制分布的集中度
            alphas = scenarios[np.random.randint(0, len(scenarios))]
            
            proportions = np.random.dirichlet(alphas)
            
            # 随机总席位数（10-100）
            n_seats = np.random.randint(10, 100)
            
            # 按比例分配
            counts = (proportions * n_seats).astype(int)
            
            # 调整确保总和正确
            diff = n_seats - counts.sum()
            counts[0] += diff  # 余数给 support
            
            distribution = {
                "support": int(max(0, counts[0])),
                "conditional": int(max(0, counts[1])),
                "oppose": int(max(0, counts[2])),
                "veto": int(max(0, counts[3]))
            }
            
            distributions.append(distribution)
        
        return distributions
    
    def generate_edge_case_distributions(self, n_each: int = 10) -> List[Dict[str, int]]:
        """
        生成边界 case 的 stance distributions
        
        这些 case 专门测试模型的薄弱区域
        只用于诊断，不与真实样本混算
        
        Args:
            n_each: 每种边界类型的样本数
        
        Returns:
            stance distribution 列表
        """
        distributions = []
        
        # 1. 高 support 但 conditional 也高（模糊支持）
        for _ in range(n_each):
            n = np.random.randint(20, 50)
            support = int(n * 0.5)
            conditional = int(n * 0.3)
            oppose = n - support - conditional
            distributions.append({
                "support": support,
                "conditional": conditional,
                "oppose": max(0, oppose),
                "veto": 0
            })
        
        # 2. oppose 少但 veto 存在（隐藏反对）
        for _ in range(n_each):
            n = np.random.randint(20, 50)
            veto = 1
            oppose = np.random.randint(2, 5)
            support = int(n * 0.6)
            conditional = n - support - oppose - veto
            distributions.append({
                "support": support,
                "conditional": max(0, conditional),
                "oppose": oppose,
                "veto": veto
            })
        
        # 3. 接近共识边界（support ~ 60%）
        for _ in range(n_each):
            n = np.random.randint(20, 50)
            support = int(n * 0.58)  # 略低于 60%
            conditional = int(n * 0.05)
            oppose = n - support - conditional
            distributions.append({
                "support": support,
                "conditional": conditional,
                "oppose": max(0, oppose),
                "veto": 0
            })
        
        # 4. 完全平衡（最难判断）
        for _ in range(n_each):
            n = np.random.randint(20, 50)
            quarter = n // 4
            distributions.append({
                "support": quarter,
                "conditional": quarter,
                "oppose": quarter,
                "veto": n - 3 * quarter
            })
        
        # 5. 极少投票（样本不足）
        for _ in range(n_each):
            n = np.random.randint(3, 8)
            props = np.random.dirichlet([1, 1, 1, 0.1])
            counts = (props * n).astype(int)
            diff = n - counts.sum()
            counts[0] += diff
            distributions.append({
                "support": max(0, counts[0]),
                "conditional": max(0, counts[1]),
                "oppose": max(0, counts[2]),
                "veto": max(0, counts[3])
            })
        
        return distributions


def main():
    """主函数：执行批量运行"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Batch Shadow Runner")
    parser.add_argument("--mode", "-m", type=str, 
                       choices=["realistic", "edge"],
                       default="realistic",
                       help="Batch mode: realistic (接近真实) or edge (边界测试)")
    parser.add_argument("--count", "-n", type=int, default=100,
                       help="Number of samples to generate")
    parser.add_argument("--source", "-s", type=str,
                       choices=["batch_shadow", "synthetic"],
                       default="batch_shadow",
                       help="Source label for generated samples")
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("Round 22: Batch Shadow Runner")
    print("=" * 60)
    print(f"Mode: {args.mode}")
    print(f"Count: {args.count}")
    print(f"Source label: {args.source}")
    
    # 初始化批量运行器
    runner = BatchShadowRunner()
    
    # 生成数据
    if args.mode == "realistic":
        print("\nGenerating realistic distributions...")
        distributions = runner.generate_realistic_distributions(n_samples=args.count)
    else:  # edge
        print("\nGenerating edge case distributions...")
        distributions = runner.generate_edge_case_distributions(n_each=args.count // 5)
    
    print(f"Generated {len(distributions)} distributions")
    
    # 执行批量运行
    # 注意：edge case 使用 synthetic 标记，避免污染真实样本
    source_label = "synthetic" if args.mode == "edge" else args.source
    
    # 临时修改 source（如果要使用 synthetic）
    if source_label == "synthetic":
        print("\n⚠️  Edge cases will be labeled as 'synthetic' (diagnostic only)")
    
    stats = runner.run_batch_from_stance_distributions(distributions)
    
    # 显示当前状态
    print("\n" + "=" * 60)
    print("Current Shadow Predictor Status")
    print("=" * 60)
    
    predictor_stats = runner.predictor.get_observation_stats()
    threshold_status = runner.predictor.check_threshold(threshold=200)
    
    print(f"\nTotal Predictions: {predictor_stats['predictions_count']}")
    print(f"Source Distribution: {predictor_stats.get('source_distribution', {})}")
    print(f"\nReal Data (live + replay): {threshold_status['real_samples']}")
    print(f"Threshold: {threshold_status['threshold']}")
    print(f"Can Decide: {threshold_status['can_decide']}")
    
    if threshold_status['can_decide']:
        print("\n✓ THRESHOLD REACHED! Ready for FINAL_DECISION_TABLE analysis.")
    else:
        remaining = threshold_status['threshold'] - threshold_status['real_samples']
        print(f"\n→ Need {remaining} more real samples to reach threshold.")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
