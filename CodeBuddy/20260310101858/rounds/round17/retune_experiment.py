#!/usr/bin/env python3
"""
Retune Experiment Runner (Round 17.2)
定点调参实验执行器

执行流程:
1. 加载已有50样本
2. 应用新配置重跑评估
3. 对比基线指标
4. 输出通过/失败判定
"""

import json
import sys
import os
import argparse
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime

sys.path.insert(0, '/home/admin/CodeBuddy/20260310101858')
sys.path.insert(0, '/home/admin/CodeBuddy/20260310101858/bridge')


@dataclass
class GateConfig:
    """门控配置"""
    name: str
    deliberation_threshold: float
    review_threshold: float
    description: str


# 预定义配置
CONFIGS = {
    'baseline': GateConfig(
        name='baseline',
        deliberation_threshold=75.0,
        review_threshold=80.0,
        description='当前基线配置 (Round 16.2最佳)'
    ),
    'deliberation_70': GateConfig(
        name='deliberation_70',
        deliberation_threshold=70.0,
        review_threshold=80.0,
        description='下调 deliberation 门槛至70'
    ),
    'deliberation_65': GateConfig(
        name='deliberation_65',
        deliberation_threshold=65.0,
        review_threshold=80.0,
        description='下调 deliberation 门槛至65'
    ),
    'review_75': GateConfig(
        name='review_75',
        deliberation_threshold=75.0,
        review_threshold=75.0,
        description='下调 review 门槛至75'
    ),
    'both_relaxed': GateConfig(
        name='both_relaxed',
        deliberation_threshold=70.0,
        review_threshold=75.0,
        description='同时下调两个门槛'
    )
}


