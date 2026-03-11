#!/usr/bin/env python3
"""
False-Block Attribution Analysis (Round 17.1)
误拦归因分析框架

目标: 对19个潜在误拦案例进行逐案复核，生成分层报表
"""

import json
import os
import sys
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from collections import defaultdict

sys.path.insert(0, '/home/admin/CodeBuddy/20260310101858')
sys.path.insert(0, '/home/admin/CodeBuddy/20260310101858/bridge')

from bridge.shadow_deployment import ShadowDeploymentManager


class FalseBlockAttributionAnalyzer:
    """误拦归因分析器"""
    
    def __init__(self, shadow_id: str = "SHADOW-20260311-PROD"):
        self.shadow_id = shadow_id
        self.storage_dir = f"/home/admin/CodeBuddy/20260310101858/data/shadow"
        self.observations: List[Dict] = []
        self.false_block_cases: List[Dict] = []
        self.accepted_risk_cases: List[Dict] = []
        self._load_observations()
        self._load_cases()
    
    def _load_observations(self):
        """从 jsonl 文件加载观察数据"""
        filename = f"{self.storage_dir}/{self.shadow_id}_observations.jsonl"
        if os.path.exists(filename):
            with open(filename, 'r') as f:
                for line in f:
                    if line.strip():
                        self.observations.append(json.loads(line))
    
    def _load_cases(self):
        """加载需要分析的案例"""
        for obs in self.observations:
            if obs.get('false_block_detected'):
                self.false_block_cases.append(obs)
            if obs.get('accepted_risk_detected'):
                self.accepted_risk_cases.append(obs)
    
    def generate_source_type_report(self) -> Dict:
        """
        报表1: Source Type × False-Block
        按样本来源分桶统计误拦率
        """
        source_stats = defaultdict(lambda: {
            'total': 0,
            'false_block': 0,
            'false_block_rate': 0.0,
            'cases': []
        })
        
        for obs in self.observations:
            source = obs.get('source_type', 'unknown')
            source_stats[source]['total'] += 1
            
            if obs.get('false_block_detected'):
                source_stats[source]['false_block'] += 1
                source_stats[source]['cases'].append({
                    'meeting_id': obs.get('meeting_id'),
                    'legacy_decision': obs.get('legacy_decision'),
                    'shadow_decision': obs.get('shadow_decision'),
                    'deliberation_score': obs.get('deliberation_score'),
                    'review_score': obs.get('review_score'),
                    'shadow_confidence': obs.get('shadow_confidence')
                })
        
        # 计算比率
        for source in source_stats:
            total = source_stats[source]['total']
            if total > 0:
                source_stats[source]['false_block_rate'] = (
                    source_stats[source]['false_block'] / total
                )
        
        return dict(source_stats)
    
    def generate_topic_type_report(self) -> Dict:
        """
        报表2: Topic Type × Disagreement
        按议题类型分桶统计分歧率
        """
        topic_stats = defaultdict(lambda: {
            'total': 0,
            'disagreement': 0,
            'disagreement_rate': 0.0,
            'avg_deliberation_score': 0.0,
            'avg_review_score': 0.0,
            'cases': []
        })
        
        for obs in self.observations:
            topic = obs.get('issue_type', 'unknown')
            topic_stats[topic]['total'] += 1
            
            if not obs.get('decision_aligned', True):
                topic_stats[topic]['disagreement'] += 1
                topic_stats[topic]['cases'].append({
                    'meeting_id': obs.get('meeting_id'),
                    'source_type': obs.get('source_type'),
                    'risk_level': obs.get('risk_level'),
                    'legacy_decision': obs.get('legacy_decision'),
                    'shadow_decision': obs.get('shadow_decision')
                })
        
        # 计算比率
        for topic in topic_stats:
            total = topic_stats[topic]['total']
            if total > 0:
                topic_stats[topic]['disagreement_rate'] = (
                    topic_stats[topic]['disagreement'] / total
                )
        
        return dict(topic_stats)
    
    def generate_gate_stage_report(self) -> Dict:
        """
        报表3: Gate Stage × Block Reason
        按门控阶段分桶统计拦截原因
        """
        gate_stats = defaultdict(lambda: {
            'total_blocks': 0,
            'by_reason': defaultdict(int),
            'avg_score_gap': 0.0,
            'cases': []
        })
        
        for obs in self.observations:
            if not obs.get('decision_aligned', True):
                # 分析门控检查确定拦截阶段
                for check in obs.get('gate_checks', []):
                    check_name = check.get('check_name', 'unknown')
                    status = check.get('status', 'unknown')
                    
                    if status == 'fail':
                        gate_stats[check_name]['total_blocks'] += 1
                        gate_stats[check_name]['by_reason'][status] += 1
                        gate_stats[check_name]['cases'].append({
                            'meeting_id': obs.get('meeting_id'),
                            'source_type': obs.get('source_type'),
                            'issue_type': obs.get('issue_type'),
                            'score': check.get('score'),
                            'threshold': check.get('threshold')
                        })
        
        return dict(gate_stats)
    
    def create_accepted_risk_tracker(self) -> List[Dict]:
        """
        创建 Accepted-Risk 30天回查表
        """
        tracker = []
        
        for case in self.accepted_risk_cases:
            tracker.append({
                'case_id': case['meeting_id'],
                'observation_id': case['observation_id'],
                'old_decision': case['legacy_decision'],
                'shadow_decision': case['shadow_decision'],
                'shadow_confidence': case['shadow_confidence'],
                'deliberation_score': case['deliberation_score'],
                'review_score': case['review_score'],
                'source_type': case['source_type'],
                'issue_type': case['issue_type'],
                'risk_level': case['risk_level'],
                'observed_outcome_after_30d': None,  # 待填写
                'validated_risk': None,  # True=真风险, False=误拦
                'validation_notes': '',
                'created_at': case['timestamp'],
                'check_due_date': '2026-04-10'  # 30天后
            })
        
        return tracker
    
    def label_false_block_cases(self, labels: Dict[str, str]) -> Dict:
        """
        对误拦案例进行逐案复核标签
        
        Args:
            labels: {meeting_id: label}，label 可选:
                - 'true_block': 真拦截（正确拒绝）
                - 'false_block': 误拦（错误拒绝）
                - 'unresolved': 未决
        """
        results = {
            'true_block': [],
            'false_block': [],
            'unresolved': [],
            'summary': {
                'total_labeled': 0,
                'true_block_count': 0,
                'false_block_count': 0,
                'unresolved_count': 0
            }
        }
        
        for case in self.false_block_cases:
            meeting_id = case['meeting_id']
            label = labels.get(meeting_id, 'unresolved')
            
            results[label].append(case)
            results['summary']['total_labeled'] += 1
            results['summary'][f'{label}_count'] += 1
        
        return results
    
    def analyze_retune_condition(self) -> Dict:
        """
        分析是否需要 retune
        条件: 如果19个潜在误拦里，大多数都集中在同一个 gate stage 或同一类 source bucket
        """
        source_report = self.generate_source_type_report()
        gate_report = self.generate_gate_stage_report()
        
        # 检查是否集中在特定 source
        source_concentration = {}
        for source, stats in source_report.items():
            if stats['total'] > 0:
                concentration = stats['false_block'] / len(self.false_block_cases) if self.false_block_cases else 0
                source_concentration[source] = concentration
        
        # 检查是否集中在特定 gate stage
        gate_concentration = {}
        total_blocks = sum(g['total_blocks'] for g in gate_report.values())
        for gate, stats in gate_report.items():
            if total_blocks > 0:
                concentration = stats['total_blocks'] / total_blocks
                gate_concentration[gate] = concentration
        
        # 判断是否需要 retune
        max_source_conc = max(source_concentration.values()) if source_concentration else 0
        max_gate_conc = max(gate_concentration.values()) if gate_concentration else 0
        
        should_retune = max_source_conc > 0.6 or max_gate_conc > 0.6
        
        return {
            'should_retune': should_retune,
            'source_concentration': source_concentration,
            'gate_concentration': gate_concentration,
            'max_source_concentration': max_source_conc,
            'max_gate_concentration': max_gate_conc,
            'reason': (
                'False-blocks are concentrated in specific source/gate stage' 
                if should_retune 
                else 'False-blocks are evenly distributed'
            )
        }
    
    def generate_full_report(self) -> Dict:
        """生成完整归因报告"""
        report = {
            'report_id': f'FBA-{datetime.now().strftime("%Y%m%d-%H%M%S")}',
            'shadow_id': self.shadow_id,
            'generated_at': datetime.now().isoformat(),
            'summary': {
                'total_observations': len(self.observations),
                'false_block_cases': len(self.false_block_cases),
                'accepted_risk_cases': len(self.accepted_risk_cases),
                'false_block_rate': len(self.false_block_cases) / len(self.observations) if self.observations else 0
            },
            'reports': {
                'source_type': self.generate_source_type_report(),
                'topic_type': self.generate_topic_type_report(),
                'gate_stage': self.generate_gate_stage_report()
            },
            'accepted_risk_tracker': self.create_accepted_risk_tracker(),
            'retune_analysis': self.analyze_retune_condition()
        }
        
        return report
    
    def save_report(self, output_path: Optional[str] = None):
        """保存报告到文件"""
        report = self.generate_full_report()
        
        if output_path is None:
            output_path = f'/home/admin/CodeBuddy/20260310101858/data/shadow/{self.shadow_id}_attribution_report.json'
        
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"📄 归因报告已保存: {output_path}")
        return report


