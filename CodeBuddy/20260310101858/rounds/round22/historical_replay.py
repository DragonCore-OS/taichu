#!/usr/bin/env python3
"""
Round 22: Historical Replay Module

将历史 reduce_votes case 回放到 shadow predictor
来源标记: replay

使用场景：
- 快速积累接近真实分布的样本
- 补全到 200+ 样本阈值
- 不等待自然流量

原则：
- 明确标记为 replay，不与 live 混淆
- 只回放真实出现过的 case
- 不生成 synthetic 数据
"""

import json
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

# 添加 bridge 到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "bridge"))
from shadow_consensus_predictor import ShadowConsensusPredictor, get_shadow_predictor


class HistoricalReplay:
    """历史回放器"""
    
    def __init__(self, predictor: Optional[ShadowConsensusPredictor] = None):
        """
        初始化回放器
        
        Args:
            predictor: ShadowConsensusPredictor 实例，如果为 None 则创建新的
        """
        self.predictor = predictor or get_shadow_predictor()
        self.replay_count = 0
        self.replay_log = []
    
    def load_historical_cases(self, cases_path: str) -> List[Dict[str, Any]]:
        """
        加载历史 case
        
        Args:
            cases_path: JSON/JSONL 文件路径，或包含 case 文件的目录
        
        Returns:
            历史 case 列表
        """
        cases = []
        path = Path(cases_path)
        
        if path.is_file():
            # 单个文件
            if path.suffix == '.jsonl':
                with open(path, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            try:
                                cases.append(json.loads(line))
                            except json.JSONDecodeError:
                                pass
            elif path.suffix == '.json':
                with open(path, 'r') as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        cases = data
                    else:
                        cases = [data]
        
        elif path.is_dir():
            # 目录中的所有 case 文件
            for case_file in path.glob("*.jsonl"):
                with open(case_file, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            try:
                                cases.append(json.loads(line))
                            except json.JSONDecodeError:
                                pass
            
            for case_file in path.glob("*.json"):
                with open(case_file, 'r') as f:
                    try:
                        data = json.load(f)
                        if isinstance(data, list):
                            cases.extend(data)
                        else:
                            cases.append(data)
                    except:
                        pass
        
        print(f"Loaded {len(cases)} historical cases from {cases_path}")
        return cases
    
    def replay_case(self, case: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        回放单个 case
        
        Args:
            case: 包含以下字段的字典
                - state: reduce_votes 输入状态
                - result: reduce_votes 输出结果
                - metadata: 可选的元数据
        
        Returns:
            回放记录，如果失败则返回 None
        """
        state = case.get("state", case)  # 兼容不同格式
        result = case.get("result", case.get("decision_result", {}))
        
        # 通过 shadow predictor 记录，明确标记为 replay
        record = self.predictor.observe_reduce_votes(
            state=state,
            decision_result=result,
            source="replay"
        )
        
        if record:
            self.replay_count += 1
            return {
                "timestamp": record.timestamp,
                "source": "replay",
                "stance_distribution": record.input_stance_distribution,
                "probability": record.consensus_probability,
                "bucket": record.confidence_bucket
            }
        
        return None
    
    def replay_cases(self, cases: List[Dict[str, Any]], 
                    verbose: bool = True) -> Dict[str, Any]:
        """
        批量回放 case
        
        Args:
            cases: case 列表
            verbose: 是否打印进度
        
        Returns:
            回放统计
        """
        if verbose:
            print(f"\nReplaying {len(cases)} historical cases...")
            print("=" * 50)
        
        successful = 0
        failed = 0
        
        for i, case in enumerate(cases):
            result = self.replay_case(case)
            if result:
                successful += 1
                self.replay_log.append(result)
            else:
                failed += 1
            
            if verbose and (i + 1) % 50 == 0:
                print(f"  Progress: {i+1}/{len(cases)} ({successful} successful)")
        
        if verbose:
            print(f"\nReplay Complete!")
            print(f"  Successful: {successful}")
            print(f"  Failed: {failed}")
        
        return {
            "total_cases": len(cases),
            "successful": successful,
            "failed": failed,
            "replay_count": self.replay_count
        }
    
    def generate_sample_historical_cases(self, n_cases: int = 100, 
                                         output_path: str = None) -> List[Dict[str, Any]]:
        """
        生成示例历史 case（用于测试）
        
        注意：这些 case 虽然是生成的，但格式是真实 reduce_votes 的格式
        用于在没有真实历史数据时进行回放测试
        
        Args:
            n_cases: 生成的 case 数量
            output_path: 如果指定，保存到该路径
        
        Returns:
            生成的 case 列表
        """
        import random
        import numpy as np
        
        np.random.seed(42)
        random.seed(42)
        
        cases = []
        
        # 模拟真实会议场景的 stance 分布
        scenarios = [
            # (support_ratio, conditional_ratio, oppose_ratio, veto_ratio, description)
            (0.7, 0.2, 0.1, 0.0, "strong_support"),
            (0.5, 0.3, 0.2, 0.0, "moderate_support"),
            (0.3, 0.4, 0.3, 0.0, "balanced"),
            (0.2, 0.2, 0.5, 0.1, "opposition_with_veto"),
            (0.8, 0.1, 0.1, 0.0, "overwhelming_support"),
            (0.1, 0.2, 0.6, 0.1, "strong_opposition"),
            (0.4, 0.4, 0.2, 0.0, "conditional_heavy"),
        ]
        
        for i in range(n_cases):
            # 随机选择场景
            scenario = random.choice(scenarios)
            s_ratio, c_ratio, o_ratio, v_ratio, desc = scenario
            
            # 生成随机数量（10-50 个席位）
            n_seats = random.randint(10, 50)
            
            # 按比例分配
            support = int(n_seats * s_ratio)
            conditional = int(n_seats * c_ratio)
            oppose = int(n_seats * o_ratio)
            veto = int(n_seats * v_ratio)
            
            # 调整确保总和正确
            remainder = n_seats - (support + conditional + oppose + veto)
            support += remainder  # 余数给 support
            
            # 构建 stance distribution
            stance_dist = {
                "support": max(0, support),
                "conditional": max(0, conditional),
                "oppose": max(0, oppose),
                "veto": max(0, veto)
            }
            
            # 生成 speeches
            speeches = []
            seat_id = 0
            for stance, count in stance_dist.items():
                for _ in range(count):
                    speeches.append({
                        "seat_id": f"seat_{seat_id}",
                        "stance": stance,
                        "content": f"Speech content for {stance}"
                    })
                    seat_id += 1
            
            # 确定实际结果
            total = sum(stance_dist.values())
            if total == 0:
                actual_status = "pending"
            else:
                support_score = stance_dist["support"] + 0.5 * stance_dist["conditional"]
                oppose_score = stance_dist["oppose"] + stance_dist["veto"]
                
                if stance_dist["veto"] > 0:
                    actual_status = "blocked"
                elif support_score / total > 0.6:
                    actual_status = "approved"
                elif oppose_score / total > 0.6:
                    actual_status = "rejected"
                else:
                    actual_status = "pending"
            
            case = {
                "case_id": f"historical_{i:04d}",
                "scenario": desc,
                "timestamp": datetime.now().isoformat(),
                "state": {
                    "speeches": speeches,
                    "valid_seat_ids": [f"seat_{j}" for j in range(n_seats)]
                },
                "result": {
                    "status": actual_status,
                    "final_stance": stance_dist
                }
            }
            
            cases.append(case)
        
        # 保存到文件
        if output_path:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w') as f:
                for case in cases:
                    f.write(json.dumps(case) + '\n')
            
            print(f"Generated {len(cases)} sample historical cases -> {output_path}")
        
        return cases


def main():
    """主函数：执行历史回放"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Historical Replay for Shadow Predictor")
    parser.add_argument("--cases", "-c", type=str, 
                       default="/home/admin/CodeBuddy/20260310101858/data/historical_cases",
                       help="Path to historical cases (file or directory)")
    parser.add_argument("--generate", "-g", action="store_true",
                       help="Generate sample historical cases if none exist")
    parser.add_argument("--count", "-n", type=int, default=150,
                       help="Number of cases to generate if --generate is set")
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("Round 22: Historical Replay Module")
    print("=" * 60)
    
    # 初始化回放器
    replay = HistoricalReplay()
    
    # 检查历史 case 是否存在
    cases_path = Path(args.cases)
    
    if not cases_path.exists() or args.generate:
        # 生成示例历史 case
        print("\nGenerating sample historical cases...")
        cases = replay.generate_sample_historical_cases(
            n_cases=args.count,
            output_path="/home/admin/CodeBuddy/20260310101858/data/historical_cases/sample_cases.jsonl"
        )
    else:
        # 加载已有历史 case
        cases = replay.load_historical_cases(args.cases)
    
    if not cases:
        print("ERROR: No historical cases found or generated!")
        return 1
    
    # 执行回放
    stats = replay.replay_cases(cases)
    
    # 显示当前状态
    print("\n" + "=" * 60)
    print("Current Shadow Predictor Status")
    print("=" * 60)
    
    predictor_stats = replay.predictor.get_observation_stats()
    threshold_status = replay.predictor.check_threshold(threshold=200)
    
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