class RetuneExperiment:
    """调参实验"""
    
    def __init__(self, config: GateConfig, samples_path: str):
        self.config = config
        self.samples_path = samples_path
        self.samples: List[Dict] = []
        self.results: List[Dict] = []
        self.metrics: Dict = {}
        
        self._load_samples()
    
    def _load_samples(self):
        """加载样本数据"""
        with open(self.samples_path, 'r') as f:
            for line in f:
                if line.strip():
                    self.samples.append(json.loads(line))
        print(f"  加载样本: {len(self.samples)} 个")
    
    def _evaluate_sample(self, sample: Dict) -> Dict:
        """用新配置评估单个样本"""
        deliberation_score = sample.get('deliberation_score', 0)
        review_score = sample.get('review_score', 0)
        legacy_decision = sample.get('legacy_decision', '')
        
        # 新配置下的影子决策
        if deliberation_score >= self.config.deliberation_threshold and \
           review_score >= self.config.review_threshold:
            new_shadow_decision = 'approved'
        elif deliberation_score >= self.config.deliberation_threshold - 5:
            new_shadow_decision = 'conditional_approved'
        elif deliberation_score >= 50:
            new_shadow_decision = 'requires_deliberation'
        else:
            new_shadow_decision = 'rejected'
        
        # 判断是否一致
        decision_aligned = (legacy_decision == new_shadow_decision)
        
        # 判断是否误拦 (旧批新拦)
        false_block = (
            legacy_decision in ['approved', 'conditional_approved'] and
            new_shadow_decision in ['rejected', 'requires_deliberation']
        )
        
        # 判断是否高置信风险
        shadow_confidence = sample.get('shadow_confidence', 0)
        accepted_risk = (
            legacy_decision in ['approved', 'conditional_approved'] and
            new_shadow_decision in ['rejected', 'requires_deliberation'] and
            shadow_confidence > 0.8
        )
        
        return {
            'meeting_id': sample.get('meeting_id'),
            'source_type': sample.get('source_type'),
            'issue_type': sample.get('issue_type'),
            'legacy_decision': legacy_decision,
            'old_shadow_decision': sample.get('shadow_decision'),
            'new_shadow_decision': new_shadow_decision,
            'decision_aligned': decision_aligned,
            'false_block': false_block,
            'accepted_risk': accepted_risk,
            'deliberation_score': deliberation_score,
            'review_score': review_score,
            'improved': false_block and not sample.get('false_block_detected', False)
        }
    
    def run(self):
        """运行实验"""
        print(f"\n🧪 运行实验: {self.config.name}")
        print(f"   配置: deliberation={self.config.deliberation_threshold}, review={self.config.review_threshold}")
        
        self.results = []
        for sample in self.samples:
            result = self._evaluate_sample(sample)
            self.results.append(result)
        
        self._calculate_metrics()
    
    def _calculate_metrics(self):
        """计算指标"""
        total = len(self.results)
        if total == 0:
            return
        
        aligned = sum(1 for r in self.results if r['decision_aligned'])
        false_blocks = sum(1 for r in self.results if r['false_block'])
        accepted_risks = sum(1 for r in self.results if r['accepted_risk'])
        
        # Source 分桶
        source_stats = {}
        for r in self.results:
            source = r['source_type']
            if source not in source_stats:
                source_stats[source] = {'total': 0, 'false_block': 0}
            source_stats[source]['total'] += 1
            if r['false_block']:
                source_stats[source]['false_block'] += 1
        
        # Topic 分桶
        topic_stats = {}
        for r in self.results:
            topic = r['issue_type']
            if topic not in topic_stats:
                topic_stats[topic] = {'total': 0, 'disagreement': 0}
            topic_stats[topic]['total'] += 1
            if not r['decision_aligned']:
                topic_stats[topic]['disagreement'] += 1
        
        self.metrics = {
            'total_samples': total,
            'decision_alignment_rate': aligned / total,
            'false_block_rate': false_blocks / total,
            'accepted_risk_count': accepted_risks,
            'source_stats': {
                source: {
                    'total': stats['total'],
                    'false_block': stats['false_block'],
                    'false_block_rate': stats['false_block'] / stats['total'] if stats['total'] > 0 else 0
                }
                for source, stats in source_stats.items()
            },
            'topic_stats': {
                topic: {
                    'total': stats['total'],
                    'disagreement': stats['disagreement'],
                    'disagreement_rate': stats['disagreement'] / stats['total'] if stats['total'] > 0 else 0
                }
                for topic, stats in topic_stats.items()
            }
        }
    
    def evaluate_pass_fail(self, baseline_metrics: Dict) -> Dict:
        """评估通过/失败"""
        fb_improvement = baseline_metrics.get('false_block_rate', 0) - self.metrics['false_block_rate']
        alignment_improvement = self.metrics['decision_alignment_rate'] - baseline_metrics.get('decision_alignment_rate', 0)
        accepted_risk_change = self.metrics['accepted_risk_count'] - baseline_metrics.get('accepted_risk_count', 0)
        
        # 通过条件
        fb_pass = fb_improvement >= 0.05  # FB Rate 下降 ≥ 5%
        alignment_pass = alignment_improvement >= 0.10  # Alignment 上升 ≥ 10%
        risk_pass = accepted_risk_change <= 3  # Accepted-Risk 不恶化 > 3个
        
        passed = fb_pass and alignment_pass and risk_pass
        
        return {
            'passed': passed,
            'fb_improvement': fb_improvement,
            'alignment_improvement': alignment_improvement,
            'accepted_risk_change': accepted_risk_change,
            'fb_pass': fb_pass,
            'alignment_pass': alignment_pass,
            'risk_pass': risk_pass
        }
    
    def print_report(self, baseline_metrics: Optional[Dict] = None):
        """打印报告"""
        print("\n" + "="*70)
        print(f"📊 实验报告: {self.config.name}")
        print(f"   {self.config.description}")
        print("="*70)
        
        print(f"\n核心指标:")
        print(f"  决策一致率: {self.metrics['decision_alignment_rate']:.1%}")
        print(f"  False-Block Rate: {self.metrics['false_block_rate']:.1%}")
        print(f"  Accepted-Risk: {self.metrics['accepted_risk_count']}")
        
        if baseline_metrics:
            eval_result = self.evaluate_pass_fail(baseline_metrics)
            print(f"\n对比基线:")
            print(f"  FB Rate 改善: {eval_result['fb_improvement']:+.1%} {'✅' if eval_result['fb_pass'] else '❌'}")
            print(f"  Alignment 改善: {eval_result['alignment_improvement']:+.1%} {'✅' if eval_result['alignment_pass'] else '❌'}")
            print(f"  Accepted-Risk 变化: {eval_result['accepted_risk_change']:+d} {'✅' if eval_result['risk_pass'] else '❌'}")
            print(f"\n  实验结果: {'🟢 PASS' if eval_result['passed'] else '🔴 FAIL'}")
        
        print(f"\nSource 分桶:")
        for source, stats in self.metrics['source_stats'].items():
            print(f"  {source}: {stats['false_block']}/{stats['total']} ({stats['false_block_rate']:.1%})")
        
        print(f"\nTopic 分桶 (Top 5 分歧):")
        sorted_topics = sorted(
            self.metrics['topic_stats'].items(),
            key=lambda x: x[1]['disagreement_rate'],
            reverse=True
        )[:5]
        for topic, stats in sorted_topics:
            print(f"  {topic}: {stats['disagreement']}/{stats['total']} ({stats['disagreement_rate']:.1%})")
        
        print("="*70)
    
    def save_report(self, output_path: str):
        """保存报告"""
        report = {
            'experiment_id': f"EXP-{self.config.name}-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
            'config': {
                'name': self.config.name,
                'deliberation_threshold': self.config.deliberation_threshold,
                'review_threshold': self.config.review_threshold,
                'description': self.config.description
            },
            'metrics': self.metrics,
            'timestamp': datetime.now().isoformat()
        }
        
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"\n📄 报告已保存: {output_path}")


def main():
    parser = argparse.ArgumentParser(description='Retune Experiment Runner')
    parser.add_argument('--config', type=str, required=True, 
                        choices=list(CONFIGS.keys()),
                        help='实验配置名称')
    parser.add_argument('--samples', type=str, 
                        default='/home/admin/CodeBuddy/20260310101858/data/shadow/SHADOW-20260311-PROD_observations.jsonl',
                        help='样本文件路径')
    parser.add_argument('--baseline', type=str,
                        help='基线报告路径 (用于对比)')
    parser.add_argument('--output', type=str,
                        help='输出报告路径')
    
    args = parser.parse_args()
    
    print("="*70)
    print("🧪 Round 17.2 Retune Experiment")
    print("   定点调参实验")
    print("="*70)
    
    # 加载配置
    config = CONFIGS[args.config]
    
    # 创建实验
    experiment = RetuneExperiment(config, args.samples)
    
    # 运行实验
    experiment.run()
    
    # 加载基线 (如果提供)
    baseline_metrics = None
    if args.baseline and os.path.exists(args.baseline):
        with open(args.baseline, 'r') as f:
            baseline_report = json.load(f)
            baseline_metrics = baseline_report.get('metrics')
        print(f"\n📊 基线报告: {args.baseline}")
    
    # 打印报告
    experiment.print_report(baseline_metrics)
    
    # 保存报告
    if args.output:
        experiment.save_report(args.output)
    else:
        default_output = f"/home/admin/CodeBuddy/20260310101858/data/shadow/retune_{config.name}_report.json"
        experiment.save_report(default_output)


if __name__ == "__main__":
    main()