def print_report_summary(report: Dict):
    """打印报告摘要"""
    print("\n" + "="*70)
    print("📊 False-Block Attribution Report Summary")
    print("="*70)
    
    summary = report['summary']
    print(f"\n样本统计:")
    print(f"  总观察数: {summary['total_observations']}")
    print(f"  潜在误拦: {summary['false_block_cases']}")
    print(f"  高置信风险: {summary['accepted_risk_cases']}")
    print(f"  误拦率: {summary['false_block_rate']:.1%}")
    
    print(f"\n报表1 - Source Type × False-Block:")
    for source, stats in report['reports']['source_type'].items():
        print(f"  {source}: {stats['false_block']}/{stats['total']} ({stats['false_block_rate']:.1%})")
    
    print(f"\n报表2 - Topic Type × Disagreement (Top 5):")
    topics = sorted(
        report['reports']['topic_type'].items(),
        key=lambda x: x[1]['disagreement_rate'],
        reverse=True
    )[:5]
    for topic, stats in topics:
        print(f"  {topic}: {stats['disagreement']}/{stats['total']} ({stats['disagreement_rate']:.1%})")
    
    print(f"\n报表3 - Gate Stage × Block Reason:")
    for gate, stats in report['reports']['gate_stage'].items():
        print(f"  {gate}: {stats['total_blocks']} blocks")
    
    print(f"\nRetune 分析:")
    retune = report['retune_analysis']
    print(f"  建议 Retune: {'是' if retune['should_retune'] else '否'}")
    print(f"  最大 Source 集中度: {retune['max_source_concentration']:.1%}")
    print(f"  最大 Gate 集中度: {retune['max_gate_concentration']:.1%}")
    print(f"  原因: {retune['reason']}")
    
    print(f"\nAccepted-Risk 追踪表:")
    print(f"  待验证案例: {len(report['accepted_risk_tracker'])}")
    print(f"  验证截止日期: 2026-04-10")
    
    print("\n" + "="*70)


def main():
    """主入口"""
    print("="*70)
    print("🔍 False-Block Attribution Analysis")
    print("   误拦归因分析 - Round 17.1")
    print("="*70)
    print()
    
    # 创建分析器
    analyzer = FalseBlockAttributionAnalyzer()
    
    print(f"加载完成:")
    print(f"  - 总观察数: {len(analyzer.observations)}")
    print(f"  - 潜在误拦: {len(analyzer.false_block_cases)}")
    print(f"  - 高置信风险: {len(analyzer.accepted_risk_cases)}")
    print()
    
    # 生成并保存报告
    report = analyzer.save_report()
    
    # 打印摘要
    print_report_summary(report)
    
    print("\n✅ 归因分析完成")
    print("\n下一步建议:")
    print("  1. 对 19 个潜在误拦案例逐案复核标签")
    print("  2. 建立 17 个 Accepted-Risk 案例的回查追踪")
    print("  3. 根据集中度分析决定是否 retune")


if __name__ == "__main__":
    main()
